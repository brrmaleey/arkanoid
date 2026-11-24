"""Логика игры: уровни, движение мяча, столкновения, очки и жизни."""

import random

from src.models.game_objects import BRICK_TYPES, Ball, Bonus, Brick, Paddle
from src.models.levels import LEVELS

FIELD_TOP = 40           # выше этой линии панель со счётом, мяч туда не летит

PADDLE_WIDTH = 100
PADDLE_HEIGHT = 14
PADDLE_SPEED = 9
PADDLE_BOTTOM_GAP = 40   # расстояние от низа поля до центра платформы

BALL_RADIUS = 8
BALL_SPEED = 6           # скорость мяча на первом уровне, пикселей за кадр
BALL_SPEED_STEP = 1      # на сколько быстрее мяч на каждом следующем уровне
MAX_BOUNCE_ANGLE = 60    # самый острый угол отскока от платформы, градусы
MAX_LAUNCH_ANGLE = 30    # разброс угла при запуске мяча, градусы

BRICK_WIDTH = 70
BRICK_HEIGHT = 24
BRICK_GAP = 4
BRICKS_TOP = 80          # верхний край первого ряда кирпичей

START_LIVES = 3

# Бонусы: широкая платформа, медленный мяч и лишняя жизнь.
BONUS_KINDS = ("expand", "slow", "life")
BONUS_CHANCE = 0.15      # вероятность, что из кирпича выпадет бонус
EXPAND_FACTOR = 1.5      # во сколько раз шире становится платформа
SLOW_SPEED = 4           # скорость мяча после бонуса «медленный мяч»

# Состояния игры.
READY = "ready"          # мяч лежит на платформе и ждёт запуска
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"
WIN = "win"


from src.models.score_storage import ScoreStorage


