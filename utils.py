import os
from config import cfg
from datetime import datetime
from datetime import timedelta

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

def _load_file(file, log=False, today=False):
    try:
        os.chdir(cfg['FOLDER'])
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


def mins(td):
    """
    Transforms the timedlta in muinutes
    """
    return td.total_seconds() / 60

def get_status(h, m, data, log=False):
    # get the status in that h:m
    time = datetime.strptime(f"{h}:{m}", "%H:%M")
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
        if status:
            last = status
        status = e['status'].upper()
        detail = e.get('detail', "")
    if log and found:
        return status, time, detail
    return "NOCAT", time, detail


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

def str_print(m):
    """
    Transform a minute (int) into a HH:MM
    """
    res = str(timedelta(minutes=m))[:-3]
    if len(res) < 5:
        res = "0" + res
    return res
