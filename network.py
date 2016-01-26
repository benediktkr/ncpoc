from twisted.internet import protocol, reator, endpoints

import messages
import node

my_nodeid = node.generate_nodeid()

class NCServer(protocol.Protocol):
    def dataReceived(self, data):
        
