import sys

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet.error import CannotListenError
from twisted.internet.task import LoopingCall

import messages
import cryptotools

bootstrap_list = ["localhost:5008",
                  "localhost:5007",
                  "localhost:5006",
                  "localhost:5005"]

class NCProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO", kind="RECV"):
        self.factory = factory
        self.state = state
        self.VERSION = 0
        self.remote_nodeid = None
        self.kind = kind
        self.nodeid = self.factory.nodeid
        self.lc_ping = LoopingCall(self.send_PING)

    def connectionMade(self):
        r_ip = self.transport.getPeer()
        h_ip = self.transport.getHost()
        self.remote_ip = r_ip.host + ":" + str(r_ip.port)
        self.host_ip = h_ip.host + ":" + str(h_ip.port)

    def print_peers(self):
        print " [ ] STATE:", self.state
        if len(self.factory.peers) == 0:
            print " [!] PEERS: No peers connected."
        else:
            print " [ ] PEERS:"
            for peer in self.factory.peers:
                addr, kind = self.factory.peers[peer] 
                print "     [*]", peer, addr, kind

    def write(self, line):
        self.transport.write(line + "\n")

    def connectionLost(self, reason):
        print " [ ] LEAVES:", self.remote_nodeid
        if self.remote_nodeid != self.nodeid:
            try:
                self.factory.peers.pop(self.remote_nodeid)
                self.print_peers()
            except KeyError:
                print " [?] GHOST:", self.remote_nodeid, self.remote_ip

    def dataReceived(self, data):
        if self.state != "READY":
            # Force first message to be HELLO or crash
            self.handle_HELLO(data)
        else:
            print "else"
            envelope = messages.read_envelope(data)
            if envelope['msgtype'] == 'ping':
                print "ping"
                self.handle_PING(data)
            elif envelope['msgtype'] == 'pong':
                self.handle_PONG(data)

    def send_PING(self):
        print " [ ] SEND_PING:", self.nodeid, "to", self.remote_nodeid
        ping = messages.create_ping(self.nodeid)
        self.write(ping)

    def handle_PING(self, ping):
        print " [ ] RECV_PING:", self.remote_nodeid
        ping = messages.read_message(ping)
        pong = messages.create_pong(self.nodeid, ping)
        print " [ ] SEND_PONG"
        self.write(pong)

    def handle_PONG(self, pong):
        # TODO: somehow get the ping nonce and check?
        pong = messages.read_message(pong)

    def send_HELLO(self):
        hello = messages.create_hello(self.nodeid, self.VERSION)
        print " [ ] SEND_HELLO:", self.nodeid, "to", self.remote_ip
        self.transport.write(hello + "\n")
        self.state = "GETHELLO"
        
    def handle_HELLO(self, hello):
        try:
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['nodeid']
            if self.remote_nodeid == self.nodeid:
                print " [!] Dropping connection to self on", self.host_ip
                self.transport.loseConnection()
            else:
                my_hello = messages.create_hello(self.nodeid, self.VERSION)
                self.transport.write(my_hello + "\n")
                self.factory.peers[self.remote_nodeid] = (self.remote_ip, self.kind)
                self.state = "READY"
                print " [ ] JOINED:", self.remote_nodeid
                self.print_peers()
                self.lc_ping.start(4.20)
        except (ValueError, ):
            print " [!] Disconnecting peer. ",
            print "Unable to read hello msg from", self.remote_ip
            self.transport.loseConnection()
        except messages.InvalidSignatureError:
            print " [!] Disconnecting peer. ",
            print "Invalid signature in hello from", self.remote_ip
            self.transport.loseConnection()

class NCFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.numProtocols = 0
        self.nodeid = cryptotools.generate_nodeid()[:10]
        print " [ ] NODEID:", self.nodeid

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
        print " [ ] LISTEN:", port
        ncfactory = NCFactory()
        endpoint.listen(ncfactory)
    except CannotListenError:
        print "[!] Address in use"
        sys.exit(1)

    
    # connect to bootstrap addresses
    print " [ ] Trying to connect to bootstrap hosts:"
    for bootstrap in bootstrap_list:
        print "     [*]", bootstrap
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO", "SEND"))
        d.addCallback(gotProtocol)
    reactor.run()
