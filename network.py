import sys

from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet import reactor

import messages
import node

class NCProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO"):
        self.factory = factory
        self.state = state
        self.VERSION = 0

    def connectionMade(self):
        self.ip = str(self.transport.getPeer())

    def connectionLost(self, reason):
        print "LEAVES:", self.ip
        try:
            # ghost peers?
            self.factory.peers.pop(self.ip)
        except KeyError:
            pass

    def dataReceived(self, data):
        if self.state == "GETHELLO":
            self.handle_HELLO(data)

    def send_HELLO(self):
        hello = messages.create_hello(self.factory.nodeid, self.VERSION)
        print "SEND_HELLO:", self.factory.nodeid
        self.transport.write(hello + "\n")
        self.state = "GETHELLO"

    def handle_HELLO(self, hello):
        try:
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['msg']['nodeid']
            if self.remote_nodeid == self.factory.nodeid:
                print "Connected to self. Aborting"
                self.transport.loseConnection()
            else:
                my_hello = messages.create_hello(self.factory.nodeid, self.VERSION)
                self.transport.write(my_hello + "\n")
                self.factory.peers[self.ip] = self.remote_nodeid
                self.state = "READY"

                print "JOIN: ", self.ip, self.remote_nodeid
                print "PEERS:", str(self.factory.peers)
        except (ValueError, ):
            print "Unable to read hello msg from " + str(self.ip)
        except messages.InvalidSignatureError:
            print "Invalid signature in hello"


class NCFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.numProtocols = 0
        self.nodeid = node.generate_nodeid()
        print "NODEID:", self.nodeid

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NCProtocol(self, "GETHELLO")

class NCClientFactory(ClientFactory):
    def __init__(self, nodeid):
        self.nodeid = nodeid

    def startFactory(self):
        self.peers = {}

    def buildProtocol(self, addr):
        print 'CONNECTED:', addr
        p = NCProtocol(self)
        p.send_HELLO()
        return p

def gotProtocol(p):
    p.send_HELLO()
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 5005
    endpoint = TCP4ServerEndpoint(reactor, port)
    print "LISTEN:", port
    ncfactory = NCFactory()
    endpoint.listen(ncfactory)
    # connect to bootstrap addresses
    for bootstrap in node.bootstrap_list:
        print "Trying to connect to bootstrap host:", bootstrap
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NCProtocol(ncfactory, "GETHELLO"))
        d.addCallback(gotProtocol)
    reactor.run()
