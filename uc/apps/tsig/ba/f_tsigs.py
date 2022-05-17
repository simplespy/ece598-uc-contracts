from ast import literal_eval
from uc import UCFunctionality
from collections import defaultdict


class F_tsigs(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.ssid = sid[0]
        sid = literal_eval(sid[1])
        self.n = n = sid[0]
        self.t = t = sid[1]
        self.k = k

        self.tsig1 = F_tsig(k, bits, crupt, [self.ssid, n - t, t], channels, pump)
        self.tsig2 = F_tsig(k, bits, crupt, [self.ssid, t + 1, t], channels, pump)

        self.party_msgs['sign1'] = self.tsig1.sign
        self.party_msgs['sign2'] = self.tsig2.sign
        self.party_msgs['getBuf1'] = self.tsig1.get_buf
        self.party_msgs['getBuf2'] = self.tsig2.get_buf
        self.party_msgs['leak'] = self.leak
        self.party_msgs['evaluate'] = self.evaluate
        self.party_msgs['broadcast'] = self.broadcast

        self.party_msgs['sendmsg'] = self.sendmsg
        self.adv_msgs['getBuf'] = self.get_buf
        self.adv_msgs['vote'] = self.adv_vote
        self.adv_msgs['writeBuf'] = self.write_buf
        self.ro_cnt = defaultdict(set)
        self.ro_table = {}

        self.debug = True

    def leak(self, sender, msg):
        self.write('f2a', msg)

    def sendmsg(self, sender, to, msg):
        if self.debug: print('[F_ro, sendmsg] from {} to {}: {}'.format(sender, to, msg))
        self.write('f2p', (to, ('recvmsg', sender, msg)))

    def get_buf(self, x, sender):
        if x == 1:
            self.tsig1.get_buf_adv(sender)
        elif x == 2:
            self.tsig2.get_buf_adv(sender)

    def write_buf(self, x, sender, buf):
        if x == 1:
            self.tsig1.write_buf(sender, buf)
        elif x == 2:
            self.tsig2.write_buf(sender, buf)

    def adv_vote(self, vid, b):
        self.pump.write('')

    def evaluate(self, sender, r):
        self.ro_cnt[r].add(sender)
        if r in self.ro_table:
            self.tsig1.add_msg(sender, ('hash', r, self.ro_table[r]))
        elif len(self.ro_cnt[r]) == self.n - self.t:
            self.ro_table[r] = self.sample(self.k)
            for i in self.ro_cnt[r]:
                self.tsig1.add_msg(i, ('hash', r, self.ro_table[r]))
        self.write(ch='f2p', msg=(sender, -1))

    def broadcast(self, sender, msg):
        for i in range(1, self.n + 1):
            self.tsig1.add_msg(i, msg)
        self.write('f2p', (sender, ('done',)))





class F_tsig(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.ssid = sid[0]
        self.c = sid[1]
        self.t = sid[2]
        self.debug = False

        if self.debug: print(f'[Ftsig] This is ({self.c}, {self.t})-signature')

        self.see = defaultdict(set)
        self.cnt = defaultdict(set)
        self.msgBuf = defaultdict(list)


    def sign(self, sender, to, msg):
        if self.debug: print(f'[f_tsigs({self.c}, {self.t})] {sender} sign {msg} to {to}')
        if type(to) == list:
            self.sign_batch(sender, to, msg)
        else:
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

        self.write('f2p', (sender, ('done',)))

    def send(self, sender, to, msg):
        if sender in self.see[msg]:
            self.see[msg].add(to)
            self.add_msg(0, ('send', sender, msg))
            self.write('f2p', (to, ('send', sender, msg)))

    def add_msg(self, to, msg):
        self.msgBuf[to].append(msg)

    def get_buf(self, sender):
        self.dedup(sender)
        self.write('f2p', (sender, ('msgBuf', self.msgBuf[sender])))
        self.msgBuf[sender] = []

    def dedup(self, sender):
        self.msgBuf[sender] = list(set(self.msgBuf[sender]))

    def get_buf_adv(self, sender):
        self.dedup(sender)
        if sender in self.crupt:
            self.write('f2p', (sender, ('msgBuf', self.msgBuf[sender])))
            self.msgBuf[sender] = []
        else:
            self.write('f2a', (sender, ('msgBuf', self.msgBuf[sender])))

    def write_buf(self, sender, buf):
        self.msgBuf[sender] = buf
        self.write('f2a', (sender, ('msgBuf', self.msgBuf[sender])))

