from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.document import Document

router = APIRouter()


class DocumentResponse(BaseModel):
    id: str
    content: Dict[str, Any]
    created_at: str
    updated_at: str


class DocumentUpdate(BaseModel):
    content: Dict[str, Any]


def _to_document_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=str(doc.id),
        content=doc.content,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
    )


@router.get("", response_model=DocumentResponse)
def get_document(db: Session = Depends(get_db)):
    doc = db.query(Document).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_document_response(doc)


@router.post(
    "", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
def create_document(response: Response, db: Session = Depends(get_db)):
    existing = db.query(Document).first()
    if existing is not None:
        response.status_code = status.HTTP_200_OK
        return _to_document_response(existing)

    doc = Document()
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _to_document_response(doc)


@router.put("/current", response_model=DocumentResponse)
def upsert_current_document(
    data: DocumentUpdate, response: Response, db: Session = Depends(get_db)
):
    doc = db.query(Document).first()
    if doc is None:
        doc = Document(content=data.content)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        response.status_code = status.HTTP_201_CREATED
        return _to_document_response(doc)

    doc.content = data.content
    db.commit()
    db.refresh(doc)
    return _to_document_response(doc)


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: str, data: DocumentUpdate, db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.content = data.content
    db.commit()
    db.refresh(doc)
    return _to_document_response(doc)
