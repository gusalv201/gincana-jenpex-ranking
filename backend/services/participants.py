from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Game, Score, User
from schemas import AdminParticipantListItem, MissingGame, PlayedGame
from services.ranking import position_of


async def list_participants(session: AsyncSession) -> list[AdminParticipantListItem]:
    result = await session.exec(
        select(
            User.id,
            User.username,
            User.participant_code,
            User.is_active,
            func.coalesce(func.sum(Score.points), 0),
            func.count(Score.id),
        )
        .outerjoin(Score, Score.participant_id == User.id)
        .where(User.role == "participant")
        .group_by(User.id, User.username, User.participant_code, User.is_active)
        .order_by(User.username.asc())
    )
    return [
        AdminParticipantListItem(
            id=pid,
            username=username,
            participant_code=code,
            is_active=is_active,
            total_points=int(total),
            games_played=int(games),
        )
        for pid, username, code, is_active, total, games in result.all()
    ]


async def participant_progress(
    session: AsyncSession,
    participant_id: int,
) -> dict:
    """Jogos jogados (com horário e chefe), jogos que faltam, posição e total."""
    master = aliased(User)
    played_rows = await session.exec(
        select(Game.id, Game.name, Score.points, Score.created_at, master.username)
        .join(Game, Game.id == Score.game_id)
        .outerjoin(master, master.id == Game.master_id)
        .where(Score.participant_id == participant_id)
        .order_by(Score.created_at)
    )
    played = [
        PlayedGame(
            game_id=game_id,
            game_name=name,
            points=points,
            created_at=created_at,
            master_username=master_name,
        )
        for game_id, name, points, created_at, master_name in played_rows.all()
    ]
    played_ids = {game.game_id for game in played}

    games_rows = await session.exec(
        select(Game.id, Game.name).where(Game.is_active.is_(True)).order_by(Game.id)
    )
    missing = [
        MissingGame(game_id=game_id, game_name=name)
        for game_id, name in games_rows.all()
        if game_id not in played_ids
    ]

    position, total_participants, _ = await position_of(session, participant_id)
    total_points = sum(game.points for game in played)
    return {
        "position": position,
        "total_participants": total_participants,
        "total_points": total_points,
        "played": played,
        "missing": missing,
    }
