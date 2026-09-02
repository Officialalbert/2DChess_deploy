import chess
import pytest


def test_valid_opening_move():
    board = chess.Board()
    move = board.parse_san("e4")
    board.push(move)
    assert board.fen().startswith("rnbqkbnr/pppppppp/8/8/4P3")


def test_invalid_move_raises():
    board = chess.Board()
    with pytest.raises(ValueError):
        board.parse_san("Ke9")  # такой клетки не существует


def test_illegal_move_for_position_raises():
    board = chess.Board()
    with pytest.raises(ValueError):
        # конём с h1 некуда так ходить в начальной позиции
        board.parse_san("Nh1-h3")


def test_checkmate_detected():
    board = chess.Board()
    # детский мат (Fool's mate) — самый короткий возможный мат
    for san in ["f3", "e5", "g4", "Qh4#"]:
        board.push_san(san)
    assert board.is_checkmate()
    assert board.result() == "0-1"
