import dump
import comm
import gevent
from gevent.queue import Queue, Channel, Empty
from gevent.event import AsyncResult
class DummyAdversary(object):
    '''Implementation of the dummy adversary. Doesn't do anything locally,
     just forwards all messages to the intended party. Z communicates with
     corrupt parties through dummy adversary'''
    def __init__(self, sid, pid, z2a, a2z, p2a, a2p, a2f, f2a):
        self.sid = sid
        self.pid = pid
        self.sender = (sid,pid)
        self.z2a = z2a; self.a2z = a2z
        self.p2a = p2a; self.a2p = a2p
        self.f2a = f2a; self.a2f = a2f

        self.input = AsyncResult()
        self.leak = AsyncResult()
        self.parties = {}
        self.leakbuffer = []
    
    def __str__(self):
        return str(self.F)

    def read(self, fro, msg):
        print(u'{:>20} -----> {}, msg={}'.format(str(fro), str(self), msg))

    def addParty(self, itm):
        if (itm.sid,itm.pid) not in self.parties:
            self.parties[itm.sid,itm.pid] = itm

    def addParties(self, itms):
        for itm in itms:
            self.addParty(itm)

    def partyInput(self, to, msg):
        self.F.input_msg(('party-input', to, msg))

    def input_delay_tx(self, fro, nonce, rounds):
        msg = ('delay-tx', fro, nonce, rounds)
        self.a2f.write( ((69,'G_ledger'), (False, msg)) )
        r = gevent.wait(objects=[self.f2a],count=1)
        r = r[0]
        msg = r.read()
        print('response DELAY', msg, '\n')
        self.a2z.write(msg)
        self.f2a.reset()

    def input_ping(self, to):
        self.a2f.write( (to, ('ping',)) )

    def getLeaks(self, fro):
        if fro[1] == 'G_ledger':
            print('Write to a2f:', fro, (False, ('get-leaks',)))
            self.a2f.write( (fro, (False,('get-leaks',))) )
        else:
            print('Write to a2f:', fro, ('get-leaks',))
            self.a2f.write( (fro, ('get-leaks',)) )
        r = gevent.wait(objects=[self.f2a],count=1)
        r = r[0]
        msg = r.read()
        print('response F', msg)
        self.a2z.write( msg )
        self.f2a.reset()

    def input_corrupt(self, pid):
        comm.corrupt(self.sid, pid)

    '''
        Instead of waiting for a party to write to the adversary
        the adversary checks leak queues of all the parties in 
        a loop and acts on the first message that is seen. The
        environment can also tell the adversary to get all of the
        messages from a particular ITM.
    '''
    def run(self):
        while True:
            ready = gevent.wait(
                objects=[self.z2a, self.f2a, self.p2a],
                count=1
            )
            r = ready[0]
            if r == self.z2a:
                msg = r.read()
                self.z2a.reset()
                if msg[0] == 'A2F':
                    t,msg = msg
                    if msg[0] == 'get-leaks':
                        self.getLeaks(msg[1])
                    else:
                        self.a2f.write( msg )
                elif msg[0] == 'A2P':
                    t,msg = msg
                    self.a2p.write( msg )
                elif msg[0] == 'corrupt':
                    self.input_corrupt(msg[1])
            elif r == self.p2a:
                msg = r.read()
                self.p2a.reset()
                print('Go back from party', msg)
                self.a2z.write( msg )
            elif r == self.f2a:
                msg = r.read()
                self.f2a.reset()
                self.a2z.write(msg)
            else:
                print('else dumping right after leak'); dump.dump()

