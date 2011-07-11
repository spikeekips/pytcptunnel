#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# `pytcptunnel`
################################################################################
#
# Usage: pytcptunnel.py
#
# The `pytcptunnel` is the TCP request forwarding server, in theory it can
# handle the almost every TCP-based protocol like `HTTP`, `HTTPS`, even in
# `ssh`.
#
# In the case of `HTTPS`, it acts like well-known SSL-tunneling software,
# `STUNNEL`, but `pytcptunnel` can append the `X-Forwarded-For` in the last
# line of header.
#
#
# This script is based on `twistd` script of `Twised Network Framework`(10.1.0
# or higher,), so all the options of `twistd` are available and there are some
# additional options for this script. For more details about options, just type
# the `pytcptunnel.py --help`
#
# Additional Options:
#      --vv                         verbose
#      --test                       run doctest
#      --without-x-forwarded-for    don't append `X-Forwarded-For` in the header
#      --without-host-translation   don't translate the original `Host` header
#  -B, --base=                      base server `protocol:host:port`
#  -T, --target=                    target server `host:port`
#      --ssl-priv-file=             SSL private key file
#      --ssl-cert-file=             SSL certificate file
#      --timeout=                   client timeout [default: 20]
#
#
# Examples:
#     shell> pytcptunnel.py --base=http:127.0.0.1:80 --target=www.microsoft.com:8080
#     shell> pytcptunnel.py --base=tcp:127.0.0.1:80 --target=www.microsoft.com:8080
#         This will forward the `HTTP` request from '127.0.0.1:80' to
#         'www.microsoft.com:8080', but the difference between the protocol
#         part, `http` or `tcp` is that with `http` protocol it can understand
#         the `HTTP` protocol, so add additional headers, `HOST` and
#         `X-Forwarded-For`. In depending on the target server, without `http`
#         protocol, the request could not properly handled.
#
#     shell> pytcptunnel.py
#         --base=http:127.0.0.1:443
#         --target=<http server>:80
#         --ssl-priv-file=./privkey.pem
#         --ssl-cert-file=./cacert.pem
#         -h
#         -n
#
#         This will bind the port, 443 in 127.0.0.1 and forward all the `HTTPs`
#         request to <http server>:80. For use `HTTPS`, `ssl-priv-file`,
#         `ssl-cert-file` options must be given.
#
# Tips:
#   If you have some trouble to generate ssl private and certificate key file,
#   see this page, http://www.akadia.com/services/ssh_test_certificate.html .
#
################################################################################


import os
import sys
import StringIO
import resource

from twisted.internet import ssl
from twisted.application import service
from twisted.application import internet
from twisted.python import log, usage
from twisted.internet import error
from twisted.internet import protocol
from twisted.scripts._twistd_unix import ServerOptions


SUPPORTED_PROTOCOLS = (
    "https",
    "http",
    "tcp",
    "ssh",
)

KNOWN_PROTOCOLS = {
    "https": 443,
    "http": 80,
    "ssh": 22,
}

KNOWN_HTTP_METHODS = (
    "OPTIONS",
    "GET",
    "HEAD",
    "POST",
    "PUT",
    "DELETE",
    "TRACE",
    "CONNECT",
)


class Sender (protocol.Protocol, ) :
    _receiver = None

    def setReceiver (self, receiver, ) :
        self._receiver = receiver

        return self

    def connectionLost (self, reason, ) :
        if self._receiver is None :
            return

        if reason.type is error.ConnectionDone :
            pass
        elif reason.type is error.ConnectionLost :
            pass
        else :
            pass

        self._receiver.transport.loseConnection()

    def dataReceived (self, data, ) :
        if self._receiver is None :
            return

        self._receiver.transport.write(data, )

    def connectionMade (self, ) :
        if self._receiver._receiverOk :
            self._receiver.setSender(self, )
        else :
            data = self._receiver.buf
            if data :
                self.transport.write(data, )

            self.transport.loseConnection()
            self.setReceiver(None, )


class SenderFactory (protocol.ClientFactory, ) :
    protocol = Sender
    noisy = 0

    def setReceiver (self, receiver, ) :
        self._receiver = receiver

        return self

    def buildProtocol (self, *a, **kw) :
        return protocol.ClientFactory.buildProtocol(
            self, *a, **kw).setReceiver(self._receiver, )

    def clientConnectionFailed (self, connector, reason, ) :
        log.msg("[ee] failed to connect to %s:%d. %s" % (
            self._receiver.factory._host,
            self._receiver.factory._port,
            reason,
        ), )

        self._receiver.transport.loseConnection()

    def stopFactory (self, *a, **kw) :
        return protocol.ClientFactory.stopFactory(self, *a, **kw)


