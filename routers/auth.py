from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import UserRegister,UserLogin,UserResponse,TokenResponse
from app.services.auth_service import register_user,authenticate_user,issue_token
router=APIRouter(prefix="/auth",tags=["Authentication"])

@router.post("/register",response_model=UserResponse,status_code=201,summary="Register a user")
def register(data:UserRegister,db:Session=Depends(get_db)):
    try:return register_user(db,data.name,data.email,data.password,data.role)
    except ValueError as e: raise HTTPException(409,str(e))

@router.post("/login",response_model=TokenResponse,summary="Login and receive JWT")
def login(data:UserLogin,db:Session=Depends(get_db)):
    user=authenticate_user(db,data.email,data.password)
    if not user: raise HTTPException(401,"Invalid email or password")
    if not user.is_active: raise HTTPException(403,"User account is inactive")
    return TokenResponse(access_token=issue_token(user))

@router.get("/me",response_model=UserResponse,summary="Get current user")
def me(user=Depends(get_current_user)): return user
