import glob
import os
import sys
import argparse
from datetime import datetime
from datetime import timedelta
from termcolor import colored
from config import cfg

argparser = argparse.ArgumentParser(description="Show presence")

argparser.add_argument('-a', dest='all',
                       help="all days", action='store_true', required=False)
argparser.add_argument('-m', type=int, dest='min',
                       help="minutes per slot", required=False)
argparser.add_argument('-d',  dest='day',
                       help="specify day YYYYMMDD", required=False)
argparser.add_argument('-v', action="store_true", dest='detail',
                       help="detail  of the day", required=False)
argparser.add_argument('-b',  dest='begin', type=int,
                       help="Begin time HH", required=False)
argparser.add_argument('-e',  dest='end', type=int,
                       help="End time HH", required=False)
args = argparser.parse_args()


def read_file(lines):
    """
    Reads the file and coverst it into a list of dict, [<H:M,STATUS>]
    """
    r = []
    for line in lines:
        s, t = line.split('$')
        d = dict(time=datetime.strptime(t.strip(), "%H:%M"), status=s)
        r.append(d)
    return r


def mins(td):
    """
    Transforms the timedlta in muinutes
    """
    return td.total_seconds() / 60

def print_h_inline(minute, t_beg=8, t_end=20):
    # prints the title
    # this computes how many char there must be for each our
    pixels =  60 // minutes
    # left part is filename + >: that is 10 chars
    print(" " * 10, end="")
    for i in range(t_beg, t_end):
        # hours is of 2 chars e.g. 08 and on blue background
        print(colored(f"{int(i):02d}", "grey", "on_blue"), end="")
        # for the rest of the time we print . in blue (-2 since there's HH)
        print(colored('.' * (pixels - 2), "blue"), end="")
    print()


def get_status(h, m, data):
    # get the status in that h: m
    time = datetime.strptime(f"{h}:{m}", "%H:%M")
    i = 0
    found = False
    status = "EMPTY"
    for e in data:
        #  until we pass the item in the array that are before the one we Look for
        if time > e['time']:
            found = True
        if found:
            # until the time in the array pass the time we search
            # so we have the one closer to what we look for
            if e['time'] > time:
                # we return the previous status, since the current one is past time
                return status, time
        status = e['status']
    return "EMPTY", time


def print_minute(m, status, detail=False):
    """
    print the minute data with color
    """
    statuses = {
        'ACTIVE': ['grey', 'on_green'],
        'SLEEP': ['grey', 'on_red'],
        "SHUTDOWN":['magenta',None ],
        "STARTUP":['yellow',None]
    }
    data_status = statuses.get(status, ['white', None])
    attrs = []
    s = f'{int(m):02d}'
    if detail:
        if int(m) % 10 == 0:
            s = " " + s
            attrs = ['underline']
        else:
            s = '.' + str(s[1])
    else:
        s = '|'
    print(colored(s, data_status[0], data_status[1], attrs=attrs), end='')


def str_print(m):
    """
    Transform a minute (int) into a HH:MM
    """
    res = str(timedelta(minutes=m))[:-3]
    if len(res) < 5:
        res = "0" + res
    return res


def str_percent_print(p, t):
    """
    computes percent and add a space, or two to be of 3 chars
    "8" > "  8"
    To mantain aligment
    """
    p = round((p / t) * 100)
    res = str(p)
    if p < 10:
        res = " " + res
    if p < 100:
        res = " " + res
    return res


def print_summary(present, away, total):
    """
    prints the summary
    """
    str_p = str_print(present)
    str_a = str_print(away)
    total += away + present or 1.0
    str_t = str_print(total)
    str_percentage = str_percent_print(present, total)
    print("["+colored(f"{str_p}/", "green")
          + colored(f"{str_a}", "red")
          + colored(f"|{str_t}|", "blue")
          + colored(f"({str_percentage}%)", "grey","on_green")
          +"]")


def print_day(name, data, minutes,t_beg, t_end, detail=False):
    # print the data of the day
    present = 0
    away = 0
    total = 0
    # not deail have the hours on top as header
    if not detail:
        print(name.split('.')[0] + ">", end=" ")
    # loop for all the time and minutes (in step of 60/delta minutes)
    for h in range(t_beg, t_end):
        # detail have hours on the left side.
        if detail:
            print(colored(f"{int(h):02d}:", "grey", "on_blue"), end='')
        for m in range(0, 60, minutes):
            # find the status of that time and prints it.
            status, time = get_status(h, m, data)
            if status == "ACTIVE":
                present += minutes
            elif status == "SLEEP":
                away += minutes
            print_minute(m, status, detail)
        if detail:
            print("")
    if not detail:
        print(" ", end="")
    print_summary(present, away, total)


if __name__ == '__main__':
    args = argparser.parse_args()
    minutes = args.min or 5
    detail = args.detail
    beg = args.begin or 8
    end = args.end or 20
    os.chdir(cfg['FOLDER'])

    if not detail:
        # prints the hour inline, calulate the size of each minute in pixels
        print_h_inline( minutes,  t_beg=beg, t_end=end)
    if args.all:
        # if all, print all files it founds
        for file in sorted(glob.glob("*.txt")):
            f = open(file, 'r')
            data = read_file(f.readlines())
            print_day(file, data, minutes, detail=False, t_beg=beg, t_end=end)
            f.close()
    else:
        # single day printing
        if args.day:
            day = args.day
        else:
            day = datetime.now().strftime('%Y%m%d')
        file = "%s.txt" % (day)
        f = open(file, 'r')
        data = f.readlines()
        # if it's today, then we add an "active" state right now, so we print
        # that we are online. otherwise the chart would be empty.
        if not args.day:
            data.append("ACTIVE$%s\n" % datetime.now().strftime('%H:%M'))
        data = read_file(data)
        # when we have the datil, we set to 1 minute window . we said detail ;)
        if detail:
            minutes = 1
            print_day(file, data, minutes, detail=True, t_beg=beg, t_end=end)
        else:
            print_day(file, data, minutes, detail=False, t_beg=beg, t_end=end)
        f.close()
