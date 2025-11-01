from api.v1._shared.schemas import UserCreate, UserUpdate, UserDelete, UserResponse
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from api.v1.user.service import UserService
from api.utils.db_filter import FilterCondition

CreateType = UserCreate
UpdateType = UserUpdate
DeleteType = UserDelete
ResponseType = UserResponse
service = UserService

class UserUseCase:

    def __init__(self, db: Session):
        self.service = service(db)

    def list(
        self,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        search: Optional[str] = None,
        filter_conditions: Optional[List[FilterCondition]] = None
    ) -> List[ResponseType]:

        # Regra de negócio: 
        # Se receber search e filter_conditions priorizar search.
        if search and filter_conditions:
            filter_conditions = None
        
        return self.service.list(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            filter_conditions=filter_conditions
        )

    def get(self, id: UUID) -> ResponseType:
        return self.service.get(id)

    def create(self, obj: CreateType) -> ResponseType:
        return self.service.create(obj)

    def update(self, obj: UpdateType) -> ResponseType:
        return self.service.update(obj)

    def delete(self, obj: DeleteType) -> ResponseType:
        return self.service.delete(obj)