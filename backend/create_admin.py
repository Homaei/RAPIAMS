#!/usr/bin/env python3
"""Script to create an admin user"""
import asyncio
import sys
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User


async def create_admin_user(username: str, email: str, password: str):
    """Create an admin user"""
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                (User.email == email) | (User.username == username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists.")
            return False

        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name="Administrator",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            two_factor_enabled=False
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print(f"Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"ID: {admin_user.id}")
        return True


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        print("Example: python create_admin.py admin admin@example.com SecurePassword123!")
        sys.exit(1)

    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]

    asyncio.run(create_admin_user(username, email, password))
