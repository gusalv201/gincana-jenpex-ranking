# JENPEX API

FastAPI backend for participant registration, game-master scoring, administration,
and ranking display.

## Configuration

Copy `.env.example` to `.env` and set:

- `DATABASE_URL`: MySQL connection string using the asynchronous `asyncmy` driver.
- `JWT_SECRET_KEY`: a long, random secret kept outside source control.
- `CORS_ORIGINS`: comma-separated, explicit frontend origins (scheme and host, with
  optional port), for example `https://jenpex.example,http://localhost:3000`.
  Leave it empty to disable cross-origin browser access. Wildcard origins are
  rejected. The API uses bearer tokens rather than cookies, so CORS credentials
  are disabled.

## Database preparation

Create the MySQL database and user, then create the tables from the SQLModel
metadata. The project does not configure migrations; `create_all` creates missing
tables but does not update existing tables:

```python
import asyncio

from db import async_engine
from sqlmodel import SQLModel
import models


async def create_tables():
    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    await async_engine.dispose()


asyncio.run(create_tables())
```

Run this snippet from the project directory after configuring `.env`. For an
existing database, apply schema changes through an explicitly reviewed database
change process; do not rely on `create_all` to migrate it.

## Initial administrator

The public registration endpoint only creates participants. Provision the first
administrator directly in MySQL with `role='admin'`, `participant_code=NULL`,
and `is_active=1`. Generate the password hash using the project's configured
Argon2 implementation rather than storing a plaintext password:

```powershell
python -c "from getpass import getpass; from security import hash_password; print(hash_password(getpass('Admin password: ')))"
```

Insert that generated hash into `user.password_hash` along with a unique
username. For example, replace the placeholders with a unique username and the
generated hash:

```sql
INSERT INTO `user` (username, password_hash, role, participant_code, is_active)
VALUES ('jenpex-admin', '<ARGON2_HASH>', 'admin', NULL, TRUE);
```

Keep the generated hash private.

## Run

With the virtual environment activated and `.env` configured:

```powershell
uvicorn main:app --reload
```

The application checks the MySQL connection when starting. It does not create or
drop tables automatically.

## Main endpoints and permissions

| Endpoint | Access |
| --- | --- |
| `POST /auth/register`, `POST /auth/login` | Public |
| `GET /me`, `GET /me/scores` | Authenticated user; scores are participant-only |
| `/admin/...`, including `GET /admin/ranking` | Administrator |
| `/game-master/...` | Authenticated table master |
| `GET /display/ranking` | Public, read-only |

The public display endpoint returns the current top five ranking entries, including
shared positions, participant codes, and total points. It does not expose
usernames, internal IDs, or account data. A display client can refresh it with an
HTTP `GET` about every five seconds; no websocket connection is required.

The administrative ranking endpoint remains protected and continues to return
the administrative ranking response.

## Tests

Run the standard-library tests with:

```powershell
python -m unittest discover -s tests -v
```
