import sys
import os
import socket
import subprocess
import re

import OpenSSL.SSL as SSL

from lib.util import rootDir, userDir, filesDir

homeDir = 'home'
authFile = os.path.join(filesDir, 'test-ofmipd.auth')
certFile = os.path.join(filesDir, 'test-ofmipd.cert')
keyFile = os.path.join(filesDir, 'test-ofmipd.key')

class TestOfmipdServer(object):
    _script = os.path.join(rootDir, 'bin', 'tmda-ofmipd')
    _commonServerOpts = ['--configdir=%s' % homeDir]
    _sslServerOpts = ['--ssl-cert=%s' % certFile,
                      '--ssl-key=%s' % keyFile]

    def init(self, addrs=None):
        if addrs is None:
            addrs = ['127.0.0.1', '::1']

        # options
        self._debug = ''
        self._ground = '-f'
        self._ssl = ''
        self._authOpts = []
        self._extraOpts = []

        self._serverProc = None
        self._v4addrs = []
        self._v6addrs = []
        for addr in list(addrs):
            if ':' in addr:
                self._v6addrs.append((addr, 8025))
            else:
                self._v4addrs.append((addr, 8025))
        return self

    def start(self):
        # With sys.executable, we make sure the server runs under the same
        # Python version.
        serverOpts = [sys.executable, self._script]
        serverOpts.extend(self._commonServerOpts)
        serverOpts.extend(self._authOpts)

        additionalOpts = [self._debug, self._ground, self._ssl]
        additionalOpts = [arg for arg in additionalOpts if arg]
        serverOpts.extend(additionalOpts)

        if self._ssl:
            serverOpts.extend(self._sslServerOpts)

        newEnv = dict(os.environ)
        newEnv['PYTHONPATH'] = rootDir
        newEnv['TMDA_TEST_HOME'] = userDir

        # XXX Figure out how to detect in-use ports and try a different one
        bindOpts = []
        for addr in self._v4addrs:
            bindOpts.append('-p')
            bindOpts.append('%s:%d' % addr)
        for addr in self._v6addrs:
            bindOpts.append('-6')
            bindOpts.append('%s:%d' % addr)

        serverOpts.extend(bindOpts)
        serverOpts.extend(self._extraOpts)

        self._serverProc = subprocess.Popen(serverOpts, env=newEnv)

        # Wait for server availability
        addr = (self._v6addrs + self._v4addrs)[0]
        family = socket.AF_INET6 if ':' in addr[0] else socket.AF_INET
        s = socket.socket(family, socket.SOCK_STREAM)
        from time import sleep
        sleep(0.1) # wait 1/10th of a second for server to start
        while True:
            try:
                s.connect(addr)
                s.close()
                break
            except socket.error:
                sleep(1) # try again once per second
                pass

    def stop(self):
        import signal

        os.kill(self._serverProc.pid, signal.SIGTERM)
        self._serverProc.wait()

    def debug(self, debug=True):
        if debug:
            self._debug = '-d'
        else:
            self._debug = ''

    def foreground(self):
        self._ground = '-f'

    def background(self):
        self._ground = '-b'

    def ssl(self, useSsl=True):
        if useSsl:
            self._ssl = '--ssl'
        else:
            self._ssl = ''

    def tls(self, option='on'):
        self._ssl = '--tls=%s' % option

    def addOptions(self, opts):
        if isinstance(opts, basestring):
            opts = [opts]

        self._extraOpts.extend(opts)

    # Various authentication types
    def addFileAuth(self, filename=authFile):
        self._authOpts.append('--authfile=%s' % filename)

    def addPamAuth(self, service):
        self._authOpts.append('--pamauth=%s' % service)

    def addProgAuth(self, program):
        self._authOpts.append('--authprog=%s' % program)

    def addRemoteAuth(self, url):
        self._authOpts.append('--remoteauth=%s' % url)

    def makeClient(self, addr=None):
        if addr is None:
            addr = (self._v6addrs + self._v4addrs)[0]
        elif addr == 'v6':
            addr = self._v6addrs[0]
        elif addr == 'v4':
            addr = self._v4addrs[0]

        client = TestOfmipdClient().init(addr)

        if self._ssl == '--ssl':
            client.ssl()
        elif self._ssl.startswith('--tls='):
            client.tls()

        return client

