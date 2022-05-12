from uc.utils import waits, collectOutputs
import os
import gevent
import secp256k1 as secp
import time

def env_crash(k, static, z2p, z2f, z2a, a2z, f2z, p2z, pump):
    print('\033[94m[ env_honest ]\033[0m')

    n = 4
    c = 2
    t = 1

    sid = ('one', f"({n}, {t})")
    static.write( (('sid',sid), ('crupt', 1)))

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

    def read_buf(x):
        print('[env] read buf')
        for i in range(t + 1, n + 1): 
            z2p.write((i, (f'getBuf', x)))
            m = waits(pump)

        print('[env] red buf from adv')
        for i in range(1, t + 1):
            z2a.write(('A2F', ('getBuf', x, i)))
            waits(pump)

        
    g1 = gevent.spawn(_a2z)
    g2 = gevent.spawn(_p2z)

    vid = 1
    votes = [0, 0, 1, 1, 1]

    adv_vote = 0

    z2a.write(('A2F', ('vote', vid, adv_vote)))
    waits(pump)

    # honest party 2, 3, 4 vote for 1
    for i in range(t + 1, n + 1):
        print(f'[env] party {i} sends vote {votes[i]}')
        z2p.write( (i, ('vote', vid, votes[i])) )
        m = waits(pump)

    read_buf(2)
    read_buf(1)
    
    for i in range(t + 1, n + 1):
        print(f'[env] party {i} getOutput')        
        z2p.write( (i, ('getOutput', vid)) )
        waits(pump)



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
from f_tsigs import F_tsigs
from f_ba import F_ba
from prot_ba import BA_Prot
from sim_ba import SimBACrash

print('\nreal\n')
treal = execUC(
    128,
    env_crash,
    F_tsigs,
    BA_Prot,
    DummyAdversary
)

print('\nideal\n')
tideal = execUC(
    128,
    env_crash,
    F_ba,
    DummyParty,
    SimBACrash
)

distinguisher(tideal, treal)
