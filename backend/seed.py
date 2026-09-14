"""Create the first hospital and clinician account for local development."""
import asyncio
import os

from sqlalchemy import select

from auth import hash_password
from database import AsyncSessionLocal, init_db
from models import Hospital, User, UserRole


async def seed() -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "drshivesh@gmail.com").lower()
    password = os.getenv("SEED_ADMIN_PASSWORD")
    if not password:
        print("SEED_ADMIN_PASSWORD is not set; skipping administrator bootstrap.")
        return
    await init_db()
    async with AsyncSessionLocal() as db:
        if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
            print(f"Account already exists: {email}")
            return
        hospital = Hospital(name="Demo Hospital", tier="clinical", city="Delhi", state="Delhi")
        db.add(hospital)
        await db.flush()
        db.add(User(
            email=email,
            full_name="Dr. Shivesh Kumar",
            designation="Administrator / Associate Consultant",
            registration_no=None,
            role=UserRole.ADMIN,
            hospital_id=hospital.id,
            hashed_password=hash_password(password),
        ))
        await db.commit()
        print(f"Created {email}. Change the password before non-local use.")


if __name__ == "__main__":
    asyncio.run(seed())
