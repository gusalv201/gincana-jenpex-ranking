"""Limitador simples, em memória, de tentativas de login com falha.

Suficiente para uma instância única (Render free). Bloqueia por IP e por
usuário após muitas falhas dentro da janela de tempo.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

WINDOW_SECONDS = 10 * 60
MAX_FAILURES_PER_IP = 20
MAX_FAILURES_PER_USERNAME = 8

_failures: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def client_ip(request: Request) -> str:
    # Atrás do proxy da hospedagem o IP real vem no X-Forwarded-For
    # (uvicorn é iniciado com --proxy-headers, que já ajusta request.client).
    return request.client.host if request.client else "unknown"


def _prune(bucket: deque[float], now: float) -> None:
    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()


def _keys(ip: str, username: str) -> tuple[str, str]:
    return f"ip:{ip}", f"user:{username.strip().lower()}"


def ensure_not_blocked(ip: str, username: str) -> None:
    now = time.monotonic()
    ip_key, user_key = _keys(ip, username)
    with _lock:
        ip_bucket = _failures[ip_key]
        user_bucket = _failures[user_key]
        _prune(ip_bucket, now)
        _prune(user_bucket, now)
        blocked = (
            len(ip_bucket) >= MAX_FAILURES_PER_IP
            or len(user_bucket) >= MAX_FAILURES_PER_USERNAME
        )
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts; try again later",
        )


def register_failure(ip: str, username: str) -> None:
    now = time.monotonic()
    with _lock:
        for key in _keys(ip, username):
            _failures[key].append(now)


def register_success(username: str) -> None:
    _, user_key = _keys("", username)
    with _lock:
        _failures.pop(user_key, None)
