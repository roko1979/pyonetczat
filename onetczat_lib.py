# -*- coding: utf-8
from twisted.internet.protocol import Protocol
from twisted.internet import task
import twisted.python.log as tlog

import time

from twisted.protocols import basic

from twisted.internet import reactor
from pprint import pformat

from twisted.internet.defer import Deferred
from twisted.web.http_headers import Headers
from twisted.internet.defer import succeed

from twisted.internet import task

from twisted.web.iweb import IBodyProducer
from twisted.web.client import Agent

from twisted.python import log

from zope.interface import implements

import sys
import re
import urllib
import logging

from xml.dom import minidom

#helper modules
import consts

# 
# All my works on that library I dedicate for Hania B. :*
# 

__all__ = ['IRCProtocol', 'CamProtocol']

logger = logging.getLogger('OnetCzat.Connection')

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class BeginningPrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10
        self.body = ''

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            self.body = self.body+display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        #print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(self.body)


class OnetAuth(object):
    def __init__(self, nickname, password):
        self.nickname = nickname
        self.password = password

        self.authorised = Deferred()

        self.agent = Agent(reactor)

    def auth(self, s):
      stringbuffer = ""
      ai = []
      pomoc = []

      f1 = [
            29, 43, 7, 5, 52, 58, 30, 59, 26, 35,
            35, 49, 45, 4, 22, 4, 0, 7, 4, 30, 51,
            39, 16, 6, 32, 13, 40, 44, 14, 58, 27,
            41, 52, 33, 9, 30, 30, 52, 16, 45, 43,
            18, 27, 52, 40, 52, 10, 8, 10, 14, 10,
            38, 27, 54, 48, 58, 17, 34, 6, 29, 53,
            39, 31, 35, 60, 44, 26, 34, 33, 31, 10,
            36, 51, 44, 39, 53, 5, 56
        ]
      f2 = [
            7, 32, 25, 39, 22, 26, 32, 27, 17, 50,
            22, 19, 36, 22, 40, 11, 41, 10, 10, 2,
            10, 8, 44, 40, 51, 7, 8, 39, 34, 52, 52,
            4, 56, 61, 59, 26, 22, 15, 17, 9, 47, 38,
            45, 10, 0, 12, 9, 20, 51, 59, 32, 58, 19,
            28, 11, 40, 8, 28, 6, 0, 13, 47, 34, 60,
            4, 56, 21, 60, 59, 16, 38, 52, 61, 44, 8,
            35, 4, 11
        ]
      f3 = [
            60, 30, 12, 34, 33, 7, 15, 29, 16, 20,
            46, 25, 8, 31, 4, 48, 6, 44, 57, 16,
            12, 58, 48, 59, 21, 32, 2, 18, 51, 8,
            50, 29, 58, 6, 24, 34, 11, 23, 57, 43,
            59, 50, 10, 56, 27, 32, 12, 59, 16, 4,
            40, 39, 26, 10, 49, 56, 51, 60, 21, 37,
            12, 56, 39, 15, 53, 11, 33, 43, 52, 37,
            30, 25, 19, 55, 7, 34, 48, 36
        ]
      p1 = [
            11, 9, 12, 0, 1, 4, 10, 13, 3,
            6, 7, 8, 15, 5, 2, 14
        ]
      p2 = [
            1, 13, 5, 8, 7, 10, 0, 15, 12, 3,
            14, 11, 2, 9, 6, 4
        ]


      if len(s) < 16:
        return "(key to short)"

      i = 0
      while i < 16:
        c = s[i]
        if c > '9':
          if c > 'Z':
            ai.insert(i, (ord(c) - 97) + 36)
          else:
            ai.insert(i, (ord(c) - 65) + 10)
        else:
          ai.insert(i, ord(c) - 48)
        i = i + 1

      i = 0
      while i < 16:
        ai[i] = f1[ai[i] + i]
        i = i + 1
      ai1 = ai

      i = 0
      while i < 16:
        pomoc.insert(i, (ai[i] + ai1[p1[i]]) % 62)
        i = i + 1
      ai = pomoc

      i = 0
      while i < 16:
        ai[i] = f2[ai[i] + i]
        i = i + 1
      ai1 = ai

      pomoc = []
      i = 0
      while i < 16:
        pomoc.insert(i, (ai[i] + ai1[p2[i]]) % 62)
        i = i + 1
      ai = pomoc

      i = 0
      while i < 16:
        ai[i] = f3[ai[i] + i]
        i = i + 1

      i = 0
      while i < 16:
        j = ai[i]
        if j >= 10:
          if j >= 36:
            ai[i] = (97 + j) - 36
          else:
            ai[i] = (65 + j) - 10
        else:
          ai[i] = 48 + j
        stringbuffer = stringbuffer + chr(ai[i])
        i = i + 1

      return stringbuffer

    def authorise(self):
        d = self.agent.request(
            'GET',
            'http://kropka.onet.pl/_s/kropka/1?DV=czat',
            None,
            None)

        d.addCallback(self.cbGetFirstCookie)
        d.addErrback(self.cbShutdown)

    def cbGetFirstCookie(self, response):
        onet_ubi_cookie = response.headers.getRawHeaders('Set-Cookie')[0]
        onetzuo_ticket_cookie = response.headers.getRawHeaders('Set-Cookie')[1]
        onet_cid_cookie = response.headers.getRawHeaders('Set-Cookie')[2]
        #onet_sgn_cookie = response.headers.getRawHeaders('Set-Cookie')[3]

        onet_ubi_match = re.search("onet_ubi=(.*?);", onet_ubi_cookie)
        if onet_ubi_match:
            onet_ubi_result = onet_ubi_match.group()
        else:
            onet_ubi_result = None

        onetzuo_ticket_match = re.search("onetzuo_ticket=(.*?);", onetzuo_ticket_cookie)
        if onetzuo_ticket_match:
            onetzuo_ticket_result = onetzuo_ticket_match.group()
        else:
            onetzuo_ticket_result = None

        onet_cid_match = re.search("onet_cid=(.*?);", onet_cid_cookie)
        if onet_cid_match:
            onet_cid_result = onet_cid_match.group()
        else:
            onet_cid_result = None

        if onet_ubi_result != None and onetzuo_ticket_result != None and onet_cid_result != None:
            finished = Deferred()
            response.deliverBody(BeginningPrinter(finished))
            finished.addCallback(self.cbGetFirstCookieSuccess, onet_ubi_result, onetzuo_ticket_result, onet_cid_result)
            finished.addErrback(self.cbShutdown)
            return finished
        else:
            self.authorise()

    def cbGetFirstCookieSuccess(self, result, onet_ubi_result, onetzuo_ticket_result, onet_cid_result):
        #now we need to have second cookie with sid
        cookie = onet_ubi_result+' '+onetzuo_ticket_result+' '+onet_cid_result
        headers = {}
        headers['Cookie'] = [cookie]
        headers['Host'] = ['czat.onet.pl']
        headers = Headers(headers)

        d = self.agent.request(
            'GET',
            'http://czat.onet.pl/myimg.gif',
            headers,
            None)

        d.addCallback(self.cbGetSecondCookie, cookie)
        d.addErrback(self.cbShutdown)


    def cbGetSecondCookie(self, response, cookie):
        onet_sid_cookie = response.headers.getRawHeaders('Set-Cookie')[0]

        onet_sid_match = re.search("onet_sid=(.*?);", onet_sid_cookie)
        if onet_sid_match:
            onet_sid_result = onet_sid_match.group()
        else:
            onet_sid_result = None


        if onet_sid_result != None:
            cookie = cookie+' '+onet_sid_result
            finished = Deferred()
            response.deliverBody(BeginningPrinter(finished))
            finished.addCallback(self.cbGetSecondCookieSuccess, cookie)
            finished.addErrback(self.cbShutdown)
            return finished
        else:
            self.authorise()

    def cbGetSecondCookieSuccess(self, result, cookie):
        if self.nickname[0] != '~':
            postvars = "r=&url=&login=%s&haslo=%s&ok=Ok" % (self.nickname, self.password)
            body = StringProducer(str(postvars))

            headers = {}
            headers['Cache-Control'] = ['no-cache']
            headers['Pragma'] = ['no-cache']
            headers['Host'] = ['secure.onet.pl']
            headers['Connection'] = ['keep-alive']
            headers['User-Agent'] = ['Mozilla/4.0 (FreeBSD) Java-brak ;)']
            headers['Content-Type'] = ['application/x-www-form-urlencoded']
            headers['Cookie'] = [cookie]
            headers = Headers(headers)

            d = self.agent.request(
                'POST',
                'http://secure.onet.pl/index.html',
                headers,
                body)

            d.addCallback(self.postLoginInfo, cookie)
            d.addErrback(self.cbShutdown)
        else:
            self.postAuth(cookie, True)

    def postLoginInfo(self, result, cookie):
        self.postAuth(cookie, False)

    def postAuth(self, cookie, anonymous=True):
        nickname = self.nickname
        if anonymous != True:
            postvars = "api_function=getUoKey&params=a:3:{s:4:\"nick\";s:%d:\"%s\";s:8:\"tempNick\";i:0;s:7:\"version\";s:22:\"1.0(20090306-1441 - R)\";}" % (len(nickname), nickname)
        else:
            postvars = "api_function=getUoKey&params=a:3:{s:4:\"nick\";s:%d:\"%s\";s:8:\"tempNick\";i:1;s:7:\"version\";s:22:\"1.0(20090306-1441 - R)\";}" % (len(nickname) - 1, nickname[1:])

        body = StringProducer(str(postvars))

        headers = {}
        headers['Cache-Control'] = ['no-cache']
        headers['Pragma'] = ['no-cache']
        headers['Host'] = ['czat.onet.pl']
        headers['Connection'] = ['close']
        headers['User-Agent'] = ['Mozilla/4.0 (FreeBSD) Java-brak ;)']
        headers['Accept'] = ['text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2']
        headers['Content-Type'] = ['application/x-www-form-urlencoded']
        headers['Cookie'] = [cookie]
        headers = Headers(headers)

        d = self.agent.request(
            'POST',
            'http://czat.onet.pl/include/ajaxapi.xml.php3',
            headers,
            body)

        d.addCallback(self.cbPostAuth, cookie)
        d.addErrback(self.cbShutdown)

    def cbPostAuth(self, response, cookie):
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        finished.addCallback(self.cbPostAuthSuccess, cookie)
        finished.addErrback(self.cbShutdown)
        return finished

    def cbPostAuthSuccess(self, result, cookie):
        result = result.decode('ISO-8859-2').encode('UTF-8')

        xml_root = minidom.parseString(result)
        try:
            bool(xml_root.getElementsByTagName('error')[0].attributes['err_code'].value)
            uokey = xml_root.getElementsByTagName('uoKey')[0].firstChild.data

            self.authorised.addCallback(self._onAuthorised, self.nickname, self.password, uokey)
            self.authorised.callback(self)

        except:
            print 'blad'


    def cbShutdown(self, ignored):
        logger.info("Something went wrong.")
        logger.info('cbShutdown: ', ignored)

    def _onAuthorised(self, result, nickname, password, uokey):
        return self.onAuthorised(nickname, password, uokey)


    def onAuthorised(nickname, password, uokey):
        pass

