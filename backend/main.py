import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from bootstrap import run_bootstrap
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
        await run_bootstrap()
        yield
    finally:
        await async_engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title="API Jenpex",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/docs"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(os.getenv("CORS_ORIGINS")),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
api_router = APIRouter(prefix="/api")
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(me_router)
api_router.include_router(game_master_router)
api_router.include_router(display_router)


@api_router.get("/")
def home():
    return {"status": "Rodando e subindo as rotas!"}


app.include_router(api_router)

# Em produção o frontend Vue compilado (frontend/dist) é servido pelo próprio
# FastAPI, então tudo fica em uma única URL e não há necessidade de CORS.
FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", Path(__file__).resolve().parent.parent / "frontend" / "dist")
)
if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
