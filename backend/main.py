import os
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import async_engine, check_database_connection
from routes.admin import router as admin_router
from routes.auth import router as auth_router
from routes.display import router as display_router
from routes.game_master import router as game_master_router
from routes.me import router as me_router


def parse_cors_origins(value: str | None) -> list[str]:
    origins: list[str] = []
    for raw_origin in (value or "").split(","):
        origin = raw_origin.strip()
        if not origin:
            continue
        parsed = urlsplit(origin)
        if (
            origin == "*"
            or parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise RuntimeError(
                f"Invalid CORS origin {origin!r}; use an explicit http(s) origin."
            )
        try:
            parsed.port
        except ValueError as exc:
            raise RuntimeError(f"Invalid CORS origin {origin!r}.") from exc
        normalized_origin = origin.rstrip("/")
        if normalized_origin not in origins:
            origins.append(normalized_origin)
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await check_database_connection()
        yield
    finally:
        await async_engine.dispose()


app = FastAPI(lifespan=lifespan, title="API Jenpex")
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(me_router)
app.include_router(game_master_router)
app.include_router(display_router)


@app.get("/")
def home():
    return {"status": "Rodando e subindo as rotas!"}
