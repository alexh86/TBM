import time


class Animation_event:
    """
    This class stores information about custom animation events
    -Object
    -Interval
    -Last Update
    -End Time
    """
    def __init__(self, idnum, obj, interval, end_time):
        self.id = idnum
        self.obj = obj
        self.interval = interval
        self.end_time = end_time
        self.last_update = time.time()
