import sys
from datetime import datetime
from time import time
from functools import partial

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet.error import CannotListenError
from twisted.internet.task import LoopingCall

import messages
import cryptotools

PING_INTERVAL = 1200.0 # 20 min = 1200.0
BOOTSTRAP_NODES = ["localhost:5008",
                  "localhost:5007",
                  "localhost:5006",
                  "localhost:5005"]

def _print(*args):
    time = datetime.now().time().isoformat()[:8]
    print time,
    print " ".join(map(str, args))
    
class NCProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO", kind="RECV"):
        self.factory = factory
        self.state = state
        self.VERSION = 0
        self.remote_nodeid = None
        self.kind = kind
        self.nodeid = self.factory.nodeid
        self.lc_ping = LoopingCall(self.send_PING)
        self.message = partial(messages.envelope_decorator, self.nodeid)

    def connectionMade(self):
        r_ip = self.transport.getPeer()
        h_ip = self.transport.getHost()
        self.remote_ip = r_ip.host + ":" + str(r_ip.port)
        self.host_ip = h_ip.host + ":" + str(h_ip.port)

    def print_peers(self):
        if len(self.factory.peers) == 0:
            _print(" [!] PEERS: No peers connected.")
        else:
            _print(" [ ] PEERS:")
            for peer in self.factory.peers:
                addr, kind = self.factory.peers[peer][:2]
                _print("     [*]", peer, "at", addr, kind)

    def write(self, line):
        self.transport.write(line + "\n")

    def connectionLost(self, reason):
        # NOTE: It looks like the NCProtocol instance will linger in memory
        # since ping keeps going if we don't .stop() it.
        try: self.lc_ping.stop()
        except AssertionError: pass
        
        try:
            self.factory.peers.pop(self.remote_nodeid)
            if self.nodeid != self.remote_nodeid:
                self.print_peers()
        except KeyError:
            if self.nodeid != self.remote_nodeid:
                _print(" [ ] GHOST LEAVES: from", self.remote_nodeid, self.remote_ip)

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            envelope = messages.read_envelope(line)
            if self.state in ["GETHELLO", "SENTHELLO"]:
                # Force first message to be HELLO or crash
                if envelope['msgtype'] == 'hello':
                    self.handle_HELLO(line)
                else:
                    _print(" [!] Ignoring", envelope['msgtype'], "in", self.state)
            else:
                if envelope['msgtype'] == 'ping':
                    self.handle_PING(line)
                elif envelope['msgtype'] == 'pong':
                    self.handle_PONG(line)
                elif envelope['msgtype'] == 'addr':
                    self.handle_ADDR(line)

    def send_PING(self):
        _print(" [>] PING   to", self.remote_nodeid, "at", self.remote_ip)
        ping = messages.create_ping(self.nodeid)
        self.write(ping)

    def handle_PING(self, ping):
        if messages.read_message(ping):
            pong = messages.create_pong(self.nodeid)
            self.write(pong)

    def send_ADDR(self):
        _print(" [>] Telling " + self.remote_nodeid + " about my peers")
        # Shouldn't this be a list and not a dict?
        peers = self.factory.peers
        listeners = [(n, peers[n][0], peers[n][1], peers[n][2])
                     for n in peers]
        addr = messages.create_addr(self.nodeid, listeners)
        self.write(addr)

    def handle_ADDR(self, addr):
        try:
            nodes = messages.read_message(addr)['nodes']
            _print(" [<] Recieved addr list from peer " + self.remote_nodeid)
            #for node in filter(lambda n: nodes[n][1] == "SEND", nodes):
            for node in nodes:
                _print("     [*] "  + node[0] + " " + node[1])
                if node[0] == self.nodeid:
                    _print(" [!] Not connecting to " + node[0] + ": thats me!")
                    return
                if node[1] != "SEND":
                    _print(" [ ] Not connecting to " + node[0] + ": is " + node[1])
                    return
                if node[0] in self.factory.peers:
                    _print(" [ ] Not connecting to " + node[0]  + ": already connected")
                    return
                _print(" [ ] Trying to connect to peer " + node[0] + " " + node[1])
                # TODO: Use [2] and a time limit to not connect to "old" peers
                host, port = node[0].split(":")
                point = TCP4ClientEndpoint(reactor, host, int(port))
                d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO", "SEND"))
                d.addCallback(gotProtocol)
        except messages.InvalidSignatureError:
            print addr
            _print(" [!] ERROR: Invalid addr sign ", self.remote_ip)
            self.transport.loseConnection()

    def handle_PONG(self, pong):
        pong = messages.read_message(pong)
        _print(" [<] PONG from", self.remote_nodeid, "at", self.remote_ip)
        # hacky
        addr, kind = self.factory.peers[self.remote_nodeid][:2]
        self.factory.peers[self.remote_nodeid] = (addr, kind, time())

    def send_HELLO(self):
        hello = messages.create_hello(self.nodeid, self.VERSION)
        #_print(" [ ] SEND_HELLO:", self.nodeid, "to", self.remote_ip)
        self.transport.write(hello + "\n")
        self.state = "SENTHELLO"
        
    def handle_HELLO(self, hello):
        try:
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['nodeid']
            if self.remote_nodeid == self.nodeid:
                _print(" [!] Found myself at", self.host_ip)
                self.transport.loseConnection()
            else:
                if self.state == "GETHELLO":
                    my_hello = messages.create_hello(self.nodeid, self.VERSION)
                    self.transport.write(my_hello + "\n")
                self.add_peer()
                self.state = "READY"
                self.print_peers()
                #self.write(messages.create_ping(self.nodeid))
                if self.kind == "RECV":
                    # The listener pings it's audience
                    _print(" [ ] Starting pinger to " + self.remote_nodeid)
                    self.lc_ping.start(PING_INTERVAL, now=False)
                    # Tell new audience about my peers
                    self.send_ADDR()
        except messages.InvalidSignatureError:
            _print(" [!] ERROR: Invalid hello sign ", self.remoteip)
            self.transport.loseConnection()

    def add_peer(self):
        entry = (self.remote_ip, self.kind, time())
        self.factory.peers[self.remote_nodeid] = entry

# Splitinto NCRecvFactory and NCSendFactory (also reconsider the names...:/)
class NCFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.numProtocols = 0
        self.nodeid = cryptotools.generate_nodeid()[:10]
        _print(" [ ] NODEID:", self.nodeid)

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NCProtocol(self, "GETHELLO", "RECV")

def gotProtocol(p):
    # ClientFactory instead?
    p.send_HELLO()
    
if __name__ == "__main__":
    # start listener
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 5005
    try:
        endpoint = TCP4ServerEndpoint(reactor, port)
        _print(" [ ] LISTEN:", port)
        ncfactory = NCFactory()
        endpoint.listen(ncfactory)
    except CannotListenError:
        _print("[!] Address in use")
        sys.exit(1)

    
    # connect to bootstrap addresses
    _print(" [ ] Trying to connect to bootstrap hosts:")
    for bootstrap in BOOTSTRAP_NODES:
        _print("     [*]", bootstrap)
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO", "SEND"))
        d.addCallback(gotProtocol)
    reactor.run()
