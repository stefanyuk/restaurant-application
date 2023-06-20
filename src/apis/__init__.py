from fastapi import APIRouter

from src.apis.categories.api import ROUTER as category_router
from src.apis.products.api import ROUTER as products_router
from src.apis.users.api import ME_ROUTER, USERS_ROUTER, ADMINS_ROUTER
from src.apis.authentication.api import ROUTER as auth_router
from src.settings import settings

ROUTER_V1 = APIRouter(prefix=settings.api_v1_version_prefix)


ROUTER_V1.include_router(USERS_ROUTER)
ROUTER_V1.include_router(ME_ROUTER)
ROUTER_V1.include_router(ADMINS_ROUTER)
ROUTER_V1.include_router(category_router)
ROUTER_V1.include_router(products_router)
ROUTER_V1.include_router(auth_router)
