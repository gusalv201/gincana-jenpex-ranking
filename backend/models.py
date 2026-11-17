from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            "role IN ('participant', 'table_master', 'admin')",
            name="ck_user_role",
        ),
        CheckConstraint(
            "(role = 'participant' AND participant_code IS NOT NULL "
            "AND length(participant_code) = 6) OR "
            "(role IN ('table_master', 'admin') AND participant_code IS NULL)",
            name="ck_user_participant_code",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=100)
    password_hash: str = Field(max_length=255)
    role: str = Field(default="participant", max_length=20, index=True)
    participant_code: str | None = Field(
        default=None,
        max_length=6,
        unique=True,
        index=True,
    )
    is_active: bool = Field(default=True)

    game_as_master: Optional["Game"] = Relationship(
        back_populates="master",
        sa_relationship_kwargs={"foreign_keys": "[Game.master_id]"},
    )
    scores_as_participant: list["Score"] = Relationship(
        back_populates="participant",
        sa_relationship_kwargs={"foreign_keys": "[Score.participant_id]"},
    )


class Game(SQLModel, table=True):
    __tablename__ = "game"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    master_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        unique=True,
        index=True,
    )
    is_active: bool = Field(default=True)

    master: User | None = Relationship(
        back_populates="game_as_master",
        sa_relationship_kwargs={"foreign_keys": "[Game.master_id]"},
    )
    scores: list["Score"] = Relationship(
        back_populates="game",
        sa_relationship_kwargs={"foreign_keys": "[Score.game_id]"},
    )


class Score(SQLModel, table=True):
    __tablename__ = "score"
    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "game_id",
            name="uq_score_participant_game",
        ),
        CheckConstraint(
            "points >= 1 AND points <= 100",
            name="ck_score_points_range",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    participant_id: int = Field(foreign_key="user.id", index=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    points: int = Field(ge=1, le=100)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    participant: User = Relationship(
        back_populates="scores_as_participant",
        sa_relationship_kwargs={"foreign_keys": "[Score.participant_id]"},
    )
    game: Game = Relationship(
        back_populates="scores",
        sa_relationship_kwargs={"foreign_keys": "[Score.game_id]"},
    )
