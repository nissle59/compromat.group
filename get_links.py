import logging
import warnings
from scraper import *

warnings.filterwarnings("ignore")

log = logging.getLogger("parser")
log_level = logging.INFO


class MsgCounterHandler(logging.Handler):
    level2count = None

    def __init__(self, *args, **kwargs):
        super(MsgCounterHandler, self).__init__(*args, **kwargs)
        self.level2count = {}

    def emit(self, record):
        levelname = record.levelname
        if levelname not in self.level2count:
            self.level2count[levelname] = 0
        self.level2count[levelname] += 1


def init_logs(logname="parser.log"):
    """ Init logging to file and stdout
    """
    dt_fmt = "%Y%m%d %H%M%S"
    # out_fmt = "{asctime}|{levelname:<1}|{name}:{message}"
    out_fmt = "%(asctime)s|%(levelname).1s|%(name)s: %(message)s"
    formatter = logging.Formatter(out_fmt, dt_fmt)
    log.setLevel(log_level)
    fh = logging.FileHandler(logname)
    fh.setFormatter(formatter)
    log.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    log.addHandler(ch)
    mh = MsgCounterHandler()
    log.addHandler(mh)
    return

if __name__ == '__main__':
    init_logs()
    create_tunnel(False)
    sql_version()
    get_articles_links()
    close_tunnel(False)