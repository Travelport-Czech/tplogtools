import datetime

def how_many_seconds_to_time(now, hour, minute):
    target_time = now.replace(hour=hour, minute=minute, second=0)
    if now >= target_time:
        target_time += datetime.timedelta(days=1)
    return int((target_time - now).total_seconds())

