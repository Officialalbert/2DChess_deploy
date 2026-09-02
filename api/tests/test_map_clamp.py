from app.utils import clamp_position


def test_move_within_bounds():
    x, y = clamp_position(x=5, y=5, dx=1, dy=0, max_x=20, max_y=20)
    assert (x, y) == (6, 5)


def test_move_cannot_go_below_zero():
    x, y = clamp_position(x=0, y=0, dx=-1, dy=-1, max_x=20, max_y=20)
    assert (x, y) == (0, 0)


def test_move_cannot_exceed_max():
    x, y = clamp_position(x=20, y=20, dx=5, dy=5, max_x=20, max_y=20)
    assert (x, y) == (20, 20)
