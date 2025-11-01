import jwt
from datetime import datetime, timedelta, timezone
from decouple import config
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from uuid import UUID

from api.utils.db_services import get_db
from api.utils.exceptions import exception_401_UNAUTHORIZED
from api.v1._shared.models import User


JWT_SECRET_KEY = str(config("JWT_SECRET_KEY")).strip()
JWT_ALGORITHM = str(config("JWT_ALGORITHM")).strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(config("REFRESH_TOKEN_EXPIRE_DAYS"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/account/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Cria um access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode('utf-8')
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Cria um refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode('utf-8')
    return encoded_jwt


def verify_refresh_token(token: str) -> dict:
    """Verifica se o refresh token é válido."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise exception_401_UNAUTHORIZED(
                detail="Token inválido: não é um refresh token",
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise exception_401_UNAUTHORIZED(
                detail="Token inválido: sem subject (user_id)",
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise exception_401_UNAUTHORIZED(
            detail="Refresh token expirado",
        )
    except jwt.JWTError:
        raise exception_401_UNAUTHORIZED(
            detail="Refresh token inválido",
        )

def authenticate_user(db: Session, email: str, senha: str) -> User:
    """Autentica um usuário pelo email e senha."""
    usuario = db.query(User).filter(User.email == email).first()
    if not usuario or not verify_password(senha, usuario.password):
        return False
    return usuario

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Retorna o usuário atual autenticado através do token JWT."""
    credentials_exception = exception_401_UNAUTHORIZED(
        detail="Could not validate credentials",
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except jwt.ExpiredSignatureError:
        raise exception_401_UNAUTHORIZED(
            detail="Token expirado. Faça login novamente.",
        )
    except jwt.InvalidSignatureError:
        raise exception_401_UNAUTHORIZED(
            detail="Token inválido: assinatura não confere.",
        )
    except jwt.PyJWTError:
        raise credentials_exception
    
    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception
    
    usuario = db.query(User).filter(
        User.id == user_uuid,
        User.flg_deleted == False
    ).first()
    
    if usuario is None:
        raise credentials_exception
    
    return usuario
