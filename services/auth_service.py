from sqlalchemy.orm import Session
from app.models import User
from app.utils.security import hash_password, verify_password, create_access_token

def register_user(db:Session,name:str,email:str,password:str,role:str="USER")->User:
    email=email.lower().strip()
    if db.query(User).filter(User.email==email).first(): raise ValueError("Email is already registered")
    user=User(name=name.strip(),email=email,password_hash=hash_password(password),role=role)
    db.add(user); db.commit(); db.refresh(user); return user

def authenticate_user(db:Session,email:str,password:str):
    user=db.query(User).filter(User.email==email.lower().strip()).first()
    if not user or not verify_password(password,user.password_hash): return None
    return user

def issue_token(user:User): return create_access_token(user.id,user.email,user.role)
