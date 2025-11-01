from datetime import datetime, timedelta
import secrets
from typing import Any, Dict
from uuid import UUID
from decouple import config

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from api.utils.exceptions import (
    exception_400_BAD_REQUEST,
    exception_401_UNAUTHORIZED,
    exception_500_INTERNAL_SERVER_ERROR,
)
from api.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from api.v1._shared.schemas import (
    AccountLogin,
    AccountResponse,
    UserCreate,
    TokenResponse,
    RefreshTokenResponse,
)
from api.v1.user.service import UserService

ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AccountService:
    """
    Serviço para autenticação e gerenciamento de contas.
    """

    def __init__(self, db: Session):
        self.user_service = UserService(db)
        
    def register(self, data: UserCreate) -> AccountResponse:
        """
        Registrar nova conta.
        
        Args:
            data: Registration data
            
        Returns:
            A conta criada
        """
        # UserService.create() já valida se o email existe
        user = self.user_service.create(data)
        return user

    def login(self, data: AccountLogin) -> TokenResponse:
        """
        Autenticar usuário e gerar tokens.
        
        - email: Email do usuário
        - password: Senha do usuário
        
        Returns:
            TokenResponse
        """
        user = self.user_service.get_user_by_email(data.email, data.password)
        
        # Povoar dados do token
        token_data = {
            "sub": str(user.id), 
            "email": user.email,
            "name": user.name
        }

        # Gerar tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60, 
        )
    
    def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        """
        Gerenciar geração de novo access token usando refresh token.
        
        - refresh_token: Valid refresh token
        """
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub") 

        user = self.user_service.get(UUID(user_id))

        if not user:
            raise exception_401_UNAUTHORIZED(detail="Token inválido")

        # Povoar dados do token
        token_data = {
            "sub": str(user.id), 
            "email": user.email,
            "name": user.name
        }

        # Gerar novos tokens
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(ACCESS_TOKEN_EXPIRE_MINUTES) * 60,
        )
    