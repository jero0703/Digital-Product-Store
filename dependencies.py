from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.utils.security import decode_access_token
bearer=HTTPBearer(auto_error=False)

def get_current_user(credentials:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    if not credentials: raise HTTPException(status_code=401,detail="Authentication credentials are required")
    try: payload=decode_access_token(credentials.credentials)
    except ValueError: raise HTTPException(status_code=401,detail="Invalid or expired token")
    user=db.query(User).filter(User.id==payload.get("user_id")).first()
    if not user: raise HTTPException(status_code=401,detail="User not found")
    if not user.is_active: raise HTTPException(status_code=403,detail="User account is inactive")
    return user

def get_current_admin(user:User=Depends(get_current_user)):
    if user.role!="ADMIN": raise HTTPException(status_code=403,detail="Admin access required")
    return user
