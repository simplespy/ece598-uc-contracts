from uc.utils import waits, collectOutputs
import os
import gevent
import secp256k1 as secp


def env_crupt_committer(k, static, z2p, z2f, z2a, a2z, f2z, p2z, pump):
    sid = ('one', "1, 2")
    static.write( (('sid',sid), ('crupt', 1)))

    transcript = []
    msgs = []

    def _p2z():
        while True:
            m = waits(p2z)
            transcript.append('p2z: ' + str(m))
            print('pump', m)
            msgs.append(m)
            pump.write('dump')
    ge2 = gevent.spawn(_p2z)

    to_commit = secp.uint256_from_str(os.urandom(32))
   
    z2a.write( ('A2P', (1, ('value',))) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    _,(fro,((g,z,g1,g2,x,c,d,h),)) = msg

    z2a.write( ('A2P', (1, ('hash_to_group', (1, to_commit)))) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    _,(fro,(hash_value,)) = msg

    r = secp.uint256_from_str(os.urandom(32))
    s = secp.uint256_from_str(os.urandom(32))
    # DCS(m, 1; r, s)
    u1 = (g1 * r, g2 * r)
    e1 = hash_value + h * r
    w = hash((secp.ser(u1[0]), secp.ser(u1[1]), secp.ser(e1)))
    v1 = (c + d * w) * r
    C1 = (u1[0], u1[1], e1, v1)

    u2 = (g1 * s, g2 * s)
    e2 = secp.identity + h * s
    v2 = (c + d * w) * s
    C2 = (u2[0], u2[1], e2, v2)

    z2a.write( ('A2P', (1, ('sendmsg', 2, ('commit', 1, C1)))) )
    
    msg = waits(p2z)
    transcript.append('p2z: ' + str(msg))
    msgs.append(msg)

    C2_ser = (secp.ser(u2[0]), secp.ser(u2[1]), secp.ser(e2), secp.ser(v2))
    k2 = secp.uint256_from_str(os.urandom(32))
    k1 = hash((to_commit, C2_ser, 1))
    cp = g * k1 + z * k2
    z2a.write( ('A2P', (1, ('sendmsg', 2, ('open1', 1, to_commit, cp)))) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)

    _,(fro,(_,_,(msg_type, cid, eps))) = msg
    z = s + eps * r
    
    (alpha, beta, gamma, delta) = C2
    u1, u2, e, v = C1
    cond1 = (g1 * z == alpha + u1 * eps)
    cond2 = (g2 * z == beta + u2 * eps)
    cond3 = h * z == gamma + (e - hash_value) * eps 
    cond4 = (c + d * w) * z == delta + v * eps 
    if cond1 and cond2 and cond3 and cond4:
        print('ok')

    gevent.kill(ge2)

    print('\ntranscript:\n\t{}'.format(transcript))
    return transcript, msgs

def iterate(t, t2):

    if isinstance(t, list) or isinstance(t, tuple):
        if len(t) != len(t2): return False
        for i in range(len(t)):
            if not iterate(t[i], t2[i]): 
                return False

    else:
        if isinstance(t, str):
            if len(t) < 10 and t != t2: 
                return False
        if isinstance(t, int):
            if t < 10 and t != t2: 
                return False
    return True

def distinguisher(t_ideal, t_real):
    print('\n\t\033[93m ideal transcript\033[0m')
    for i in t_ideal[0]: print(str(i))

    print('\n\t\033[93m real transcript\033[0m')
    for i in t_real[0]: print(str(i))

    if iterate(t_ideal[1], t_real[1]):
        print("\033[92m[distinguisher] they're the same\033[0m")
    else:
        print("\033[91m[distinguisher] they're different\033[0m")

from uc.adversary import DummyAdversary
from uc.protocol import DummyParty
from uc.execuc import execUC
from f_crs import F_CRS
from f_mcom import F_Mcom
from sim_mcom import Sim_Mcom
from prot_com import Commitment_Prot
from prot_mcom import MCommitment_Prot

print('\nreal\n')
treal = execUC(
    128,
    env_crupt_committer,
    F_CRS,
    MCommitment_Prot,
    DummyAdversary
)

print('\nideal\n')
tideal = execUC(
    128,
    env_crupt_committer,
    F_Mcom,
    DummyParty,
    Sim_Mcom
) 

distinguisher(tideal, treal)
