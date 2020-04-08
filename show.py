import glob
import argparse
from datetime import timedelta, datetime
import os
from config import cfg
import calendar
from utils import _load_file, read_file, mins, get_status,str_percent_print, str_print

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
argparser.add_argument('-d', dest='day',
                       help="specify day YYYYMMDD", required=False)
argparser.add_argument('-s', dest='subtract',
                       help="Diff day: how many days subtracted from today (-1=yesterday)",
                       required=False)
argparser.add_argument('-c', action="store_false", dest='detail',
                       help="Compact view of the day, default is detailed",
                       required=False)
argparser.add_argument('-b', dest='begin', type=int,
                       help="Begin time HH", required=False)
argparser.add_argument('-e', dest='end', type=int,
                       help="End time HH", required=False)
argparser.add_argument('-dh', dest='detail_hour',
                       help="Do NOT show the detail per hour",
                       action='store_false', required=False)
argparser.add_argument('-dc', dest='detail_category',
                       help="Do NOT show the detail per category",
                       action='store_false', required=False)
argparser.add_argument('-l', dest='daily_log',
                       help="Print detail of the daily log to be copied.",
                       action='store_true', required=False)
argparser.add_argument('--cron', dest='cron',
                       help="cron notification", action='store_true',
                       required=False)
args = argparser.parse_args()





def print_h_inline(minute, t_beg=8, t_end=20):
    # prints the title for the compact view
    # this computes how many chars there must be for each our
    pixels = 60 // minutes
    # left part is filename + >: that is 10 chars
    print(" " * 10, end="")
    for i in range(t_beg, t_end):
        # hours is of 2 chars e.g. 08 and on blue background
        print(colored(f"{int(i):02d}", "grey", "on_blue"), end="")
        # for the rest of the time we print . in blue (-2 since there's HH)
        print(colored('.' * (pixels - 2), "blue"), end=" ")
    print()



def print_minute(m, status, detail=False, str_to_print='', first=False,
                 end=''):
    """
    print the minute data with color
    """
    statuses = {
        'ACTIVE': ['grey', 'on_green'],
        'SLEEP': ['grey', 'on_red'],
        "SHUTDOWN": ['magenta', None],
        "STARTUP": ['yellow', None]
    }
    # here we receive a dict or a key, depends if it's computed
    # or from file (-a -c)
    if type(status) == dict:
        sta = status['status']
    else:
        sta = status
    data_status = statuses.get(sta, ['white', None])
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
    print(colored(s, data_status[0], data_status[1], attrs=attrs), end=end)






