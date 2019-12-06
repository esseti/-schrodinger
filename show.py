import glob
import os
import sys
import argparse
from datetime import datetime
from datetime import timedelta
from config import cfg
from datetime import date
import calendar
try:
    from termcolor import colored
except:
    print("INSTALL TERMCOLOR")

    def colored(s, c=None, d=None, attrs=None):
        return s


argparser = argparse.ArgumentParser(description="Show presence")

argparser.add_argument('-a', dest='all',
                       help="all days", action='store_true', required=False)
argparser.add_argument('-m', type=int, dest='min',
                       help="minutes per slot", required=False)
argparser.add_argument('-d',  dest='day',
                       help="specify day YYYYMMDD", required=False)
argparser.add_argument('-s',  dest='subtract',
                       help="Diff day: how many days subtracted from today (-1=yesterday)", required=False)
argparser.add_argument('-c', action="store_false", dest='detail',
                       help="Compact view of the day, default is detailed", required=False)
argparser.add_argument('-b',  dest='begin', type=int,
                       help="Begin time HH", required=False)
argparser.add_argument('-e',  dest='end', type=int,
                       help="End time HH", required=False)
argparser.add_argument('-dh', dest='detail_hour',
                       help="Do NOT show the detail per hour", action='store_false', required=False)
argparser.add_argument('-dc', dest='detail_category',
                       help="Do NOT show the detail per category", action='store_false', required=False)
argparser.add_argument('-l', dest='daily_log',
                       help="Print detail of the daily log to be copied.", action='store_true', required=False)
argparser.add_argument('--cron', dest='cron',
                       help="cron notification", action='store_true', required=False)
args = argparser.parse_args()


def read_file(lines):
    """
    Reads the file and coverst it into a list of dict, [<H:M,STATUS>]
    """
    r = []
    for line in lines:
        try:
            s, t = line.split('$')
            t = t.strip()
            if len(t) > 5:
                t = t[:-3]
            try:
                s, d = s.split(".")
            except:
                d = ""
            d = dict(time=datetime.strptime(t, "%H:%M"),
                     status=s.strip(), detail=d.strip())
            r.append(d)
        except:
            pass
    # todo: order by time
    r = sorted(r, key=lambda k: k['time'])
    return r


def mins(td):
    """
    Transforms the timedlta in muinutes
    """
    return td.total_seconds() / 60


def print_h_inline(minute, t_beg=8, t_end=20):
    # prints the title
    # this computes how many char there must be for each our
    pixels = 60 // minutes
    # left part is filename + >: that is 10 chars
    print(" " * 10, end="")
    for i in range(t_beg, t_end):
        # hours is of 2 chars e.g. 08 and on blue background
        print(colored(f"{int(i):02d}", "grey", "on_blue"), end="")
        # for the rest of the time we print . in blue (-2 since there's HH)
        print(colored('.' * (pixels - 2), "blue"), end=" ")
    print()


def get_status(h, m, data, log=False):
    # get the status in that h: m
    time = datetime.strptime(f"{h}:{m}", "%H:%M")
    i = 0
    found = False
    status = "NOCAT"
    detail = ""
    for e in data:
        #  until we pass the item in the array that are before the one we Look for
        if time > e['time']:
            found = True
        if found:
            # until the time in the array pass the time we search
            # so we have the one closer to what we look for
            if e['time'] > time:
                # we return the previous status, since the current one is past time
                return status, time, detail
        status = e['status'].upper()
        detail = e.get('detail', "")
    if log and found:
        return status, time, detail
    return "NOCAT", time, detail


def print_minute(m, status, detail=False, str_to_print='', first=False):
    """
    print the minute data with color
    """
    statuses = {
        'ACTIVE': ['grey', 'on_green'],
        'SLEEP': ['grey', 'on_red'],
        "SHUTDOWN": ['magenta', None],
        "STARTUP": ['yellow', None]
    }
    data_status = statuses.get(status, ['white', None])
    attrs = []
    s = f'{int(m):02d}'
    if detail:
        if int(m) % 10 == 0:
            s = " " + s
            if str_to_print:
                if first:
                    data_status[1] = "on_magenta"
                    s = "  " + str_to_print
            attrs.append('underline')
        else:
            s = "." + str(s[1])
            if str_to_print:
                if first:
                    data_status[1] = "on_magenta"
                    s = "." + str_to_print

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


