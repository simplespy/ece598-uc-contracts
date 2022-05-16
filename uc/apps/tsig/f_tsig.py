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
        self.t = sid[2]

        print(f'[Ftsig] This is ({self.c}, {self.t})-signature')

        self.see = defaultdict(set)
        self.cnt = defaultdict(set)

        self.party_msgs['sign'] = self.sign
        self.party_msgs['sign_batch'] = self.sign_batch
        self.party_msgs['send'] = self.send
        self.party_msgs['getBuf'] = self.getBuf

        self.msgBuf = defaultdict(list)

    def sign(self, sender, to, msg):
        self.add_msg(0, ('sign', sender, to, msg))
        self.add_msg(to, ('sign', sender, to, msg))
        self.cnt[(to, msg)].add(sender)
        self.cnt[msg].add(sender)

        if len(self.cnt[msg]) == self.c:
            self.see[msg].add(0)
            self.add_msg(0, ('signature', msg))

        if len(self.cnt[(to, msg)]) == self.c:
            self.see[msg].add(to)
            self.add_msg(to, ('signature', msg))

        self.pump.write('')

    def sign_batch(self, sender, to_list, msg):
        for to in to_list:
            self.add_msg(0, ('sign', sender, to, msg))
            self.add_msg(to, ('sign', sender, to, msg))
            self.cnt[(to, msg)].add(sender)
            self.cnt[msg].add(sender)

            if len(self.cnt[msg]) == self.c:
                self.see[msg].add(0)
                self.add_msg(0, ('signature', msg))

            if len(self.cnt[(to, msg)]) == self.c:
                self.see[msg].add(to)
                self.add_msg(to, ('signature', msg))

        self.pump.write('')
            
    def send(self, sender, to, msg):
        if sender in self.see[msg]:
            self.see[msg].add(to)
            self.write('f2a', ('send', sender, msg))
            self.add_msg(to, ('send', sender, msg))


            #self.write('f2p', (to, ('send', sender, msg)))
            

    def add_msg(self, to, msg):
        self.msgBuf[to].append(msg)

    def getBuf(self, sender):
        if len(self.msgBuf[sender]) == 0: self.pump.write('0')
        else:
            if sender == 0:
                self.write('f2a', ('msgBuf', self.msgBuf[sender]))

            else:
                self.write('f2p', (sender, ('msgBuf', self.msgBuf[sender])))

            self.msgBuf[sender] = []




