import os

import chess
import chess.engine
from celery import Celery

from database import SessionLocal
import models

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")

app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@app.task(name="worker.tasks.analyze_game")
def analyze_game(game_id: int):
    """
    Прогоняет завершённую партию через Stockfish ход за ходом
    и сохраняет оценку позиции + лучший ход после каждого хода.
    """
    db = SessionLocal()
    try:
        game = db.query(models.Game).filter_by(id=game_id).first()
        if not game:
            return

        board = chess.Board()
        moves = (
            db.query(models.Move)
            .filter_by(game_id=game_id)
            .order_by(models.Move.move_number)
            .all()
        )

        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            for move in moves:
                board.push_san(move.san)
                info = engine.analyse(board, chess.engine.Limit(depth=12))
                score = info["score"].white().score(mate_score=100000)
                best = info.get("pv", [None])[0]

                db.add(
                    models.GameAnalysis(
                        game_id=game_id,
                        move_number=move.move_number,
                        eval_cp=score,
                        best_move=board.san(best) if best else None,
                    )
                )
            db.commit()
    finally:
        db.close()
