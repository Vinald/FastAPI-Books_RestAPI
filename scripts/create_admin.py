#!/usr/bin/env python
"""
Script to create an admin user.

Usage:
    # Interactive mode (will prompt for input)
    python scripts/create_admin.py

    # With command line arguments
    python scripts/create_admin.py --email admin@example.com --username admin --password yourpassword

    # Short form
    python scripts/create_admin.py -e admin@example.com -u admin -p yourpassword

    # With optional first/last name
    python scripts/create_admin.py -e admin@example.com -u admin -p yourpassword -f John -l Doe

Note:
    - Password must be at least 8 characters
    - If user already exists, you'll be prompted to upgrade them to admin
    - Run from the project root directory
"""
import argparse
import asyncio
import getpass
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def create_admin_user(
        email: str,
        username: str,
        password: str,
        first_name: str = "Admin",
        last_name: str = "User"
) -> None:
    """Create an admin user in the database."""
    async with AsyncSessionLocal() as session:
        # Check if email already exists
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()

        if existing_user:
            print(f"User with email '{email}' already exists.")

            # Offer to upgrade to admin
            if existing_user.role != UserRole.ADMIN:
                upgrade = input(f"   Current role: {existing_user.role.value}. Upgrade to admin? (y/n): ")
                if upgrade.lower() == 'y':
                    existing_user.role = UserRole.ADMIN
                    await session.commit()
                    print(f"User '{email}' upgraded to admin!")
            else:
                print(f"   User is already an admin.")
            return

        # Check if username already exists
        result = await session.execute(select(User).where(User.username == username))
        if result.scalars().first():
            print(f"Username '{username}' already taken.")
            return

        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            is_active=True
        )

        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   UUID: {admin_user.uuid}")


def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--email", "-e", help="Admin email address")
    parser.add_argument("--username", "-u", help="Admin username")
    parser.add_argument("--password", "-p", help="Admin password (will prompt if not provided)")
    parser.add_argument("--first-name", "-f", default="Admin", help="First name")
    parser.add_argument("--last-name", "-l", default="User", help="Last name")

    args = parser.parse_args()

    # Interactive mode if arguments not provided
    email = args.email or input("Email: ")
    username = args.username or input("Username: ")
    password = args.password or getpass.getpass("Password: ")
    first_name = args.first_name
    last_name = args.last_name

    if not email or not username or not password:
        print("Email, username, and password are required.")
        sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    # Run async function
    asyncio.run(create_admin_user(email, username, password, first_name, last_name))


if __name__ == "__main__":
    main()