def str_percent_print(p, t, space=True, reverse=False):
    """
    computes percent and add a space, or two to be of 3 chars
    "8" > "  8"
    To mantain aligment
    """
    p = round((p / t) * 100)
    res = str(p)
    if reverse:
        res = res + "%"
    if space:

        if p < 10:
            if reverse:
                res = res + " "
            else:
                res = " " + res
        if p < 100:
            if reverse:
                res = res + " "
            else:
                res = " " + res
    if not reverse:
        return res + "%"
    else:
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
    print("[" + colored(f"{str_p}/", "green") +
          colored(f"{str_a}", "red") +
          colored(f"|{str_t}|", "blue") +
          colored(f"({str_percentage})", "grey", "on_green") +
          "]")


def print_day(name, data, minutes, t_beg, t_end, detail=False, log_data=[],
              detail_hour=True, detail_category=True, daily_log=False):
    # print the data of the day
    present = 0
    away = 0
    total = 0
    time_spent = dict(NOCAT=dict(minutes=0, detail="", index='-', away=0))
    hourly_data = dict()
    start_time = None
    end_time = None
    # not deail have the hours on top as header
    if not detail:
        my_date = datetime.strptime(name.split('.')[0], "%Y%m%d")
        day_week = calendar.day_name[my_date.weekday()][0]
        print(name.split('.')[0] + day_week, end=" ")

    # loop for all the time and minutes (in step of 60/delta minutes)
    i = 0
    old_log = ""
    for h in range(t_beg, t_end):
        hourly_data[str(h)] = dict()
        # detail have hours on the left side.
        if detail:
            print(colored(f"{int(h):02d}:", "grey", "on_blue"), end='')
        for m in range(0, 60, minutes):
            log_str = ""
            # find the status of that time and prints it.
            status, _, _ = get_status(h, m, data)
            # find what's the log, if any
            log, _, log_det = get_status(h, m, log_data, True)
            # init time spent if does not exists
            if log not in time_spent:
                if log != "NOCAT":
                    index = chr(i + 65)
                    i += 1
                    time_spent[log] = dict(
                        minutes=0, away=0, index=index, detail="")
            first = False

            if status == "ACTIVE":
                if not start_time:
                    start_time = f"{h}:{m}"

                end_time = f"{h}:{m}"
                present += minutes
                first = old_log != log
                time_spent[log]['minutes'] = time_spent[log]['minutes'] + 1
                if log_det not in time_spent[log]['detail']:
                    time_spent[log]['detail'] += log_det
                log_str = time_spent[log]['index']
                old_log = log
                try:
                    hourly_data[str(h)][time_spent[log]
                                        ['index']]['active'] += 1
                except:
                    hourly_data[str(h)][time_spent[log]['index']
                                        ] = dict(active=1, sleep=0)
            elif status == "SLEEP":
                # we keep track of the time of the task as well, maybe is a task away from the pc
                away += minutes
                first = old_log != log
                time_spent[log]['away'] = time_spent[log]['away'] + 1
                if log_det not in time_spent[log]['detail']:
                    time_spent[log]['detail'] += log_det
                log_str = time_spent[log]['index']
                old_log = log

                try:
                    hourly_data[str(h)][time_spent[log]['index']]['sleep'] += 1
                except:
                    hourly_data[str(h)][time_spent[log]['index']
                                        ] = dict(sleep=1, active=0)

            print_minute(m, status, detail, log_str, first)

        if detail:
            print("")
        else:
            print(" ", end="")
    if not detail:
        print(" ", end="")
    else:
        if detail_category:
            print_spent(time_spent, total + present)

    if daily_log:
        print_daily_log(hourly_data, time_spent, t_beg, t_end,
                        start_time, end_time, present + away)
        print("")
    else:
        for h in range(int(t_beg), int(t_end)):
            print(colored(f"{int(h):02d}:", "grey", "on_blue"), end='')
            print_hourly_data(hourly_data[str(h)], time_spent)
            print("")

    print_summary(present, away, total)


def print_daily_log(hd, ld, start, end, start_time, end_time, total):
    print(start_time)
    index_name = dict()
    elements = {}
    # # print(ld)
    for k, v in ld.items():
        # print(v)
        index_name[v['index']] = k
    for h in range(int(start), int(end)):

        hour_data = hd.get(str(h))
        if hour_data:
            print(f"{h}:", end='')
    #
            try:
                for k, v in hour_data.items():
                    name = index_name[k].capitalize()
                    spent = v.get('active', 0) + v.get('sleep', 0)
                    print(f"{name} ({str_print(spent)}|{str_percent_print((spent),60,space=False)})", end=" ")
                    if name in elements:
                        elements[name] += spent
                    else:
                        elements[name] = spent
            except:
                pass
            print()
    print(end_time)
    print()
    for i, v in elements.items():
        print(f"{i} ({str_print(v)}|{str_percent_print(v,total,space=False)})| ", end="")