class Receiver (protocol.Protocol, ) :
    buf = str()
    _sender = None
    _receiverOk = 0

    def __init__ (self, *a, **kw) :
        self.buf = str()
        self._receiverOk = 0
        self._sender = None

    def _modify_header (self, buf, ) :
        return buf

    def connectionMade (self, ) :
        self._receiverOk = 1
        self.client_addr = self.transport.client
        sender = SenderFactory()
        sender.setReceiver(self, )

        if self.factory._kw.get("verbose") :
            log.msg(
                "connection: %s > %s:%d" % (
                    ("%s:%d" % self.client_addr),
                    self.factory._host,
                    self.factory._port,
                ),
            )

        from twisted.internet import reactor
        reactor.connectTCP(
            self.factory._host,
            self.factory._port,
            sender,
            timeout=self.factory._timeout,
        )

    def setSender (self, sender, ) :
        self._sender = sender
        if self.buf :
            self.send()

        return self

    def connectionLost (self, reason, ) :
        if self._sender :
            self._sender.setReceiver(None, )
            self._sender.transport.loseConnection()

        self._receiverOk = 0

    def dataReceived (self, data, ) :
        self.buf += data

        if self._sender is not None :
            self.send()

    def send (self, ) :
        #map(
        #    lambda x : self._sender.transport.write(x, ),
        #    self._modify_header(self.buf, )
        #)
        self._sender.transport.write(self._modify_header(self.buf, ), ),

        self.buf = str()


class HTTPReceiver (Receiver, ) :
    def _modify_header (self, buf, ) :
        """
        >>> class F (object, ) :
        ...    _host = "127.0.0.1"
        ...    _port = 8080
        ...    _without_x_forwarded_for = False
        ...    _without_host_translation = False
        >>> _h = HTTPReceiver()
        >>> _h.factory = F()
        >>> _h.client_addr = ("10.0.1.2", 394802 , )

        >>> _msg = 'POST / HTTP/1.1\\r\\nUser-Agent: Wget/1.12 (darwin10.6.0)\\r\\nAccept: */*\\r\\nHost: localhost:9993\\r\\nConnection: Keep-Alive\\r\\nContent-Type: application/x-www-form-urlencoded\\r\\nContent-Length: 3\\r\\n\\r\\na=1&b=2'

        >>> _o = [i for i in _h._modify_header(_msg, )]
        >>> _o[3] == "Host: %s:%s\\r\\n" % (F._host, F._port, )
        True
        >>> True in [i.lower().startswith("x-forwarded-for: ") for i in _o]
        True
        >>> _o[7] == "X-Forwarded-For: %s\\r\\n" % _h.client_addr[0]
        True

        Not append `X-Forwarded-For` header

        >>> F._without_x_forwarded_for = True
        >>> _h.factory = F()
        >>> _o = [i for i in _h._modify_header(_msg, )]
        >>> True not in [i.lower().startswith("x-forwarded-for: ") for i in _o]
        True

        Without translating `Host` header

        >>> F._without_x_forwarded_for = False
        >>> F._without_host_translation = True
        >>> _h.factory = F()
        >>> _o = [i for i in _h._modify_header(_msg, )]
        >>> _o[3] == (_msg.split("\\r\\n")[3] + "\\r\\n")
        True

        If applied both,

        >>> F._without_x_forwarded_for = True
        >>> F._without_host_translation = True
        >>> _h.factory = F()
        >>> _o = [i for i in _h._modify_header(_msg, )]
        >>> _o[0] == _msg
        True

        """

        if self.factory._without_x_forwarded_for and self.factory._without_host_translation :
            return buf
        else :
            _st = str()
            _b = StringIO.StringIO(buf, )
            _found_header = True
            while True :
                _s = _b.readline()
                if not _s :
                    break

                if _found_header and _s == "\r\n" :
                    _found_header = False
                    if not self.factory._without_x_forwarded_for :
                        _st += "X-Forwarded-For: %s\r\n" % self.client_addr[0]
                    _st += _s
                elif (_found_header and not self.factory._without_host_translation and
                        _s[:6].upper().startswith("HOST: ")) :

                    _st += "Host: " + self.factory._host + ":" + str(self.factory._port) + "\r\n"
                    continue

                _st += _s

            return _st


class ReceiverFactory (protocol.ServerFactory, ) :
    protocol = Receiver
    noisy = 0

    def __init__(self, name, (host, port, ), timeout=20, **kw) :
        self._name = name
        self._host = host
        self._port = port
        self._timeout = timeout

        self._kw = kw


class HTTPReceiverFactory (ReceiverFactory, ) :
    protocol = HTTPReceiver

    def __init__(self, *a, **kw) :
        ReceiverFactory.__init__(self, *a, **kw)

        self._without_x_forwarded_for = kw.get("without_x_forwarded_for", False, )
        self._without_host_translation = kw.get("without_host_translation", False, )