class GameModel:
    """Всё состояние игры и правила, по которым оно меняется."""

    def __init__(self, width, height, bonus_chance=BONUS_CHANCE,
                 score_storage=None):
        self.width = width
        self.height = height
        self.bonus_chance = bonus_chance
        self.score_storage = score_storage or ScoreStorage()
        self.best_score = self.score_storage.load_best_score()
        self.new_game()

    def new_game(self):
        """Начать игру заново с первого уровня."""
        self.score = 0
        self.lives = START_LIVES
        self.level = 1
        self.paddle = Paddle(self.width / 2,
                             self.height - PADDLE_BOTTOM_GAP,
                             PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED)
        self.ball = Ball(0, 0, BALL_RADIUS)
        self.load_level()

    def load_level(self):
        """Построить кирпичи текущего уровня по его схеме."""
        layout = LEVELS[self.level - 1]
        step_x = BRICK_WIDTH + BRICK_GAP
        step_y = BRICK_HEIGHT + BRICK_GAP
        # Ряд кирпичей ставим по центру поля: считаем ширину ряда
        # и отступаем от левого края половину оставшегося места.
        row_width = len(layout[0]) * step_x - BRICK_GAP
        start_x = (self.width - row_width) / 2 + BRICK_WIDTH / 2
        start_y = BRICKS_TOP + BRICK_HEIGHT / 2

        self.bricks = []
        for row, line in enumerate(layout):
            for col, kind in enumerate(line):
                if kind in BRICK_TYPES:
                    brick = Brick(start_x + col * step_x,
                                  start_y + row * step_y,
                                  BRICK_WIDTH, BRICK_HEIGHT, kind)
                    self.bricks.append(brick)
        self.reset_ball()

    def reset_ball(self):
        """Убрать бонусы, положить мяч на платформу и ждать запуска."""
        self.bonuses = []
        self.paddle.width = PADDLE_WIDTH
        self.state = READY
        self.stick_ball_to_paddle()

    def stick_ball_to_paddle(self):
        """Поставить мяч на середину платформы."""
        self.ball.x = self.paddle.x
        self.ball.y = self.paddle.top - self.ball.radius

    def level_speed(self):
        """Скорость мяча на текущем уровне."""
        return BALL_SPEED + (self.level - 1) * BALL_SPEED_STEP

    def can_move_paddle(self):
        """Платформой можно управлять, только пока идёт игра."""
        return self.state in (READY, PLAYING)

    def move_paddle(self, direction):
        """Сдвинуть платформу клавишами: -1 влево, 1 вправо."""
        if self.can_move_paddle():
            self.paddle.move(direction, self.width)

    def set_paddle_x(self, x):
        """Поставить платформу под курсор мыши."""
        if self.can_move_paddle():
            self.paddle.move_to(x, self.width)

    def launch(self):
        """Запустить мяч с платформы под случайным углом вверх."""
        if self.state == READY:
            angle = random.uniform(-MAX_LAUNCH_ANGLE, MAX_LAUNCH_ANGLE)
            self.ball.set_direction(angle, self.level_speed())
            self.state = PLAYING

    def toggle_pause(self):
        """Поставить игру на паузу или снять с паузы."""
        if self.state == PLAYING:
            self.state = PAUSED
        elif self.state == PAUSED:
            self.state = PLAYING

    def step(self):
        """Один кадр игры."""
        if self.state == READY:
            self.stick_ball_to_paddle()
        elif self.state == PLAYING:
            self.move_ball()
            self.move_bonuses()
            self.check_ball_lost()
            self.check_level_cleared()

    def move_ball(self):
        """Сдвинуть мяч и обработать все отскоки.

        Мяч двигается в два шага: сначала по x, потом по y. Если после
        шага по x мяч задел кирпич, значит удар пришёлся в бок кирпича
        и разворачивать нужно dx. Если после шага по y — удар сверху
        или снизу, разворачиваем dy. Так не нужно вычислять, в какую
        именно сторону кирпича попал мяч.
        """
        ball = self.ball

        ball.x += ball.dx
        if ball.left < 0:
            ball.x = ball.radius
            ball.dx = abs(ball.dx)
        elif ball.right > self.width:
            ball.x = self.width - ball.radius
            ball.dx = -abs(ball.dx)
        elif self.hit_brick():
            ball.x -= ball.dx
            ball.dx = -ball.dx

        ball.y += ball.dy
        if ball.top < FIELD_TOP:
            ball.y = FIELD_TOP + ball.radius
            ball.dy = abs(ball.dy)
        elif self.hit_brick():
            ball.y -= ball.dy
            ball.dy = -ball.dy
        elif (ball.dy > 0 and ball.overlaps(self.paddle)
              and ball.y < self.paddle.y):
            self.bounce_from_paddle()

    def hit_brick(self):
        """Ударить кирпич, которого касается мяч.

        Вернуть True, если удар был.
        """
        for brick in self.bricks:
            if self.ball.overlaps(brick):
                if brick.hit():
                    self.bricks.remove(brick)
                    self.add_score(brick.points)
                    self.maybe_drop_bonus(brick)
                return True
        return False

    def maybe_drop_bonus(self, brick):
        """С вероятностью bonus_chance выбросить бонус из кирпича."""
        if random.random() < self.bonus_chance:
            kind = random.choice(BONUS_KINDS)
            self.bonuses.append(Bonus(brick.x, brick.y, kind))

    def move_bonuses(self):
        """Сдвинуть бонусы вниз и применить те, что поймала платформа."""
        caught = []
        for bonus in self.bonuses:
            bonus.fall()
            if bonus.overlaps(self.paddle):
                caught.append(bonus)
                self.apply_bonus(bonus.kind)
        # Оставляем только непойманные бонусы, которые ещё не упали за край.
        self.bonuses = [bonus for bonus in self.bonuses
                        if bonus not in caught and bonus.top < self.height]

    def apply_bonus(self, kind):
        """Применить пойманный бонус."""
        if kind == "expand":
            self.paddle.width = PADDLE_WIDTH * EXPAND_FACTOR
            # Широкая платформа не должна вылезти за край поля.
            self.paddle.move_to(self.paddle.x, self.width)
        elif kind == "slow":
            self.ball.set_speed(SLOW_SPEED)
        elif kind == "life":
            self.lives += 1

    def bounce_from_paddle(self):
        """Отбить мяч платформой.

        Угол отскока зависит от того, куда мяч попал: offset — это
        смещение от центра платформы от -1 (левый край) до 1 (правый).
        Умножаем его на MAX_BOUNCE_ANGLE и получаем угол от вертикали.
        Так игрок может направлять мяч: попал краем — мяч уходит в сторону.
        """
        half = self.paddle.width / 2
        offset = (self.ball.x - self.paddle.x) / half
        offset = max(-1, min(1, offset))
        self.ball.set_direction(offset * MAX_BOUNCE_ANGLE, self.ball.speed)
        self.ball.y = self.paddle.top - self.ball.radius

    def add_score(self, points):
        """???????? ???? ? ????????? ????? ??????."""
        self.score += points
        if self.score > self.best_score:
            self.best_score = self.score
            self.score_storage.save_best_score(self.best_score)

    def check_ball_lost(self):
        """Если мяч упал ниже поля, отнять жизнь."""
        if self.ball.top > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.state = GAME_OVER
            else:
                self.reset_ball()

    def check_level_cleared(self):
        """Если кирпичей не осталось, перейти на следующий уровень."""
        if self.state == PLAYING and not self.bricks:
            if self.level == len(LEVELS):
                self.state = WIN
            else:
                self.level += 1
                self.load_level()