class AvatarFetcher(object):
    def __init__(self, nick, url):
        self.nick = nick
        self.url = url
        self.agent = Agent(reactor)

    def get(self):
        d = self.agent.request(
            'GET',
            self.url,
            None,
            None)

        d.addCallback(self.cbGetContent)
        d.addErrback(self.cbShutdown)

    def cbGetContent(self, response):
#        print 'Response version:', response.version
#        print 'Response code:', response.code
#        print 'Response phrase:', response.phrase
#        print 'Response headers:'
#        print pformat(list(response.headers.getAllRawHeaders()))
        mime = response.headers.getRawHeaders('Content-Type')[0]
        finished = Deferred()
        response.deliverBody(BeginningPrinter(finished))
        finished.addCallback(self.cbGetContentSuccess, mime)
        finished.addErrback(self.cbShutdown)
        return finished

    def cbGetContentSuccess(self, content, mime):
        self.onAvatarFetched(self.nick, mime, content)

    def onAvatarFetched(nick, mime, data):
        pass

    def cbShutdown(self, ignored):
        logger.info("Something went wrong.")
        logger.info('cbShutdown: ', ignored)

class IRCProtocol(basic.LineReceiver):

    def __init__(self, profile):
        self.user_profile = profile # the user connected to this client

        self.loginSuccess = Deferred()
        self.loginSuccess.addCallback(profile._loginSuccess)

        self.uokey = None

        self.serv_id = None
        self.room_list = ''
        self.nicks = {}
        self.user_info = {}

    def connectionMade(self):
        self.auth = OnetAuth(self.user_profile.account, self.user_profile.password)
        self.auth.onAuthorised = self.onAuthorised
        self.auth.authorise()

        logger.info("Connected to Onet Czat at %s." %
                        time.asctime(time.localtime(time.time())))

    def onAuthorised(self, nickname, password, uokey):
        self.uokey = uokey
        logger.info("Authorised to Onet Czat at %s." %
                        time.asctime(time.localtime(time.time())))
        self.register()

    def onAuthKeyRecv(self):
        nick = 'NICK %s' % self.user_profile.account
        self.sendData(nick)
        user = 'USER * %s czat-app.onet.pl :%s' % (self.uokey, self.user_profile.account)
        self.sendData(user)
        auth = "AUTHKEY %s" % self.auth.auth(self.authkey)
        self.sendData(auth)

    def connectionLost(self, reason):
        basic.LineReceiver.connectionLost(self, reason)

    def lineReceived(self, line):
        line = line.decode('ISO-8859-2').encode('UTF-8')
        #print "[recv]:", line

        part = line.split(' ', 4)
        if part[0].startswith(':'):
            #Lets get server id
            if part[1] == 'NOTICE' and part[2] == 'Auth':
                self.serv_id = part[0]
            if part[0] == self.serv_id:
                if part[1] in consts.numeric_to_symbolic:
                    packet_id = consts.numeric_to_symbolic[part[1]]
                    #print "[recv packet]:", packet_id
                    if packet_id == 'ONETAUTHKEY':
                        self.authkey = part[3][1:]
                        self.onAuthKeyRecv()
                    elif packet_id == 'RPL_WELCOME':
                        self.sendData("PROTOCTL ONETNAMESX")
                        self.loginSuccess.callback(self)
                    elif packet_id == 'RPL_ROOMLIST_START':
                        self.room_list = ''
                    elif packet_id == 'RPL_ROOMLIST_MORE':
                        self.room_list += part[3][1:]+','
                    elif packet_id == 'RPL_ROOMLIST_END':
                        self.room_list = self.room_list
                    elif packet_id == 'RPL_TOPIC':
                        room_id = part[3]
                        topic = part[4][1:]
                        self.user_profile.onTopicRecv(room_id, topic)
                    elif packet_id == 'RPL_NAMREPLY':
                        #napisac obsluge wiekszej ilosci ludzi w pokoju, yay!
                        room_id, nicks = part[4].split(' :', 2)
                        try:
                            self.nicks[str(room_id)] = str(self.nicks[str(room_id)]+' '+nicks)
                        except:
                            self.nicks[str(room_id)] = nicks
                    elif packet_id == 'RPL_ENDOFNAMES':
                        room_id = part[3]
                        nicks = self.nicks[room_id]
                        self.user_profile.onNicksRecv(room_id, nicks)
            if part[1] == 'PRIVMSG':
                #:Meia!52087932@2294E8.464015.8C906F.765D3D PRIVMSG #Admin :%Fb:times%adminer przekaza� mu co� ? :x
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]
                room_id = part[2]
                try:
                    msg = part[3]+' '+part[4]
                except:
                    msg = part[3]
                msg = msg[1:]
