"""Игровые объекты: платформа, мяч, кирпич и бонус."""

import math

# Виды кирпичей: сколько очков дают и сколько ударов выдерживают.
# Буква — это обозначение кирпича в схеме уровня (см. levels.py).
BRICK_TYPES = {
    "S": {"points": 50, "hits": 2},    # серебряный, нужно два удара
    "R": {"points": 90, "hits": 1},    # красный
    "O": {"points": 60, "hits": 1},    # оранжевый
    "Y": {"points": 120, "hits": 1},   # жёлтый
    "G": {"points": 80, "hits": 1},    # зелёный
    "B": {"points": 100, "hits": 1},   # синий
    "P": {"points": 110, "hits": 1},   # фиолетовый
}


class GameObject:
    """Прямоугольный объект с центром в точке (x, y).

    Все объекты игры для простоты считаются прямоугольниками:
    так столкновения проверяются одной общей формулой.
    """

    def __init__(self, x, y, width, height):
        """Создать объект размером width x height с центром в (x, y)."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def left(self):
        """Левая граница."""
        return self.x - self.width / 2

    @property
    def right(self):
        """Правая граница."""
        return self.x + self.width / 2

    @property
    def top(self):
        """Верхняя граница."""
        return self.y - self.height / 2

    @property
    def bottom(self):
        """Нижняя граница."""
        return self.y + self.height / 2

    def overlaps(self, other):
        """Проверить, пересекается ли объект с другим.

        Два прямоугольника пересекаются, если каждый из них начинается
        раньше, чем заканчивается другой, и по x, и по y.
        """
        return (self.left < other.right and self.right > other.left
                and self.top < other.bottom and self.bottom > other.top)


class Paddle(GameObject):
    """Платформа игрока внизу экрана."""

    def __init__(self, x, y, width, height, speed):
        """Создать платформу, которая двигается со скоростью speed."""
        super().__init__(x, y, width, height)
        self.speed = speed

    def move(self, direction, field_width):
        """Сдвинуть платформу: direction = -1 влево, 1 вправо, 0 стоять."""
        self.move_to(self.x + direction * self.speed, field_width)

    def move_to(self, x, field_width):
        """Поставить центр платформы в x, не выпуская её за края поля."""
        half = self.width / 2
        self.x = max(half, min(field_width - half, x))


class Ball(GameObject):
    """Мяч. Скорость задаётся сдвигами dx и dy за один кадр."""

    def __init__(self, x, y, radius):
        """Создать неподвижный мяч радиуса radius."""
        super().__init__(x, y, radius * 2, radius * 2)
        self.radius = radius
        self.dx = 0
        self.dy = 0

    @property
    def speed(self):
        """Модуль скорости: длина вектора (dx, dy)."""
        return math.hypot(self.dx, self.dy)

    def set_direction(self, angle, speed):
        """Направить мяч вверх под углом angle к вертикали.

        Угол в градусах: 0 — строго вверх, плюс — вправо, минус — влево.
        Вектор скорости раскладываем на проекции через синус и косинус.
        Минус у dy, потому что на холсте ось y направлена вниз.
        """
        radians = math.radians(angle)
        self.dx = speed * math.sin(radians)
        self.dy = -speed * math.cos(radians)

    def set_speed(self, speed):
        """Изменить скорость, сохранив направление полёта."""
        factor = speed / self.speed
        self.dx *= factor
        self.dy *= factor


class Brick(GameObject):
    """Кирпич, который разбивается мячом."""

    def __init__(self, x, y, width, height, kind):
        """Создать кирпич вида kind (буква из BRICK_TYPES)."""
        super().__init__(x, y, width, height)
        self.kind = kind
        self.points = BRICK_TYPES[kind]["points"]
        self.max_hits = BRICK_TYPES[kind]["hits"]
        self.hits_left = self.max_hits

    def hit(self):
        """Ударить кирпич. Вернуть True, если он разбит."""
        self.hits_left -= 1
        return self.hits_left <= 0


class Bonus(GameObject):
    """Капсула с бонусом, которая падает из разбитого кирпича."""

    WIDTH = 36
    HEIGHT = 16
    SPEED = 3

    def __init__(self, x, y, kind):
        """Создать бонус вида kind в точке (x, y)."""
        super().__init__(x, y, self.WIDTH, self.HEIGHT)
        self.kind = kind

    def fall(self):
        """Сдвинуть бонус вниз."""
        self.y += self.SPEED
