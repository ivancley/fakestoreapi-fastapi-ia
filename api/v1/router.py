from fastapi import APIRouter
from api.v1.user.controller import router as user_router

routes = APIRouter(prefix="/api/v1")

routes.include_router(user_router)