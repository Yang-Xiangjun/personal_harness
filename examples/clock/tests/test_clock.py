from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock_label import format_elapsed


class ClockLabelTests(unittest.TestCase):
    def test_minutes_and_seconds(self):
        self.assertEqual(format_elapsed(65), "01:05")

    def test_boundaries(self):
        for value, expected in [(0, "00:00"), (59, "00:59"), (60, "01:00"), (3600, "60:00")]:
            with self.subTest(value=value):
                self.assertEqual(format_elapsed(value), expected)


if __name__ == "__main__":
    unittest.main()
