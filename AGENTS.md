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

---

## 7. Security & Architecture Golden Standards
1. **JWT Exception Handling:**
   - In `app/dependencies/auth.py`, explicitly catch `jwt.exceptions.ExpiredSignatureError` (return 401 with `"Token has expired"`) and `jwt.exceptions.InvalidTokenError` (return 401 with `"Could not validate credentials"`). Never let JWT exceptions raise unhandled HTTP 500 errors.
2. **Production Security Validation (Fail-Fast):**
   - In `app/core/config.py`, support `environment: Literal["development", "production", "test"]`.
   - In production mode, validate that `jwt_secret_key` is explicitly set via environment variables, is at least 32 characters, and is not a default dev key.
3. **Cookie Security (cookie_secure):**
   - When `environment == "production"`, `cookie_secure` MUST automatically be `True` (HTTPS only). In development, it MUST be `False` to allow local HTTP testing.
4. **Refresh Token Exclusively via HttpOnly Cookies:**
   - Refresh tokens MUST travel ONLY via `HttpOnly` cookies (`path="/auth"`, `samesite="lax"`, `secure=settings.cookie_secure`).
   - NEVER return or accept refresh tokens in JSON request/response bodies (prevents XSS token exfiltration).
5. **No Hardcoded Owner / Admin Identifiers:**
   - System owner/admin email and credentials MUST be loaded from settings (`settings.owner_email` / `OWNER_EMAIL`).
   - NEVER hardcode specific developer emails or magic user IDs (`id == 2`) in services or controllers.
6. **Secrets & Environment Isolation:**
   - `.env` MUST be in `.gitignore` and NEVER tracked in Git.
   - Maintain `.env.example` with safe placeholder templates for repository consumers.

---

## 8. Database Query & API Design Standards
1. **Deterministic Pagination Ordering:**
   - Any paginated SQL query using `.offset()` and `.limit()` MUST explicitly define ordering (e.g. `.order_by(Product.id.asc())`). Relational databases (MySQL, PostgreSQL) do not guarantee row order without an explicit `ORDER BY`, which causes data duplication or omission across pages.
2. **Partial Updates via PATCH:**
   - Resource updates where individual fields can change (e.g. fast inventory/stock adjustments, price changes) MUST support `PATCH` alongside or instead of full `PUT`.
   - The corresponding schema (e.g. `ProductPatch`) must have all fields optional (`| None = None`), and service update methods must use `.model_dump(exclude_unset=True)` to prevent overwriting omitted fields with nulls.
3. **E-Commerce Catalog Access vs. IDOR:**
   - In single-store E-commerce models, deletion must be strictly restricted to `AdminUser` (RBAC), while catalog managers (`ManagerUser`) collaborate on inventory. In multi-vendor/marketplace models, enforce strict ownership checks (`product.seller_id == current_user.id`).


