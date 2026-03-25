import os
import time
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import httpx

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-defense-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/github/callback", auto_error=False)

class TokenData(BaseModel):
    github_id: str
    username: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        github_id: str = payload.get("sub")
        username: str = payload.get("username")
        if github_id is None:
            raise credentials_exception
        return TokenData(github_id=github_id, username=username)
    except JWTError:
        raise credentials_exception

async def get_github_user(access_token: str):
    """
    Fetches user data from GitHub using an OAuth access token.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"}
        )
        if resp.status_code != 200:
            return None
        return resp.json()
