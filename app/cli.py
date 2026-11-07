import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def create_admin() -> None:
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password: ")

    if not email:
        print("Email cannot be empty.")
        return

    if not password:
        print("Password cannot be empty.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )

        existing_user = result.scalar_one_or_none()

        if existing_user is not None:
            print("User with this email already exists.")
            return

        admin = User(
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
        )

        session.add(admin)
        await session.commit()

        print(f"Admin created: {admin.email}")


def main() -> None:
    asyncio.run(create_admin())


if __name__ == "__main__":
    main()