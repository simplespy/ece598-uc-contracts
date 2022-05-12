from uc.adversary import UCAdversary
from collections import defaultdict

class F_ba(UCAdversary):
    def __init__(self, k, bits, crupt, sid, pid, channels, pump):
        UCAdversary.__init__(self, k, bits, crupt, sid, pid, channels, pump)
        
        