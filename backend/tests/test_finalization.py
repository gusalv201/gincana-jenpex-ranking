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


class _FakeRequest:
    client = None
    headers = {}


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
                        _FakeRequest(),
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
                _FakeRequest(),
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
        paths = __import__("main").app.openapi()["paths"]
        self.assertIn("/api/display/ranking", paths)
        self.assertNotIn("security", paths["/api/display/ranking"]["get"])
        # Cadastro de participantes é restrito ao admin
        self.assertIn("security", paths["/api/auth/register"]["post"])
        self.assertNotIn("security", paths["/api/auth/login"]["post"])

    def test_public_ranking_is_sequential_with_names_and_safe(self):
        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            # Ordem de cadastro diferente da ordem alfabética dos códigos, para
            # provar que o desempate é por cadastro e não pelo código.
            codes = ("ZZZ001", "AAA002", "MMM003", "BBB004", "CCC005", "DDD006", "EEE007")
            users = [
                models.User(
                    username=f"Aluno {index}",
                    password_hash="not-returned",
                    role="participant",
                    participant_code=code,
                )
                for index, code in enumerate(codes, start=1)
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
            games = [models.Game(name="Robótica"), models.Game(name="Quiz")]
            session.add_all(games)
            session.flush()

            scores = {0: (20, 10), 1: (30, None), 2: (20, None), 3: (10, None), 4: (5, None)}
            for index, (first, second) in scores.items():
                for game, points in zip(games, (first, second)):
                    if points:
                        session.add(
                            models.Score(
                                participant_id=users[index].id,
                                game_id=game.id,
                                points=points,
                                created_at=datetime.now(timezone.utc),
                            )
                        )
            session.add(
                models.Score(
                    participant_id=inactive.id,
                    game_id=games[0].id,
                    points=100,
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()

            result = asyncio.run(read_display_ranking(_AsyncSessionAdapter(session)))
            payload = result.model_dump()
            participant_count = asyncio.run(
                get_general_ranking(_AsyncSessionAdapter(session))
            ).total_participants

        self.assertEqual(
            [(e.position, e.participant_code, e.username, e.total_points) for e in result.ranking],
            [
                (1, "ZZZ001", "Aluno 1", 30),  # empate 30 x 30: cadastrou primeiro
                (2, "AAA002", "Aluno 2", 30),
                (3, "MMM003", "Aluno 3", 20),
                (4, "BBB004", "Aluno 4", 10),
                (5, "CCC005", "Aluno 5", 5),
                (6, "DDD006", "Aluno 6", 0),
                (7, "EEE007", "Aluno 7", 0),
            ],
        )
        self.assertEqual(
            [(g.game_name, g.points) for g in result.ranking[0].games],
            [("Robótica", 20), ("Quiz", 10)],
        )
        self.assertEqual(result.games, ["Robótica", "Quiz"])
        self.assertEqual(set(payload), {"games", "ranking"})
        self.assertNotIn("password_hash", repr(payload))
        self.assertNotIn("not-returned", repr(payload))
        self.assertNotIn("ZZZ999", repr(payload))
        self.assertNotIn("administrator", repr(payload))
        self.assertEqual(participant_count, 7)

    def test_ranking_is_limited_to_ten_without_repeated_positions(self):
        ranking = self._ranking_for_points((5,) * 12)

        self.assertEqual([entry.position for entry in ranking], list(range(1, 11)))
        self.assertEqual(
            [entry.participant_code for entry in ranking],
            [f"AAA{index:03d}" for index in range(1, 11)],
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
