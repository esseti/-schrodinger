from datetime import datetime
import os
import sys
from config import cfg


def _read_status_time(filename):
    """
    Gets the last status and time
    """
    f = open(filename, 'r')
    lineList = f.readlines()
    last = lineList[-1]
    status, time = last.split("$")
    time = datetime.strptime(time.strip(), "%H:%M")
    f.close()
    return status, time


def _write(filename, status, now):
    f = open(filename, 'a')
    f.writelines(status + "$" + now.strftime('%H:%M') + '\n')
    f.close()


def logit(d):
    """
    write the log
    """
    f = open(cfg["FOLDER"] + 'log.log', 'a')
    f.writelines(d + "\n")
    f.close()


def _init(filename, status, now):
    if not os.path.isfile(filename):
        _write(filename, status, now)

if __name__ == '__main__':

    status = sys.argv[1]
    # now time must be H:M if we use now and subtract prev time
    # we will subract today - 1900 01 01 H M
    # we have to use the now_time to have the same day
    # there should be a better way of doing this. But works for time being.
    now = datetime.now()
    now_time = datetime.strptime(now.strftime("%H:%M"), "%H:%M")

    filename = cfg["FOLDER"] + now.strftime('%Y%m%d') + ".txt"
    _init(filename, status, now)
    old_status, time = _read_status_time(filename)
    delta = ((now_time - time).total_seconds())

    if status == old_status:
        # no new status no party
        pass
    else:
        if cfg["DEBUG"]:
            s = "%s %s %s %s" % (now.strftime("%H:%M"), old_status, status, delta)
            logit(s)
        _write(filename, status, now)