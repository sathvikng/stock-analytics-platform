from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import chat, stocks
from .api import auth, config
from .db.client import close_pool
from .db.migrations import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_migrations()
    yield
    await close_pool()


app = FastAPI(title="MeshDefend Stock Analytics", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(config.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
