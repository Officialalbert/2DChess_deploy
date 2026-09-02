def clamp_position(x: int, y: int, dx: int, dy: int, max_x: int, max_y: int, min_v: int = 0):
    """
    Считает новую позицию игрока на карте с учётом границ поля.
    Вынесено из роутера в чистую функцию специально, чтобы тестировать
    без поднятой БД и без HTTP-запроса.
    """
    new_x = max(min_v, min(max_x, x + dx))
    new_y = max(min_v, min(max_y, y + dy))
    return new_x, new_y
