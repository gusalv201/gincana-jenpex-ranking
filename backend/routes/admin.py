from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import select

from dependencies import SessionDep, require_admin
from models import Game, Score, User
from schemas import (
    AdminGameCreate,
    AdminGameResponse,
    AdminMasterCreate,
    AdminMasterListItem,
    AdminMasterSummary,
    MasterAssignment,
    RankingResponse,
    ScoreCorrection,
    ScoreCorrectionResponse,
)
from security import hash_password
from services.ranking import get_general_ranking
from services.scoring import update_score

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


def _game_response(
    game: Game,
    master: User | None,
) -> AdminGameResponse:
    return AdminGameResponse(
        id=game.id,
        name=game.name,
        is_active=game.is_active,
        master=AdminMasterSummary.model_validate(master) if master else None,
    )


@router.post(
    "/games",
    response_model=AdminGameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_game(
    game_data: AdminGameCreate,
    session: SessionDep,
) -> AdminGameResponse:
    game = Game(name=game_data.name)
    session.add(game)
    await session.flush()
    await session.commit()
    if game.id is None:
        raise RuntimeError("Persisted game is missing its database identifier.")
    return _game_response(game, None)


@router.get("/games", response_model=list[AdminGameResponse])
async def list_games(session: SessionDep) -> list[AdminGameResponse]:
    result = await session.exec(
        select(Game)
        .options(selectinload(Game.master))
        .order_by(Game.id)
    )
    return [_game_response(game, game.master) for game in result.all()]


@router.get("/masters", response_model=list[AdminMasterListItem])
async def list_masters(session: SessionDep) -> list[AdminMasterListItem]:
    result = await session.exec(
        select(
            User.id,
            User.username,
            User.is_active,
            Game.id,
            Game.name,
        )
        .outerjoin(Game, Game.master_id == User.id)
        .where(User.role == "table_master")
        .order_by(User.username.asc())
    )
    return [
        AdminMasterListItem(
            id=master_id,
            username=username,
            is_active=is_active,
            game_id=game_id,
            game_name=game_name,
        )
        for master_id, username, is_active, game_id, game_name in result.all()
    ]


@router.post(
    "/masters",
    response_model=AdminMasterSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_master(
    master_data: AdminMasterCreate,
    session: SessionDep,
) -> AdminMasterSummary:
    existing_user = await session.exec(
        select(User.id).where(User.username == master_data.username)
    )
    if existing_user.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    master = User(
        username=master_data.username,
        password_hash=hash_password(master_data.password),
        role="table_master",
        participant_code=None,
    )
    session.add(master)
    try:
        await session.flush()
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing_user = await session.exec(
            select(User.id).where(User.username == master_data.username)
        )
        if existing_user.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            ) from None
        raise

    if master.id is None:
        raise RuntimeError("Persisted master is missing its database identifier.")
    return AdminMasterSummary.model_validate(master)


@router.put(
    "/games/{game_id}/master",
    response_model=AdminGameResponse,
)
async def assign_master(
    game_id: int,
    assignment: MasterAssignment,
    session: SessionDep,
) -> AdminGameResponse:
    game_result = await session.exec(
        select(Game)
        .where(Game.id == game_id)
        .with_for_update()
    )
    game = game_result.first()
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )
    if not game.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign a master to an inactive game",
        )

    master = await session.get(User, assignment.master_id)
    if master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )
    if master.role != "table_master":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is not a table master",
        )
    if not master.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign an inactive master",
        )

    if game.master_id != master.id:
        other_game = await session.exec(
            select(Game.id).where(
                Game.master_id == master.id,
                Game.id != game.id,
            )
        )
        if other_game.first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Master is already assigned to another game",
            )

        if game.master_id is not None:
            existing_score = await session.exec(
                select(Score.id)
                .where(Score.game_id == game.id)
                .limit(1)
            )
            if existing_score.first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A game with scores cannot be reassigned",
                )

        game.master_id = master.id
        try:
            await session.flush()
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Master or game association changed concurrently",
            ) from None

    return _game_response(game, master)


@router.patch(
    "/scores/{score_id}",
    response_model=ScoreCorrectionResponse,
)
async def correct_score(
    score_id: int,
    correction: ScoreCorrection,
    session: SessionDep,
) -> ScoreCorrectionResponse:
    score = await update_score(session, score_id, correction.points)
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not found",
        )
    if score.id is None:
        raise RuntimeError("Persisted score is missing its database identifier.")
    return ScoreCorrectionResponse(id=score.id, points=score.points)


@router.get("/ranking", response_model=RankingResponse)
async def read_general_ranking(
    session: SessionDep,
) -> RankingResponse:
    return await get_general_ranking(session)
