#!/usr/bin/env python3

import unittest
import datetime
from tplogtools.timediff import how_many_seconds_to_time

class TestTimediff(unittest.TestCase):

    def test_how_many_seconds_to_time(self):
        now = datetime.datetime(year=2019, month=12, day=30, hour=21, minute=52, second=15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 54), 2 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 22, 0), 8 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 20, 52), 24 * 60 * 60 - 60 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 0), 24 * 60 * 60 - 52 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 52), 24 * 60 * 60 - 15)

if __name__ == '__main__':
    unittest.main()
