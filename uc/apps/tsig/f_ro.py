from uc import UCFunctionality
import logging
from ast import literal_eval
from collections import defaultdict
import rsa
import secp256k1 as secp


log = logging.getLogger(__name__)

class F_CRO_FC(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.table = {}
        self.inv_table = {}
        self.ssid = sid[0]
        sid = literal_eval(sid[1])
        self.n = sid[0]
        self.c = sid[1]
        self.t = sid[2]
        self.party_msgs['evaluate'] = self.evaluate
        self.party_msgs['evaluate_all'] = self.evaluate_all
        self.party_msgs['invert'] = self.invert
        self.party_msgs['broadcast'] = self.broadcast
        self.party_msgs['getBuf'] = self.getBuf
        self.party_msgs['sendmsg'] = self.sendmsg

        self.cnt_eval = defaultdict(set)
        self.cnt_inv = defaultdict(set)

        self.msgBuf = defaultdict(set)

        (self.pk, self.sk) = rsa.newkeys(512)

    def _hash(self, x):
        if x not in self.table:
            v = self.sample(self.k)
            self.table[x] = v
            self.inv_table[v] = pow(v, self.sk.d, self.pk.n)
        return self.table[x]

    def evaluate(self, sender, to, msg):
        print(f'[F_ro, evaluate] ({to}, {msg}) from {sender}')

        #self.add_msg(0, ('evaluate', sender, to, msg))
        #self.add_msg(to, ('evaluate', sender, to, msg))
        self.cnt_eval[msg].add(sender)
        self.cnt_eval[(to, msg)].add(sender)

        if len(self.cnt_eval[msg]) == self.c:
            self.add_msg(0, ('evaluate', self._hash(msg)))

        if len(self.cnt_eval[(to, msg)]) == self.c:
            self.add_msg(to, ('evaluate', msg, self._hash(msg)))

        self.pump.write('back from evaluate')  

    def evaluate_all(self, sender, msg):
        for to in range(1, self.n + 1):
            print(f'[F_ro, evaluate_all] ({to}, {msg}) from {sender}')

            #self.add_msg(0, ('evaluate', sender, to, msg))
            #self.add_msg(to, ('evaluate', sender, to, msg))
            self.cnt_eval[msg].add(sender)
            self.cnt_eval[(to, msg)].add(sender)

            if len(self.cnt_eval[msg]) == self.c:
                self.add_msg(0, ('evaluate', self._hash(msg)))

            if len(self.cnt_eval[(to, msg)]) == self.c:
                self.add_msg(to, ('evaluate', msg, self._hash(msg)))

        self.pump.write('back from evaluate_all')

    def invert(self, sender, to, msg):
        print(f'[F_ro, invert] ({to}, {msg}) from {sender}')
        #self.add_msg(0, ('invert', sender, to, msg))
        #self.add_msg(to, ('invert', sender, to, msg))
        self.cnt_inv[msg].add(sender)
        self.cnt_inv[(to, msg)].add(sender)
        
        if len(self.cnt_inv[msg]) == self.c:
            self.add_msg(0, ('invert', self.inv_table[msg]))

        if len(self.cnt_inv[(to, msg)]) == self.c:
            #print(f'[F_ro, invert] {msg} to {sender}')
            self.write('f2p', (to, ('invert', self.inv_table[msg])))
            
        else: self.pump.write('back from invert')


    def ahash(self, s):
        self.write(
            ch='f2a',
            msg=self._hash(s)
        )

    def sendmsg(self, sender, to, msg):
        print('[F_ro, sendmsg] from {} to {}: {}'.format(sender, to, msg))
        self.write('f2p', (to, ('recvmsg', sender, msg)))

    def broadcast(self, sender, msg):
        for to in range(1, self.n + 1):
            self.msgBuf[to].add(msg)
        self.pump.write('back from broadcast')

    def add_msg(self, to, msg):
        self.msgBuf[to].add(msg)

    def getBuf(self, sender):
        
        if sender == 0:
            self.write('f2a', ('msgBuf', self.msgBuf[sender]))

        else:
            self.write('f2p', (sender, ('msgBuf', self.msgBuf[sender])))

        self.msgBuf[sender] = set()


