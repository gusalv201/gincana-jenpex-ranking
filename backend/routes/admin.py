from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func
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
    AdminParticipantListItem,
    StaffCreate,
    StaffSummary,
    MasterAssignment,
    RankingResponse,
    ScoreCorrection,
    ScoreCorrectionResponse,
)
from security import hash_password
from services.participants import list_participants as list_participants_service
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


@router.get("/participants", response_model=list[AdminParticipantListItem])
async def list_participants(session: SessionDep) -> list[AdminParticipantListItem]:
    return await list_participants_service(session)


@router.delete(
    "/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_participant(participant_id: int, session: SessionDep) -> Response:
    """Exclui o aluno e todas as pontuações dele (não pode ser desfeito)."""
    participant = await session.get(User, participant_id)
    if participant is None or participant.role != "participant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    await session.exec(delete(Score).where(Score.participant_id == participant_id))
    await session.delete(participant)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Equipe da recepção (perfil "reception"): cadastra, consulta e corrige alunos
# ---------------------------------------------------------------------------
@router.get("/staff", response_model=list[StaffSummary])
async def list_staff(session: SessionDep) -> list[StaffSummary]:
    result = await session.exec(
        select(User).where(User.role == "reception").order_by(User.username.asc())
    )
    return [StaffSummary.model_validate(user) for user in result.all()]


@router.post("/staff", response_model=StaffSummary, status_code=status.HTTP_201_CREATED)
async def create_staff(staff_data: StaffCreate, session: SessionDep) -> StaffSummary:
    username = staff_data.username.strip()
    existing = await session.exec(select(User.id).where(User.username == username))
    if existing.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    user = User(
        username=username,
        password_hash=hash_password(staff_data.password),
        role="reception",
        participant_code=None,
    )
    session.add(user)
    await session.commit()
    return StaffSummary.model_validate(user)


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(staff_id: int, session: SessionDep) -> Response:
    user = await session.get(User, staff_id)
    if user is None or user.role != "reception":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Exportação para relatório (sem senhas nem hashes)
# ---------------------------------------------------------------------------
@router.get("/export")
async def export_event_data(session: SessionDep) -> dict:
    from datetime import datetime, timezone

    games = (await session.exec(select(Game).order_by(Game.id))).all()
    users = (await session.exec(select(User).order_by(User.id))).all()
    scores = (await session.exec(select(Score).order_by(Score.created_at))).all()
    names = {user.id: user.username for user in users}

    def iso(value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games": [
            {
                "id": game.id,
                "name": game.name,
                "is_active": game.is_active,
                "master": names.get(game.master_id),
            }
            for game in games
        ],
        "participants": [
            {
                "id": user.id,
                "username": user.username,
                "participant_code": user.participant_code,
                "is_active": user.is_active,
            }
            for user in users
            if user.role == "participant"
        ],
        "staff": {
            "table_masters": sum(1 for user in users if user.role == "table_master"),
            "reception": sum(1 for user in users if user.role == "reception"),
        },
        "scores": [
            {
                "id": score.id,
                "participant_id": score.participant_id,
                "game_id": score.game_id,
                "points": score.points,
                "created_at": iso(score.created_at),
            }
            for score in scores
        ],
    }
