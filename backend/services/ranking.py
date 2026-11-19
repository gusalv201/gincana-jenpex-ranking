from collections import defaultdict

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Game, Score, User
from schemas import RankingEntry, RankingGameScore, RankingResponse

RANKING_LIMIT = 10


async def ordered_participants(session: AsyncSession) -> list[tuple[int, str, str, int]]:
    """Todos os participantes ativos em ordem de classificação.

    Critério: maior pontuação total; em caso de empate, quem se cadastrou
    primeiro (menor id) fica à frente. Retorna (id, código, nome, total).
    """
    result = await session.exec(
        select(
            User.id,
            User.participant_code,
            User.username,
            func.coalesce(func.sum(Score.points), 0),
        )
        .outerjoin(Score, Score.participant_id == User.id)
        .where(User.role == "participant", User.is_active.is_(True))
        .group_by(User.id, User.participant_code, User.username)
        .order_by(func.coalesce(func.sum(Score.points), 0).desc(), User.id.asc())
    )
    return [(pid, code, name, int(total)) for pid, code, name, total in result.all()]


async def position_of(session: AsyncSession, participant_id: int) -> tuple[int | None, int, int]:
    """(posição, total de participantes, pontos) de um participante."""
    rows = await ordered_participants(session)
    for index, (pid, _code, _name, total) in enumerate(rows, start=1):
        if pid == participant_id:
            return index, len(rows), total
    return None, len(rows), 0


async def active_game_names(session: AsyncSession) -> list[str]:
    result = await session.exec(
        select(Game.name).where(Game.is_active.is_(True)).order_by(Game.id)
    )
    return list(result.all())


async def get_general_ranking(
    session: AsyncSession,
    limit: int = RANKING_LIMIT,
) -> RankingResponse:
    rows = await ordered_participants(session)
    top = rows[:limit]
    ids = [pid for pid, *_ in top]

    games_by_participant: dict[int, list[RankingGameScore]] = defaultdict(list)
    if ids:
        score_rows = await session.exec(
            select(Score.participant_id, Game.name, Score.points)
            .join(Game, Game.id == Score.game_id)
            .where(Score.participant_id.in_(ids))
            .order_by(Game.id)
        )
        for pid, game_name, points in score_rows.all():
            games_by_participant[pid].append(
                RankingGameScore(game_name=game_name, points=points)
            )

    ranking = [
        RankingEntry(
            position=index,
            participant_code=code,
            username=name,
            total_points=total,
            games=games_by_participant.get(pid, []),
        )
        for index, (pid, code, name, total) in enumerate(top, start=1)
    ]
    return RankingResponse(
        total_participants=len(rows),
        games=await active_game_names(session),
        ranking=ranking,
    )
