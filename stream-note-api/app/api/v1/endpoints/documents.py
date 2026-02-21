import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.models.database import get_db
from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.models.user import User
from app.services.silent_analysis import enqueue_silent_analysis

router = APIRouter()

AUTO_SNAPSHOT_INTERVAL_SECONDS = 30.0
AUTO_SNAPSHOT_ABS_CHAR_DELTA = 120
AUTO_SNAPSHOT_RELATIVE_DELTA = 0.18
PRE_DESTRUCTIVE_DROP_RATIO = 0.4
PRE_DESTRUCTIVE_MIN_CHAR_COUNT = 80
RECOVERY_YESTERDAY_HOURS = 24


class DocumentResponse(BaseModel):
    id: str
    content: Dict[str, Any]
    created_at: str
    updated_at: str


class DocumentUpdate(BaseModel):
    content: Dict[str, Any]


class DocumentRecoveryCandidate(BaseModel):
    id: str
    kind: str
    created_at: str
    char_count: int
    revision_no: int
    reason: str


class DocumentRecoveryCandidatesResponse(BaseModel):
    candidates: List[DocumentRecoveryCandidate]


class DocumentRecoveryRestoreResponse(BaseModel):
    document: DocumentResponse
    restored_revision_id: Optional[str]
    undo_revision_id: Optional[str]


def _to_document_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        content=doc.content,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _hash_document_content(content: Dict[str, Any]) -> str:
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _count_text_chars(node: Any) -> int:
    if isinstance(node, str):
        return len(node)
    if isinstance(node, list):
        return sum(_count_text_chars(item) for item in node)
    if isinstance(node, dict):
        total = 0
        text_value = node.get("text")
        if isinstance(text_value, str):
            total += len(text_value)
        content_value = node.get("content")
        if isinstance(content_value, (dict, list, str)):
            total += _count_text_chars(content_value)
        return total
    return 0


def _latest_revision(
    db: Session,
    *,
    user_id: str,
    document_id: str,
) -> Optional[DocumentRevision]:
    return (
        db.query(DocumentRevision)
        .filter(
            DocumentRevision.user_id == user_id,
            DocumentRevision.document_id == document_id,
        )
        .order_by(DocumentRevision.revision_no.desc())
        .first()
    )


def _create_revision(
    db: Session,
    *,
    user_id: str,
    document_id: str,
    content: Dict[str, Any],
    reason: str,
    restored_from_revision_id: Optional[str] = None,
    force: bool = False,
) -> Optional[DocumentRevision]:
    content_hash = _hash_document_content(content)
    char_count = _count_text_chars(content)
    latest = _latest_revision(db, user_id=user_id, document_id=document_id)

    if not force and latest is not None and latest.content_hash == content_hash:
        return None

    next_revision_no = 1 if latest is None else latest.revision_no + 1
    revision = DocumentRevision(
        user_id=user_id,
        document_id=document_id,
        revision_no=next_revision_no,
        content=content,
        content_hash=content_hash,
        char_count=char_count,
        reason=reason,
        restored_from_revision_id=restored_from_revision_id,
    )
    db.add(revision)
    db.flush()
    return revision


def _should_capture_pre_destructive(old_char_count: int, new_char_count: int) -> bool:
    if old_char_count < PRE_DESTRUCTIVE_MIN_CHAR_COUNT:
        return False
    if new_char_count >= old_char_count:
        return False
    dropped_ratio = (old_char_count - new_char_count) / old_char_count
    return dropped_ratio >= PRE_DESTRUCTIVE_DROP_RATIO


def _should_create_auto_snapshot(
    latest: Optional[DocumentRevision],
    *,
    new_hash: str,
    new_char_count: int,
    now: datetime,
) -> bool:
    if latest is None:
        return True
    if latest.content_hash == new_hash:
        return False

    elapsed_seconds = (now - latest.created_at).total_seconds()
    if elapsed_seconds >= AUTO_SNAPSHOT_INTERVAL_SECONDS:
        return True

    char_delta = abs(new_char_count - latest.char_count)
    if char_delta >= AUTO_SNAPSHOT_ABS_CHAR_DELTA:
        return True

    if latest.char_count > 0:
        relative_delta = char_delta / latest.char_count
        if relative_delta >= AUTO_SNAPSHOT_RELATIVE_DELTA:
            return True

    return False


