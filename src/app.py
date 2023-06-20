from fastapi import FastAPI
from fastapi_pagination import add_pagination

from src.apis import ROUTER_V1

app = FastAPI()

add_pagination(app)

app.include_router(ROUTER_V1)
