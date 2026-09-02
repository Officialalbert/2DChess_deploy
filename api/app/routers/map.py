import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..redis_client import redis_client
from ..utils import clamp_position

router = APIRouter(prefix="/map", tags=["map"])

MAP_WIDTH = 20
MAP_HEIGHT = 20
ARENA_X, ARENA_Y = 10, 10  # клетка с шахматной ареной

@router.post("/move", response_model=schemas.PositionOut)
def move_player(payload: schemas.PositionUpdate, db: Session = Depends(get_db)):
    position = (
        db.query(models.PlayerPosition)
        .filter_by(user_id=payload.user_id)
        .first()
    )
    if not position:
        raise HTTPException(404, "Игрок не найден на карте")

    new_x, new_y = clamp_position(
        position.x, position.y, payload.dx, payload.dy, MAP_WIDTH, MAP_HEIGHT
    )
    position.x, position.y = new_x, new_y
    db.commit()
    db.refresh(position)

    redis_client.hset(
        "player_positions",
        str(payload.user_id),
        json.dumps({"x": new_x, "y": new_y}),
    )

    return schemas.PositionOut(user_id=payload.user_id, x=new_x, y=new_y)

@router.get("/players")
def list_players():
    cached = redis_client.hgetall("player_positions")
    return {
        "arena": {"x": ARENA_X, "y": ARENA_Y},
        "players": {uid: json.loads(pos) for uid, pos in cached.items()},
    }
    
    
