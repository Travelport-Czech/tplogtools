#!/usr/bin/env python3

import unittest
import subprocess
import datetime
from tplogtools.timetools import how_many_seconds_to_time, local_tz_now

class TestTimediff(unittest.TestCase):

    def test_how_many_seconds_to_time(self):
        now = datetime.datetime(year=2019, month=12, day=30, hour=21, minute=52, second=15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 54), 2 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 22, 0), 8 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 20, 52), 24 * 60 * 60 - 60 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 0), 24 * 60 * 60 - 52 * 60 - 15)
        self.assertEqual(how_many_seconds_to_time(now, 21, 52), 24 * 60 * 60 - 15)

    def test_local_tz_now(self):
        """Test detection of local timezone"""
        now = local_tz_now()
        date_result = subprocess.run(['date', '+%Z %z'],  stdout=subprocess.PIPE, universal_newlines=True)
        tz_name, tz_offset = date_result.stdout.strip().split(' ')
        self.assertEqual(tz_offset, now.strftime('%z'))
        self.assertEqual(tz_name, now.strftime('%Z'))
