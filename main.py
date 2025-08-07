from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.database import engine, Base
from app.auth.routes import auth_router
from app.core.limiter import limiter

from app.business.routes import business_router

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    #Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(business_router)

app.state.limiter = limiter

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(SlowAPIMiddleware)
