import argparse
import asyncio
import getpass
import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.enums import Role
from app.models.user import User


async def create_admin_account(email: str, password: str) -> bool:
    """Створює обліковий запис адміністратора в базі даних."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User.id).where(User.email == email.strip().lower())
            )
            if result.scalar_one_or_none() is not None:
                return False

            hashed_password = await hash_password(password)
            admin = User(
                email=email.strip().lower(),
                password_hash=hashed_password,
                role=Role.admin,
                is_active=True,
                is_admin=True,
            )

            session.add(admin)
            try:
                await session.commit()
                return True
            except IntegrityError:
                await session.rollback()
                return False
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Консольна утиліта керування Gadget Zone",
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    admin_parser = subparsers.add_parser(
        "create-admin",
        help="Безпечне створення нового адміністратора",
    )
    admin_parser.add_argument(
        "--email",
        "--username",
        dest="email",
        help="Email нового адміністратора",
    )
    admin_parser.add_argument(
        "--password",
        dest="password",
        help="Пароль (якщо не вказано — буде запитано приховано)",
    )

    args = parser.parse_args()

    # Якщо викликано без субкоманди, за замовчуванням запускаємо створення адміна
    email = getattr(args, "email", None)
    if not email:
        email = input("Email адміністратора: ").strip()

    if not email or "@" not in email:
        print("Помилка: введіть коректну email-адресу.")
        return 1

    password = getattr(args, "password", None) or os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Пароль адміністратора: ")

    if not password or len(password) < 6:
        print("Помилка: пароль має містити щонайменше 6 символів.")
        return 1

    created = asyncio.run(create_admin_account(email, password))

    if created:
        print(f"Адміністратора {email} успішно створено!")
        return 0
    else:
        print(f"Помилка: користувач {email} уже існує в системі.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
