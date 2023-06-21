from typing import Optional
from pydantic import BaseModel
from fastapi import Query


class BaseFilterParams(BaseModel):
    search: Optional[str] = Query(None)
    sort: Optional[str] = Query(None)
