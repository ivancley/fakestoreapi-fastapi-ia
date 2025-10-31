import pytz
import jwt
from datetime import datetime, timedelta

from decouple import config
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.utils.db_services import get_db
from api.utils.exceptions import exception_401_UNAUTHORIZED
from api.v1._shared.models import User


JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS = config("REFRESH_TOKEN_EXPIRE_DAYS")
tz = pytz.timezone('America/Sao_Paulo')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/conta/login/oauth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """
    Cria um access token.
    """
    to_encode = data.copy()
    expire = datetime.now(tz) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Cria um refresh token.
    """
    to_encode = data.copy()
    expire = datetime.now(tz) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> dict:
    """
    Verifica se o refresh token é válido.
    
    Args:
        token: O refresh token a ser verificado
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verificar se é um refresh token
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

def authenticate_user(
    db: Session, 
    email: str, senha: str) -> User:
    usuario = db.query(User).filter(User.email == email).first()
    if not usuario:
        return False
    if not verify_password(senha, usuario.password):
        return False
    return usuario

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """ 
    Autentica um usuário por email e senha.
    
    Args:
        db: Session do banco de dados
        email: Email do usuário
        senha: Senha do usuário
        
    Returns:
        User: Usuário autenticado
    """
    credentials_exception = exception_401_UNAUTHORIZED(
        detail="Credenciais inválidas",
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise credentials_exception
            
        user_id: str = payload.get("sub") 
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    usuario = db.query(User).filter(User.id == user_id).first()
    if usuario is None:
        raise credentials_exception
    return usuario
