from uc.utils import waits, collectOutputs
import os
import gevent
import secp256k1 as secp

def env_crupt_receiver(k, static, z2p, z2f, z2a, a2z, f2z, p2z, pump):
    sid = ('one', "1, 2")
    static.write( (('sid',sid), ('crupt', 2)))

    transcript = []
    msgs = []

    def _p2z():
        while True:
            m = waits(p2z)
            transcript.append('p2z: ' + str(m))
            pump.write('dump')

    ge1 = gevent.spawn(_p2z)

    m = secp.uint256_from_str(os.urandom(32))
   
    z2p.write( (1, ('commit', 1, m)) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)


    _,(fro,(_,_,(_, cid, C1))) = msg
    u1, u2, e, v = C1

    z2a.write( ('A2P', (2, ('value',))) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)
    
    _,(fro,((g,z,g1,g2,x,c,d,h),)) = msg

    z2p.write( (1, ('reveal', 1)) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)
    _,(fro,(_,_,(msg_type, cid, preimage, cp))) = msg

    assert (msg_type == 'open1')
    eps = secp.uint256_from_str(os.urandom(32))
    z2p.write( (1,  ('sendmsg', 2, ('response1', cid, eps))))
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)
    _,(fro,(_,_,(msg_type, cid, C2, k2, z))) = msg

    assert (msg_type == 'open2')

    z2a.write( ('A2P', (2, ('hash_to_group', (1, preimage)))) )
    msg = waits(a2z)
    transcript.append('a2z: ' + str(msg))
    msgs.append(msg)
    _,(fro,(hash_value,)) = msg

    #checkcommitment
    w = hash((secp.ser(u1), secp.ser(u2), secp.ser(e)))
    (alpha, beta, gamma, delta) = C2
    alpha = secp.deser(alpha)
    beta = secp.deser(beta)
    gamma = secp.deser(gamma)
    delta = secp.deser(delta)
    cond1 = (g1 * z == alpha + u1 * eps)
    cond2 = (g2 * z == beta + u2 * eps)
    cond3 = h * z == gamma + (e - hash_value) * eps 
    cond4 = (c + d * w) * z == delta + v * eps

    gevent.kill(ge1)
    
    print('\ntranscript:\n\t{}'.format(transcript))
    if cond1 and cond2 and cond3 and cond4: print('ok')
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
from prot_mcom import MCommitment_Prot

treal = execUC(
    128,
    env_crupt_receiver,
    F_CRS,
    MCommitment_Prot,
    DummyAdversary
)

tideal = execUC(
    128,
    env_crupt_receiver,
    F_Mcom,
    DummyParty,
    Sim_Mcom
) 

distinguisher(tideal, treal)
