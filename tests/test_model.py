"""Тесты для игровых объектов и логики игры."""

import unittest
import tempfile
from pathlib import Path
from src.models.score_storage import ScoreStorage

from src.models.game_model import (BALL_SPEED, FIELD_TOP, GAME_OVER,
                                   PADDLE_WIDTH, PAUSED, PLAYING, READY,
                                   SLOW_SPEED, START_LIVES, WIN, GameModel)
from src.models.game_objects import Ball, Bonus, Brick, Paddle
from src.models.levels import LEVELS

WIDTH = 800
HEIGHT = 600


def make_model():
    """Создать игру без случайных бонусов и с запущенным мячом."""
    model = GameModel(WIDTH, HEIGHT, bonus_chance=0)
    model.launch()
    return model


class TestGameObjects(unittest.TestCase):
    """Проверки классов Paddle, Ball и Brick."""

    def test_overlaps(self):
        """Пересечение прямоугольников определяется верно."""
        brick = Brick(100, 100, 70, 24, "R")
        self.assertTrue(Ball(100, 115, 8).overlaps(brick))
        self.assertFalse(Ball(100, 140, 8).overlaps(brick))

    def test_paddle_stays_in_field(self):
        """Платформа не выезжает за края поля."""
        paddle = Paddle(60, 560, 100, 14, 9)
        for _ in range(20):
            paddle.move(-1, WIDTH)
        self.assertEqual(paddle.left, 0)
        paddle.move_to(10000, WIDTH)
        self.assertEqual(paddle.right, WIDTH)

    def test_ball_direction(self):
        """Угол 0 — мяч летит строго вверх с заданной скоростью."""
        ball = Ball(0, 0, 8)
        ball.set_direction(0, 5)
        self.assertAlmostEqual(ball.dx, 0)
        self.assertAlmostEqual(ball.dy, -5)
        ball.set_speed(10)
        self.assertAlmostEqual(ball.speed, 10)

    def test_silver_brick_needs_two_hits(self):
        """Серебряный кирпич разбивается только со второго удара."""
        brick = Brick(0, 0, 70, 24, "S")
        self.assertFalse(brick.hit())
        self.assertTrue(brick.hit())


class TestGameModel(unittest.TestCase):
    """Проверки класса GameModel."""

    def test_new_game(self):
        """Новая игра: первый уровень, все кирпичи, мяч на платформе."""
        model = GameModel(WIDTH, HEIGHT)
        bricks = sum(len(line) - line.count(".") for line in LEVELS[0])
        self.assertEqual(model.state, READY)
        self.assertEqual(model.lives, START_LIVES)
        self.assertEqual(len(model.bricks), bricks)
        self.assertEqual(model.ball.x, model.paddle.x)

    def test_launch(self):
        """После запуска мяч летит вверх со скоростью уровня."""
        model = make_model()
        self.assertEqual(model.state, PLAYING)
        self.assertLess(model.ball.dy, 0)
        self.assertAlmostEqual(model.ball.speed, BALL_SPEED)

    def test_bounce_from_walls(self):
        """Мяч отскакивает от левой стены и от потолка."""
        model = make_model()
        model.bricks = []
        model.ball.x, model.ball.y = 10, 300
        model.ball.dx, model.ball.dy = -5, 0
        model.move_ball()
        self.assertGreater(model.ball.dx, 0)

        model.ball.x, model.ball.y = 400, FIELD_TOP + 10
        model.ball.dx, model.ball.dy = 0, -5
        model.move_ball()
        self.assertGreater(model.ball.dy, 0)

    def test_hit_brick(self):
        """Мяч разбивает кирпич, отскакивает и приносит очки."""
        model = make_model()
        brick = Brick(400, 200, 70, 24, "R")
        model.bricks = [brick, Brick(100, 100, 70, 24, "R")]
        model.ball.x, model.ball.y = 400, 222
        model.ball.dx, model.ball.dy = 0, -5
        model.move_ball()
        self.assertNotIn(brick, model.bricks)
        self.assertEqual(model.score, brick.points)
        self.assertGreater(model.ball.dy, 0)

    def test_paddle_bounce_angle(self):
        """Удар правым краем платформы отправляет мяч вверх и вправо."""
        model = make_model()
        model.ball.x = model.paddle.right - 5
        model.ball.dx, model.ball.dy = 0, 5
        model.bounce_from_paddle()
        self.assertLess(model.ball.dy, 0)
        self.assertGreater(model.ball.dx, 0)

    def test_lose_life_and_game_over(self):
        """Упавший мяч отнимает жизнь, без жизней — конец игры."""
        model = make_model()
        model.ball.y = HEIGHT + 50
        model.step()
        self.assertEqual(model.lives, START_LIVES - 1)
        self.assertEqual(model.state, READY)

        model.lives = 1
        model.launch()
        model.ball.y = HEIGHT + 50
        model.step()
        self.assertEqual(model.state, GAME_OVER)

    def test_next_level_and_win(self):
        """Без кирпичей — следующий уровень, после последнего — победа."""
        model = make_model()
        model.bricks = []
        model.step()
        self.assertEqual(model.level, 2)
        self.assertEqual(model.state, READY)

        model.level = len(LEVELS)
        model.launch()
        model.bricks = []
        model.step()
        self.assertEqual(model.state, WIN)

    def test_pause(self):
        """На паузе мяч стоит на месте."""
        model = make_model()
        model.toggle_pause()
        self.assertEqual(model.state, PAUSED)
        x, y = model.ball.x, model.ball.y
        model.step()
        self.assertEqual((model.ball.x, model.ball.y), (x, y))
        model.toggle_pause()
        self.assertEqual(model.state, PLAYING)

    def test_bonuses(self):
        """Пойманные бонусы расширяют платформу, замедляют мяч и дают жизнь."""
        model = make_model()
        model.apply_bonus("expand")
        self.assertGreater(model.paddle.width, PADDLE_WIDTH)
        model.apply_bonus("slow")
        self.assertAlmostEqual(model.ball.speed, SLOW_SPEED)
        model.apply_bonus("life")
        self.assertEqual(model.lives, START_LIVES + 1)

    def test_bonus_is_caught_by_paddle(self):
        """Бонус, упавший на платформу, применяется и исчезает."""
        model = make_model()
        model.bonuses = [Bonus(model.paddle.x, model.paddle.top - 5, "life")]
        model.move_bonuses()
        self.assertEqual(model.bonuses, [])
        self.assertEqual(model.lives, START_LIVES + 1)


    def test_best_score_persists_across_models(self):
        """?????? ??????????? ? ????????? ? ??????????? ????? ???????."""
        with tempfile.TemporaryDirectory() as directory:
            storage = ScoreStorage(Path(directory) / "best_score.json")
            model = GameModel(480, 640, score_storage=storage)
            model.add_score(420)

            reloaded_model = GameModel(480, 640, score_storage=storage)
            self.assertEqual(reloaded_model.best_score, 420)


    def test_lower_score_does_not_overwrite_best_score(self):
        """????? ????????? ???? ??????? ?? ?????????????? ??????????? ??????."""
        with tempfile.TemporaryDirectory() as directory:
            storage = ScoreStorage(Path(directory) / "best_score.json")
            storage.save_best_score(420)

            model = GameModel(480, 640, score_storage=storage)
            model.add_score(100)

            self.assertEqual(model.best_score, 420)
            self.assertEqual(storage.load_best_score(), 420)


if __name__ == "__main__":
    unittest.main()
