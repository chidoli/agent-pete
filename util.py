from datetime import datetime
from dateutil import tz

tz_utc = tz.tzutc()
tz_local = tz.tzutc()

def set_timezone(timezone):
    global tz_local
    tz_local = tz.gettz(timezone)

def date_str(date, form):
    date = date.replace(tzinfo=tz_utc)
    date = date.astimezone(tz_local)
    d_str = date.strftime(form)
    return d_str


def now_str(form):
    now = datetime.utcnow()
    n_str = date_str(now, form)
    return n_str

def log(*args):
    try:
        msg = u' '.join([unicode(x) for x in args])
        msg = msg.encode('utf-8')
    except Exception as e:
        print e
        msg =  'invalid msg'
    print now_str('%Y-%m-%d %H:%M:%S'), msg
