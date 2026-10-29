import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python', 'scripts', 'client', 'gui', 'mods'))
from x5_counter import count_tokens


class TestCounter(unittest.TestCase):
    def test_counts_active(self):
        data = {
            'battle_bonus_x5': {'count': 3},
            'battle_bonus_x5_extra': {'value': '2'},
            'other': {'count': 12}
        }
        self.assertEqual(count_tokens(data, 100), 5)

    def test_expired(self):
        self.assertEqual(count_tokens({
            'battle_bonus_x5': {'count': 3, 'expire': 99}
        }, 100), 0)

    def test_invalid(self):
        self.assertEqual(count_tokens({
            'battle_bonus_x5': {'count': 'wrong'}
        }, 100), 0)


if __name__ == '__main__':
    unittest.main()
