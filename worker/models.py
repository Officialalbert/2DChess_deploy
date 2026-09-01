import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class GameStatus(str, enum.Enum):
    active = "active"
    finished = "finished"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("PlayerPosition", back_populates="user", uselist=False)


class PlayerPosition(Base):
    __tablename__ = "player_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="position")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_name = Column(String(64), nullable=False)
    black_name = Column(String(64), nullable=False)
    status = Column(Enum(GameStatus), default=GameStatus.active)
    result = Column(String(16), nullable=True)  # "1-0", "0-1", "1/2-1/2"
    fen = Column(Text, default="startpos")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    moves = relationship("Move", back_populates="game", order_by="Move.move_number")
    analysis = relationship("GameAnalysis", back_populates="game")


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    san = Column(String(16), nullable=False)
    fen_after = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="moves")


class GameAnalysis(Base):
    __tablename__ = "game_analysis"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    eval_cp = Column(Float, nullable=True)  # оценка позиции в сантипешках
    best_move = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="analysis")
