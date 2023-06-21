from fastapi import APIRouter, Depends
from src.apis.auth_dependencies import authenticated_admin_user
from src.apis.admin.categories.api import ROUTER as category_router
from src.apis.admin.products.api import ROUTER as products_router
from src.apis.admin.users.api import ROUTER as admin_users_router


ADMINS_ROUTER = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(authenticated_admin_user)],
)

ADMINS_ROUTER.include_router(category_router)
ADMINS_ROUTER.include_router(products_router)
ADMINS_ROUTER.include_router(admin_users_router)
