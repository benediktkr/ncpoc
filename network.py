import sys

from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet import reactor
from twisted.internet.error import CannotListenError

import messages
import node

class NCProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO"):
        self.factory = factory
        self.state = state
        self.VERSION = 0
        self.remote_nodeid = None

    def connectionMade(self):
        r_ip = self.transport.getPeer()
        h_ip = self.transport.getHost()
        self.remote_ip = r_ip.host + ":" + str(r_ip.port)
        self.host_ip = h_ip.host + ":" + str(h_ip.port)

    def print_peers(self):
        if len(self.factory.peers) == 0:
            print " [ ] PEERS: No peers connected."
        else:
            print " [ ] PEERS:"
            for peer in self.factory.peers:
                print "     [*]", peer, self.factory.peers[peer]

    def connectionLost(self, reason):
        print " [ ] LEAVES:", self.remote_nodeid
        try:
            # ghost peers?
            self.factory.peers.pop(self.remote_nodeid)
            self.print_peers()
        except KeyError:
            pass

    def dataReceived(self, data):
        if self.state == "GETHELLO":
            self.handle_HELLO(data)

    def send_HELLO(self):
        hello = messages.create_hello(self.factory.nodeid, self.VERSION)
        print " [ ] SEND_HELLO:", self.factory.nodeid, "to", self.remote_ip
        self.transport.write(hello + "\n")
        self.state = "GETHELLO"

    def handle_HELLO(self, hello):
        try:
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['msg']['nodeid']
            if self.remote_nodeid == self.factory.nodeid:
                print "     [!] Dropping connection to self on", self.host_ip
                self.transport.loseConnection()
            else:
                my_hello = messages.create_hello(self.factory.nodeid, self.VERSION)
                self.transport.write(my_hello + "\n")
                self.factory.peers[self.remote_nodeid] = self.remote_ip
                self.state = "READY"

                print " [ ] JOINED:", self.remote_nodeid
                self.print_peers()
        except (ValueError, ):
            print " [!] Disconnecting peer. Unable to read hello msg from " + self.remote_ip
            self.transport.loseConnection()
        except messages.InvalidSignatureError:
            print " [!] Disconnecting peer. Invalid signature in hello from " + self.remote_ip
            self.transport.loseConnection()

class NCFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.numProtocols = 0
        self.nodeid = node.generate_nodeid()[:10]
        print " [ ] NODEID:", self.nodeid

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NCProtocol(self, "GETHELLO")

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
    for bootstrap in node.bootstrap_list:
        print "     [*]", bootstrap
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "SENDHELLO"))
        d.addCallback(gotProtocol)
    reactor.run()
