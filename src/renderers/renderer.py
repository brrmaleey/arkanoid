"""Отрисовка игры на холсте tkinter."""

from src import __author__
from src.models.game_model import FIELD_TOP, GAME_OVER, PAUSED, READY, WIN
from src.models.levels import LEVELS

TEXT_COLOR = "white"
HINT_COLOR = "#9aa4b8"
LINE_COLOR = "#2a3350"
PADDLE_COLOR = "#c0c6d0"
PADDLE_EDGE_COLOR = "#ff5a5f"
PADDLE_EDGE_WIDTH = 12
BALL_COLOR = "white"

# Цвет кирпича по его виду (буквы те же, что в BRICK_TYPES).
BRICK_COLORS = {
    "S": "#c0c6d0",
    "R": "#ff5a5f",
    "O": "#ff9f40",
    "Y": "#ffd93d",
    "G": "#6bcb77",
    "B": "#4d96ff",
    "P": "#c77dff",
}
DAMAGED_BRICK_COLOR = "#6e7585"   # серебряный кирпич после первого удара

# Цвет и надпись капсулы для каждого вида бонуса.
BONUS_COLORS = {"expand": "#4d96ff", "slow": "#ff9f40", "life": "#ff5a5f"}
BONUS_LABELS = {"expand": "E", "slow": "S", "life": "♥"}
BONUS_TEXT_COLOR = "#0b1020"
BONUS_FONT = ("Helvetica", 11, "bold")

TITLE_FONT = ("Helvetica", 40, "bold")
MESSAGE_FONT = ("Helvetica", 28, "bold")
HINT_FONT = ("Helvetica", 14)
HUD_FONT = ("Helvetica", 14, "bold")


class Renderer:
    """Рисует кадр игры: панель счёта, кирпичи, платформу, мяч и надписи."""

    def __init__(self, canvas):
        """Запомнить холст, на котором будем рисовать."""
        self.canvas = canvas

    def draw(self, model):
        """Очистить холст и нарисовать текущее состояние игры."""
        self.canvas.delete("all")
        self.draw_hud(model)
        for brick in model.bricks:
            self.draw_brick(brick)
        for bonus in model.bonuses:
            self.draw_bonus(bonus)
        self.draw_paddle(model.paddle)
        self.draw_ball(model.ball)
        self.draw_message(model)

    def draw_hud(self, model):
        """Нарисовать панель со счётом, уровнем и жизнями."""
        middle = FIELD_TOP / 2
        self.canvas.create_text(15, middle, anchor="w", fill=TEXT_COLOR,
                                font=HUD_FONT,
                                text=f"Очки: {model.score}"
                                     f"    Рекорд: {model.best_score}")
        self.canvas.create_text(model.width / 2, middle, fill=TEXT_COLOR,
                                font=HUD_FONT,
                                text=f"Уровень {model.level}/{len(LEVELS)}")
        self.canvas.create_text(model.width - 15, middle, anchor="e",
                                fill=PADDLE_EDGE_COLOR, font=HUD_FONT,
                                text="♥" * model.lives)
        self.canvas.create_line(0, FIELD_TOP, model.width, FIELD_TOP,
                                fill=LINE_COLOR, width=2)

    def draw_brick(self, brick):
        """Нарисовать кирпич; повреждённый серебряный темнее."""
        color = BRICK_COLORS[brick.kind]
        if brick.hits_left < brick.max_hits:
            color = DAMAGED_BRICK_COLOR
        self.canvas.create_rectangle(brick.left, brick.top,
                                     brick.right, brick.bottom,
                                     fill=color, outline="")

    def draw_bonus(self, bonus):
        """Нарисовать капсулу бонуса с буквой внутри."""
        self.canvas.create_oval(bonus.left, bonus.top,
                                bonus.right, bonus.bottom,
                                fill=BONUS_COLORS[bonus.kind], outline="")
        self.canvas.create_text(bonus.x, bonus.y,
                                text=BONUS_LABELS[bonus.kind],
                                fill=BONUS_TEXT_COLOR, font=BONUS_FONT)

    def draw_paddle(self, paddle):
        """Нарисовать платформу: серая середина и красные края."""
        self.canvas.create_rectangle(paddle.left, paddle.top,
                                     paddle.right, paddle.bottom,
                                     fill=PADDLE_COLOR, outline="")
        self.canvas.create_rectangle(paddle.left, paddle.top,
                                     paddle.left + PADDLE_EDGE_WIDTH,
                                     paddle.bottom,
                                     fill=PADDLE_EDGE_COLOR, outline="")
        self.canvas.create_rectangle(paddle.right - PADDLE_EDGE_WIDTH,
                                     paddle.top, paddle.right, paddle.bottom,
                                     fill=PADDLE_EDGE_COLOR, outline="")

    def draw_ball(self, ball):
        """Нарисовать мяч."""
        self.canvas.create_oval(ball.left, ball.top, ball.right, ball.bottom,
                                fill=BALL_COLOR, outline="")

    def draw_message(self, model):
        """Нарисовать надпись по центру в зависимости от состояния игры."""
        if model.state == READY and model.level == 1 and model.score == 0:
            self.draw_text(model, 340, "АРКАНОИД", TITLE_FONT)
            self.draw_text(model, 385, f"Авторы: {__author__}, ПИ25-1",
                           HINT_FONT, HINT_COLOR)
            self.draw_text(model, 420, "Пробел — запустить мяч", HINT_FONT)
            self.draw_text(model, 445,
                           "← → или мышь — платформа    P — пауза"
                           "    R — заново", HINT_FONT, HINT_COLOR)
        elif model.state == READY:
            self.draw_text(model, 400, "Пробел — запустить мяч", HINT_FONT)
        elif model.state == PAUSED:
            self.draw_text(model, 380, "Пауза", MESSAGE_FONT)
            self.draw_text(model, 420, "P — продолжить", HINT_FONT)
        elif model.state == GAME_OVER:
            self.draw_text(model, 360, "Игра окончена", MESSAGE_FONT)
            self.draw_text(model, 400, f"Счёт: {model.score}", HINT_FONT)
            self.draw_text(model, 430, "R — сыграть ещё раз", HINT_FONT)
        elif model.state == WIN:
            self.draw_text(model, 360, "Победа!", MESSAGE_FONT)
            self.draw_text(model, 400, f"Счёт: {model.score}", HINT_FONT)
            self.draw_text(model, 430, "R — сыграть ещё раз", HINT_FONT)

    def draw_text(self, model, y, text, font, color=TEXT_COLOR):
        """Нарисовать строку текста по центру поля на высоте y."""
        self.canvas.create_text(model.width / 2, y, text=text,
                                fill=color, font=font)
