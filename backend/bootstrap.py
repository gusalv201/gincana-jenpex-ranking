"""Preparação automática do banco ao iniciar a aplicação.

- Cria as tabelas que ainda não existem (não altera tabelas existentes).
- Garante que exista o administrador definido por ADMIN_USERNAME / ADMIN_PASSWORD.
  A senha do admin é sempre sincronizada com a variável de ambiente, então para
  trocar a senha basta alterar a variável no painel da hospedagem e reiniciar.
"""

import logging
import os

from sqlmodel import SQLModel, select

import models  # noqa: F401  (registra as tabelas no metadata)
from db import async_engine, async_session
from models import User
from security import hash_password, verify_password

logger = logging.getLogger("jenpex.bootstrap")

MIN_ADMIN_PASSWORD_LENGTH = 12


async def create_tables() -> None:
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def ensure_admin() -> None:
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        logger.warning("ADMIN_USERNAME/ADMIN_PASSWORD não definidos; nenhum admin criado.")
        return
    if len(password) < MIN_ADMIN_PASSWORD_LENGTH:
        raise RuntimeError(
            f"ADMIN_PASSWORD deve ter pelo menos {MIN_ADMIN_PASSWORD_LENGTH} caracteres."
        )

    async with async_session() as session:
        result = await session.exec(select(User).where(User.username == username))
        user = result.first()
        if user is None:
            session.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    role="admin",
                    participant_code=None,
                    is_active=True,
                )
            )
            await session.commit()
            logger.info("Administrador '%s' criado.", username)
            return

        if user.role != "admin":
            raise RuntimeError(
                f"ADMIN_USERNAME '{username}' já pertence a um usuário que não é admin."
            )
        changed = False
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            session.add(user)
            await session.commit()
            logger.info("Administrador '%s' atualizado.", username)


async def run_bootstrap() -> None:
    await create_tables()
    await ensure_admin()
