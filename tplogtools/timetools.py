#!/usr/bin/env python3
"""Extended tools for datetime"""

import datetime

def how_many_seconds_to_time(now, hour, minute):
    """Return amount seconds from now to given hour and minute"""
    target_time = now.replace(hour=hour, minute=minute, second=0)
    if now >= target_time:
        target_time += datetime.timedelta(days=1)
    return int((target_time - now).total_seconds())

def local_tz_now():
    """Return current time with local timezone"""
    return datetime.datetime.now(datetime.timezone.utc).astimezone()
