from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UserRole = Literal["participant", "table_master", "admin", "reception"]


class ParticipantRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    # Opcional: se omitida, o servidor gera um PIN de 6 dígitos.
    password: str | None = Field(default=None, min_length=6, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole
    participant_code: str | None = Field(default=None, min_length=6, max_length=6)
    is_active: bool


class ParticipantRegistered(AuthenticatedUser):
    # PIN gerado pelo servidor (somente quando a senha não foi informada).
    password: str | None = None


class PersonalScore(BaseModel):
    game_name: str
    points: int = Field(ge=1, le=100)


class AdminGameCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)


class AdminMasterCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class MasterAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    master_id: int = Field(gt=0)


class AdminMasterSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Literal["table_master"]
    is_active: bool


class AdminMasterListItem(BaseModel):
    id: int
    username: str
    is_active: bool
    game_id: int | None
    game_name: str | None


class AdminGameResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    master: AdminMasterSummary | None = None


class GameMasterGameResponse(BaseModel):
    id: int
    name: str
    is_active: bool


class ScoreSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participant_code: str = Field(min_length=6, max_length=6)
    points: int = Field(strict=True, ge=1, le=100)


class GameMasterScoreResponse(BaseModel):
    participant_code: str
    username: str | None = None
    points: int = Field(ge=1, le=100)
    created_at: datetime


class ScoreCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: int = Field(strict=True, ge=1, le=100)


class ScoreCorrectionResponse(BaseModel):
    id: int
    points: int = Field(ge=1, le=100)


class RankingGameScore(BaseModel):
    game_name: str
    points: int = Field(ge=1, le=100)


class RankingEntry(BaseModel):
    position: int = Field(ge=1)
    participant_code: str
    username: str
    total_points: int = Field(ge=0)
    games: list[RankingGameScore] = []


class RankingResponse(BaseModel):
    total_participants: int = Field(ge=0)
    games: list[str] = []
    ranking: list[RankingEntry]


class DisplayRankingResponse(BaseModel):
    games: list[str] = []
    ranking: list[RankingEntry]


class AdminParticipantListItem(BaseModel):
    id: int
    username: str
    participant_code: str
    is_active: bool
    total_points: int = Field(ge=0)
    games_played: int = Field(ge=0)


class GameMasterParticipant(BaseModel):
    participant_code: str
    username: str


class StaffCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=128)


class StaffSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_active: bool


class ParticipantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1, max_length=100)
    # True gera um novo PIN de 6 dígitos (devolvido uma única vez na resposta).
    reset_password: bool = False


class PlayedGame(BaseModel):
    game_id: int
    game_name: str
    points: int = Field(ge=1, le=100)
    created_at: datetime
    master_username: str | None = None


class MissingGame(BaseModel):
    game_id: int
    game_name: str


class ParticipantDetail(BaseModel):
    id: int
    username: str
    participant_code: str
    is_active: bool
    position: int | None = None
    total_participants: int = Field(ge=0)
    total_points: int = Field(ge=0)
    played: list[PlayedGame]
    missing: list[MissingGame]


class MySummary(BaseModel):
    username: str
    participant_code: str
    position: int | None = None
    total_participants: int = Field(ge=0)
    total_points: int = Field(ge=0)
    played: list[PlayedGame]
    missing: list[MissingGame]
