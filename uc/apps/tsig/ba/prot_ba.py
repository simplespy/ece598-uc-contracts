import os
from ast import literal_eval
from uc import UCProtocol
from uc.utils import waits, wait_for
from collections import defaultdict
import logging
import time

log = logging.getLogger(__name__)


class BA_Prot(UCProtocol):
    def __init__(self, k, bits, sid, pid, channels, pump):
        UCProtocol.__init__(self, k, bits, sid, pid, channels, pump)
        self.ssid, sid = sid

        sid = literal_eval(sid)

        self.n = int(sid[0])
        self.t = int(sid[1])

        self.pid = pid

        self.env_msgs['vote'] = self.env_vote
        self.env_msgs['getOutput'] = self.env_getOutput
        self.env_msgs['getBuf'] = self.env_getBuf

        self.rnd_cnt = {}
        self.outputs = {}
        self.initial_sign_cnt1 = defaultdict(set)
        self.initial_sign_cnt2 = defaultdict(set)
        self.prevote_cnt = defaultdict(set)
        self.mainvote_cnt = defaultdict(set)
        self.msgs = []
        self.debug = True
        self.signatures = defaultdict(set)
        self.coin = {}

    def env_vote(self, vid, b):
        if vid not in self.outputs:
            self.rnd_cnt[vid] = 0
            message = ("pre", 0, (vid, b))
            to_list = [i for i in range(1, self.n + 1)]
            msg = ('sign2', to_list, message)
            ack = self.write_and_wait_for(ch='p2f', msg=msg, read='f2p')
            if ack[0] == 'done':
                self.write(ch='p2f', msg=('leak', ('vote', vid, self.pid, b)))
        else:
            self.pump.write('')

    def env_getOutput(self, vid):
        if self.debug: print('[Pba] receive get Output')
        if vid in self.outputs:
            self.write('p2z', ('decide', vid, self.outputs[vid]))
        else:
            self.pump.write('')

    def advance(self, vid):
        if self.debug: print('[Pba] advance', self.pid, vid)
        if vid not in self.rnd_cnt: return
        self.rnd_cnt[vid] += 1
        h = self.write_and_wait_for('p2f', ('evaluate', (vid, self.rnd_cnt[vid])), read='f2p')

    def sign_and_wait_for(self, x, type, r, vid, b):
        message = (type, r, (vid, b))
        to_list = [i for i in range(1, self.n + 1)]
        msg = (f'sign{x}', to_list, message)
        ack = self.write_and_wait_for(ch='p2f', msg=msg, read='f2p')
        return ack

    def pre_vote(self, vid, r):
        if vid in self.outputs: return
        for b in [0, 1]:
            if ('pre', r - 1, (vid, b)) in self.signatures[vid]:
                ack = self.sign_and_wait_for(1, 'pre', r, vid, b)
                if ack[0] == 'done':
                    return 1
        if ('main', r - 1, (vid, -1)) in self.signatures[vid]:
            ack = self.sign_and_wait_for(1, 'main', r, vid, self.coin[(vid, r)])
            if ack[0] == 'done':
                return 1

    def main_vote(self, vid, r):
        if vid in self.outputs: return
        for b in [0, 1]:
            if ('pre', r, (vid, b)) in self.signatures[vid]:
                ack = self.sign_and_wait_for(1, 'main', r, vid, b)
                if ack[0] == 'done':
                    return 1
        if ('main', r - 1, (vid, 1 - self.coin[(vid, r)])) in self.signatures[vid]:
            ack = self.sign_and_wait_for(1, 'main', r, vid, -1)
            if ack[0] == 'done':
                return 1

    def recv_sign(self, fro, msg):
        if self.debug: print('[Pba] process sign', msg)
        type, round, (vid, b) = msg
        msg = (type, (vid, round))
        if type == 'pre' and round == 0:
            self.initial_sign_cnt1[msg].add(fro)
        elif type == 'main' and round == 0:
            self.initial_sign_cnt2[msg].add(fro)
            if len(self.initial_sign_cnt2[msg]) == self.n - self.t:
                self.advance(vid)
        elif type == 'pre' and round > 0:
            self.prevote_cnt[msg].add(fro)
            if len(self.prevote_cnt[msg]) == self.n - self.t:
                self.main_vote(vid, round)

        elif type == 'main' and round > 0:
            self.mainvote_cnt[msg].add(fro)
            if len(self.mainvote_cnt[msg]) == self.n - self.t:
                self.advance(vid)

    def recv_signature(self, msg):
        if self.debug: print('[Pba] process signature', msg)
        type, round, (vid, value) = msg
        self.signatures[vid].add(msg)
        msg = (type, (vid, round))
        if type == 'pre' and len(self.initial_sign_cnt1[msg]) >= 2 * self.t + 1:
            message = ("main", 0, (vid, value))
            to_list = [i for i in range(1, self.n + 1)]
            msg = ('sign1', to_list, message)
            ack = self.write_and_wait_for(ch='p2f', msg=msg, read='f2p')
            if ack[0] == 'done':
                return 1

        elif type == 'main' and len(self.initial_sign_cnt2[msg]) >= self.n - self.t:
            self.outputs[vid] = value
            return 1
        return 0

    def env_getBuf(self, x):
        output_msg = []
        while True:
            m = self.write_and_wait_for(ch='p2f', msg=(f'getBuf{x}',), read='f2p')
            if self.debug: print('[Pba] read buf', self.pid)
            self.msgs.extend(list(m[1]))

            if len(m[1]) == 0: break

        if self.debug: print('[Pba] process messages', self.pid, self.msgs)

        while True:
            processed = []
            for msg in list(self.msgs):
                if msg[0] == 'sign':
                    self.recv_sign(msg[1], msg[3])
                    self.msgs.remove(msg)
                    processed.append(msg)
                if msg[0] == 'signature':
                    status = self.recv_signature(msg[1])
                    if self.debug: print('return ', status)
                    if status == 1:
                        self.msgs.remove(msg)
                        processed.append(msg)
                if msg[0] == 'hash':
                    vid, r = msg[1]
                    self.coin[(vid, r)] = msg[2] % 2
                    self.pre_vote(vid, r)
                    self.msgs.remove(msg)
                    processed.append(msg)
            output_msg.extend(processed)
            if len(processed) == 0:
                break
        if len(output_msg) == 0:
            self.pump.write('0')
        else:
            self.pump.write('1')
