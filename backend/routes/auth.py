
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from code_generator import participant_code_generator
from dependencies import SessionDep, require_staff
from models import User
from rate_limit import (
    client_ip,
    ensure_not_blocked,
    register_failure,
    register_success,
)
from schemas import (
    LoginRequest,
    ParticipantRegister,
    ParticipantRegistered,
    TokenResponse,
)
from security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_MAX_CODE_GENERATION_ATTEMPTS = 5


def _generate_pin() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


@router.post(
    "/register",
    response_model=ParticipantRegistered,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def register_participant(
    registration: ParticipantRegister,
    session: SessionDep,
) -> ParticipantRegistered:
    """Cadastra participante. Restrito ao admin e à equipe da recepção.

    Se a senha não for informada, gera um PIN de 6 dígitos, devolvido uma
    única vez nesta resposta para ser entregue ao aluno.
    """
    username_result = await session.exec(
        select(User.id).where(User.username == registration.username)
    )
    if username_result.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    plain_password = registration.password or _generate_pin()
    password_hash = await run_in_threadpool(hash_password, plain_password)
    for _ in range(_MAX_CODE_GENERATION_ATTEMPTS):
        participant_code = participant_code_generator()
        code_result = await session.exec(
            select(User.id).where(User.participant_code == participant_code)
        )
        if code_result.first() is not None:
            continue

        user = User(
            username=registration.username,
            password_hash=password_hash,
            role="participant",
            participant_code=participant_code,
        )
        session.add(user)
        try:
            await session.flush()
            await session.commit()
        except IntegrityError:
            await session.rollback()

            username_result = await session.exec(
                select(User.id).where(User.username == registration.username)
            )
            if username_result.first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already registered",
                ) from None

            code_result = await session.exec(
                select(User.id).where(User.participant_code == participant_code)
            )
            if code_result.first() is not None:
                continue
            raise

        return ParticipantRegistered(
            id=user.id,
            username=user.username,
            role="participant",
            participant_code=user.participant_code,
            is_active=user.is_active,
            password=None if registration.password else plain_password,
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Unable to allocate a unique participant code; try again",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    session: SessionDep,
    request: Request,
) -> TokenResponse:
    """Login por nome de usuário ou, para alunos, pelo código de participante."""
    ip = client_ip(request)
    identifier = credentials.username.strip()
    ensure_not_blocked(ip, identifier)

    result = await session.exec(
        select(User).where(
            or_(
                User.username == identifier,
                User.participant_code == identifier.upper(),
            )
        )
    )
    user = result.first()
    if user is None:
        await run_in_threadpool(verify_password, credentials.password, DUMMY_PASSWORD_HASH)
        register_failure(ip, identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_is_valid = await run_in_threadpool(
        verify_password,
        credentials.password,
        user.password_hash,
    )
    if not password_is_valid or not user.is_active:
        register_failure(ip, identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.id is None:
        raise RuntimeError("Persisted user is missing its database identifier.")

    register_success(ip, identifier)
    return TokenResponse(access_token=create_access_token(user.id))
