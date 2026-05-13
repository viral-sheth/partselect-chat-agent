from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from db.database import init_db, AsyncSessionLocal
from db.seed import seed_if_empty
from api.chat import router as chat_router
from api.cart import router as cart_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_if_empty(db)
    yield


app = FastAPI(
    title="PartSelect Chat Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/v1")
app.include_router(cart_router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
