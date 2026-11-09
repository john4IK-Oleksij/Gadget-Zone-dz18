# Strict Code Quality & Linter Rules (Pylance Strict & Ruff)

This project and workspace enforce strict Python typing (`Pylance` in strict mode) and `Ruff` linter rules.
When generating or modifying any Python code, **strictly obey the following rules** to prevent any red squiggly lines or warnings in VS Code:

---

## 1. FastAPI Route Return Types & Service Typing
- Service methods returning data to API endpoints MUST explicitly return the corresponding Pydantic schema model (e.g. `-> AdminStatsResponse`), NEVER a raw `dict` (e.g. `dict[str, int]` or `dict[str, Any]`), avoiding `Pylance(reportReturnType)`.
- Explicitly narrow optional variables (e.g. `user: User | None`) with `if not user or user.id is None: raise ...` before accessing `.id` or other fields to prevent `Pylance(reportOptionalMemberAccess)` ("'id' is not a known attribute of 'None'").

---

## 2. Starlette & FastAPI Middleware Strict Typing
All middleware parameters and returns must be strictly typed:
```python
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

async def custom_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    response: Response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response
```
Do not leave `call_next` unannotated or return unannotated responses.

---

## 3. Modern FastAPI UploadFile Defaults (Ruff B008)
- Never write `file: UploadFile = File(...)`. This triggers Ruff `B008` ("Do not perform function call File in argument defaults").
- Always use the modern `Annotated` syntax:
```python
from typing import Annotated
from fastapi import File, UploadFile

async def upload_file(
    file: Annotated[UploadFile, File()],
) -> ...:
    ...
```

---

## 4. Non-Blocking File I/O in Async Handlers (Ruff ASYNC230)
- Never use blocking file operations (`open()`, `shutil.copyfileobj()`, `json.load(open(...))`) directly inside async functions.
- Always isolate blocking I/O into a dedicated synchronous helper function and run it via `await asyncio.to_thread(_helper_sync, ...)`:
```python
import asyncio

def _sync_save(destination_path: Path, data: bytes) -> None:
    destination_path.write_bytes(data)

async def handle_upload(...) -> None:
    content = await file.read()
    await asyncio.to_thread(_sync_save, file_path, content)
```

---

## 5. Clean Imports & No Unused Entities (Ruff F401 / Pylance reportUnusedImport)
- Never leave unused imports or definitions in code.
- If an import is only needed to register SQLAlchemy models on `Base`, use a tuple assignment or explicit registration instead of raw `# noqa: F401`:
```python
from app.models import CartItem, Product, RefreshToken, User

_ALL_MODELS = (CartItem, Product, RefreshToken, User)
```

---

## 6. Datetime, Timezone & Cookie Literals
- Always import `datetime` and `timezone` from standard `datetime`.
- Use timezone-aware UTC datetimes: `datetime.now(timezone.utc)`.
- Restrict cookie `samesite` settings with `Literal["lax", "strict", "none"]` to satisfy Pylance strict parameter typing.
