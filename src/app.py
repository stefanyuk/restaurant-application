from fastapi import FastAPI, status
from fastapi_pagination import add_pagination
from fastapi.exceptions import ValidationError
from fastapi.responses import JSONResponse
from src.apis import ROUTER_V1
from fastapi.encoders import jsonable_encoder

app = FastAPI()

add_pagination(app)

app.include_router(ROUTER_V1)


@app.exception_handler(ValidationError)
def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
