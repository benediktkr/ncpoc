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

    def test_pingpong(self):
        ping = messages.create_ping(self.nodeid)
        # check that InvalidSignatureError isn't raised
        read_ping = messages.read_message(ping)
        pong = messages.create_pong(self.nodeid, read_ping)
        # exceptions?
        read_pong = messages.read_message(pong)
        expected_nonce = messages.incr_nonce(read_ping)
        self.assertEquals(read_pong['data']['nonce'], expected_nonce)
                                    
if __name__ == "__main__":
    unittest.main()            
