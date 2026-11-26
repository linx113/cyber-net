from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID

from app.database import get_db
from app.models import DeviceCommand
from app.schemas import CommandCreate, CommandResponse
from app.models import CommandOutbox


router = APIRouter()


@router.post(
    "/commands",
    response_model=CommandResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_command(
    payload: CommandCreate,
    db: Session = Depends(get_db)
):
    command = DeviceCommand(
        device_id=payload.device_id,
        command=payload.command,
        parameters=payload.parameters,
        status="pending"
    )

    try:
        db.add(command)
        db.flush()
        db.add(CommandOutbox(
            payload={
                "id": str(command.id),
                "device_id": command.device_id,
                "command": command.command,
                "parameters": command.parameters,
                "status": command.status,
                "created_at": command.created_at.isoformat()
            }
        ))
        db.commit()
        db.refresh(command)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save command"
        )

    return command


@router.get(
    "/commands/{command_id}",
    response_model=CommandResponse
)
def get_command(
    command_id: UUID,
    db: Session = Depends(get_db)
):
    command = db.query(DeviceCommand).filter(
        DeviceCommand.id == command_id
    ).first()

    if command is None:
        raise HTTPException(
            status_code=404,
            detail="Command not found"
        )

    return command


@router.get(
    "/commands",
    response_model=list[CommandResponse]
)
def get_commands(
    db: Session = Depends(get_db)
):
    return db.query(DeviceCommand).order_by(
        DeviceCommand.created_at.desc()
    ).limit(100).all()
