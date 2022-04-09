from uc import UCAdversary
from ast import literal_eval
from collections import defaultdict
import secp256k1 as secp
import os

class Sim_Mcom(UCAdversary):
    def __init__(self, k, bits, crupt, sid, pid, channels, pump):
        UCAdversary.__init__(self, k, bits, crupt, sid, pid, channels, pump)
        self.ssid = sid[0]
        sid = literal_eval(sid[1])
        self.committer = sid[0]
        self.receiver = sid[1]

        self.state = defaultdict(int)
        self.msg = {}
        self.randomness = {}
        self.commitment = {}
        self.commitment2 = {}
        self.hash_table = {}

        self.g = None
        self.z = None
        self.g1 = None
        self.g2 = None
        self.x = None
        self.c = None
        self.d = None
        self.h = None   
        self.receiver_commitment = None

        self.party_msgs['recvmsg'] = self.recvmsg
        self.z2a2p_msgs['value'] = self.value
        self.z2a2p_msgs['hash_to_group'] = self.hash_to_group
        
        if self.is_dishonest(self.receiver):
            self.party_msgs['commit'] = self.recv_commit
            self.party_msgs['open'] = self.recv_open
        if self.is_dishonest(self.committer):
            self.z2a2p_msgs['sendmsg'] = self.sendmsg

    def value(self, to):
        self.sample_g_h()
        self.write('a2z', ('P2A', (to, ((self.g,self.z,self.g1,self.g2,self.x,self.c,self.d,self.h),))))

    def make_random_point(self):
        return secp.make_random_point(lambda x: self.sample(8*x).to_bytes(x, 'little'))

    def sample_g_h(self):
        if self.g is None:
            self.g = self.make_random_point()
            self.h = self.make_random_point()
            self.z = self.make_random_point()

            self.g1 = self.make_random_point()
            self.g2 = self.make_random_point()

            self.x = [secp.uint256_from_str(os.urandom(32)) for i in range(5)]
            self.c = self.g1 * self.x[0] + self.g2 * self.x[1]
            self.d = self.g1 * self.x[2] + self.g2 * self.x[3]
            self.h = self.g1 * self.x[4]

    def find_msg(self, commitment):
        u1, u2, e, v = commitment
        w = hash((secp.ser(u1), secp.ser(u2), secp.ser(e)))
        assert(u1 * (self.x[0] + w * self.x[2]) + u2 * (self.x[1] + w * self.x[3]) == v)

        hash_value = e - u1 * self.x[4]
        return self.group_to_hash(hash_value)


    def sendmsg(self, to, recv, msg):
        if msg[0] == 'commit':
            _, cid, self.commitment[cid] = msg
            if self.state[cid] == 0:
                self.msg[cid] = self.find_msg(self.commitment[cid])[1]
                self.write( 'a2p', (to, ('commit', cid, self.msg[cid])) )
                self.z2a2p_msgs['sendmsg'] = self.open_send
                self.state[cid] = 1
            else: self.pump.write('')
        else: self.pump.write('')

    def open_send(self, to, recv, msg):
        if msg[0] == 'open1':
            _, cid, preimage, ped = msg
            assert(preimage == self.msg[cid])
            if self.state[cid] == 1:
                self.eps = secp.uint256_from_str(os.urandom(32))
                self.write('a2z', ('P2A', (self.committer, ('recvmsg', self.receiver, ('response1', cid, self.eps)))) )
                self.state[cid] = 2
            else: self.pump.write('')
        
        else: self.pump.write('')



    def recvmsg(self, sender, msg):
        if msg[0] == 'response1':
            cid, eps = msg[1:]
            (r, s) = self.randomness[cid]
            z = s + eps * r
            self.write('a2z', ('P2A', (self.receiver, ('recvmsg', self.committer, ('open2', cid, self.commitment2[cid], self.k2, z)))) )
        else:
            self.write('a2z', ('P2A', (sender, ('recvmsg', self.committer, msg))) )

    def recv_commit(self, sender, cid):
        self.sample_g_h()
        r = secp.uint256_from_str(os.urandom(32))
        s = secp.uint256_from_str(os.urandom(32))
        self.randomness[cid] = (r, s)
        u1 = (self.g1 * r, self.g2 * r)
        hash_value = self.make_random_point()
        e1 = hash_value + self.h * r
        self.hash_table[(sender, cid)] = hash_value
        self.w = w = hash((secp.ser(u1[0]), secp.ser(u1[1]), secp.ser(e1)))
        v1 = (self.c + self.d * w) * r
        self.receiver_commitment = (u1[0], u1[1], e1, v1)
        self.write('a2z', msg=('P2A', (sender, ('recvmsg', self.committer, ('commit', cid, self.receiver_commitment)))))

    def recv_open(self, sender, cid, m):
        s = self.randomness[cid][1]
        u2 = (self.g1 * s, self.g2 * s)
        e2 = secp.identity + self.h * s
        w = self.w
        v2 = (self.c + self.d * w) * s
        self.k2 = secp.uint256_from_str(os.urandom(32))
        self.commitment2[cid] = (secp.ser(u2[0]), secp.ser(u2[1]), secp.ser(e2), secp.ser(v2))
        k1 = hash((m, self.commitment2[cid], cid))
        cp = self.g * k1 + self.z * self.k2
        self.write( 'a2z', ('P2A', (sender, ('recvmsg', self.committer, ('open1', cid, m, cp)))) )

    def recv_response1(self, sender, cid, eps):
        r, s = self.randomness[cid]
        z = s + eps * r
        self.write( 'a2z', ('P2A', (sender, ('recvmsg', self.committer, ('open2', cid, self.commitment2[cid], self.k2, z)))) )

    def hash_to_group(self, sender, msg):
        if sender == self.committer:
            self.hash_table[msg] = self.hash_table.setdefault(msg, self.make_random_point())
        else:
            cid = msg[0]
            self.hash_table[msg] = self.hash_table[(sender, cid)]
        self.write('a2z', ('P2A', (sender, (self.hash_table[msg],))))

    def group_to_hash(self, hash_value):
        for key in self.hash_table:
            if self.hash_table[key] == hash_value:
                return key
        return None
