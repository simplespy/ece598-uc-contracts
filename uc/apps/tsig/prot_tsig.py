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
        sid = literal_eval(sid)
        self.n = sid[0]
        self.c = sid[1]
        self.t = sid[2]
        self.pid = pid

        self.env_msgs['sign'] = self.env_sign
        self.env_msgs['send'] = self.env_send
        self.env_msgs['getBuf'] = self.env_getBuf

        self.func_msgs['evaluate'] = self.recv_evaluate
        self.func_msgs['invert'] = self.recv_invert
        self.func_msgs['recvmsg'] = self.func_receive

        self.see = {}
        self.cnt = {}
        self.eval = None
        self.inv = None
        self.to = None

    def env_sign(self, to, msg):
        self.to = to
        self.write( ch='p2f', msg=('broadcast', ('evaluate_all', msg)))
        
    def env_send(self, to, msg):
        print('[Ptsig] env_send', self.pid, self.eval, self.inv)
        if self.inv is not None and self.eval is not None:
            self.write('p2f', ('sendmsg', to, ('send', msg, self.inv)))

    def recv_evaluate(self, m, hm):
        print('[Ptsig]', self.pid, 'recv_evaluate')
        self.eval = hm
        if self.to is not None:
            self.write( ch='p2f', msg=('invert', self.to, hm))
        waits(self.pump)
        
    def recv_invert(self, m):
        print(f'[Ptsig] [{self.pid}, recv_invert]')
        self.inv = m
        if self.eval is not None:
            self.write( ch='p2z', msg=('signature', m))
        waits(self.pump)
        
    def func_receive(self, fro, msg):
        print(f'[Ptsig] [{self.pid}, receive]', msg, 'from', fro)
        if msg[0] == 'send':
            m = msg[1]
            inv = msg[2]
            self.write( ch='p2z', msg=('send', fro, m))

    def env_getBuf(self):
        if self.pid == 0:
            self.write('p2f', ('getBuf', ))
        else:
            m = self.write_and_wait_for( ch='p2f', msg=('getBuf', ), read='f2p' )
            print('[Ptsig]', self.pid)
            msgs = list(m[1])
            if len(msgs) == 0: self.pump.write('0')
            print('[Ptsig]', self.pid, msgs)
            for msg in msgs:
                if msg[0] == 'evaluate_all':
                    self.write(ch='p2f', msg=msg)
                    waits(self.pump)
                if msg[0] == 'evaluate':
                    self.recv_evaluate(msg[1], msg[2])
                    
                if msg[0] == 'invert':
                    self.recv_invert(msg[1])
                    



                    

            



        
        

    