from api.v1._shared.shemas import UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioDelete
from api.v1._shared.models import User
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from api.utils.db_filter import (
    validate_sort_field, 
    build_search_filter, 
    build_query_filter,
    FilterCondition
)
from api.utils.security import get_password_hash, verify_password
from api.utils.exceptions import exception_404_NOT_FOUND, exception_400_BAD_REQUEST, exception_401_UNAUTHORIZED

# Utilizo essa estratégia para gerar novos arquivos services 
# trocando apenas o nome do arquivo e o objeto que será usado.
CreateType = UsuarioCreate
UpdateType = UsuarioUpdate
DeleteType = UsuarioDelete
ResponseType = UsuarioResponse
ObjectType = User

filter_fields = ["name", "email"]
sort_fields = ["name", "email"]

class UserService:

    def __init__(self, db: Session):
        self.db = db

    def _to_response(self, user: ObjectType) -> ResponseType:
        """Converte objeto User para UsuarioResponse usando spread"""
        return ResponseType.model_validate({
            **user.__dict__,
            "permissions": user.permissions or []
        })

    def list(
        self,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        search: Optional[str] = None,
        filter_conditions: Optional[List[FilterCondition]] = None
    ) -> List[ResponseType]:
        # Listagem com paginação, ordenação e filtros
        query = self.db.query(ObjectType).filter(ObjectType.flg_deleted == False)

        # Aplicar filtros (preferência por search)
        if search:
            query = query.filter(build_search_filter(search, ObjectType, filter_fields))
        elif filter_conditions:
            filter_result = build_query_filter(filter_conditions, ObjectType, filter_fields)
            if filter_result is not None:
                query = query.filter(filter_result)

        # Validar e aplicar ordenação
        if sort_by:
            # Aqui eu valido e se tiver erro eu gero uma Exception
            validate_sort_field(sort_by, sort_fields, "usuário")
            column = getattr(ObjectType, sort_by)
            if sort_dir.lower() == "desc":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            # Ordenação padrão por created_at desc
            query = query.order_by(ObjectType.created_at.desc())

        # Aplicar paginação
        users = query.offset(skip).limit(limit).all()

        # Converter para schema de resposta
        return [self._to_response(user) for user in users]

    def get(self, id: UUID) -> ResponseType:
        user = self.db.query(ObjectType).filter(
            ObjectType.id == id,
            ObjectType.flg_deleted == False
        ).first()
        
        if not user:
            raise exception_404_NOT_FOUND(detail=f"Usuário com ID {id} não encontrado")
        
        return self._to_response(user)

    def create(self, obj: CreateType) -> ResponseType:
        # Verificar se email já existe
        existing_user = self.db.query(ObjectType).filter(
            ObjectType.email == obj.email,
            ObjectType.flg_deleted == False
        ).first()
        
        if existing_user:
            raise exception_400_BAD_REQUEST(detail=f"Email {obj.email} já está em uso")
        
        # Hash da senha
        hashed_password = get_password_hash(obj.password)
        
        # Criar usuário
        new_user = ObjectType(
            name=obj.name,
            email=obj.email,
            password=hashed_password,
            permissions=obj.permissions or []
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return self._to_response(new_user)

    def update(self, obj: UpdateType) -> ResponseType:
        user = self.db.query(ObjectType).filter(
            ObjectType.id == obj.id,
            ObjectType.flg_deleted == False
        ).first()
        
        if not user:
            raise exception_404_NOT_FOUND(detail=f"Usuário com ID {obj.id} não encontrado")
        
        # Verificar se email já existe em outro usuário
        if obj.email and obj.email != user.email:
            existing_user = self.db.query(ObjectType).filter(
                ObjectType.email == obj.email,
                ObjectType.flg_deleted == False,
                ObjectType.id != obj.id
            ).first()
            
            if existing_user:
                raise exception_400_BAD_REQUEST(detail=f"Email {obj.email} já está em uso")
        
        # Atualizar campos se fornecidos usando model_dump (exclui None e id)
        update_data = obj.model_dump(exclude_none=True, exclude={"id", "password"})
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        # Password precisa de hash especial
        if obj.password is not None:
            user.password = get_password_hash(obj.password)
        
        self.db.commit()
        self.db.refresh(user)
        
        return self._to_response(user)

    def delete(self, obj: DeleteType) -> ResponseType:
        # Deleta um usuário após validar a senha
        user = self.db.query(ObjectType).filter(
            ObjectType.id == obj.id,
            ObjectType.flg_deleted == False
        ).first()
        
        if not user:
            raise exception_404_NOT_FOUND(detail=f"Usuário com ID {obj.id} não encontrado")
        
        # Validar senha
        if not verify_password(obj.password, user.password):
            raise exception_401_UNAUTHORIZED(detail="Senha incorreta")
        
        # Soft delete
        user.flg_deleted = True
        self.db.commit()
        
        return self._to_response(user)