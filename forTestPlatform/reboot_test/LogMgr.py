# !/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import logging
import datetime as dt

_levelDict = {
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

class Config(object):
    syslogLevel = "DEBUG"
    resetlogLevel = "DEBUG"
    debug = True
    debuglogLevel = "DEBUG"
    testlogLevel = "DEBUG"
    logPath = os.path.dirname(os.path.realpath(__file__))
    logPrefix = dt.datetime.now().strftime("%Y%m%d_%H%M%S")


class LogMgr(object):

    def __init__(self, syslogPath):
        self._top = logging.getLogger("bdrl")
        self._top.setLevel(_levelDict[Config.resetlogLevel])
        # self._sysFileHandler = logging.handlers.RotatingFileHandler(filename = syslogPath, mode="w", maxBytes=1048576, backupCount=5)
        self._sysFileHandler = logging.FileHandler(filename=syslogPath, mode="a", encoding='utf-8')
        self._sysFileHandler.setLevel(_levelDict[Config.syslogLevel])
        formatter = logging.Formatter(
                                      fmt="%(asctime)s %(name)s %(levelname)s: %(message)s",
                                      # datefmt='%Y%m%d_%H%M%S %a',
                                      # fmt='%(asctime)s %(levelname)-8s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'
                                      )
        self._sysFileHandler.setFormatter(formatter)
        self._top.addHandler(self._sysFileHandler)
        if Config.debug:
            console = logging.StreamHandler()
            console.setLevel(_levelDict[Config.debuglogLevel])
            console.setFormatter(formatter)
            self._top.addHandler(console)
        self._testcaseFileHandler = None

    def AddTestLog(self, filePath):
        if self._testcaseFileHandler:
            self._top.removeHandler(self._testcaseFileHandler)
        self._testcaseFileHandler = logging.FileHandler(filename=filePath, mode='a', encoding='utf-8')
        formatter = logging.Formatter(
                                        # fmt='%(asctime)s %(levelname)-8s %(message)s',
                                        fmt="%(asctime)s %(name)s %(levelname)s: %(message)s",
                                        datefmt='%Y-%m-%d %H:%M:%S'
                                        # datefmt='%Y%m%d_%H%M%S %a',
                                      )
        self._testcaseFileHandler.setFormatter(formatter)
        self._testcaseFileHandler.setLevel(_levelDict[Config.testlogLevel])
        self._top.addHandler(self._testcaseFileHandler)

    def RemoveTestLog(self):
        if self._testcaseFileHandler:
            self._top.removeHandler(self._testcaseFileHandler)
            self._testcaseFileHandler = None


_syslogFilePath = os.path.join(Config.logPath, Config.logPrefix + ".log")
_logMgr = LogMgr(_syslogFilePath)


def Reset():
    global _logMgr
    del _logMgr
    _logMgr = LogMgr(_syslogFilePath)


def Error(msg, *args, **kwargs):
    _logMgr._top.error(msg, *args, **kwargs)


def Warning(msg, *args, **kwargs):
    _logMgr._top.warning(msg, *args, **kwargs)


def Info(msg, *args, **kwargs):
    _logMgr._top.info(msg, *args, **kwargs)


def Log(lvl, msg, *args, **kwargs):
    _logMgr._top.log(lvl, msg, *args, **kwargs)


def AddTestLog(_fn):
    _logMgr.AddTestLog(_fn)


def RemoveTestLog():
    _logMgr.RemoveTestLog()


