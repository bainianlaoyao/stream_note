from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.v1.deps import get_current_user
from app.models.database import get_db
from app.models.block import Block
from app.models.user import User

router = APIRouter()


class BlockResponse(BaseModel):
    id: str
    document_id: str
    content: str
    position: int
    is_task: bool
    is_completed: bool


class BlockUpdate(BaseModel):
    is_completed: bool


@router.get("", response_model=list[BlockResponse])
def get_blocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blocks = (
        db.query(Block)
        .filter(Block.user_id == str(current_user.id))
        .order_by(Block.position)
        .all()
    )
    return blocks


@router.get("/{block_id}", response_model=BlockResponse)
def get_block(
    block_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    block = (
        db.query(Block)
        .filter(Block.id == block_id, Block.user_id == str(current_user.id))
        .first()
    )
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return block


@router.patch("/{block_id}", response_model=BlockResponse)
def update_block(
    block_id: str,
    data: BlockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    block = (
        db.query(Block)
        .filter(Block.id == block_id, Block.user_id == str(current_user.id))
        .first()
    )
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")

    block.is_completed = data.is_completed
    db.commit()
    db.refresh(block)
    return block
