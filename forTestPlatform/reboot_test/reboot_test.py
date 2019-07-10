#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Reproduce the issue that ECC errors occur after many times of reboot."""
import serial  
import time
import re
import sys
import requests
import json
import argparse
import datetime as dt
import LogMgr


class Config(object):
    COM = 'COM2'
    BPS = 115200
    TIMEOUT = 1
    rebootTimeList = [70, 30, 10, 5, 50, 120]
    powerOffTime = 3
    TotalNumberOfRestarts = 10000000
    NETWORK_RELAY_IP = '192.168.63.34'
    relayTimeout = 1
    relayOutPort = 1
    errorPatterns = ('uncorrectable error', 'returned ECC error')
    errorCntThreshold = 6


def set_relay_io(index, level):
    '''
    index: IO index, 1-based
    level: True 1, False 0

    return: True success, False failed
    '''
    ret = False
    try:
        url = "http://admin:12345678@%s/relay?relay%s%d" % (Config.NETWORK_RELAY_IP, "on" if level else 'off', index)
        requests.get(url, timeout = Config.relayTimeout)
        res = requests.get("http://admin:12345678@%s/state.cgi" % Config.NETWORK_RELAY_IP, timeout = Config.relayTimeout)
        data = json.loads(res.text.replace("output", "out", 1).replace("output", "in"))
        value = True if '1' == data['out'][index - 1] else False
        if value != level:
            ulog("Set network relay failed, value: %s, expect %d@$d" % (data['out'], level, index))
        else:
            ret = True
    except:
        ulog("Failed to request network relay!")
    return ret


def get_relay_io(index):
    '''
    Get level of output point specified by index.
    index: IO index, 1-based

    return: 1: high level, 0: low level, None: failed
    '''
    ret = None
    if index > 8 or index < 1:
        return ret
    try:
        res = requests.get("http://admin:12345678@%s/state.cgi" % Config.NETWORK_RELAY_IP, timeout = Config.relayTimeout)
        data = json.loads(res.text.replace("output", "out", 1).replace("output", "in"))
        ret = 1 if '1' == data['out'][index - 1] else 0
    except:
        ulog("Failed to request network relay!")
    return ret


def openPort(portx, bps, timeout):
    """open a serial port
        
    portx，on GNU / Linux ,is / dev / ttyUSB0 and so on, or, on Windows, COMx
    
    bps，：baud rate = 50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
    
    timeout, None：wait forever，0 return immediately, other numbers second(s)
    """
    ret = False
    try:
        ser = serial.Serial(portx, bps, timeout=timeout) # open serial
        if (ser.is_open):
            ret = True
    except Exception as e:
        ulog(e)
    return ser, ret


def writePort(ser, text):
    """write serial port
    
    ser: serial object

    text: a string you want to send by serial port

    """
    result = ser.write(text.encode("ASCII")) 
    return result


