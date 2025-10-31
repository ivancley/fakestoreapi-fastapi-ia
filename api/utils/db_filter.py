from enum import Enum
import re
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, field_validator
from sqlalchemy import and_, or_

from api.utils.exceptions import exception_400_BAD_REQUEST


class FilterOperator(str, Enum):
    # Operadores de comparação
    EQ = "eq"
    NE = "ne"
    CONTAINS = "contains"


class FilterCondition(BaseModel):
    campo: str 
    operador: Optional[FilterOperator] 
    valor: str 
    
    @field_validator('operador')
    @classmethod
    def validate_operador(cls, v: str) -> str:
        if v not in FilterOperator:
            raise ValueError(f"Operador '{v}' não é válido. Operadores válidos: {FilterOperator}")
        return v

def validate_sort_field(
    sort_by: Optional[str], 
    sort_fields: List[str], 
    model_name: str = "modelo"
) -> None:
    """ Verifica se o campo de ordenação é válido """
    if sort_by and sort_by not in sort_fields:
        valid_fields = ", ".join(sort_fields)
        raise exception_400_BAD_REQUEST(
            detail=f"Campo de ordenação '{sort_by}' não é válido para {model_name}. Campos válidos: {valid_fields}"
        )


def build_search_filter(
    search: str, 
    model: Type[Any], 
    filter_fields: List[str]
):
    """ Pesquisa em todos os campos do modelo """
    filters = []
    for field in filter_fields:
        column = getattr(model, field)
        filters.append(column.ilike(f"%{search}%"))
    return or_(*filters)


def parse_filter_params(
    query_params: Dict[str, Any], 
    filter_fields: List[str],
    known_params: Optional[List[str]] 
) -> Optional[List[FilterCondition]]:
    """
    Essa função serve para extrair os filtros da requisição e retornar uma lista de FilterCondition.
    O que o usuário poderá enviar:  
    Ex: nome[eq]=Jose, nome[contains]=Jose ou nome=Jose
    
    Retorna uma listas de condições de filtro:
        List[FilterCondition] se houver filtros, None caso contrário
    """
    
    # Remover parâmetros conhecidos
    filter_query = {k: v for k, v in query_params.items() if k not in known_params}
    
    # Se não houver filtros, retorna None
    if not filter_query:
        return None
    
    filter_conditions = []
    pattern = re.compile(r'^(\w+)\[(\w+)\]$')
    
    for key, value in filter_query.items():
        match = pattern.match(key)
        
        if match:
            # encontrou campo no formato: campo[operador]=valor
            field_name = match.group(1)
            operator = match.group(2)
            
            # Validar campo
            if field_name not in filter_fields:
                valid_fields = ", ".join(filter_fields)
                raise exception_400_BAD_REQUEST(
                    detail=f"Campo '{field_name}' não é válido. Campos válidos: {valid_fields}"
                )
            
            # Criar FilterCondition (validação do operador será feita pelo Pydantic)
            try:
                filter_condition = FilterCondition(
                    campo=field_name,
                    operador=operator,
                    valor=str(value)
                )
                filter_conditions.append(filter_condition)
            except ValueError as e:
                raise exception_400_BAD_REQUEST(detail=str(e))
        else:
            # Formato simples: campo=valor (assume operador padrão 'eq')
            if key in filter_fields:
                try:
                    filter_condition = FilterCondition(
                        campo=key,
                        operador=FilterOperator.EQ.value,
                        valor=str(value)
                    )
                    filter_conditions.append(filter_condition)
                except ValueError as e:
                    raise exception_400_BAD_REQUEST(detail=str(e))
    
    return filter_conditions


def build_query_filter(
    filter_conditions: List[FilterCondition], 
    model: Type[Any], 
    filter_fields: List[str]
):
    """Constrói filtros a partir de lista de FilterCondition"""
    filters = []
    
    for condition in filter_conditions:
        # Validar campo
        if condition.campo not in filter_fields:
            valid_fields = ", ".join(filter_fields)
            raise exception_400_BAD_REQUEST(
                detail=f"Campo '{condition.campo}' não é válido. Campos válidos: {valid_fields}"
            )
        
        column = getattr(model, condition.campo)
        
        # Aplicar operador
        if condition.operador == FilterOperator.CONTAINS.value:
            filters.append(column.ilike(f"%{condition.valor}%"))
        elif condition.operador == FilterOperator.EQ.value:
            filters.append(column == condition.valor)
        elif condition.operador == FilterOperator.NE.value:
            filters.append(column != condition.valor)
    
    return and_(*filters) if filters else None

