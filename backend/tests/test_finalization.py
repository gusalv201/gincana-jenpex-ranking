import asyncio
import os
import unittest
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "mysql+asyncmy://test:test@localhost:3306/test"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-0123456789abcdef"

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

import models
from dependencies import require_admin, require_table_master
from routes.admin import router as admin_router
from routes.auth import login
from routes.display import read_display_ranking, router as display_router
from routes.game_master import router as game_master_router
from routes.me import router as me_router
from schemas import LoginRequest
from security import decode_access_token, hash_password
from services.ranking import get_general_ranking


class _ExecResult:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value


class _LoginSession:
    def __init__(self, user):
        self.user = user

    async def exec(self, _statement):
        return _ExecResult(self.user)


class _AsyncSessionAdapter:
    def __init__(self, session):
        self.session = session

    async def exec(self, statement):
        return self.session.exec(statement)


class FinalizationTests(unittest.TestCase):
    def _ranking_for_points(self, totals):
        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            participants = [
                models.User(
                    username=f"player-{index}",
                    password_hash="not-returned",
                    role="participant",
                    participant_code=f"AAA{index:03d}",
                )
                for index in range(1, len(totals) + 1)
            ]
            game = models.Game(name="game")
            session.add_all([*participants, game])
            session.flush()
            for participant, points in zip(participants, totals):
                if points:
                    session.add(
                        models.Score(
                            participant_id=participant.id,
                            game_id=game.id,
                            points=points,
                            created_at=datetime.now(timezone.utc),
                        )
                    )
            session.commit()
            response = asyncio.run(
                get_general_ranking(_AsyncSessionAdapter(session))
            )
        engine.dispose()
        return response.ranking

    def test_unknown_username_and_wrong_password_have_same_response(self):
        user = models.User(
            id=1,
            username="known",
            password_hash=hash_password("correct-password"),
            role="participant",
            participant_code="ABC123",
        )

        outcomes = []
        for username, stored_user in (("missing", None), ("known", user)):
            try:
                asyncio.run(
                    login(
                        LoginRequest(username=username, password="wrong-password"),
                        _LoginSession(stored_user),
                    )
                )
            except HTTPException as error:
                outcomes.append(
                    (error.status_code, error.detail, error.headers)
                )
            else:
                self.fail("Invalid credentials unexpectedly succeeded")

        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0][0], 401)

    def test_valid_login_returns_a_token_for_user(self):
        user = models.User(
            id=42,
            username="known",
            password_hash=hash_password("correct-password"),
            role="participant",
            participant_code="ABC123",
        )
        response = asyncio.run(
            login(
                LoginRequest(username="known", password="correct-password"),
                _LoginSession(user),
            )
        )
        self.assertEqual(decode_access_token(response.access_token), 42)

    def test_cors_origins_are_explicit_and_validated(self):
        from main import parse_cors_origins

        self.assertEqual(
            parse_cors_origins(" https://frontend.example/,http://localhost:3000 "),
            ["https://frontend.example", "http://localhost:3000"],
        )
        for invalid in ("*", "file://frontend.example", "https://example/a"):
            with self.subTest(origin=invalid):
                with self.assertRaises(RuntimeError):
                    parse_cors_origins(invalid)

    def test_public_and_protected_routers_have_separate_permissions(self):
        self.assertFalse(display_router.dependencies)
        self.assertEqual(
            [dependency.dependency for dependency in admin_router.dependencies],
            [require_admin],
        )
        self.assertEqual(
            [dependency.dependency for dependency in game_master_router.dependencies],
            [require_table_master],
        )
        self.assertTrue(me_router.dependencies)
        self.assertIn(
            "/display/ranking",
            __import__("main").app.openapi()["paths"],
        )

    def test_public_ranking_contains_only_top_five_safe_entries(self):
        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            users = [
                models.User(
                    username=f"player-{index}",
                    password_hash="not-returned",
                    role="participant",
                    participant_code=code,
                )
                for index, code in enumerate(
                    ("AAA001", "AAA002", "AAA003", "AAA004", "AAA005", "AAA006", "AAA007")
                )
            ]
            inactive = models.User(
                username="inactive",
                password_hash="not-returned",
                role="participant",
                participant_code="ZZZ999",
                is_active=False,
            )
            administrator = models.User(
                username="administrator",
                password_hash="not-returned",
                role="admin",
                participant_code=None,
            )
            session.add_all(users)
            session.add_all([inactive, administrator])
            session.flush()
            games = [models.Game(name="game")]
            session.add_all(games)
            session.flush()

            totals = (30, 30, 20, 10, 5, 0, 0)
            for user, total in zip(users, totals):
                if total:
                    session.add(
                        models.Score(
                            participant_id=user.id,
                            game_id=games[0].id,
                            points=total,
                            created_at=datetime.now(timezone.utc),
                        )
                    )
            session.commit()

            result = asyncio.run(
                read_display_ranking(_AsyncSessionAdapter(session))
            )
            payload = result.model_dump()
            participant_count = asyncio.run(
                get_general_ranking(_AsyncSessionAdapter(session))
            ).total_participants

        self.assertEqual(
            [(entry.position, entry.participant_code, entry.total_points) for entry in result.ranking],
            [
                (1, "AAA001", 30),
                (1, "AAA002", 30),
                (3, "AAA003", 20),
                (4, "AAA004", 10),
                (5, "AAA005", 5),
            ],
        )
        self.assertEqual(set(payload), {"ranking"})
        self.assertEqual(len(result.ranking), 5)
        self.assertNotIn("username", repr(payload))
        self.assertNotIn("password_hash", repr(payload))
        self.assertNotIn("ZZZ999", repr(payload))
        self.assertNotIn("administrator", repr(payload))
        self.assertEqual(participant_count, 7)

    def test_ranking_includes_all_participants_tied_for_fifth(self):
        ranking = self._ranking_for_points((40, 30, 20, 10, 5, 5, 0))

        self.assertEqual(
            [
                (entry.position, entry.participant_code, entry.total_points)
                for entry in ranking
            ],
            [
                (1, "AAA001", 40),
                (2, "AAA002", 30),
                (3, "AAA003", 20),
                (4, "AAA004", 10),
                (5, "AAA005", 5),
                (5, "AAA006", 5),
            ],
        )

    def test_ranking_includes_all_zero_point_participants_tied_for_fifth(self):
        ranking = self._ranking_for_points((40, 30, 20, 10, 0, 0, 0))

        self.assertEqual(
            [
                (entry.position, entry.participant_code, entry.total_points)
                for entry in ranking
            ],
            [
                (1, "AAA001", 40),
                (2, "AAA002", 30),
                (3, "AAA003", 20),
                (4, "AAA004", 10),
                (5, "AAA005", 0),
                (5, "AAA006", 0),
                (5, "AAA007", 0),
            ],
        )

    def test_database_rejects_duplicate_score_for_participant_and_game(self):
        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            participant = models.User(
                username="participant",
                password_hash="not-returned",
                role="participant",
                participant_code="ABC123",
            )
            game = models.Game(name="game")
            session.add_all([participant, game])
            session.flush()
            score = models.Score(
                participant_id=participant.id,
                game_id=game.id,
                points=50,
                created_at=datetime.now(timezone.utc),
            )
            session.add(score)
            session.commit()

            session.add(
                models.Score(
                    participant_id=participant.id,
                    game_id=game.id,
                    points=60,
                    created_at=datetime.now(timezone.utc),
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()

            self.assertEqual(
                session.exec(select(func.count()).select_from(models.Score)).one(),
                1,
            )


if __name__ == "__main__":
    unittest.main()
