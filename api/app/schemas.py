from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class PositionUpdate(BaseModel):
    user_id: int
    dx: int
    dy: int


class PositionOut(BaseModel):
    user_id: int
    x: int
    y: int

    class Config:
        from_attributes = True


class GameCreate(BaseModel):
    white_name: str
    black_name: str


class MoveIn(BaseModel):
    san: str  # ход в алгебраической нотации, например "e4"


class MoveOut(BaseModel):
    move_number: int
    san: str
    fen_after: str
    created_at: datetime

    class Config:
        from_attributes = True


class GameOut(BaseModel):
    id: int
    white_name: str
    black_name: str
    status: str
    result: Optional[str]
    fen: str
    moves: List[MoveOut] = []

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    move_number: int
    eval_cp: Optional[float]
    best_move: Optional[str]

    class Config:
        from_attributes = True
