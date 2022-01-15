import uc.itm

from uc.itm import GenChannel, waits, ITM
from gevent import wait


def Echo( q2p, p2q ):
    x = waits(q2p)
    print("Echo received:", x)

    p2q.write(x)

def Write1 ( z2q, q2z, p2q, q2p ):
    waits(z2q)
    q2p.write("Hello")

    x = waits(p2q)
    print('Write1 received:', x)

    q2z.write("Received: " + x)



class EchoITM(ITM):
    def __init__(self, k, q2p, p2q):
        handlers = {
            q2p : self.handler_echo,
        }
        channels = { 'q2p': q2p, 'p2q': p2q }
        ITM.__init__(self, k, None, None, None, channels, handlers, None)
        
    def handler_echo(self, msg):
        print('Echo Handler received:', msg)
        self.channels['p2q'].write('hi')
        # self.write('p2q', msg)


if __name__=='__main__':

    def test1():
        p2q = GenChannel('p2q')
        q2p = GenChannel('q2p')
        z2q = GenChannel('z2q')
        q2z = GenChannel('q2z')
        p = gevent.spawn(Echo, q2p, p2q)
        q = gevent.spawn(Write1,  z2q, q2z, p2q, q2p)
        z2q.write( "ok" )
        return gevent.wait((p,q))

    gevent.wait(test1())

    def test2():
        p2q = GenChannel('p2q')
        q2p = GenChannel('q2p')
        q2p.write( "Hello World" )
        e = EchoITM(120, q2p, p2q)
        gevent.spawn(e.run())
        x = waits(p2q)
        print("test2 Received: ", x)
        return x

    gevent.wait(test2())
