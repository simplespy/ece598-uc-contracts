# Applications build using the UC framework. 

Almost all applications in this directory contain some ideal functionality, a real-world protocol, a simulator to satisfy the UC emulation definition, and at least one environment to run the real/ideal worlds.

The basic example and the place to start is the `commitment/` example. This is a simple bit commitment in the random oracle model. 
This is the best example to get familiar with how to write *environments* and interact with the protocol/adversary. See `commitment/env.py` for throroughly commented environment examples.

## Note regarding secp256k1 and elliptic curve cryptography
Normally, you can run the application environments from anywhere as the paths are all relative and rely on the `uc` package that is installed. 
The elliptic curve crypto and `secp256k1.py` file (can be seen in the `pedersen/` example) are all local to that directory and imported with a relative path. Therefore, to run, say, `pedersen/env_honest.py`, you need to make sure you are *in* the `pedersen/` directory.
