"""Authentication service: user registration, login, password hashing."""

from uuid import UUID

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, Department

password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


async def get_department_by_id(db: AsyncSession, department_id: UUID) -> Department | None:
    result = await db.execute(select(Department).where(Department.id == department_id))
    return result.scalar_one_or_none()


async def list_departments(db: AsyncSession) -> list[Department]:
    result = await db.execute(select(Department).order_by(Department.name))
    return list(result.scalars().all())


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, 
    name: str, 
    email: str, 
    password: str, 
    department_id: UUID | None = None,
    department: str | None = None,
) -> User:
    dept = None
    if department_id:
        dept = await get_department_by_id(db, department_id)
        if not dept:
            raise ValueError("Selected department does not exist")

    resolved_dept_name = dept.name if dept else (department or 'Engineering')
    resolved_dept_id = dept.id if dept else None

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        department=resolved_dept_name,
        department_id=resolved_dept_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
