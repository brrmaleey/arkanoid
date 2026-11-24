"""Главное окно игры и игровой цикл."""

import tkinter as tk

from src.models.game_model import GameModel
from src.renderers.renderer import Renderer

WIDTH = 800
HEIGHT = 600
BACKGROUND = "#0b1020"
FRAME_DELAY_MS = 16      # примерно 60 кадров в секунду

# Названия клавиш в tkinter (в нижнем регистре). Кириллические
# варианты нужны, чтобы управление работало и в русской раскладке.
LEFT_KEYS = {"left", "a", "cyrillic_ef"}
RIGHT_KEYS = {"right", "d", "cyrillic_ve"}
PAUSE_KEYS = {"p", "cyrillic_ze", "escape"}
RESTART_KEYS = {"r", "cyrillic_ka"}


class App:
    """Окно с холстом, на котором идёт игра."""

    def __init__(self):
        """Создать окно, холст, модель игры и отрисовщик."""
        self.window = tk.Tk()
        self.window.title("Арканоид")
        self.window.resizable(False, False)

        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT,
                                bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack()

        self.model = GameModel(WIDTH, HEIGHT)
        self.renderer = Renderer(self.canvas)

        # Клавиши, которые сейчас зажаты. Платформа едет, пока клавиша
        # в этом множестве, поэтому движение плавное, без рывков автоповтора.
        self.pressed = set()
        self.window.bind("<KeyPress>", self.on_key_press)
        self.window.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", lambda event: self.model.launch())

    def on_key_press(self, event):
        """Запомнить нажатую клавишу и выполнить её команду."""
        key = event.keysym.lower()
        self.pressed.add(key)
        if key == "space":
            self.model.launch()
        elif key in PAUSE_KEYS:
            self.model.toggle_pause()
        elif key in RESTART_KEYS:
            self.model.new_game()

    def on_key_release(self, event):
        """Забыть отпущенную клавишу."""
        self.pressed.discard(event.keysym.lower())

    def on_mouse_move(self, event):
        """Двигать платформу за курсором мыши."""
        self.model.set_paddle_x(event.x)

    def paddle_direction(self):
        """Куда двигать платформу: -1 влево, 1 вправо, 0 стоять."""
        direction = 0
        if self.pressed & LEFT_KEYS:
            direction -= 1
        if self.pressed & RIGHT_KEYS:
            direction += 1
        return direction

    def update(self):
        """Обновить модель, перерисовать и запланировать следующий кадр."""
        self.model.move_paddle(self.paddle_direction())
        self.model.step()
        self.renderer.draw(self.model)
        self.window.after(FRAME_DELAY_MS, self.update)

    def run(self):
        """Запустить игровой цикл и главный цикл tkinter."""
        # Сразу забрать фокус, чтобы клавиши работали без клика по окну.
        self.window.focus_force()
        self.update()
        self.window.mainloop()
