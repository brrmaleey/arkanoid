"""Тесты хранилища рекорда."""

import json
import tempfile
import unittest
from pathlib import Path

from src.models.score_storage import ScoreStorage


class TestScoreStorage(unittest.TestCase):
    """Проверки загрузки и сохранения рекорда."""

    def test_missing_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ScoreStorage(Path(directory) / "best_score.json")
            self.assertEqual(storage.load_best_score(), 0)

    def test_save_and_load_score(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ScoreStorage(Path(directory) / "best_score.json")
            self.assertTrue(storage.save_best_score(420))
            self.assertEqual(storage.load_best_score(), 420)

    def test_corrupted_json_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_score.json"
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(ScoreStorage(path).load_best_score(), 0)

    def test_invalid_utf8_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_score.json"
            path.write_bytes(b"\xff")
            self.assertEqual(ScoreStorage(path).load_best_score(), 0)

    def test_invalid_score_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ScoreStorage(Path(directory) / "best_score.json")
            with self.assertRaises(ValueError):
                storage.save_best_score(-1)


    def test_missing_key_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_score.json"
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(ScoreStorage(path).load_best_score(), 0)

    def test_negative_score_in_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_score.json"
            path.write_text('{"best_score": -50}', encoding="utf-8")
            self.assertEqual(ScoreStorage(path).load_best_score(), 0)

    def test_string_score_in_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "best_score.json"
            path.write_text('{"best_score": "420"}', encoding="utf-8")
            self.assertEqual(ScoreStorage(path).load_best_score(), 0)


if __name__ == "__main__":
    unittest.main()
