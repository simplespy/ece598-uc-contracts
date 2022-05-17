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

        self.env_msgs['A2F'] = self.a2f

        self.votes = defaultdict(set)
        self.debug = True
        self.msgBuf = defaultdict(list)
        self.log = defaultdict(set)
        self.see = defaultdict(set)
        self.cnt = defaultdict(set)
        self.ro_cnt = defaultdict(set)
        self.ro_table = {}

        self.parties = {}
        for i in range(1, self.n + 1):
            self.parties[i] = Party(i, self.n, self.t, self)

    def add_log(self, pid, vid, round, message):
        self.parties[pid].add_log(vid, round, message)

    def func_msg(self, msg):
        if msg[0] == 'vote':
            vid, pid, b = msg[1:]
            self.parties[pid].vote(vid, b)
            self.parties[pid].log[vid].append([])
            message = ("pre", 0, (vid, b))
            self.add_log(pid, vid, 0, message)
            to_list = [i for i in range(1, self.n + 1)]
            self.sign_batch_2(pid, to_list, message)

            self.write(
                ch='a2z',
                msg=('F2A', msg)
            )

        elif msg[0] == 'getTranscript':
            pid = msg[1]
            self.process_msg_buf()
            self.process_msg_buf()
            self.write(
                ch='a2z',
                msg=(pid, set(self.log[pid]))
            )

    def process_msg_buf(self):
        for i in range(1, self.n + 1):
            if i in self.crupt: continue
            self.dedup(i)
            self.parties[i].process_msg_buf(self.msgBuf[i])
            self.msgBuf[i] = []


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
        self.log[to].add(msg)

    def dedup(self, sender):
        self.msgBuf[sender] = list(set(self.msgBuf[sender]))

    def a2f(self, msg):
        if msg[0] == 'getBuf':
            x, pid = msg[1:]
            if x == 2:
                self.dedup(pid)
                self.write(ch='a2z',
                           msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))
                self.msgBuf[pid] = []

            elif x == 1:
                self.process_msg_buf()
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

    def evaluate(self, sender, r):
        if self.debug: print('[Sba] evaluate add', sender, r)
        self.ro_cnt[r].add(sender)
        if r in self.ro_table:
            self.add_msg(sender, ('hash', r, self.ro_table[r]))
        elif len(self.ro_cnt[r]) == self.n - self.t:
            self.ro_table[r] = self.sample(self.k)
            for i in self.ro_cnt[r]:
                self.add_msg(i, ('hash', r, self.ro_table[r]))

    def broadcast(self, msg):
        for i in range(1, self.n + 1):
            self.add_msg(i, msg)

class SimBA(UCAdversary):
    def __init__(self, k, bits, crupt, sid, pid, channels, pump):
        UCAdversary.__init__(self, k, bits, crupt, sid, pid, channels, pump)
        self.ssid, sid = sid

        sid = literal_eval(sid)

        self.n = int(sid[0])
        self.t = int(sid[1])
        self.crupt = crupt
        self.k = k

        self.pid = pid

        self.env_msgs['A2F'] = self.a2f

        self.votes = defaultdict(set)
        self.debug = True
        self.msgBuf = defaultdict(list)
        self.log = defaultdict(set)
        self.see = defaultdict(set)
        self.cnt = defaultdict(set)
        self.ro_cnt = defaultdict(set)
        self.ro_table = {}

        self.parties = {}
        for i in range(1, self.n + 1):
            self.parties[i] = Party(i, self.n, self.t, self)

    def add_log(self, pid, vid, round, message):
        self.parties[pid].add_log(vid, round, message)

    def func_msg(self, msg):
        if msg[0] == 'vote':
            vid, pid, b = msg[1:]
            self.parties[pid].vote(vid, b)
            self.parties[pid].log[vid].append([])
            message = ("pre", 0, (vid, b))
            self.add_log(pid, vid, 0, message)
            to_list = [i for i in range(1, self.n + 1)]
            self.sign_batch_2(pid, to_list, message)

            self.write(
                ch='a2z',
                msg=('F2A', msg)
            )

        elif msg[0] == 'getTranscript':
            pid = msg[1]
            for i in range(5):
                print('-'*50)
                self.process_msg_buf()
            self.write(
                ch='a2z',
                msg=(pid, self.log[pid])
            )

    def process_msg_buf(self):
        for i in range(1, self.n + 1):
            if i in self.crupt: continue
            self.dedup(i)
            print(f'send buf to party {i}')
            msgs = list(self.msgBuf[i])
            self.msgBuf[i] = []
            self.parties[i].process_msg_buf(msgs)


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
        self.log[to].add(msg)

    def dedup(self, sender):
        self.msgBuf[sender] = list(set(self.msgBuf[sender]))

    def a2f(self, msg):
        if msg[0] == 'getBuf':
            x, pid = msg[1:]
            if x == 2:
                self.dedup(pid)
                self.write(ch='a2z',
                           msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))
                print(f'a2f get buf {pid} (x=2)')
                self.msgBuf[pid] = []

            elif x == 1:
                self.process_msg_buf()
                self.dedup(pid)
                self.write(ch='a2z',
                           msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))
                print(f'a2f get buf {pid} (x=1)')
                self.msgBuf[pid] = []
            else:
                self.pump.write('')
        elif msg[0] == 'vote':
            self.write('a2f', msg)
        elif msg[0] == 'writeBuf':
            x, pid, buf = msg[1:]
            print(f'a2f modify buf {pid}')
            self.msgBuf[pid] = buf
            self.write(ch='a2z',
                       msg=('P2A', (pid, ('msgBuf', self.msgBuf[pid]))))

        else:
            self.pump.write('')

    def evaluate(self, sender, r):
        self.ro_cnt[r].add(sender)
        if r in self.ro_table:
            self.add_msg(sender, ('hash', r, self.ro_table[r]))
        elif len(self.ro_cnt[r]) == self.n - self.t:
            self.ro_table[r] = self.sample(self.k)
            for i in self.ro_cnt[r]:
                self.add_msg(i, ('hash', r, self.ro_table[r]))

    def broadcast(self, msg):
        for i in range(1, self.n + 1):
            self.add_msg(i, msg)


