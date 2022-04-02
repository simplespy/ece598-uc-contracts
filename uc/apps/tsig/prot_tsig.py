import os 
from ast import literal_eval
from uc import UCProtocol
from uc.utils import waits, wait_for
from collections import defaultdict
import logging

log = logging.getLogger(__name__)

class Tsig_Prot(UCProtocol):
    def __init__(self, k, bits, sid, pid, channels, pump):
        UCProtocol.__init__(self, k, bits, sid, pid, channels, pump) 
        self.ssid,sid = sid
        parties = literal_eval(sid)
        self.n = sid[0]
        self.c = sid[1]
        self.pid = pid

        self.env_msgs['sign'] = self.env_sign
        self.env_msgs['send'] = self.env_send
        self.env_msgs['getLeaks'] = self.env_leak

        self.func_msgs['evaluate'] = self.recv_evaluate
        self.func_msgs['invert'] = self.recv_invert
        self.func_msgs['recvmsg'] = self.func_receive

        self.see = {}
        self.cnt = {}
        self.eval = None
        self.inv = None

    def env_sign(self, to, msg):
        self.to = to
        self.write( ch='p2f', msg=('evaluate', self.pid, msg))

        #for i in range(1, int(self.n)):
        #    if i != self.pid:
        #        self.write( ch='p2f', msg=('sendmsg', i, ('evaluate', self.pid, msg)))
        #        waits(self.pump)
        

    def env_send(self, to, msg):
        print('env_send', self.pid, self.eval, self.inv)
        if self.inv is not None:
            self.write('p2f', ('sendmsg', to, ('send', msg, self.inv)))

    def recv_evaluate(self, m, hm):
        print(self.pid, 'recv_evaluate')
        self.eval = hm
        self.write( ch='p2f', msg=('invert', self.to, hm))
        

    def recv_invert(self, m):
        print(f'[{self.pid}, recv_invert]')
        self.inv = m
        self.write( ch='p2z', msg=('signature', m))
        

    def func_receive(self, fro, msg):
        print(f'[{self.pid}, receive]', msg, 'from', fro)
        if msg[0] == 'send':
            m = msg[1]
            inv = msg[2]
            self.write( ch='p2z', msg=('send', fro, m))
        if msg[0] == 'evaluate':
            self.write( ch='p2f', msg=msg)

    def env_leak(self):
        if self.pid == 0:
            self.write('p2f', ('getLeaks', ))
        else:
            self.pump.write('')



        
        

    