class Options (ServerOptions, ) :
    synopsis = "Usage: %s [options]" % os.path.basename(sys.argv[0])
    optFlags = (
        ["vv", None, "verbose", ],
        ["test", None, "run doctest", ],
        ["without-x-forwarded-for", None,
            "don't append `X-Forwarded-For` in the header", ],
        ["without-host-translation", None,
            "don't translate the original `Host` header", ],
    )
    optParameters = (
        ["base", "B", None, "base server `protocol:host:port`", ],
        ["target", "T", None, "target server `host:port`", ],
        ["ssl-priv-file", None, None, "SSL private key file", ],
        ["ssl-cert-file", None, None, "SSL certificate file", ],
        ["timeout", None, 20, "client timeout", ],
    )
    unused_short = ("-o", "-f", "-s", "-y", "-d", )
    unused_long = ("--rundir=", "--python=", "--savestats", "--no_save",
        "--encrypted", "--file=", "--source=", "--test", "--originalname", )

    def __init__ (self, *a, **kw) :
        ServerOptions.__init__(self, *a, **kw)

        for i in self.unused_long :
            if self.longOpt.count(i[2:]) > 0 :
                del self.longOpt[self.longOpt.index(i[2:])]

    def __getattribute__ (self, k, ) :
        if k == "subCommands" :
            raise AttributeError

        return ServerOptions.__getattribute__(self, k, )

    def parseOptions (self, *a, **kw) :
        self._skip_reactor = kw.get("skip_reactor")
        if "skip_reactor" in kw :
            del kw["skip_reactor"]

        super(Options, self).parseOptions(*a, **kw)

        if not self.get("base") or not self.get("target") :
            raise usage.UsageError("`base` and `target` must be given.", )

        if self.get("base")[0] in ("https", ) :
            if not self.get("ssl-priv-file") or not self.get("ssl-cert-file") :
                raise usage.UsageError(
            "For `https`, `ssl-priv-file` and `ssl-cert-file` must be given.", )

    def opt_base (self, value, ) :
        try :
            (_proto, _host_and_port, ) = value.split(":", 1, )
        except ValueError :
            raise usage.UsageError(
            "invalid format of `base`, '<protocol>:<host address>[:<port>]'", )
        else :
            if _proto.lower() not in SUPPORTED_PROTOCOLS :
                raise usage.UsageError(
                    "invalid `protocol`, %s" % ", ".join(SUPPORTED_PROTOCOLS), )

            _proto = _proto.lower()

        _a = _host_and_port.split(":", 1)
        _a.append(None, )
        _host, _port = _a[0], _a[1]

        if _port is None and _proto in KNOWN_PROTOCOLS :
            _port = KNOWN_PROTOCOLS.get(_proto, )
        else :
            try :
                _port = int(_port)
            except ValueError :
                raise usage.UsageError(
                    "invalid `port`, '%s', it must be int value." % _port, )

        if _host == "*" :
            _host = None

        self["base"] = (_proto, _host, _port, )

    def opt_target (self, value, ) :
        try :
            (_host, _port, ) = value.split(":", 1, )
        except ValueError :
            raise usage.UsageError(
                "invalid format of `target`, '<host address or ip>:<port>'", )

        try :
            _port = int(_port)
        except ValueError :
            raise usage.UsageError(
                "invalid `port`, '%s', it must be int value." % _port, )

        self["target"] = (_host, _port, )

    def opt_timeout (self, value, ) :
        try :
            _v = int(value, )
        except ValueError :
            raise usage.UsageError(
                "invalid `timeout`, '%s', it must be int value." % value, )

        self["timeout"] = _v

    def opt_vv (self, value, ) :
        del self["vv"]
        self["verbose"] = True

    def opt_reactor (self, v, ) :
        if self._skip_reactor :
            return
        return ServerOptions.opt_reactor(self, v, )


if __name__ == "__builtin__"  :
    _options = Options()
    _options.parseOptions(skip_reactor=True, )

    if _options.get("test") :
        import doctest
        doctest.testmod()
        sys.exit()

    (_proto, _host, _port, ) = _options.get("base")

    _a = list()
    _kw = dict()
    if _host :
        _kw["interface"] = _host

    _server = internet.TCPServer
    _factory = ReceiverFactory
    if _proto == "https" :
        _server = internet.SSLServer
        _a.append(
            ssl.DefaultOpenSSLContextFactory(
                _options.get("ssl-priv-file"),
                _options.get("ssl-cert-file"),
            ),
        )

    if _proto in ("https", "http", ) :
        _factory = HTTPReceiverFactory

    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024, ), )
    application = service.Application("pytcptunnel", )

    _server(
        _port,
        _factory(
            "target",
            _options.get("target"),
            timeout=_options.get("timeout"),
            without_x_forwarded_for=_options.get("without-x-forwarded-for"),
            without_host_translation=_options.get("without-host-translation"),
            verbose=_options.get("verbose"),
        ),
        *_a,
        **_kw
    ).setServiceParent(application, )


elif __name__ == "__main__"  :
    _found = False
    _n = list()
    _n.append(sys.argv[0], )
    for i in sys.argv[1:] :
        if _found :
            _found = False
            continue
        elif i in Options.unused_short :
            _found = True
            continue
        elif filter(i.startswith, Options.unused_long, ) :
            continue

        _n.append(i, )

    _n.extend(["-y", __file__, ], )
    sys.argv = _n

    from twisted.application import app
    from twisted.scripts.twistd import runApp
    app.run(runApp , Options, )

