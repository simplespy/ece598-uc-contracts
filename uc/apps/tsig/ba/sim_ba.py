from uc import UCAdversary
from ast import literal_eval
from collections import defaultdict
import secp256k1 as secp


class SimBACrash(UCAdversary):
    def __init__(self, k, bits, crupt, sid, pid, channels, pump):
        UCAdversary.__init__(self, k, bits, crupt, sid, pid, channels, pump)
        self.ssid, sid = sid

        sid = literal_eval(sid)

        self.n = int(sid[0])
        self.t = int(sid[1])
        self.crupt = crupt

        self.pid = pid

        self.party_msgs['decide'] = self.recv_vote
        self.env_msgs['A2F'] = self.a2f

        self.votes = defaultdict(set)
        self.debug = False
        self.msgBuf = defaultdict(list)
        self.see = defaultdict(set)
        self.cnt = defaultdict(set)

        self.parties = {}
        for i in range(1, self.n + 1):
            self.parties[i] = Party(i, self.n, self.t)

    def recv_vote(self, sender, vid, b):
        print('[Sba] recv_vote')

    def func_msg(self, msg):
        """
        Forward messages from the functionality to the environment.
        Args:
            msg (tuple): message from the functionality
        """
        if msg[0] == 'vote':
            vid, pid, b = msg[1:]
            self.parties[pid].vote(vid, b)

        self.write(
            ch='a2z',
            msg=('F2A', msg)
        )

    def simulate_1(self):
        for sender in range(1, self.n + 1):
            if sender in self.crupt: continue
            for (vid, b) in self.parties[sender].votes.items():
                msg = ("pre", 0, (vid, b))
                to_list = [i for i in range(1, self.n + 1)]
                self.sign_batch_2(sender, to_list, msg)

    def simulate_2(self):
        for i in range(1, self.n + 1):
            if i in self.crupt: continue
            while True:
                processed = []
                for msg in list(self.msgBuf[i]):
                    if msg[0] == 'sign':
                        self.parties[i].recv_sign(msg[1], msg[3])
                        self.msgBuf[i].remove(msg)
                        processed.append(msg)
                    if msg[0] == 'signature':
                        status = self.parties[i].recv_signature(msg[1])
                        if status == 1:
                            vid, value = msg[1][2]
                            message = ("main", 0, (vid, value))
                            to_list = [i for i in range(1, self.n + 1)]
                            self.sign_batch_1(i, to_list, message)

                        if status > 0:
                            self.msgBuf[i].remove(msg)
                            processed.append(msg)
                if len(processed) == 0:
                    break

    def sign_batch_2(self, sender, to_list, msg):
        for to in to_list:
            self.add_msg(0, ('sign', sender, to, msg))
            self.add_msg(to, ('sign', sender, to, msg))
            self.cnt[(to, msg)].add(sender)
            self.cnt[msg].add(sender)

            if len(self.cnt[msg]) == self.t + 1:
                self.see[msg].add(0)
                self.add_msg(0, ('signature', msg))

            if len(self.cnt[(to, msg)]) == self.t + 1:
                self.see[msg].add(to)
                self.add_msg(to, ('signature', msg))

    def sign_batch_1(self, sender, to_list, msg):
        for to in to_list:
            self.add_msg(0, ('sign', sender, to, msg))
            self.add_msg(to, ('sign', sender, to, msg))
            self.cnt[(to, msg)].add(sender)
            self.cnt[msg].add(sender)

            if len(self.cnt[msg]) == self.n - self.t:
                self.see[msg].add(0)
                self.add_msg(0, ('signature', msg))

            if len(self.cnt[(to, msg)]) == self.n - self.t:
                self.see[msg].add(to)
                self.add_msg(to, ('signature', msg))

    def add_msg(self, to, msg):
        self.msgBuf[to].append(msg)

    def dedup(self, sender):
        self.msgBuf[sender] = list(set(self.msgBuf[sender]))

    def a2f(self, msg):
        if msg[0] == 'getBuf':
            x, pid = msg[1:]
            if x == 2:
                self.simulate_1()
                self.dedup(pid)
                self.write(ch='a2z',
                           msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))
                self.msgBuf[pid] = []

            elif x == 1:
                self.simulate_2()
                self.dedup(pid)
                self.write(ch='a2z',
                           msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))
                self.msgBuf[pid] = []
            else:
                self.pump.write('')
        elif msg[0] == 'vote':
            self.write('a2f', msg)
        elif msg[0] == 'writeBuf':
            x, pid, buf = msg[1:]
            self.msgBuf[pid] = buf
            self.write(ch='a2z',
                       msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))

        else:
            self.pump.write('')


class Party:
    def __init__(self, pid, n, t):
        self.pid = pid
        self.n = n
        self.t = t
        self.votes = {}
        self.rnd_cnt = {}
        self.outputs = {}
        self.initial_sign_cnt1 = defaultdict(set)
        self.initial_sign_cnt2 = defaultdict(set)

    def vote(self, vid, b):
        if vid not in self.votes:
            self.votes[vid] = b

    def recv_sign(self, fro, msg):
        if msg[0] == 'pre':
            self.initial_sign_cnt1[msg].add(fro)
        elif msg[0] == 'main':
            self.initial_sign_cnt2[msg].add(fro)

    def recv_signature(self, msg):

        if msg[0] == 'pre' and len(self.initial_sign_cnt1[msg]) >= 2 * self.t + 1:
            return 1

        elif msg[0] == 'main' and len(self.initial_sign_cnt2[msg]) >= self.n - self.t:
            vid, value = msg[2]
            self.outputs[vid] = value
            return 2
        return 0