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
        self.env_msgs['getTranscript'] = self.get_transcript

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
        self.log = defaultdict(list)
        self.transcript = []

    def sign_and_wait_for(self, x, message):
        to_list = [i for i in range(1, self.n + 1)]
        msg = (f'sign{x}', to_list, message)
        ack = self.write_and_wait_for(ch='p2f', msg=msg, read='f2p')
        return ack

    def env_vote(self, vid, b):
        if vid not in self.outputs:
            self.rnd_cnt[vid] = 0
            self.log[vid].append([])
            message = ("pre", 0, (vid, b))
            self.add_log(vid, 0, message)
            ack = self.sign_and_wait_for(2, message)
            if ack[0] == 'done':
                self.write(ch='p2f', msg=('leak', ('vote', vid, self.pid, b)))
        else:
            self.pump.write('')

    def env_getOutput(self, vid):
        if self.debug: print(f'[Pba {self.pid}] receive get Output')
        if vid in self.outputs:
            self.write('p2z', ('decide', vid, self.outputs[vid]))
        else:
            self.pump.write('')

    def advance(self, vid):
        if self.debug: print(f'[Pba, {self.pid}] advance', vid)
        if vid not in self.rnd_cnt: return
        self.rnd_cnt[vid] += 1
        self.log[vid].append([])
        h = self.write_and_wait_for('p2f', ('evaluate', (vid, self.rnd_cnt[vid])), read='f2p')

    def pre_vote(self, vid, r):
        if vid in self.outputs: return 'vid already has output'
        if len(self.log[vid][r]) == 0: return 'coin value needed'
        if len(self.log[vid][r]) >= 2: return 'vid has already been pre-voted'
        for b in [0, 1]:
            if ('pre', r - 1, (vid, b)) in self.signatures[vid]:
                print(f'[Pba, {self.pid}] pre vote case 1, (pre, {r}, ({vid}, {b}))')
                sig = ('signature', ('pre', r - 1, (vid, b)))
                ack = self.write_and_wait_for('p2f', ('broadcast', sig), 'f2p')
                message = ('pre', r, (vid, b))
                self.add_log(vid, r, message)
                ack = self.sign_and_wait_for(1, message)
                if ack[0] == 'done':
                    return 1
        if ('main', r - 1, (vid, -1)) in self.signatures[vid]:
            print(f'[Pba, {self.pid}] pre vote case 2, (pre, {r}, ({vid}, {self.coin[(vid, r)]}))')
            sig = ('signature', ('main', r - 1, (vid, -1)))
            ack = self.write_and_wait_for('p2f', ('broadcast', sig), 'f2p')
            message = ('pre', r, (vid, self.coin[(vid, r)]))
            self.add_log(vid, r, message)
            ack = self.sign_and_wait_for(1, message)
            if ack[0] == 'done':
                return 1

    def main_vote(self, vid, r):
        if vid in self.outputs: return 'vid already has output'
        if len(self.log[vid][r]) < 2: return 'the first two phases not finished'
        if len(self.log[vid][r]) >= 3: return 'vid has already been main-voted'
        for b in [0, 1]:
            if ('pre', r, (vid, b)) in self.signatures[vid]:
                print(f'[Pba, {self.pid}] main vote case 1, (main, {r}, ({vid}, {b}))')
                sig = ('signature', ('pre', r, (vid, b)))
                ack = self.write_and_wait_for('p2f', ('broadcast', sig), 'f2p')
                message = ('main', r, (vid, b))
                self.add_log(vid, r, message)
                ack = self.sign_and_wait_for(1, message)
                if ack[0] == 'done':
                    return 1
        if ('pre', r - 1, (vid, 1 - self.coin[(vid, r)])) in self.signatures[vid]:
            print(f'[Pba, {self.pid}] main vote case 2, (main, {r}, ({vid}, bot))')
            sig = ('signature', ('pre', r - 1, (vid, 1 - self.coin[(vid, r)])))
            ack = self.write_and_wait_for('p2f', ('broadcast', sig), 'f2p')
            message = ('main', r, (vid, -1))
            self.add_log(vid, r, message)
            ack = self.sign_and_wait_for(1, message)
            if ack[0] == 'done':
                return 1
        print(f'[Pba, {self.pid}] main vote failed')

    def recv_sign(self, fro, msg):
        if self.debug: print(f'[Pba, {self.pid}] process sign', msg)
        type, round, (vid, b) = msg
        if vid in self.outputs: return 'vid already has output'
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

    def recv_signature(self, _msg):
        if self.debug: print(f'[Pba {self.pid}] process signature', _msg)
        type, round, (vid, value) = _msg
        self.signatures[vid].add(_msg)
        if vid in self.outputs: return 'vid already has output'
        msg = (type, (vid, round))
        if type == 'pre' and len(self.initial_sign_cnt1[msg]) >= 2 * self.t + 1 and round == 0:
            if vid not in self.log: return 'not receive vote'
            if len(self.log[vid][round]) >= 2: return 'already main-voted, no need to process'
            message = ("main", 0, (vid, value))
            self.add_log(vid, round, message)
            ack = self.sign_and_wait_for(1, message)
            if ack[0] == 'done':
                return 'sign initial main'

        elif type == 'main':
            if value != -1:
                self.outputs[vid] = value
                ack = self.write_and_wait_for('p2f', ('broadcast', ('signature', _msg)), 'f2p')
                return f'output at round {round}'
            return 'signature for main bot'
        return 0

    def add_log(self, vid, round, message):
        self.log[vid][round].append(message)
        print('[message log]')
        for r in range(round + 1):
            print(f'Party{self.pid}\t Round{r}: {self.log[vid][r]}')
    def env_getBuf(self, x):
        output_msg = []
        while True:
            m = self.write_and_wait_for(ch='p2f', msg=(f'getBuf{x}',), read='f2p')
            self.msgs.extend(list(set(m[1])))

            if len(m[1]) == 0: break

        if self.debug: print(f'[Pba, {self.pid}] process messages', self.msgs)

        while True:
            processed = []
            for msg in list(self.msgs):
                if msg[0] == 'hash':
                    vid, r = msg[1]
                    self.coin[(vid, r)] = msg[2] % 2
                    self.add_log(vid, r, ('coin', msg[2] % 2))
                    self.pre_vote(vid, r)
                    self.msgs.remove(msg)
                    processed.append(msg)
                if msg[0] == 'signature':
                    status = self.recv_signature(msg[1])
                    if self.debug: print('return ', status)
                    if status != 0:
                        self.msgs.remove(msg)
                        processed.append(msg)
            for msg in list(self.msgs):
                if msg[0] == 'sign':
                    self.recv_sign(msg[1], msg[3])
                    self.msgs.remove(msg)
                    processed.append(msg)
            output_msg.extend(processed)
            if len(processed) == 0:
                break
        self.transcript.extend(output_msg)
        self.pump.write('0')

    def get_transcript(self):
        self.write('p2z', set(self.transcript))
