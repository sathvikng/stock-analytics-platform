from fastapi import APIRouter, HTTPException, Depends
from asyncpg.exceptions import UniqueViolationError
from ..models.request import SignupRequest, LoginRequest
from ..models.response import AuthResponse, AuthUser
from ..services.auth import hash_password, verify_password, create_jwt
from ..db.queries import create_user, get_user_by_email, get_user_by_id
from ..middleware.auth import get_current_user

router = APIRouter()


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    try:
        user = await create_user(req.email, hash_password(req.password), req.display_name)
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="Email already registered")
    token = create_jwt(str(user["id"]))
    return AuthResponse(access_token=token, user=AuthUser(
        id=str(user["id"]), email=user["email"], display_name=user.get("display_name")
    ))


@router.post("/auth/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(str(user["id"]))
    return AuthResponse(access_token=token, user=AuthUser(
        id=str(user["id"]), email=user["email"], display_name=user.get("display_name")
    ))


@router.get("/auth/me", response_model=AuthUser)
async def me(user_id: str = Depends(get_current_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return AuthUser(id=str(user["id"]), email=user["email"], display_name=user.get("display_name"))
