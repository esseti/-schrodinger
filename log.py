from datetime import datetime, timedelta
import os
import sys
from config import cfg
import argparse

from utils import _load_file


def _write(filename, log, time):
    if cfg['DEBUG']:
        print("write")
    os.chdir(cfg['FOLDER'])
    f = open(filename, 'a')
    data = log.split("|")
    f.writelines(log + "$" + time.strftime('%H:%M') + '\n')
    f.close()


argparser = argparse.ArgumentParser(description="Show presence")
argparser.add_argument('-t', dest='time',
                       help="time in HH:MM", required=False)
argparser.add_argument('-s', dest='subtract',
                       help="minutes to subtract", required=False)
argparser.add_argument('--last', dest='last', action='store_const',
                       const=True, default=False,
                       help="reuse the last status before the current",
                       required=False)

if __name__ == '__main__':
    args = argparser.parse_known_args()
    time = datetime.now()
    if args[0].time:
        time = datetime.strptime(args[0].time, "%H:%M")
    elif args[0].subtract:
        time -= timedelta(minutes=int(args[0].subtract))
    last = args[0].last
    filename = datetime.now().strftime('%Y%m%d') + "_log.txt"
    status = None
    if last:
        # in case os last, we find the last that is not -
        data = _load_file(filename, log=True)
        for i in range(len(data)-1,0,-1):
            last_data = data[i]
            status = last_data['status']
            if not status.startswith('-'):
                break
        if not status:
            raise Exception("can't find a last")
    else:
        status = " ".join(e for e in args[1])

    # if args
    _write(filename, status.strip(), time)
