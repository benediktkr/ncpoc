import sys

from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import messages
import node

my_nodeid = node.generate_nodeid()

class NCServer(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.state = "GETHELLO"

    def connectionMade(self):
        # Send and recieve hello and helloack
        self.ip = self.transport.getPeer()
        print "JOIN: ", self.ip
        self.factory.peers[self.ip] = self
        self.transport.write(str(len(self.factory.peers)) + " peers connected\n")

    def connectionLost(self, reason):
        print "LEAVES:", self.ip
        del self.factory.peers[self.ip]

    def looseConnection(self):
        del self.factory.peers[self.ip]

    def dataReceived(self, data):
        if self.state == "GETHELLO":
            self.handle_HELLO(data)

    def handle_HELLO(self, hello):
        try:
            hello = messages.read_hello(hello)
            self.remote_nodeid = hello['msg']['nodeid']
            if self.remote_nodeid == self.factory.nodeid:
                print "Connected to self. Aborting"
                self.transport.looseConnection()
            print "HELLO from", self.remote_nodeid
            my_hello = messages.create_hello(self.factory.nodeid, 0)
            self.transport.write(my_hello + "\n")
            self.state = "READY"
        except (ValueError, ):
            print "Unable to read hello msg from " + str(self.ip)
        except messages.InvalidSignatureError:
            print "Invalid signature in hello"


class NCFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.numProtocols = 0
        self.peers = {}
        self.nodeid = node.generate_nodeid()
        print "NODEID:", self.nodeid

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NCServer(self)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 8007
    endpoint = TCP4ServerEndpoint(reactor, port)
    print "LISTEN:", port
    endpoint.listen(NCFactory())
    reactor.run()
