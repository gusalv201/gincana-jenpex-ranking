from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UserRole = Literal["participant", "table_master", "admin"]


class ParticipantRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


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
    points: int = Field(ge=1, le=100)
    created_at: datetime


class ScoreCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: int = Field(strict=True, ge=1, le=100)


class ScoreCorrectionResponse(BaseModel):
    id: int
    points: int = Field(ge=1, le=100)


class RankingEntry(BaseModel):
    position: int = Field(ge=1)
    participant_code: str
    total_points: int = Field(ge=0)


class RankingResponse(BaseModel):
    total_participants: int = Field(ge=0)
    ranking: list[RankingEntry]


class DisplayRankingResponse(BaseModel):
    ranking: list[RankingEntry]
