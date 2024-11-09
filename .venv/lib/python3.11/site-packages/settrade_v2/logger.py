import logging
import os
import re
import time
import time as t
from functools import wraps
from logging import Formatter
from logging.handlers import BaseRotatingHandler, TimedRotatingFileHandler
from typing import Callable

from .config import DIRECTORY
from .config import config as cfg
from .errors import SettradeError


# ref: https://stackoverflow.com/questions/24649789/how-to-force-a-rotating-name-with-pythons-timedrotatingfilehandler
class ParallelTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        postfix=".log",
    ):

        self.origFileName = filename
        self.when = when.upper()
        self.interval = interval
        self.backupCount = backupCount
        self.utc = utc
        self.postfix = postfix

        if self.when == "S":
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"  # type: ignore
        elif self.when == "M":
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$"  # type: ignore
        elif self.when == "H":
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}$"  # type: ignore
        elif self.when == "D" or self.when == "MIDNIGHT":
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"  # type: ignore
        elif self.when.startswith("W"):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError(
                    "You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s"
                    % self.when
                )
            if self.when[1] < "0" or self.when[1] > "6":
                raise ValueError(
                    "Invalid day specified for weekly rollover: %s" % self.when
                )
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"  # type: ignore
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        currenttime = int(time.time())
        BaseRotatingHandler.__init__(
            self, self.calculateFileName(currenttime), "a", encoding, delay
        )

        self.extMatch = re.compile(self.extMatch)
        self.interval = self.interval * interval  # multiply by units requested

        self.rolloverAt = self.computeRollover(currenttime)

    def calculateFileName(self, currenttime):
        if self.utc:
            timeTuple = time.gmtime(currenttime)
        else:
            timeTuple = time.localtime(currenttime)

        return self.origFileName + time.strftime(self.suffix, timeTuple) + self.postfix

    def getFilesToDelete(self, newFileName):
        dirName, fName = os.path.split(self.origFileName)
        dName, newFileName = os.path.split(newFileName)

        fileNames = os.listdir(dirName)
        result = []
        prefix = fName
        postfix = self.postfix
        prelen = len(prefix)
        postlen = len(postfix)
        for fileName in fileNames:
            if (
                fileName[:prelen] == prefix
                and fileName[-postlen:] == postfix
                and len(fileName) - postlen > prelen
                and fileName != newFileName
            ):
                suffix = fileName[prelen : len(fileName) - postlen]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[: len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore

        currentTime = self.rolloverAt
        newFileName = self.calculateFileName(currentTime)
        newBaseFileName = os.path.abspath(newFileName)
        self.baseFilename = newBaseFileName
        self.mode = "a"
        self.stream = self._open()

        if self.backupCount > 0:
            for s in self.getFilesToDelete(newFileName):
                try:
                    os.remove(s)
                except:
                    pass

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if (
                    not dstNow
                ):  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt


LOG_DIRECTORY = DIRECTORY / "settradev2_log"
if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

handler = ParallelTimedRotatingFileHandler(
    filename=str(LOG_DIRECTORY) + "/",
    when="D",
    interval=1,
    backupCount=cfg["clear_log"],
    postfix=".txt",
)

logging.basicConfig(handlers=[])

logger = logging.getLogger("settradev2")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

formatter = Formatter(
    f"[%(asctime)s] - %(message)s - [{cfg['environment']}] - [PYTHON_%(levelname)s]",
    "%Y-%m-%d %H:%M:%S",
)
for i in logger.handlers:
    handler.setFormatter(formatter)

message_format = "[Elapsed time {:.6f}s]{method_name} - {msg}"


def log_wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwargs):
        s = t.time()
        msg = "success"
        try:
            return method(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            if isinstance(e, SettradeError):
                msg = {"code": e.code, "message": msg}
            raise e
        finally:
            level = logging.INFO if msg == "success" else logging.ERROR
            msg = message_format.format(
                t.time() - s, method_name=method.__name__, msg=msg
            )
            logger.log(level=level, msg=msg)

    return wrapped


class LogWrapperMetaClass(type):
    """Wrap all public methods of a class with log_wrapper.

    Example
    -------
    >>> class MyClass(metaclass=LogWrapperMetaClass):
    ...     def my_method(self):
    ...         pass
    """

    def __new__(cls, clsname, bases, attrs):
        new_attrs = {
            k: log_wrapper(v)
            if not k.startswith("_") and isinstance(v, Callable)
            else v
            for k, v in attrs.items()
        }
        return type(clsname, bases, new_attrs)
