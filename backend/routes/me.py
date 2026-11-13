from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from dependencies import CurrentUserDep, SessionDep, get_current_user
from models import Game, Score
from schemas import AuthenticatedUser, PersonalScore

router = APIRouter(
    prefix="/me",
    tags=["me"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=AuthenticatedUser)
async def read_my_profile(current_user: CurrentUserDep) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)


@router.get("/scores", response_model=list[PersonalScore])
async def read_my_scores(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[PersonalScore]:
    if current_user.role != "participant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Participant role required",
        )
    if current_user.id is None:
        raise RuntimeError("Persisted user is missing its database identifier.")

    result = await session.exec(
        select(Game.name, Score.points)
        .join(Game, Game.id == Score.game_id)
        .where(Score.participant_id == current_user.id)
        .order_by(Score.created_at, Game.name)
    )
    return [
        PersonalScore(game_name=game_name, points=points)
        for game_name, points in result.all()
    ]
