
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from code_generator import participant_code_generator
from dependencies import SessionDep
from models import User
from schemas import (
    AuthenticatedUser,
    LoginRequest,
    ParticipantRegister,
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


@router.post(
    "/register",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_201_CREATED,
)
async def register_participant(
    registration: ParticipantRegister,
    session: SessionDep,
) -> AuthenticatedUser:
    username_result = await session.exec(
        select(User.id).where(User.username == registration.username)
    )
    if username_result.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    password_hash = hash_password(registration.password)
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

        return AuthenticatedUser.model_validate(user)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Unable to allocate a unique participant code; try again",
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    session: SessionDep,
) -> TokenResponse:
    result = await session.exec(
        select(User).where(User.username == credentials.username)
    )
    user = result.first()
    if user is None:
        verify_password(credentials.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    password_is_valid = verify_password(
        credentials.password,
        user.password_hash,
    )
    if not password_is_valid or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.id is None:
        raise RuntimeError("Persisted user is missing its database identifier.")

    return TokenResponse(access_token=create_access_token(user.id))
