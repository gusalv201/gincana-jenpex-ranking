from fastapi import APIRouter, Depends, status

from dependencies import CurrentUserDep, SessionDep, require_table_master
from sqlmodel import select

from models import User
from schemas import (
    GameMasterGameResponse,
    GameMasterParticipant,
    GameMasterScoreResponse,
    ScoreSubmission,
)
from services.scoring import (
    create_score,
    get_active_game_for_master,
    list_scores_for_game,
)

router = APIRouter(
    prefix="/game-master",
    tags=["game-master"],
    dependencies=[Depends(require_table_master)],
)


@router.get("/game", response_model=GameMasterGameResponse)
async def read_my_game(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> GameMasterGameResponse:
    if current_user.id is None:
        raise RuntimeError("Persisted master is missing its database identifier.")

    game = await get_active_game_for_master(session, current_user.id)
    if game.id is None:
        raise RuntimeError("Persisted game is missing its database identifier.")
    return GameMasterGameResponse(
        id=game.id,
        name=game.name,
        is_active=game.is_active,
    )


@router.get("/scores", response_model=list[GameMasterScoreResponse])
async def read_game_scores(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[GameMasterScoreResponse]:
    if current_user.id is None:
        raise RuntimeError("Persisted master is missing its database identifier.")

    game = await get_active_game_for_master(session, current_user.id)
    if game.id is None:
        raise RuntimeError("Persisted game is missing its database identifier.")

    rows = await list_scores_for_game(session, game.id)
    return [
        GameMasterScoreResponse(
            participant_code=participant_code,
            username=username,
            points=points,
            created_at=created_at,
        )
        for participant_code, points, created_at, username in rows
    ]


@router.post(
    "/scores",
    response_model=GameMasterScoreResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_game_score(
    score_data: ScoreSubmission,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> GameMasterScoreResponse:
    if current_user.id is None:
        raise RuntimeError("Persisted master is missing its database identifier.")

    game = await get_active_game_for_master(
        session,
        current_user.id,
        for_update=True,
    )
    if game.id is None:
        raise RuntimeError("Persisted game is missing its database identifier.")

    score = await create_score(
        session,
        game_id=game.id,
        participant_code=score_data.participant_code,
        points=score_data.points,
    )
    participant = await session.get(User, score.participant_id)
    return GameMasterScoreResponse(
        participant_code=score_data.participant_code,
        username=participant.username if participant else None,
        points=score.points,
        created_at=score.created_at,
    )


@router.get("/participants", response_model=list[GameMasterParticipant])
async def read_participants(session: SessionDep) -> list[GameMasterParticipant]:
    """Nome e código dos alunos ativos, para o chefe de mesa localizar quem vai jogar."""
    result = await session.exec(
        select(User.participant_code, User.username)
        .where(User.role == "participant", User.is_active.is_(True))
        .order_by(User.username.asc())
    )
    return [
        GameMasterParticipant(participant_code=code, username=name)
        for code, name in result.all()
    ]
