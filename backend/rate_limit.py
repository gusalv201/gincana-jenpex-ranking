"""Limitador simples, em memória, de tentativas de login com falha.

Suficiente para uma instância única (Render free).

- Por IP: muitas falhas a partir do mesmo endereço bloqueiam esse endereço.
  O limite é alto porque, no campus, todos os alunos saem pelo mesmo IP.
- Por usuário + IP: bloqueia a adivinhação de senha de uma conta específica
  sem permitir que alguém, de outro lugar, tranque a conta de um chefe de mesa
  só errando a senha dele de propósito.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

WINDOW_SECONDS = 10 * 60
MAX_FAILURES_PER_IP = 100
MAX_FAILURES_PER_USER_AND_IP = 8

_failures: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def client_ip(request: Request) -> str:
    """IP real do cliente atrás do proxy da hospedagem.

    O proxy acrescenta o IP de quem conectou ao FINAL do X-Forwarded-For; os
    valores do início podem ter sido inventados pelo próprio cliente, por isso
    usamos sempre o último.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
    if hops:
        return hops[-1]
    return request.client.host if request.client else "unknown"


def _prune(bucket: deque[float], now: float) -> None:
    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()


def _keys(ip: str, username: str) -> tuple[str, str]:
    return f"ip:{ip}", f"user:{username.strip().lower()}|{ip}"


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
            or len(user_bucket) >= MAX_FAILURES_PER_USER_AND_IP
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


def register_success(ip: str, username: str) -> None:
    _, user_key = _keys(ip, username)
    with _lock:
        _failures.pop(user_key, None)
