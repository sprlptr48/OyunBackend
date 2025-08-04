import logging

from fastapi import APIRouter

from .models import *

logger = logging.getLogger('uvicorn.error')
business_router = APIRouter(prefix="/business", tags=["Auth"])
