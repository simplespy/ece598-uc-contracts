from ast import literal_eval
from uc import UCFunctionality
from uc.utils import read_one, read
from secp256k1 import make_random_point
import logging
import secp256k1 as secp
import os
log = logging.getLogger(__name__)


class F_CRS(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.ssid,sid = sid

        self.output_value = None
        self.bit = None
        self.state = 0 # wait to commit, 1: committed, 2: reveal

        self.party_msgs['value'] = self.value
        self.party_msgs['sendmsg'] = self.sendmsg
        self.party_msgs['hash_to_group'] = self.hash_to_group
        self.hash_table = {}

    def value(self, sender):
        if self.output_value is None:
            g = make_random_point(lambda x: self.sample(8*x).to_bytes(x,'little') )
            z = make_random_point(lambda x: self.sample(8*x).to_bytes(x,'little') )
        
            g1 = make_random_point(lambda x: self.sample(8*x).to_bytes(x,'little') )
            g2 = make_random_point(lambda x: self.sample(8*x).to_bytes(x,'little') )

            x = [secp.uint256_from_str(os.urandom(32)) for i in range(5)]
            c = g1 * x[0] + g2 * x[1]
            d = g1 * x[2] + g2 * x[3]
            h = g1 * x[4]
            
            self.output_value = (g,h,g1,g2,x,c,d,h)
        self.write( 'f2p', (sender, (self.output_value,)) )

    def sendmsg(self, sender, to, msg):
        self.write(
            ch='f2p',
            msg=(to, ('recvmsg', sender, msg)),
        )

    def hash_to_group(self, sender, msg):
        self.hash_table[msg] = self.hash_table.setdefault(msg, make_random_point(lambda x: self.sample(8*x).to_bytes(x,'little') ))
        self.write( 'f2p', (sender, (self.hash_table[msg],)) )

            

