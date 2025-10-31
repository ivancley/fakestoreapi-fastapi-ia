from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from api.v1._shared.models import BaseModel as CustomBaseModel, get_permissions



class CustomBaseModel(BaseModel):
    flg_deleted: bool = Field(False)
    model_config: Dict[str, Any] = {
        "arbitrary_types_allowed": True,
        "from_attributes": True 
    }


class UsuarioBase(CustomBaseModel):
    name: str
    email: str


class UsuarioCreate(BaseModel): 
    name: str 
    email: str 
    password: str
    permissions: Optional[List[str]] = Field(default=get_permissions()[0])


class UsuarioUpdate(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    permissions: Optional[List[str]] = None
    
    @model_validator(mode='after')
    def validate_permissoes(self):
        if self.permissions is not None:
            valid_perms = set(get_permissions())
            invalid = set(self.permissions) - valid_perms
            if invalid:
                raise ValueError(f"Permissões inválidas: {', '.join(invalid)}. Permissões válidas: {', '.join(valid_perms)}")
        return self


class UsuarioResponse(CustomBaseModel):
    id: UUID 
    name: str
    email: str
    permissions: List[str]
    created_at: datetime
    updated_at: datetime


class UsuarioDelete(BaseModel):
    id: UUID
    password: str

    