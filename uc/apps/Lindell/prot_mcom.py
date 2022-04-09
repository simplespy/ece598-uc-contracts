import os 
from ast import literal_eval
from uc import UCProtocol
from uc.utils import waits, wait_for
from collections import defaultdict
import secp256k1 as secp
import logging

log = logging.getLogger(__name__)

class MCommitment_Prot(UCProtocol):
    def __init__(self, k, bits, sid, pid, channels, pump):
        UCProtocol.__init__(self, k, bits, sid, pid, channels, pump) 
        self.ssid,sid = sid
        parties = literal_eval(sid)
        self.committer = parties[0]
        self.receiver = parties[1]
        self.iscommitter = pid == self.committer

        self.env_msgs['commit'] = self.env_commit
        self.env_msgs['reveal'] = self.env_reveal
        self.env_msgs['sendmsg'] = self.func_receive
        self.func_msgs['recvmsg'] = self.func_receive

        self.msg = {}
        self.randomness = {}
        self.commitment = {}
        self.commitment2 = {}

        self.first = True
        self.state = defaultdict(int)

    def env_commit(self, cid, to_commit):
        if self.first:
            m = self.write_and_wait_for('p2f', ('value',), 'f2p')[0]
            self.g = m[0]
            self.z = m[1]

            self.g1 = m[2]
            self.g2 = m[3]
            self.x = m[4]
            self.c = m[5]
            self.d = m[6]
            self.h = m[7]
            self.first = True

        if self.iscommitter and self.state[cid] == 0:
            self.msg[cid] = to_commit
            hash_value = self.write_and_wait_for('p2f', ('hash_to_group', (cid, to_commit)), 'f2p')[0]
            r = secp.uint256_from_str(os.urandom(32))
            s = secp.uint256_from_str(os.urandom(32))
            self.randomness[cid] = (r, s) #r, s
            # DCS(m, 1; r, s)
            u1 = (self.g1 * r, self.g2 * r)
            e1 = hash_value + self.h * r
            w = hash((secp.ser(u1[0]), secp.ser(u1[1]), secp.ser(e1)))
            v1 = (self.c + self.d * w) * r
            C1 = (u1[0], u1[1], e1, v1)

            u2 = (self.g1 * s, self.g2 * s)
            e2 = secp.identity + self.h * s
            v2 = (self.c + self.d * w) * s
            C2 = (u2[0], u2[1], e2, v2)

            self.commitment2[cid] = (secp.ser(u2[0]), secp.ser(u2[1]), secp.ser(e2), secp.ser(v2))

            self.commitment[cid] = (u1[0], u1[1], e1, v1)
            self.write('p2f', ('sendmsg', self.receiver, ('commit', cid, C1)))
            self.state[cid] = 1
        else:
            self.pump.write('')

    def env_reveal(self, cid):

        if self.iscommitter and self.state[cid] == 1:
            self.k2 = secp.uint256_from_str(os.urandom(32))
            k1 = hash((self.msg[cid], self.commitment2[cid], cid))
            cp = self.g * k1 + self.z * self.k2
            self.write( 'p2f', ('sendmsg', self.receiver, ('open1', cid, self.msg[cid], cp)) )
            self.state[cid] = 2
        else:
            self.pump.write('')
    
    def reveal(self, cid, eps):   
        if self.iscommitter and self.state[cid] == 2:
            
            (r, s) = self.randomness[cid]
            z = s + eps * r
            self.write( 'p2f', ('sendmsg', self.receiver, ('open2', cid, self.commitment2[cid], self.k2, z)) )

        else:
            self.pump.write('')

    def check_commit_1(self, cid, preimage, ped):
        
        eps = secp.uint256_from_str(os.urandom(32))
        self.write('p2f', ('sendmsg', self.committer, ('response1', cid, eps)))
        return (preimage, ped, eps)
        

    def check_commit_2(self, cid, C2, k2, z, preimage, ped, eps):
        m = self.write_and_wait_for('p2f', ('value',), 'f2p')[0]
        self.g = m[0]
        self.z = m[1]
        self.g1 = m[2]
        self.g2 = m[3]

        self.x = m[4]
        self.c = m[5]
        self.d = m[6]
        self.h = m[7]
        (alpha, beta, gamma, delta) = C2
        alpha = secp.deser(alpha)
        beta = secp.deser(beta)
        gamma = secp.deser(gamma)
        delta = secp.deser(delta)

        C1 = self.commitment[cid]
        u1, u2, e, v = C1
        w = hash((secp.ser(u1), secp.ser(u2), secp.ser(e)))

        hash_value = self.write_and_wait_for('p2f', ('hash_to_group', (cid, preimage)), 'f2p')[0]

        cond1 = (self.g1 * z == alpha + u1 * eps)
        cond2 = (self.g2 * z == beta + u2 * eps)
        cond3 = self.h * z == gamma + (e - hash_value) * eps 
        cond4 = (self.c + self.d * w) * z == delta + v * eps 
        if cond1 and cond2 and cond3 and cond4:
            self.write( 'p2z', ('open', cid, preimage) )
        else:
            self.pump.write('error')

    def func_receive(self, fro, msg):
        if not self.iscommitter and self.state[msg[1]] == 0 and msg[0] == 'commit':
            self.write('p2z', msg=('commit', msg[1]))
            self.commitment[msg[1]] = msg[2]
            self.state[msg[1]] = 1
        elif not self.iscommitter and self.state[msg[1]] == 1 and msg[0] == 'open1':
            self.open1 = self.check_commit_1(msg[1], msg[2], msg[3])
            self.state[msg[1]] = 2
        elif not self.iscommitter and self.state[msg[1]] == 2 and msg[0] == 'open2':
            preimage, ped, eps =  self.open1
            self.check_commit_2(msg[1], msg[2], msg[3], msg[4], preimage, ped, eps)
            self.state[msg[1]] = 3
        elif self.iscommitter and self.state[msg[1]] == 2 and msg[0] == 'response1':
            self.reveal(msg[1], msg[2])
        else:
            self.write( 'p2z', ('recvmsg', msg) )
