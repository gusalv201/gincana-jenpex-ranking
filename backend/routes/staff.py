import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlmodel import select

from dependencies import SessionDep, require_staff
from models import User
from schemas import (
    AdminParticipantListItem,
    ParticipantDetail,
    ParticipantRegistered,
    ParticipantUpdate,
)
from security import hash_password
from services.participants import list_participants, participant_progress

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
    dependencies=[Depends(require_staff)],
)


async def _get_participant(session, participant_id: int) -> User:
    participant = await session.get(User, participant_id)
    if participant is None or participant.role != "participant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    return participant


@router.get("/participants", response_model=list[AdminParticipantListItem])
async def read_participants(session: SessionDep) -> list[AdminParticipantListItem]:
    return await list_participants(session)


@router.get("/participants/{participant_id}", response_model=ParticipantDetail)
async def read_participant_detail(
    participant_id: int,
    session: SessionDep,
) -> ParticipantDetail:
    participant = await _get_participant(session, participant_id)
    progress = await participant_progress(session, participant_id)
    return ParticipantDetail(
        id=participant.id,
        username=participant.username,
        participant_code=participant.participant_code,
        is_active=participant.is_active,
        **progress,
    )


@router.patch("/participants/{participant_id}", response_model=ParticipantRegistered)
async def update_participant(
    participant_id: int,
    changes: ParticipantUpdate,
    session: SessionDep,
) -> ParticipantRegistered:
    """Corrige o nome do aluno e/ou gera um novo PIN para ele."""
    participant = await _get_participant(session, participant_id)

    if changes.username is not None:
        new_name = changes.username.strip()
        if not new_name:
            raise HTTPException(status_code=422, detail="Name cannot be empty")
        if new_name != participant.username:
            taken = await session.exec(
                select(User.id).where(User.username == new_name, User.id != participant.id)
            )
            if taken.first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already registered",
                )
            participant.username = new_name

    new_pin = None
    if changes.reset_password:
        new_pin = "".join(secrets.choice("0123456789") for _ in range(6))
        participant.password_hash = await run_in_threadpool(hash_password, new_pin)

    session.add(participant)
    await session.commit()
    return ParticipantRegistered(
        id=participant.id,
        username=participant.username,
        role="participant",
        participant_code=participant.participant_code,
        is_active=participant.is_active,
        password=new_pin,
    )
