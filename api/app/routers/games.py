import chess
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..celery_app import celery_app

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=schemas.GameOut)
def create_game(payload: schemas.GameCreate, db: Session = Depends(get_db)):
    board = chess.Board()
    game = models.Game(
        white_name=payload.white_name,
        black_name=payload.black_name,
        fen=board.fen(),
        status=models.GameStatus.active,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


@router.get("/{game_id}", response_model=schemas.GameOut)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter_by(id=game_id).first()
    if not game:
        raise HTTPException(404, "Партия не найдена")
    return game


@router.post("/{game_id}/moves", response_model=schemas.GameOut)
def make_move(game_id: int, payload: schemas.MoveIn, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter_by(id=game_id).first()
    if not game:
        raise HTTPException(404, "Партия не найдена")
    if game.status != models.GameStatus.active:
        raise HTTPException(400, "Партия уже завершена")

    board = chess.Board(game.fen)

    try:
        move = board.parse_san(payload.san)
    except ValueError:
        raise HTTPException(400, f"Недопустимый ход: {payload.san}")

    board.push(move)
    game.fen = board.fen()

    move_number = len(game.moves) + 1
    db.add(
        models.Move(
            game_id=game.id,
            move_number=move_number,
            san=payload.san,
            fen_after=game.fen,
        )
    )

    if board.is_game_over():
        game.status = models.GameStatus.finished
        game.result = board.result()
        db.commit()
        # ставим задачу воркеру: прогнать партию через Stockfish и сохранить анализ
        celery_app.send_task("worker.tasks.analyze_game", args=[game.id])
    else:
        db.commit()

    db.refresh(game)
    return game


@router.get("/{game_id}/analysis", response_model=list[schemas.AnalysisOut])
def get_analysis(game_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.GameAnalysis).filter_by(game_id=game_id).order_by(
        models.GameAnalysis.move_number
    ).all()
    return rows
