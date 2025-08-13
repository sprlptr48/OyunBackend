import random
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
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

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:51208",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or your specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(SlowAPIMiddleware)

@app.get("/", include_in_schema=False)
def root_redirect():
    """
    Redirects the root URL to the API documentation.
    """
    if random.Random().random() >= 0.5:
        return {"message": "Hello Word"}
    return RedirectResponse(url="/docs")