def print_hourly_data(hourly_data, ld):
    hourly_data = dict(
        sorted(hourly_data.items(), key=lambda t: t[1]['active'], reverse=True))
    logged_sum = sum(time['active'] for _, time in hourly_data.items())
    print(" ", end='')
    for log, time in hourly_data.items():
        # print(time,end='')
        if time.get('sleep', 0):
            away = colored(str_print(time.get('sleep', 0))
                           [3:], 'grey', 'on_red')
        else:
            away = colored(str_print(time.get('sleep', 0))[3:], 'red')
        if time.get('active', 0):
            present = colored(str_print(time.get('active', 0))[
                              3:], 'grey', 'on_green')
        else:
            present = colored(str_print(time.get('active', 0))[3:], 'green')
        name = ""
        for k, v in ld.items():
            if v['index'] == log:
                name = k
        print(f"{colored(name,'magenta'):<17} {present}|{away}|{colored(str_percent_print(time.get('active',0),60, reverse=True),'green')}", end=' ')


def print_spent(data, real_total):
    total = 0
    away = 0
    print("-" * 80)
    print(f"INDEX\tACTIV|SLEEP|TOTAL (PERC)\tSTATUS\t\tDETAIL")
    for status, item in data.items():
        total += item['minutes']
        away += item.get('away', 0)

        print(f"{colored(item['index'],'magenta'):}\t{colored(str_print(item['minutes']),'green')}|{colored(str_print(item.get('away',0)),'red')}|{colored(str_print(item.get('away',0)+item.get('minutes',0)),'blue')} ({colored(str_percent_print(item['minutes'],real_total),'blue')})",
              "\t" + status,
              f"\t\t{item.get('detail','-')}")
    print("-" * 80)


def _load_file(file, log=False, today=False):
    try:
        f = open(file, 'r')
        data = f.readlines()
        f.close()
        # if it's today, then we add an "active" state right now, so we print
        # that we are online. otherwise the chart would be NOCAT.
        if today and not log:
            data.append("ACTIVE$%s\n" % datetime.now().strftime('%H:%M'))

        return read_file(data)
    except:
        return []

def percent(start, workday=8):
    now_dt = datetime.now()
    now = datetime.strptime(f"{now_dt.hour}:{now_dt.minute}", "%H:%M")
    start = start
    end = start + timedelta(hours=workday)
    total = mins(end-start)
    spent = mins(now-start)
    percent = float(float(spent)/float(total))
    percent = round(percent*100)
    import osascript
    code,out,err = osascript.run(f'display notification "spent {percent}%" with title "{now.hour}:{now.minute} ({start.strftime("%H:%M")}-{end.strftime("%H:%M")})" ')


if __name__ == '__main__':
    args = argparser.parse_args()
    minutes = args.min or 5
    detail = args.detail
    beg = args.begin or 7
    end = args.end or 22
    dh = args.detail_hour
    dc = args.detail_category
    daily_log = args.daily_log
    os.chdir(cfg['FOLDER'])
    if args.cron:
        day = datetime.now()
        day = day.strftime('%Y%m%d')
        data = _load_file("%s.txt" % (day), today=True)
        # print(data)
        start = data[0]['time']
        percent(start)

    elif args.all:
        # if all, print all files it founds
        print_h_inline(minutes,  t_beg=beg, t_end=end)
        for file in sorted(glob.glob("*.txt")):
            if "_log" not in file:
                f = open(file, 'r')
                data = read_file(f.readlines())
                print_day(file, data, minutes, detail=False,
                          t_beg=beg, t_end=end, detail_hour=False)
                f.close()
    else:
        # single day printing
        today = True
        if args.day:
            day = args.day
            today = False
            print(day)
        else:
            day = datetime.now()
            if args.subtract:
                day -= timedelta(days=int(args.subtract))
                today = False
            day = day.strftime('%Y%m%d')
        data = _load_file("%s.txt" % (day), today=today)
        print(data)
        # when we have the datil, we set to 1 minute window . we said detail ;)
        if detail:
            minutes = 1
            log_data = _load_file("%s_log.txt" % (day), log=True)
            print_day(day, data, minutes, detail=True,
                      t_beg=beg, t_end=end, log_data=log_data, detail_hour=dh,
                      detail_category=dc, daily_log=daily_log)
        else:
            print_h_inline(minutes,  t_beg=beg, t_end=end)
            print_day(day, data, minutes, detail=False,
                      t_beg=beg, t_end=end, detail_hour=False)
