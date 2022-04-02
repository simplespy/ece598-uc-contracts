from ast import literal_eval
from uc import UCFunctionality
from collections import defaultdict

class F_tsig(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.ssid = sid[0]
        sid = literal_eval(sid[1])
        self.n = sid[0]
        self.c = sid[1]

        self.see = defaultdict(set)
        self.cnt = defaultdict(set)

        self.party_msgs['sign'] = self.sign
        self.party_msgs['send'] = self.send
        self.party_msgs['getLeaks'] = self.getLeaks

        self.leakBuf = []

    def sign(self, sender, to, msg):
        #self.write('f2p', (to, ('sign', sender, to, msg)))
        self.leak(str(('sign', sender, to, msg)))
        self.cnt[(to, msg)].add(sender)
        self.cnt[msg].add(sender)

        if len(self.cnt[msg]) == self.c:
            self.see[msg].add(0)
            self.leak(str(('signature', msg)))

        if len(self.cnt[(to, msg)]) == self.c:
            self.see[msg].add(to)
            self.write('f2p', (to, ('signature', msg)))

        else:
            self.pump.write('')
            
    def send(self, sender, to, msg):
        if sender in self.see[msg]:
            self.see[msg].add(to)
            self.write('f2p', (to, ('send', sender, msg)))
            self.leak(str(('send', sender, msg)))

    def leak(self, msg):
        self.leakBuf.append(msg)

    def getLeaks(self, sender):
        if sender == 0:
            self.write('f2a', ('leakBuf', self.leakBuf))
        else:
            self.pump.write('')




