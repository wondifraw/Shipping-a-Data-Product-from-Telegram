import unittest
from src import scrape_telegram

class TestScrapeTelegram(unittest.TestCase):
    def test_convert_datetime(self):
        from datetime import datetime
        data = {'a': datetime(2020, 1, 1, 12, 0, 0)}
        result = scrape_telegram.convert_datetime(data)
        self.assertEqual(result['a'], '2020-01-01T12:00:00')

if __name__ == '__main__':
    unittest.main() 