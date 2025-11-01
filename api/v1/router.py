from fastapi import APIRouter
from api.v1.user.controller import router as user_router
from api.v1.account.controller import router as account_router

routes = APIRouter(prefix="/api/v1")

routes.include_router(account_router)
routes.include_router(user_router)