class Party:
    def __init__(self, pid, n, t, outer):
        self.pid = pid
        self.n = n
        self.t = t
        self.votes = {}
        self.rnd_cnt = {}
        self.outputs = {}
        self.initial_sign_cnt1 = defaultdict(set)
        self.initial_sign_cnt2 = defaultdict(set)
        self.log = defaultdict(list)
        self.prevote_cnt = defaultdict(set)
        self.mainvote_cnt = defaultdict(set)
        self.msgs = []
        self.debug = True
        self.signatures = defaultdict(set)
        self.coin = {}
        self.log = defaultdict(list)
        self.transcript = []
        self.outer = outer

    def vote(self, vid, b):
        if vid not in self.votes:
            self.votes[vid] = b
            self.rnd_cnt[vid] = 0
            
    def advance(self, vid):
        if self.debug: print(f'[Sba, {self.pid}] advance', vid)
        if vid not in self.rnd_cnt: return
        self.rnd_cnt[vid] += 1
        self.log[vid].append([])
        self.outer.evaluate(self.pid, (vid, self.rnd_cnt[vid]))

    def pre_vote(self, vid, r):
        if vid in self.outputs: return 'vid already has output'
        if len(self.log[vid][r]) == 0: return 'coin value needed'
        if len(self.log[vid][r]) >= 2: return 'vid has already been pre-voted'
        for b in [0, 1]:
            if ('pre', r - 1, (vid, b)) in self.signatures[vid]:
                print(f'[Sba, {self.pid}] pre vote case 1, (pre, {r}, ({vid}, {b}))')
                sig = ('signature', ('pre', r - 1, (vid, b)))
                self.outer.broadcast(sig)
                message = ('pre', r, (vid, b))
                self.add_log(vid, r, message)
                to_list = [i for i in range(1, self.n + 1)]
                self.outer.sign_batch_1(self.pid, to_list, message)

        if ('main', r - 1, (vid, -1)) in self.signatures[vid]:
            print(f'[Sba, {self.pid}] pre vote case 2, (pre, {r}, ({vid}, {self.coin[(vid, r)]}))')
            sig = ('signature', ('main', r - 1, (vid, -1)))
            self.outer.broadcast(sig)
            message = ('pre', r, (vid, self.coin[(vid, r)]))
            self.add_log(vid, r, message)
            to_list = [i for i in range(1, self.n + 1)]
            self.outer.sign_batch_1(self.pid, to_list, message)
    
    def main_vote(self, vid, r):
        if vid in self.outputs: return 'vid already has output'
        if len(self.log[vid][r]) < 2: return 'the first two phases not finished'
        if len(self.log[vid][r]) >= 3: return 'vid has already been main-voted'
        for b in [0, 1]:
            if ('pre', r, (vid, b)) in self.signatures[vid]:
                print(f'[Sba, {self.pid}] main vote case 1, (main, {r}, ({vid}, {b}))')
                sig = ('signature', ('pre', r, (vid, b)))
                self.outer.broadcast(sig)
                message = ('main', r, (vid, b))
                self.add_log(vid, r, message)
                to_list = [i for i in range(1, self.n + 1)]
                self.outer.sign_batch_1(self.pid, to_list, message)
        if ('pre', r - 1, (vid, 1 - self.coin[(vid, r)])) in self.signatures[vid]:
            print(f'[Sba, {self.pid}] main vote case 2, (main, {r}, ({vid}, bot))')
            sig = ('signature', ('pre', r - 1, (vid, 1 - self.coin[(vid, r)])))
            self.outer.broadcast(sig)
            message = ('main', r, (vid, -1))
            self.add_log(vid, r, message)
            to_list = [i for i in range(1, self.n + 1)]
            self.outer.sign_batch_1(self.pid, to_list, message)
        print(f'[Sba, {self.pid}] main vote failed')

    def recv_sign(self, fro, msg):
        if self.debug: print(f'[Sba, {self.pid}] process sign', msg)
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
        if self.debug: print(f'[Sba {self.pid}] process signature', _msg)
        type, round, (vid, value) = _msg
        self.signatures[vid].add(_msg)
        if vid in self.outputs: return 'vid already has output'
        msg = (type, (vid, round))
        if type == 'pre' and len(self.initial_sign_cnt1[msg]) >= 2 * self.t + 1 and round == 0:
            if vid not in self.log: return 'not receive vote'
            if len(self.log[vid][round]) >= 2: return 'already main-voted, no need to process'
            message = ("main", 0, (vid, value))
            self.add_log(vid, round, message)
            to_list = [i for i in range(1, self.n + 1)]
            self.outer.sign_batch_1(self.pid, to_list, message)
            return 'sign initial main'

        elif type == 'main':
            if value != -1:
                self.outputs[vid] = value
                sig = ('signature', _msg)
                self.outer.broadcast(sig)
                return f'output at round {round}'
            return 'signature for main bot'
        return 0

    def add_log(self, vid, round, message):
        self.log[vid][round].append(message)
        print('[message log]')
        for r in range(round + 1):
            print(f'Party{self.pid}\t Round{r}: {self.log[vid][r]}')

    def process_msg_buf(self, m):
        output_msg = []
        self.msgs.extend(m)
        if self.debug: print(f'[Sba, {self.pid}] process messages', self.msgs)

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