def _to_recovery_candidate(
    *,
    revision: DocumentRevision,
    kind: str,
) -> DocumentRecoveryCandidate:
    return DocumentRecoveryCandidate(
        id=str(revision.id),
        kind=kind,
        created_at=revision.created_at.isoformat(),
        char_count=revision.char_count,
        revision_no=revision.revision_no,
        reason=revision.reason,
    )


@router.get("", response_model=DocumentResponse)
def get_document(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.user_id == str(current_user.id)).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_document_response(doc)


@router.post(
    "", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
def create_document(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Document).filter(Document.user_id == str(current_user.id)).first()
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return _to_document_response(existing)

    doc = Document(user_id=str(current_user.id))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _to_document_response(doc)


@router.put("/current", response_model=DocumentResponse)
def upsert_current_document(
    data: DocumentUpdate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)
    now = _utcnow_naive()
    new_content = data.content
    new_hash = _hash_document_content(new_content)
    new_char_count = _count_text_chars(new_content)

    doc = db.query(Document).filter(Document.user_id == user_id).first()
    if doc is None:
        doc = Document(user_id=user_id, content=new_content)
        db.add(doc)
        db.flush()
        _create_revision(
            db,
            user_id=user_id,
            document_id=str(doc.id),
            content=new_content,
            reason="auto_save",
            force=True,
        )
        db.commit()
        db.refresh(doc)
        enqueue_silent_analysis(
            document_id=str(doc.id),
            user_id=user_id,
            content=doc.content,
        )
        response.status_code = status.HTTP_201_CREATED
        return _to_document_response(doc)

    old_content: Dict[str, Any] = (
        doc.content if doc.content else {"type": "doc", "content": []}
    )
    old_hash = _hash_document_content(old_content)
    old_char_count = _count_text_chars(old_content)

    latest = _latest_revision(db, user_id=user_id, document_id=str(doc.id))
    should_capture_old = (
        old_hash != new_hash
        and _should_capture_pre_destructive(old_char_count, new_char_count)
        and (latest is None or latest.content_hash != old_hash)
    )
    if should_capture_old:
        _create_revision(
            db,
            user_id=user_id,
            document_id=str(doc.id),
            content=old_content,
            reason="pre_destructive",
            force=True,
        )

    latest_for_new = _latest_revision(db, user_id=user_id, document_id=str(doc.id))
    if _should_create_auto_snapshot(
        latest_for_new,
        new_hash=new_hash,
        new_char_count=new_char_count,
        now=now,
    ):
        _create_revision(
            db,
            user_id=user_id,
            document_id=str(doc.id),
            content=new_content,
            reason="auto_save",
            force=True,
        )

    doc.content = new_content
    db.commit()
    db.refresh(doc)
    enqueue_silent_analysis(
        document_id=str(doc.id),
        user_id=user_id,
        content=doc.content,
    )
    return _to_document_response(doc)


@router.get(
    "/recovery/candidates",
    response_model=DocumentRecoveryCandidatesResponse,
)
def get_recovery_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRecoveryCandidatesResponse:
    user_id = str(current_user.id)
    revisions = (
        db.query(DocumentRevision)
        .filter(DocumentRevision.user_id == user_id)
        .order_by(DocumentRevision.created_at.desc(), DocumentRevision.revision_no.desc())
        .limit(200)
        .all()
    )
    if len(revisions) == 0:
        return DocumentRecoveryCandidatesResponse(candidates=[])

    selected_ids = set()
    candidates: List[DocumentRecoveryCandidate] = []

    latest = revisions[0]
    candidates.append(_to_recovery_candidate(revision=latest, kind="latest"))
    selected_ids.add(str(latest.id))

    yesterday_cutoff = _utcnow_naive() - timedelta(hours=RECOVERY_YESTERDAY_HOURS)
    yesterday_revision = next(
        (
            revision
            for revision in revisions
            if revision.created_at <= yesterday_cutoff and str(revision.id) not in selected_ids
        ),
        None,
    )
    if yesterday_revision is not None:
        candidates.append(_to_recovery_candidate(revision=yesterday_revision, kind="yesterday"))
        selected_ids.add(str(yesterday_revision.id))

    stable_revision = next(
        (
            revision
            for revision in sorted(
                revisions,
                key=lambda item: (item.char_count, item.created_at),
                reverse=True,
            )
            if str(revision.id) not in selected_ids
        ),
        None,
    )
    if stable_revision is not None:
        candidates.append(_to_recovery_candidate(revision=stable_revision, kind="stable"))

    return DocumentRecoveryCandidatesResponse(candidates=candidates[:3])


@router.post(
    "/recovery/{revision_id}/restore",
    response_model=DocumentRecoveryRestoreResponse,
)
def restore_recovery_revision(
    revision_id: str,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentRecoveryRestoreResponse:
    user_id = str(current_user.id)
    target_revision = (
        db.query(DocumentRevision)
        .filter(
            DocumentRevision.id == revision_id,
            DocumentRevision.user_id == user_id,
        )
        .first()
    )
    if target_revision is None:
        raise HTTPException(status_code=404, detail="Recovery revision not found")

    doc = db.query(Document).filter(Document.user_id == user_id).first()
    if doc is None:
        doc = Document(user_id=user_id, content=target_revision.content)
        db.add(doc)
        db.flush()
        restored_revision = _create_revision(
            db,
            user_id=user_id,
            document_id=str(doc.id),
            content=target_revision.content,
            reason="restore",
            restored_from_revision_id=str(target_revision.id),
            force=True,
        )
        db.commit()
        db.refresh(doc)
        enqueue_silent_analysis(document_id=str(doc.id), user_id=user_id, content=doc.content)
        response.status_code = status.HTTP_201_CREATED
        return DocumentRecoveryRestoreResponse(
            document=_to_document_response(doc),
            restored_revision_id=(
                None if restored_revision is None else str(restored_revision.id)
            ),
            undo_revision_id=None,
        )

    current_content: Dict[str, Any] = (
        doc.content if doc.content else {"type": "doc", "content": []}
    )
    current_hash = _hash_document_content(current_content)
    target_hash = _hash_document_content(target_revision.content)

    undo_revision_id: Optional[str] = None
    restored_revision_id: Optional[str] = None
    if current_hash != target_hash:
        latest = _latest_revision(db, user_id=user_id, document_id=str(doc.id))
        if latest is not None and latest.content_hash == current_hash:
            undo_revision_id = str(latest.id)
        else:
            undo_revision = _create_revision(
                db,
                user_id=user_id,
                document_id=str(doc.id),
                content=current_content,
                reason="pre_restore",
                force=True,
            )
            if undo_revision is not None:
                undo_revision_id = str(undo_revision.id)

        doc.content = target_revision.content
        restored_revision = _create_revision(
            db,
            user_id=user_id,
            document_id=str(doc.id),
            content=target_revision.content,
            reason="restore",
            restored_from_revision_id=str(target_revision.id),
            force=False,
        )
        if restored_revision is not None:
            restored_revision_id = str(restored_revision.id)
        db.commit()
        db.refresh(doc)
        enqueue_silent_analysis(document_id=str(doc.id), user_id=user_id, content=doc.content)

    return DocumentRecoveryRestoreResponse(
        document=_to_document_response(doc),
        restored_revision_id=restored_revision_id,
        undo_revision_id=undo_revision_id,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == str(current_user.id),
        )
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.content = data.content
    db.commit()
    db.refresh(doc)
    return _to_document_response(doc)
