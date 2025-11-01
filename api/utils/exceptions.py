from fastapi import HTTPException

def exception_400_BAD_REQUEST(detail: str) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=detail,
    )

def exception_401_UNAUTHORIZED(detail: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def exception_404_NOT_FOUND(detail: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=detail,
    )

def exception_500_INTERNAL_SERVER_ERROR(detail: str) -> HTTPException:
    return HTTPException(
        status_code=500,
        detail=detail,
    )