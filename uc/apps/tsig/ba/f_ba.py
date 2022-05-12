from ast import literal_eval
from uc import UCFunctionality
from collections import defaultdict


class F_ba(UCFunctionality):
    def __init__(self, k, bits, crupt, sid, channels, pump):
        UCFunctionality.__init__(self, k, bits, crupt, sid, channels, pump)
        self.ssid = sid[0]
        sid = literal_eval(sid[1])
        self.n = sid[0]
        self.t = sid[1]
        self.crupt = crupt

        self.voting = defaultdict(set)
        self.cnt = defaultdict(int)
        self.cnt_honest = defaultdict(int)

        self.party_msgs['vote'] = self.vote
        self.party_msgs['getOutput'] = self.get_output
        self.party_msgs['getBuf'] = self.get_buf

        self.adv_msgs['vote'] = self.vote_by_adv
        self.adv_msgs['getBuf'] = self.get_buf
        self.adv_msgs['writeBuf'] = self.write_buf

        self.adv_vote = {}
        self.outputs = {}

    def vote(self, sender, vid, b):
        self.voting[(vid, b)].add(sender)
        self.write('f2a', ('vote', vid, sender, b))

        if sender not in self.crupt:
            self.cnt_honest[(vid, b)] += 1
        self.cnt[(vid, b)] += 1

        if self.cnt_honest[(vid, b)] == self.n - self.t:
            self.output(vid, b)

        elif self.cnt_honest[(vid, b)] + self.cnt_honest[(vid, 1 - b)] == self.n - self.t:
            if vid in self.adv_vote:
                self.output(vid, self.adv_vote[vid])

        elif self.cnt[(vid, b)] == self.n - self.t:
            if len(self.voting[(vid, b)]) == self.t + 1 and self.adv_vote.setdefault(vid, -1) == b:
                self.output(vid, b)

    def vote_by_adv(self, vid, b):
        print('[FBA] set adv input')
        self.adv_vote[vid] = b
        self.pump.write('')

    def output(self, vid, b):
        self.outputs[vid] = b

    def get_output(self, sender, vid):
        if vid in self.outputs:
            self.write('f2p', (sender, ('decide', vid, self.outputs[vid])))
        else:
            self.pump.write('')

    def add_msg(self, to, msg):
        self.msgBuf[to].append(msg)

    def get_buf(self, sender, x):
        self.pump.write('0')

    def write_buf(self, sender, to):
        self.pump.write('0')