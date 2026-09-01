from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import users, map as map_router, games

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chess Map API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(map_router.router)
app.include_router(games.router)


@app.get("/health")
def health():
    return {"status": "ok"}
