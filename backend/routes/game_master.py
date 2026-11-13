from fastapi import APIRouter, Depends, status

from dependencies import CurrentUserDep, SessionDep, require_table_master
from schemas import (
    GameMasterGameResponse,
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
            points=points,
            created_at=created_at,
        )
        for participant_code, points, created_at in rows
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
    return GameMasterScoreResponse(
        participant_code=score_data.participant_code,
        points=score.points,
        created_at=score.created_at,
    )
