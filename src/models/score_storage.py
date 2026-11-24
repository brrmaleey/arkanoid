"""Чтение и запись рекорда игры в JSON-файл."""

import json
from pathlib import Path


class ScoreStorage:
    """Хранилище лучшего результата между запусками игры."""

    def __init__(self, path=None):
        """Создать хранилище по заданному пути или в data/best_score.json."""
        default_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "best_score.json"
        )
        self.path = Path(path) if path is not None else default_path

    def load_best_score(self):
        """Вернуть сохранённый рекорд или 0, если файла нет или он повреждён."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return 0

        if not isinstance(data, dict):
            return 0
        score = data.get("best_score", 0)
        if isinstance(score, bool) or not isinstance(score, int) or score < 0:
            return 0
        return score

    def save_best_score(self, score):
        """Атомарно сохранить неотрицательный рекорд; вернуть False при ошибке IO."""
        if isinstance(score, bool) or not isinstance(score, int) or score < 0:
            raise ValueError("Рекорд должен быть неотрицательным целым числом")

        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps({"best_score": score}, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
        return True
