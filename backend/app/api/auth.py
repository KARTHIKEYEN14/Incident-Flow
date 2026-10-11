"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user_id
from app.db.session import get_db
from app.schemas.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse, DepartmentResponse
from app.services.auth_service import (
    authenticate_user, 
    create_user, 
    get_user_by_id, 
    get_user_by_email,
    get_department_by_id,
    list_departments,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/departments", response_model=list[DepartmentResponse])
async def get_departments(db: AsyncSession = Depends(get_db)):
    """List all available departments for employee registration."""
    departments = await list_departments(db)
    return [DepartmentResponse.model_validate(d) for d in departments]


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    dept = await get_department_by_id(db, data.department_id)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Selected department does not exist. Please choose a valid department."
        )

    user = await create_user(
        db, 
        name=data.name, 
        email=data.email, 
        password=data.password, 
        department_id=dept.id,
        department=dept.name,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all users (for participant selection)."""
    from sqlalchemy import select
    from app.models.models import User
    result = await db.execute(select(User).order_by(User.name))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]