class TestOfmipdClient(object):
    def init(self, address, family=None):
        if family is None:
            if ':' in address[0]:
                family = socket.AF_INET6
            else:
                family = socket.AF_INET

        self._address = address
        self._normalSock = socket.socket(family, socket.SOCK_STREAM)
        self._sslSock = None
        self._sock = self._normalSock
        self._ssl = 'off' # or 'ssl', or 'tls'
        self._connected = False
        return self

    # Option setting

    def ssl(self, useSsl=True):
        if useSsl:
            self._ssl = 'ssl'
        else:
            self._ssl = 'off'

    def tls(self, useTls=True):
        if useTls:
            self._ssl = 'tls'
        else:
            self._ssl = 'off'

    # Operations

    def connect(self, start_tls=False):
        if self._ssl == 'ssl':
            self.startSsl()

        self._sock.connect(self._address)
        self._sock.recv(200)

        if start_tls and self._ssl == 'tls':
            self.startTls()

        self._connected = True

    def startSsl(self):
        context = SSL.Context(SSL.SSLv23_METHOD)
        self._sslSock = SSL.Connection(context, self._normalSock)
        self._sslSock.set_connect_state()

        self._sock = self._sslSock

    def startTls(self):
        (code, lines) = self.exchange('STARTTLS\r\n')
        assert code == 220, 'STARTTLS failed, code=%d' % code
        self.startSsl()

    def signOn(self, username='testuser', password='testpassword'):
        if not self._connected:
            self.connect(True)

        userpass = '%s\x00%s\x00%s' % (username, username, password)
        userpass = userpass.encode('base64')[:-1]
        (code, lines) = self.exchange('AUTH PLAIN %s\r\n' % userpass)
        assert code == 235, 'AUTH failed, code=%d' % code

    def receiveUntil(self, finished):
        data = ''
        while not finished(data):
            data += self._sock.recv(200)
        return data

    def send(self, data):
        self._sock.send(data)

    def exchange(self, msg):
        self.send(msg)
        response = self.receiveUntil(self._completeResponse)
        return self._splitResponse(response)

    # Helpers, etc.

    _responseMatcher = re.compile(r'^\d{3} .*\r\n', re.MULTILINE)
    def _completeResponse(self, data):
        return self._responseMatcher.search(data) is not None

    _responseLineMatcher = re.compile(r'^(?P<code>\d{3})[- ](?P<line>.*)\r\n',
                                      re.MULTILINE)
    def _splitResponse(self, response):
        'return (code, [lines])'
        lines = []
        code = None
        for m in self._responseLineMatcher.finditer(response):
            newCode = int(m.group('code'))
            if code is not None and code != newCode:
                raise ValueError('mismatched result codes in response')
            code = newCode
            lines.append(m.group('line'))

        return (code, lines)

    def _needsTls(self):
        return self._ssl == 'tls' and self._sslSock is None

# This is a mixin for unittest.TestCases that need to create a server and poke
# at it. It spawns a server and acts as a client for that server. It has a lot
# of methods to allow derived classes to override behavior.
class ServerClientMixin(object):
    def setUp(self):
        self.serverSetUp()
        self.clientSetUp()

    def tearDown(self):
        self.server.stop()

    # Server parts
    def serverSetUp(self):
        self.server = self.serverCreate()
        self.serverAddOptions()
        self.serverStart()

    # Override serverCreate to add server options.
    def serverCreate(self):
        return TestOfmipdServer().init()

    def serverAddOptions(self):
        pass

    def serverStart(self):
        self.server.start()

    # Client parts
    client_addr = 'v6'
    client_starttls_on_connect = True

    def clientSetUp(self):
        self.client = self.clientCreate()
        self.clientAddOptions()
        self.clientConnect()
        self.clientBeginCommunication()

    def clientCreate(self):
        return self.server.makeClient(self.client_addr)

    def clientAddOptions(self):
        pass

    def clientConnect(self):
        # start_tls=True only has an effect if the server is actually in
        # starttls mode.
        self.client.connect(self.client_starttls_on_connect)

    def clientBeginCommunication(self):
        pass