#                try:
#                    formatting = re.findall("%(.+?)%", msg)[0]
#                    msg = msg[len(formatting)+2:]
#                except:
#                    formatting = None
                formatting = None

                self.user_profile.onMsgRecv(room_id, nick, msg, formatting)
            elif part[1] == 'QUIT':
                #:Hydroxyzine!47450187@3DE379.794AE2.DC10C3.260DFE QUIT :Ping timeout: 121 seconds
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                self.user_profile.onNickQuit(nick)
            elif part[1] == 'JOIN':
                #:BaSzKaX!25901787@F4C727.DA810F.2A0EF1.B54653 JOIN #testy :x,0
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]
                room_id = part[2]
                flags = part[3]

                self.user_profile.onNickJoin(nick, room_id, flags)
            elif part[1] == 'PART':
                #:ona_niesklasyfikowana!25306191@0AD995.23792D.D70710.950B18 PART #testy
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                room_id = part[2]

                self.user_profile.onNickPart(nick, room_id)
            elif part[1] == 'NOTICE':
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                if nick == 'NickServ':
                    packet = part[3][1:]
                    if packet == '111':
                        result = part[4].split(' ', 2)
                        info_nick = result[0]
                        info_key = result[1]
                        info_val = result[2]

                        if info_nick not in self.user_info:
                            self.user_info[str(info_nick)] = {}

                        self.user_info[str(info_nick)][str(info_key)] = info_val[1:]
                    elif packet == '112':
                        result = part[4].split(' :')
                        nick = result[0]

                        self.user_profile.userInfoRecv(nick, self.user_info[str(nick)])
                        del self.user_info[str(nick)]
            elif part[1] == 'MODE':
                #:Merovingian!26269559@jest.piekny.i.uroczy.ma.przesliczne.oczy MODE Merovingian :+b
                #:Merovingian!26269559@2294E8.94913F.2EAEC9.11F26D MODE Merovingian :+b
                #:ankaszo!51613093@F4C727.446F67.966AC9.BAAE26 MODE ankaszo -W
                #:NickServ!service@service.onet MODE scc_test +r
                #:ChanServ!service@service.onet MODE #scc +ips
                #:ChanServ!service@service.onet MODE #scc +o scc_test
                #:ChanServ!service@service.onet MODE #scc +eo *!51976824@* scc_test
                #:ChanServ!service@service.onet MODE #abc123 +il-e 1 *!51976824@*
                nick = part[0]
                nick = nick[nick.find(':')+1:nick.find('!')]

                if nick == 'NickServ':
                    info_nick = part[2]
                    info_mode = part[3]

                    self.user_profile.userModeRecv(info_nick, info_mode)
                elif nick == 'ChanServ':
                    pass
                else:
                    if nick == part[2]:
                        info_nick = part[2]
                        info_mode = part[3]
                        if info_mode[0] == ':':
                           info_mode = info_mode[1:]

                        self.user_profile.userModeRecv(info_nick, info_mode)
                    else:
                        pass

        elif part[1] == 'INVITE':
            who = part[0]
            who = who[who.find(':')+1:who.find('!')]
            
            nick = part[2]
            room_id = part[3]
            room_id = room_id[1:]
            
            self.user_profile.userInviteRecv(room_id, who, nick)
            
        elif part[0] == 'PING':
            self.sendPong()

    def sendData(self, line):
        #print '[send] '+line
        self.sendLine(str(line+"\n\r").encode('ISO-8859-2'))

    def register(self):
        self.sendData('AUTHKEY')

    def sendPong(self):
        self.sendData('PONG '+self.serv_id)

    #
    # High-level interface callbacks
    #

    def _warn(self, obj):
        tlog.warning( str(obj) )

    def _log(self, obj):
        tlog.msg( str(obj) )

    def _log_failure(self, failure, *args, **kwargs):
        print "Failure:"
        failure.printTraceback()


