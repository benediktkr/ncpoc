import sys
sys.path.append("..")
import unittest

import messages
import cryptotools

class TestMessages(unittest.TestCase):
    def setUp(self):
        self.nodeid = cryptotools.generate_nodeid()

    def tearDown(self):
        pass

    def test_hello(self):
        hello = messages.create_hello(self.nodeid, 0)
        # check that InvalidSignatureError is not raised
        return messages.read_message(hello)

    def test_ackhello(self):
        ackhello = messages.create_ackhello(self.nodeid)
        return messages.read_message(ackhello)

    def test_ping(self):
        ping = messages.create_ping(self.nodeid)
        # check that InvalidSignatureError isn't raised
        return messages.read_message(ping)

    def test_pong(self):
        pong = messages.create_pong(self.nodeid)
        # exceptions?
        return messages.read_message(pong)
                                    
if __name__ == "__main__":
    unittest.main()            