def resolveData(ser):
    """resolve serial data

    ser: serial object
    """
    if isinstance(ser, serial.Serial):
        pass
    else:
        return
    powerOnCount = 0
    powerOffCount = 0
    currentCyrcleRebootCount = 0
    cycleCount = 0
    set_relay_io(Config.relayOutPort, 0)
    time.sleep(Config.powerOffTime)
    while True:
        cycleCount += 1
        currentCyrcleRebootCount = 0
        for rebootTime in Config.rebootTimeList:
            eccErrorCnt = 0
            currentCyrcleRebootCount += 1
            if 0 == get_relay_io(Config.relayOutPort):
                ser.reset_output_buffer()  # clear serial buffer
                if set_relay_io(Config.relayOutPort, 1):
                    powerOnCount = powerOnCount + 1
            ulog('-' * 80)
            ulog('')
            ulog('')
            ulog('Power On: Total power-on times: %4d Length of time to turn on the power:%4d',
                 powerOnCount, rebootTime)
            ulog('')
            ulog('')
            ulog('-' * 80)
            thisTime = rebootTime + time.time()  # initalize setup time: from power on to power off
            while thisTime > time.time() and ser.is_open:    
                try:
                    serialSingleLine = ser.readline().decode("ASCII",'ignore')  # read serial data.
                    if len(serialSingleLine) > 0:
                        ulog(serialSingleLine.rstrip('\n'))
                        # reduce
                        eccErrorCnt += len([ x for x in Config.errorPatterns if x in serialSingleLine])
                except  UnicodeDecodeError as e:
                    ulog("UnicodeDecodeError: %s", str(e))
                except serial.SerialTimeoutException as e:
                    ulog("serial.SerialTimeoutException: %s", str(e))
                except serial.SerialException as e:
                    ulog("serial.SerialException: %s",str(e))
            ulog('Power Off: Total power-off times: %4d Number of current cycle restarts: %4d Total number of cycles: %4d eccErrorCnt = %4d',
                 powerOffCount, currentCyrcleRebootCount, cycleCount, eccErrorCnt)
            if eccErrorCnt > Config.errorCntThreshold:
                ulog('+' * 80)
                ulog('')
                ulog('')
                ulog('ECC too many!')
                ulog('')
                ulog('')
                ulog('+' * 80)
                return
                
            if 1 == get_relay_io(Config.relayOutPort):
                if set_relay_io(Config.relayOutPort, 0):
                    powerOffCount = powerOffCount + 1
            if Config.TotalNumberOfRestarts <= min(powerOffCount,powerOnCount):
                ulog("run over. total number of restarts = %d", Config.TotalNumberOfRestarts)
                return
            time.sleep(Config.powerOffTime)


def startTrans():
    """open serial port"""
    ser, ret = openPort(Config.COM, Config.BPS, Config.TIMEOUT)
    if (ret == True):
        ulog("open serial successfully")
        return ser
    ulog("open serial error")
    return 0


def ulog(msg, *args, **kwargs):
    """redefine logout function name"""
    LogMgr.Log(LogMgr._levelDict[LogMgr.Config.testlogLevel], msg, *args, **kwargs)
    return         


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', required=True, type=str, metavar="TYPE",
                        help='serial port name: COMx, ttySx, ttyUSBx')
    parser.add_argument('-r', required=True, type=int, metavar="relayOutPort", choices=[1, 2, 3, 4, 5, 6, 7, 8, ],
                        help='Relay port')
    parser.add_argument('-tc', required=False, type=int, metavar="Number_Restart", default=Config.TotalNumberOfRestarts,
                        help='Total Number Of Restarts')
    parser.add_argument('-ri', required=False, type=str, metavar="RELAY_IP", default=Config.NETWORK_RELAY_IP,
                        help='relay ip address: 192.168.63.34')
    parser.add_argument('-rt', required=False, type=int, metavar="relayTimeout", default=Config.relayTimeout,
                        help='relay Timeout')
    parser.add_argument('-err', required=False, type=int, metavar="errorCntThreshold", default=Config.errorCntThreshold,
                        help='error Cnt Threshold')
    parser.add_argument('-sb', required=False, type=int, metavar="BPS", default=Config.BPS,
                        help='serial baud rate')
    parser.add_argument('-st', required=False, type=int, metavar="serial_TIMEOUT", default=Config.TIMEOUT,
                        help='serial TIMEOUT')
    parser.add_argument('-bo', required=False, type=int, metavar="powerOffTime", default=Config.powerOffTime,
                        help='base board powerOffTime')
    args = parser.parse_args()
    ulog("%s" % str(args))
    if args.s:
        Config.COM = args.s
    if args.r:
        Config.relayOutPort = args.r
    if args.tc:
        Config.TotalNumberOfRestarts = args.tc
    if args.ri:
        Config.NETWORK_RELAY_IP = args.ri
    if args.rt:
        Config.relayTimeout = args.rt
    if args.err:
        Config.errorCntThreshold = args.err
    if args.sb:
        Config.BPS = args.sb
    if args.st:
        Config.TIMEOUT = args.st
    if args.bo:
        Config.powerOffTime = args.bo
    return


if __name__ == '__main__':
    parse_args()
    ulog("start reboot test.")
    ser = startTrans()  # open serial
    ulog(ser)
    try:
        resolveData(ser)  # start resolve serial data
    except KeyboardInterrupt:
        ser.close()
        ulog("serial has been closed")
        ulog("main thread was killed by user")

