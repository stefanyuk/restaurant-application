from fastapi import APIRouter
from src.apis.users.api import ME_ROUTER, USERS_ROUTER
from src.apis.admin import ADMINS_ROUTER
from src.apis.authentication.api import ROUTER as auth_router
from src.settings import settings

ROUTER_V1 = APIRouter(prefix=settings.api_v1_version_prefix)


ROUTER_V1.include_router(USERS_ROUTER)
ROUTER_V1.include_router(ME_ROUTER)
ROUTER_V1.include_router(ADMINS_ROUTER)
ROUTER_V1.include_router(auth_router)
