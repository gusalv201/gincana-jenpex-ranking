from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Score, User
from schemas import RankingEntry, RankingResponse

RANKING_LIMIT = 5


async def get_general_ranking(session: AsyncSession) -> RankingResponse:
    active_participants = (
        select(
            User.id.label("participant_id"),
            User.participant_code.label("participant_code"),
            func.coalesce(func.sum(Score.points), 0).label("total_points"),
        )
        .outerjoin(Score, Score.participant_id == User.id)
        .where(
            User.role == "participant",
            User.is_active.is_(True),
        )
        .group_by(User.id, User.participant_code)
        .subquery()
    )

    ranking_query = (
        select(
            active_participants.c.participant_code,
            active_participants.c.total_points,
        )
        .order_by(
            active_participants.c.total_points.desc(),
            active_participants.c.participant_code.asc(),
        )
    )
    ranking_rows = (await session.exec(ranking_query)).all()

    participant_count_query = select(func.count(User.id)).where(
        User.role == "participant",
        User.is_active.is_(True),
    )
    total_participants = int(
        (await session.exec(participant_count_query)).one()
    )

    ranking: list[RankingEntry] = []
    previous_total: int | None = None
    position = 0
    for row_number, row in enumerate(ranking_rows, start=1):
        participant_code, raw_total = row
        total_points = int(raw_total)
        if total_points != previous_total:
            position = row_number
            previous_total = total_points

        if position > RANKING_LIMIT:
            break

        if participant_code is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An active participant is missing its participant code",
            )

        ranking.append(
            RankingEntry(
                position=position,
                participant_code=participant_code,
                total_points=total_points,
            )
        )

    return RankingResponse(
        total_participants=total_participants,
        ranking=ranking,
    )
