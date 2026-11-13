from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Game, Score, User


async def get_active_game_for_master(
    session: AsyncSession,
    master_id: int,
    *,
    for_update: bool = False,
) -> Game:
    statement = select(Game).where(
        Game.master_id == master_id,
        Game.is_active.is_(True),
    )
    if for_update:
        statement = statement.with_for_update()
    result = await session.exec(statement)
    game = result.first()
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active game assigned to this table master",
        )
    return game


async def list_scores_for_game(
    session: AsyncSession,
    game_id: int,
) -> list[tuple[str | None, int, datetime]]:
    result = await session.exec(
        select(User.participant_code, Score.points, Score.created_at)
        .join(User, User.id == Score.participant_id)
        .where(Score.game_id == game_id)
        .order_by(Score.created_at, User.participant_code)
    )
    return [
        (row[0], row[1], row[2])
        for row in result.all()
    ]


async def create_score(
    session: AsyncSession,
    game_id: int,
    participant_code: str,
    points: int,
) -> Score:
    participant_result = await session.exec(
        select(User).where(User.participant_code == participant_code)
    )
    participant = participant_result.first()
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    if participant.role != "participant" or not participant.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Code does not belong to an active participant",
        )
    if participant.id is None:
        raise RuntimeError("Persisted participant is missing its database identifier.")

    existing_score = await session.exec(
        select(Score.id).where(
            Score.participant_id == participant.id,
            Score.game_id == game_id,
        )
    )
    if existing_score.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant already has a score for this game",
        )

    score = Score(
        participant_id=participant.id,
        game_id=game_id,
        points=points,
    )
    session.add(score)
    try:
        await session.flush()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_score = await session.exec(
            select(Score.id).where(
                Score.participant_id == participant.id,
                Score.game_id == game_id,
            )
        )
        if existing_score.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Participant already has a score for this game",
            ) from None
        raise

    if score.id is None:
        raise RuntimeError("Persisted score is missing its database identifier.")
    return score


async def update_score(
    session: AsyncSession,
    score_id: int,
    points: int,
) -> Score | None:
    score = await session.get(Score, score_id)
    if score is None:
        return None

    score.points = points
    await session.commit()
    return score
