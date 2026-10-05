import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY", "change-me")
ALGORITHM=os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str)->str: return pwd_context.hash(password)
def verify_password(plain:str, hashed:str)->bool: return pwd_context.verify(plain, hashed)
def create_access_token(user_id:int,email:str,role:str)->str:
    exp=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"user_id":user_id,"email":email,"role":role,"exp":exp}, SECRET_KEY, algorithm=ALGORITHM)
def decode_access_token(token:str)->dict:
    try: return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e: raise ValueError("Invalid or expired token") from e