def print_summary(present, away, total):
    """
    prints the summary
    ```
        [03:30/02:30|06:00|( 58%)]
    ```
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


def print_day(name, t_beg, t_end, minutes, data):
    """
    Print the inline day

    :param name:
    :param t_beg:
    :param t_end:
    :param minutes:
    :param data:
    :return:

    ```
                  07 08 09 10 11 12 13 14 15 16 17 18 19 20 21
        20200407T || || || || || || || || || || || || || || ||
    ```
    """
    my_date = datetime.strptime(name.split('.')[0], "%Y%m%d")
    day_week = calendar.day_name[my_date.weekday()][0]
    print(name.split('.')[0] + day_week, end=" ")
    for h in range(t_beg, t_end):
        for m in range(0, 60, minutes):
            status, _, _ = get_status(h, m, data)
            print_minute(m, status)
        print(" ", end="")
    print("")


def print_day_datail(daily_data, hourly_data, minute_data, time_spent,
                     t_beg, t_end,
                     daily_log):

    """
    print the minute by minute day, plust deatils and the rest, normal call

    :param daily_data:
    :param hourly_data:
    :param minute_data:
    :param time_spent:
    :param t_beg: time to start printing (hour)
    :param t_end: time to end priinting (hour)
    :param detail:
    :param detail_category:
    :param daily_log:
    :return:
    """
    old = ""
    first = False
    detail = True
    for time_data, status_data in minute_data.items():
        # key is h:m
        h, m = time_data.split(':')
        if int(m) == 0:
            print(colored(f"{int(h):02d}:", "grey", "on_blue"), end='')
        if int(m) == 59:
            end = '\n'
        else:
            end = ''
        # the check is to understand if a "we should print the start"
        str_to_print = time_spent[status_data['cat']]['index']

        if old:
            first = old != status_data['cat']
        print_minute(m, status_data, detail, str_to_print, first, end=end)
        old = status_data['cat']


    print_spent(time_spent, daily_data['total'])

    if daily_log:
        print("")
        print_daily_log(hourly_data, time_spent, t_beg, t_end,
                        daily_data['start_time'], daily_data['end_time'],
                        daily_data['total'])
        print("")
    else:
        #prints
        for h in range(int(t_beg), int(t_end)):
            print(colored(f"{int(h):02d}:", "grey", "on_blue"), end='')
            print_hourly_data(hourly_data[str(h)], time_spent)
            print("")

    print_summary(daily_data['active'], daily_data['away'], 0)


def print_daily_log(hourly_data, time_spent, start, end, start_time, end_time, total):
    """
    Prints the summary of the day logs in the -l version, easier to copy/paste

    :param hourly_data:
    :param time_spent:
    :param start:
    :param end:
    :param start_time:
    :param end_time:
    :param total:
    :return:


    ```
        8:55
        8:Misc (00:05|8%)
        9:Misc (01:00|100%)
        10:Misc (00:42|70%) Exercises (00:18|30%)
        11:Exercises (00:19|32%) Misc (00:41|68%)
        12:Misc (00:12|20%) Lunch (00:48|80%)
        13:Lunch (01:00|100%)
        14:Misc (00:55|92%)
        14:54

        Misc (03:35|60%)|Exercises (00:37|10%)|Lunch (01:48|30%)|
        Misc|Exercises|Lunch|
    ```
    """
    print(start_time)
    index_name = dict()
    elements = {}
    for k, v in time_spent.items():
        index_name[v['index']] = k
    for h in range(int(start), int(end)):
        hour_data = hourly_data.get(str(h))
        if hour_data:
            print(f"{h}:", end='')
            #
            try:
                for k, v in hour_data.items():
                    name = index_name[k].capitalize()
                    spent = v.get('active', 0) + v.get('sleep', 0)
                    print(
                        f"{name} ({str_print(spent)}|{str_percent_print(spent, 60, space=False)})",
                        end=" ")
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
        print(
            f"{i} ({str_print(v)}|{str_percent_print(v, total, space=False)})",
            end="|")
    print()
    for i, v in elements.items():
        print(
            f"{i}", end="|")


def print_hourly_data(hourly_data, ld):
    """
    prints the hourly data colored
    :param hourly_data:
    :param ld:
    :return:

    ```
        07:
        08: MISC     05|00|8%
        09: MISC     00|00|100%
        10: MISC     42|00|70%  EXERCISES 00|18|30%
        11: MISC     41|00|68%  EXERCISES 00|19|32%
        12: MISC     12|00|20%  LUNCH    00|48|80%
        13: LUNCH    00|00|100%
        14: MISC     49|05|90%
        15:
        16:
        17:
        18:
        19:
        20:
        21:
    ```
    """
    hourly_data = dict(
        sorted(hourly_data.items(), key=lambda t: t[1]['active'],
               reverse=True))
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
        print(
            f"{colored(name, 'magenta'):<17} {present}|{away}|{colored(str_percent_print(time.get('active', 0)+time.get('sleep', 0), 60, reverse=True), 'green')}",
            end=' ')


def print_spent(data, real_total):
    """


    :param data:
    :param real_total:
    :return:

    ```
        --------------------------------------------------------------------------------
        INDEX	ACTIV|SLEEP|TOTAL (PERC)	STATUS		DETAIL
        -	00:00|00:00|00:00 (  0%) 	NOCAT
        A	03:30|00:05|03:35 ( 60%) 	MISC
        B	00:00|00:37|00:37 ( 10%) 	EXERCISES
        C	00:00|01:48|01:48 ( 30%) 	LUNCH
        --------------------------------------------------------------------------------
    ```
    """
    total = 0
    away = 0
    print("-" * 80)
    print(f"INDEX\tACTIV|SLEEP|TOTAL (PERC)\tSTATUS\t\tDETAIL")
    for status, item in data.items():
        total += item['minutes']
        away += item.get('away', 0)

        print(
            f"{colored(item['index'], 'magenta'):}\t{colored(str_print(item['minutes']), 'green')}|{colored(str_print(item.get('away', 0)), 'red')}|{colored(str_print(item.get('away', 0) + item.get('minutes', 0)), 'blue')} ({colored(str_percent_print(item.get('away', 0) + item.get('minutes', 0), real_total), 'blue')})",
            "\t" + status,
            f"\t\t{item.get('detail', '-')}")
    print("-" * 80)



def percent(start, workday=8):
    now_dt = datetime.now()
    now = datetime.strptime(f"{now_dt.hour}:{now_dt.minute}", "%H:%M")
    start = start
    end = start + timedelta(hours=workday)
    total = mins(end - start)
    spent = mins(now - start)
    percent = float(float(spent) / float(total))
    percent = round(percent * 100)
    import osascript
    code, out, err = osascript.run(
        f'display notification "spent {percent}%" with title "{now.hour}:{now.minute} ({start.strftime("%H:%M")}-{end.strftime("%H:%M")})" ')


def calculate_day(data, minutes, t_beg, t_end, log_data=[]):
    """
    This function computes the data used later on

    :param data:
    :param minutes:
    :param t_beg:
    :param t_end:
    :param log_data:
    :return:
        - day_data: data of the day (sleep/presnt)
        - hourly_data: the data for each hour (e.g. action a (sleep present))
        - minute_data: each minut what was the action/status
        - time_spent: spent time per action

    """
    present = 0
    away = 0
    # this is present+away+other
    total = 0
    time_spent = dict(NOCAT=dict(minutes=0, detail="", index='-', away=0))
    hourly_data = dict()
    start_time = None
    end_time = None

    # loop for all the time and minutes (in step of 60/delta minutes)
    i = 0
    old_log = ""
    minute_data = dict()
    for h in range(t_beg, t_end):
        hourly_data[str(h)] = dict()
        # detail have hours on the left side.
        for m in range(0, 60, minutes):
            # find the status of that time and prints it.
            status, _, _ = get_status(h, m, data)
            # find what's the log, if any
            log, _, log_det = get_status(h, m, log_data, True)
            # in case it starts with -, we default set it to sleep
            if log.startswith('-'):
                # only when status exists, it may be NOCAT
                if status == "ACTIVE":
                    status = "SLEEP"
                log = log[1:]
            # init time spent if does not exists
            if log not in time_spent:
                if log != "NOCAT":
                    index = chr(i + 65)
                    i += 1
                    time_spent[log] = dict(
                        minutes=0, away=0, index=index, detail="")
            if status == "ACTIVE":
                if not start_time:
                    start_time = f"{h}:{m}"

                end_time = f"{h}:{m}"
                present += minutes
                time_spent[log]['minutes'] = time_spent[log]['minutes'] + 1
                if log_det not in time_spent[log]['detail']:
                    time_spent[log]['detail'] += log_det
                try:
                    hourly_data[str(h)][time_spent[log]
                    ['index']]['active'] += 1
                except:
                    hourly_data[str(h)][time_spent[log]['index']
                    ] = dict(active=1, sleep=0)
            elif status == "SLEEP":
                # we keep track of the time of the task as well, maybe is a task away from the pc
                away += minutes
                time_spent[log]['away'] = time_spent[log]['away'] + 1
                if log_det not in time_spent[log]['detail']:
                    time_spent[log]['detail'] += log_det

                try:
                    hourly_data[str(h)][time_spent[log]['index']]['sleep'] += 1
                except:
                    hourly_data[str(h)][time_spent[log]['index']
                    ] = dict(sleep=1, active=0)
            elif status != 'NOCAT':
                # any other category
                total += minutes

            k = "%s:%s" % (h, m)
            minute_data[k] = dict()
            minute_data[k]['status'] = status
            minute_data[k]['cat'] = log
            if log_det:
                minute_data[k]['detail'] = log_det
    active = away = 0
    for status, item in time_spent.items():
        active += item['minutes']
        away += item.get('away', 0)
    day_data = dict(active=active, away=away, total=total + active + away,
                    start_time=start_time,
                    end_time=end_time)
    return day_data, hourly_data, minute_data, time_spent


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
        print_h_inline(minutes, t_beg=beg, t_end=end)
        for file in sorted(glob.glob("*.txt")):
            if "_log" not in file:
                f = open(file, 'r')
                data = read_file(f.readlines())

                print_day(name=file, data=data, minutes=minutes, t_beg=beg,
                          t_end=end)
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
        # when we have the datil, we set to 1 minute window . we said detail ;)
        if detail:
            minutes = 1
            log_data = _load_file("%s_log.txt" % (day), log=True)
            daily_data, hourly_data, minute_data, time_spent = calculate_day(
                data=data, minutes=minutes, log_data=log_data,
                t_beg=beg, t_end=end)

            print_day_datail(daily_data, hourly_data, minute_data, time_spent,
                             daily_log=daily_log, t_beg=beg,
                             t_end=end)
        else:
            print_h_inline(minutes, t_beg=beg, t_end=end)
            print_day(name=day, data=data, minutes=minutes, t_beg=beg,
                      t_end=end)