class CamProtocol(Protocol):
#[recv]: 231 0 OK kkszysiu2
#[recv]: 232 0 CMODE 0
#[recv]: 264 0 CODE_ACCEPTED ffffffff 2147483647
#[recv]: 233 0 QUALITY_FACTOR 1
#[recv]: 250 10118 OK
#[recv]: dlazdecydowanejnapriv:1::0::0251 118 UPDATE
#[recv]: RRadekk:1:3/0/#SEX_CZAT/0,3/0/#chc�_sexu/0,3/0/#kamera_sex/0,3/0/#BEZ_MAJTECZEK/0,3/0/#Ukryta_kamera/0,3/0/#Bi/0:5::16251 22 UPDATE
#[recv]: lessbijkaaaaa:1::1:4:0251 34 UPDATE
#[recv]: slodka36:0:3/0/#kamera_sex/0:0:0:0251 38 UPDATE
#[recv]: x19kamil88x21:0:3/0/#chc�_sexu/0:0:0:0251 38 UPDATE
#[recv]: x19kamil88x21:0:3/0/#chc�_sexu/0:0:0:0254 1021 USER_COUNT_UPDATE
    def __init__(self, conn, nick, uokey):
        self.conn = conn
        self.nick = nick # the user connected to this client
        self.uokey = uokey
        
        self.packet_id = None
        self.packet_info = None
        self.buffer = ''
        self.tlen = 0
        self.applet_ver = '3.1(applet)'

        self.img_id = 0

        self.loop = None

        self.loginSuccess = Deferred()
        self.loginSuccess.addCallback(self.conn._loginSuccess)

    def connectionMade(self):
        self.sendData('CAUTH 1234567890123456 %s' % (self.applet_ver))
        print ("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def onAuthorised(self, nickname, password, uokey):
        print ("[authorised at %s]" %
                        time.asctime(time.localtime(time.time())))

    def onAuthKeyRecv(self):
        pass

    def connectionLost(self, reason):
        print reason

    def packetHandler(self, pid, data):
        handle_method_name = 'handle_%s' % pid
        handle_method = getattr(self, handle_method_name)
        if handle_method:
            try:
                handle_method(data)
            except Exception, e:
                print 'Failed to call %s: ' % handle_method_name, e
        else:
            print 'Unhandled method: ', message.method

    def dataReceived(self, data):
        self.buffer += data

        while True:
            if self.packet_info is not None:
                if int(self.packet_info['length']) == 0:
                    try:
                        data = self.buffer[:self.buffer.index('\n')]

                        print "packet: %s" % (self.packet_info['pid'])
                        print "data:\n%s\n" % (data)
                        self.packetHandler(self.packet_info['pid'], data)

                        #at the end we cutting off parsed bytes, simply!
                        dlen = len(data)+1
                        self.buffer = self.buffer[dlen:]
                        
                        self.packet_info = None
                    except:
                        break
                else:
                    #tlen = (9+len(self.packet_info['length'])+int(self.packet_info['length']))
                    tlen = len(self.buffer[:self.buffer.index('\r\n')])+2+int(self.packet_info['length'])
                    #print int(self.packet_info['length'])
                    #print "%s vs %s" % (tlen, len(self.buffer))
                    if len(self.buffer) >= tlen:
                        print 'ook:\n', repr(self.buffer[:tlen])
                        tmp = self.buffer[:tlen]
                        data = tmp[len(self.buffer[:self.buffer.index('\r\n')])+2:]

                        print "packet: %s" % (self.packet_info['pid'])
                        print "data:\n%s\n" % (data)
                        self.packetHandler(self.packet_info['pid'], data)

                        self.buffer = self.buffer[tlen:]
                        self.packet_info = None
                    else:
                        break
            else:
                if len(self.buffer) >= 10:
                    tmp = self.buffer[:10]
                    #print 'tmp: ', tmp
                    pid, length, crap = tmp.split(' ', 2)
                    if len(self.buffer) >= (6+len(length)+int(length)):
                        self.packet_info = {}
                        self.packet_info['pid'] = pid
                        self.packet_info['length'] = length
                    else:
                        break
                else:
                    break

    def keepAliving(self, nick):
        self.sendData('KEEPALIVE_BIG %s' % (nick))

    def startPing(self, nick):
        self.loop = task.LoopingCall(self.keepAliving, nick)
        self.loop.start(5.0)

    def stopPing(self, nick):
        if self.loop:
            self.loop.stop()

    def sendData(self, line):
        print '[send]:', line.encode('ISO-8859-2')
        self.transport.write(str(line+"\n\r").encode('ISO-8859-2'))

    def recvLine(self, line):
        print '[recv]:', line.decode('ISO-8859-2').encode('UTF-8')

    # Packed handling function
    
    def handle_268(self, data):
        auth = 'AUTH %s %s' % (self.uokey, self.applet_ver)
        self.sendData(auth)

    def handle_231(self, data):
        pass

    def handle_232(self, data):
        pass

    def handle_233(self, data):
        pass

    def handle_200(self, data):
        pass

    def handle_264(self, data):
        pass

    def handle_412(self, data):
        pass

    def handle_413(self, data):
        part = data.split(' ', 4)
        nick = part[3]

        self.conn.onSubscribeDenied(nick)

    def handle_408(self, data):
        part = data.split(' ', 4)
        nick = part[3]

        self.conn.onNoSuchUser(nick)

    def handle_405(self, data):
        part = data.split(' ', 4)
        nick = part[3]

        self.conn.onUserGone(data)

    def handle_252(self, data):
        pass

    def handle_253(self, data):
        pass

    def handle_413(self, data):
        pass

    def handle_250(self, data):
        self.loginSuccess.callback(self)
        self.conn.onUserList(data)
        
    def handle_251(self, data):
        print "251 data:", repr(data)

    def handle_254(self, data):
        self.conn.onUserCountUpdate(data)

    def handle_202(self, data):
        self.conn.onImgRecv('aa', data)
        self.img_id += 1

