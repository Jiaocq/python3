"""manage switch, open or close port, and mirror a port"""
from html.parser import HTMLParser
import requests
import sys
sys.path.append("..")
from logManager import LogMgr


class Config(object):
    SWITCH_IP = "192.168.63.22"
    SWITCH_TIMEOUT = 2


class ParserHtml(HTMLParser):
    morroState = ['禁用', 'Rx', 'Tx', 'Both', ]

    def __init__(self, tagStr):
        HTMLParser.__init__(self )
        self.a_text = False
        self.tagStr = tagStr
        self.categories = []

    def handle_starttag(self, tag, attr):
        if tag == self.tagStr:
            self.a_text = True
            # print (dict(attr))

    def handle_endtag(self, tag):
        if tag == self.tagStr:
            self.a_text = False

    def handle_data(self, data):
        if self.a_text:
            if data.isspace() == 0:
                self.categories.append(data)

    def portStateIsCorrect(self, port, state):
        if state == 0:
            ret = "Disabled" == self.categories[self.categories.index("Port %d" % port) + 1]
        elif state == 1:
            ret = "Enabled" == self.categories[self.categories.index("Port %d" % port) + 1]
        return ret

    def getLinkState(self, port):
        ret = None
        if "Link Up" == self.categories[self.categories.index("Port %d" % port) + 2]:
            ret = 1
        elif "Link Up" == self.categories[self.categories.index("Port %d" % port) + 2]:
            ret = 0
        return ret

    def mirrorStateIsCorrect(self, mirror_direction, mirroring_port, mirrored_port):
        if mirror_direction == 0:
            if ParserHtml.morroState[mirror_direction] == self.categories[-3]:
                ret = True
            else:
                ret = False
        else:
            if str(mirroring_port) == self.categories[-2] and \
               str(mirrored_port) == self.categories[-1] and \
               ParserHtml.morroState[mirror_direction] == self.categories[-3]:
                ret = True
            else:
                ret = False
        return ret


class Switch(object):
    @classmethod
    def setSwitchPort(cls, port, state):
        """
        open or close switch port
        :param port: 1-8
        :param state: 0-1
        :return: true or false
        """
        ret = False
        if port > 8 or port < 1:
            return ret
        try:
            requests.post("http://admin:admin@%s/port.cgi?portid=%d&state=%d" %
                          (Config.SWITCH_IP, port - 1, state), verify=False,
                          timeout=Config.SWITCH_TIMEOUT)
            res = requests.get("http://admin:admin@%s/port.cgi?page=stats" % Config.SWITCH_IP, verify=False,
                               timeout=Config.SWITCH_TIMEOUT)
            yk = ParserHtml("tr")
            yk.feed(res.text)
            ret = yk.portStateIsCorrect(port, state)
            yk.close()
        except requests.exceptions.ConnectTimeout as e:
            ulog(e)
        finally:
            return ret

    @classmethod
    def setSwitchMirror(cls, mirroring_port, mirrored_port, mirror_direction):
        """
        set a port to receive another port data
        :param mirroring_port: 1-8
        :param mirrored_port: 1-8
        :param mirror_direction: 0-3  represents ['禁用', 'Rx', 'Tx', 'Both', ]
        :return: true or flase
        """
        ret = False
        if mirroring_port > 8 or mirroring_port < 1:
            return ret
        if mirrored_port > 8 or mirrored_port < 1:
            return ret
        if mirror_direction > 3 or mirror_direction < 0:
            return ret
        try:
            requests.post("http://admin:admin@%s/port.cgi?page=mirroring"
                          "&mirror_direction=%d&mirroring_port=%d&mirrored_port=Port+%d&cmd=mirror" %
                          (Config.SWITCH_IP, mirror_direction, mirroring_port-1, mirrored_port), verify=False,
                          timeout=Config.SWITCH_TIMEOUT)
            res = requests.get("http://admin:admin@%s/port.cgi?page=mirroring" % Config.SWITCH_IP, verify=False,
                               timeout=Config.SWITCH_TIMEOUT)
            yk = ParserHtml('tr')
            yk.feed(res.text)
            ret = yk.mirrorStateIsCorrect(mirror_direction, mirroring_port, mirrored_port)
            yk.close()
        except requests.exceptions.ConnectTimeout as e:
            ulog(e)
        finally:
            return ret


def ulog(msg, *args, **kwargs):
    """redefine logout function name"""
    LogMgr.Log(LogMgr._levelDict[LogMgr.Config.testlogLevel], msg, *args, **kwargs)
    return


if __name__ == '__main__':
    ulog("start control switch")
    ulog(Switch.setSwitchPort(5, 0))
    ulog(Switch.setSwitchMirror(2, 6, 3))


