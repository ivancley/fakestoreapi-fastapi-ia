from datetime import datetime
from enum import Enum as PyEnum
import logging
from typing import List
import uuid

import pytz
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime, 
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import  declarative_base


Base = declarative_base()
tz = pytz.timezone('America/Sao_Paulo')
logger = logging.getLogger(__name__)


class PermissionType(str, PyEnum):
    USER = "USER"
    ADMIN = "ADMIN"

def get_permissions() -> List[str]:
    return [PermissionType.ADMIN.value, PermissionType.USER.value]


class BaseModel(Base):
    __abstract__ = True
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz), onupdate=lambda: datetime.now(tz), nullable=False)
    flg_deleted = Column(Boolean, default=False, nullable=False, server_default='false')


class User(BaseModel):
    __tablename__ = 'user'
       
    name = Column(String(255), nullable=False)   
    email = Column(String(255), nullable=False, unique=True, index=True)   
    password = Column(String(255), nullable=True)
    permissions = Column(ARRAY(String), nullable=False, default=list, server_default='{}')
