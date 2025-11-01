from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from api.utils.db_filter import parse_filter_params
from api.utils.db_services import get_db
from api.utils.security import get_current_user
from api.v1._shared.models import User
from api.v1._shared.schemas import UserCreate, UserDelete, UserResponse, UserUpdate
from api.v1.user.use_case import UserUseCase


router = APIRouter(
    prefix="/users",
    tags=["Users"], 
)

filter_fields = ["name", "email"]


@router.get("", response_model=List[UserResponse])
async def list(
    request: Request,
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenação"),
    sort_dir: str = Query("asc", regex="^(asc|desc)$", description="Direção da ordenação (asc ou desc)"),
    search: Optional[str] = Query(None, description="Busca textual nos campos padrões (name, email)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Listar usuários
    
    - skip: Número de registros para pular (padrão: 0)
    - limit: Número máximo de registros a retornar (padrão: 10, máximo: 100)
    - sort_by: Campo para ordenação
    - sort_dir: Direção da ordenação - "asc" ou "desc"
    - search: Busca textual nos campos padrões
    - Filtros via URL: Use formato campo[operador]=valor
        - Ex: name[eq]=Jose ou name[contains]=Jo
        - Operadores válidos: eq, ne, contains
        - Campos válidos: name, email
    """
    # envio o request.query_params caso tenha filtros válidos preenche o filter_conditions
    # estou deixando o known_params dessa forma pois no futuro posso adicionar mais parâmetros
    filter_conditions = parse_filter_params(
        dict(request.query_params), 
        filter_fields,
        known_params=["skip", "limit", "sort_by", "sort_dir", "search"]
    )
    
    use_case = UserUseCase(db)
    return use_case.list(
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search=search,
        filter_conditions=filter_conditions
    )


@router.get("/{id}", response_model=UserResponse)
async def get_by_id(
    id: UUID = Path(..., description="ID do usuário"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    use_case = UserUseCase(db)
    return use_case.get(id)

"""
@router.post("", response_model=UserResponse, status_code=201)
async def create(
    User: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    use_case = UserUseCase(db)
    return use_case.create(User)
"""


@router.put("", response_model=UserResponse)
async def update(
    User: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    use_case = UserUseCase(db)
    return use_case.update(User)


@router.delete("", response_model=UserResponse)
async def delete(
    User: UserDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    # Deleta um usuário validando senha
    
    use_case = UserUseCase(db)
    return use_case.delete(User)