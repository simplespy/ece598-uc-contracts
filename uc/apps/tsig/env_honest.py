from uc.utils import waits, collectOutputs
import os
import gevent
import secp256k1 as secp

def env_honest(k, static, z2p, z2f, z2a, a2z, f2z, p2z, pump):
    print('\033[94m[ env_honest ]\033[0m')

    sid = ('one', "4, 2") # n, c
    static.write( (('sid',sid), ('crupt',)))

    transcript = []
    msgs = []
    def _a2z():
        while True:
            m = waits(a2z)
            transcript.append('a2z: ' + str(m))
            msgs.append(m)
            pump.write('dump')

    def _p2z():
        while True:
            m = waits(p2z)
            transcript.append('p2z: ' + str(m))
            msgs.append(m)
            pump.write('dump')

    g1 = gevent.spawn(_a2z)
    g2 = gevent.spawn(_p2z)

    # party 2, 3 give the permission to sign m to party 1
    m = secp.uint256_from_str(os.urandom(32))
    for i in range(2, 4):
        print('\n sign the message: \n\t{}\n'.format(m))
        z2p.write( (i, ('sign', 1, m)) )
        waits(pump)

    # party 1 send signature of m to party 4
    z2p.write( (1, ('send', 4, m)) )
    waits(pump)

    #z2p.write((0, ('getLeaks', )))
    #waits(pump)
    
    gevent.kill(g1)
    gevent.kill(g2)
    
    print('transcript', transcript)
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
from f_tsig import F_tsig
from f_ro import F_CRO_FC
from prot_tsig import Tsig_Prot

print('\nreal\n')
treal = execUC(
    128,
    env_honest,
    F_CRO_FC,
    Tsig_Prot,
    DummyAdversary
)

print('\nideal\n')
tideal = execUC(
    128,
    env_honest,
    F_tsig,
    DummyParty,
    DummyAdversary
)

distinguisher(tideal, treal)
