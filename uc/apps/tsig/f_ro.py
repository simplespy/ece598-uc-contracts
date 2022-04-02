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
        self.party_msgs['evaluate'] = self.evaluate
        self.party_msgs['invert'] = self.invert
        self.party_msgs['sendmsg'] = self.sendmsg
        self.party_msgs['getLeaks'] = self.getLeaks

        self.cnt_eval = defaultdict(set)
        self.cnt_inv = defaultdict(set)

        self.leakBuf = []

        (self.pk, self.sk) = rsa.newkeys(512)

    def _hash(self, x):
        if x not in self.table:
            v = self.sample(self.k)
            self.table[x] = v
            self.inv_table[v] = pow(v, self.sk.d, self.pk.n)
        return self.table[x]

    def c_evaluate(self, sender, to, msg):
        print(f'[F_ro, evaluate] ({to}, {msg}) from {sender}')

        self.cnt_eval[msg].add(sender)
        self.cnt_eval[(to, msg)].add(sender)
        self.leak(str(('evaluate', sender, to, msg)))
        
        if len(self.cnt_eval[msg]) == self.c:
            self.leak(str(('evaluate', self._hash(msg))))

        if len(self.cnt_eval[(to, msg)]) == self.c:
            print('can evaluate')
            self.write(
                ch='f2p',
                msg=(to, ('evaluate', msg, self._hash(msg)))
            )

        else:
            self.pump.write('')

    def evaluate(self, sender, to, msg):
        self.write(
            ch='f2p',
            msg=(to, ('evaluate', msg, self._hash(msg)))
        )

        

    def invert(self, sender, to, msg):
        print(f'[F_ro, invert] ({to}, {msg}) from {sender}')
        self.cnt_inv[msg].add(sender)
        self.cnt_inv[(to, msg)].add(sender)
        self.leak(str(('invert', sender, to, msg)))
        
        if len(self.cnt_inv[msg]) == self.c:
            self.leak(str(('invert', self.inv_table[msg])))

        if len(self.cnt_inv[(to, msg)]) == self.c:
            self.write(
                ch='f2p',
                msg=(to, ('invert', self.inv_table[msg]))
            )
        else:
            self.pump.write('')


    def ahash(self, s):
        self.write(
            ch='f2a',
            msg=self._hash(s)
        )

    def sendmsg(self, sender, to, msg):
        print('[F_ro, sendmsg] from {} to {}: {}'.format(sender, to, msg))
        self.write(
            ch='f2p',
            msg=(to, ('recvmsg', sender, msg)),
        )

    def leak(self, msg):
        self.leakBuf.append(msg)

    def getLeaks(self, sender):
        if sender == 0:
            self.write('f2a', ('leakBuf', self.leakBuf))
        else:
            self.pump.write('')


