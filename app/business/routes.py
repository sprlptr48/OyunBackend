import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import service
from .models import *
from .schemas import BusinessCreateResponse, BusinessCreateSchema, CustomBusinessCreationResponse, BranchCreateSchema, \
    CustomBranchCreationResponse, BranchCreateResponse, PointSchema
from ..core.database import get_db

logger = logging.getLogger('uvicorn.error')
business_router = APIRouter(prefix="/business", tags=["Auth"])

@business_router.post("/create", response_model=CustomBusinessCreationResponse)
def create_business_endpoint(business_data: BusinessCreateSchema, db: Session = Depends(get_db)):
    result = service.create_business(business_data, db)
    if not result:
        return CustomBusinessCreationResponse(success=False, message="Business Creation Fail")
    return CustomBusinessCreationResponse(
        success=True, message="Business Created", business=BusinessCreateResponse.model_validate(result.__dict__))

@business_router.post("/create-branch")
def create_branch_endpoint(branch_data: BranchCreateSchema, db: Session = Depends(get_db)):
    result = service.create_branch(branch_data, db)
    if not result:
        return CustomBranchCreationResponse(success=False, message="Business Creation Fail")
    return CustomBranchCreationResponse(
        success=True, message="Branch Created", branch=BranchCreateResponse.model_validate(result.__dict__))

@business_router.get("/near-me")
def business_near_me(location: PointSchema,db: Session = Depends(get_db)):
    raise HTTPException(status_code=500, detail="not implemented")
