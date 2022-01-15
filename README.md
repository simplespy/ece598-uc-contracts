# uc-contract
This is a python implementation of the UC framework alongside the changes required for smart contract applications to be expressed.


## Installation
Use `pip install -r uc/requirements.txt` to install all required pip modules for this project. Python version is **>= 3.5.3**.

Run `pip install -e .` to install the `uc/` local module for development in this directory.

The first test can be run as `python uc/apps/coinflip/env.py`.


## Folder structure

`uc/`: Python UC module

`uc/apps/`: Examples of using python UC module

`uc/tutorial/`: Tutorials following along the SaUCy course


### Files under `uc/`
> more detailed explanation of `uc/` could be referred to the `README.md` inside `uc/` folder.

`itm.py`: basic class of Interactive Turing Machine(ITM).

`adversary.py`: basic class of adversary.

`functionality.py`: basic class of functionality.

`protocol.py`: basic class of protocol.

`exeuc.py`: {execute|create} (wrapped)UC.

`utils.py`: utility functions that are used by ITM.


### Files under `uc/apps/`

`commitment/`: example of commitment protocol

`coinflip/`: example of coinflip protocol

`simplecomp/`: example of a composition


## Other modules used in this project

`gevent`: [gevent](https://www.gevent.org/) is a [coroutine](https://en.wikipedia.org/wiki/Coroutine)-based Python networking library that uses `greenlet` to provide a high-level synchronous API on top of the `libev` or `libuv` event loop.

Features include:

- Fast event loop based on `libev` or `libuv`.

- Lightweight execution units based on `greenlets`.

- API that re-uses concepts from the Python standard library (for examples there are events and queues).

- Cooperative sockets with SSL support

- Cooperative DNS queries performed through a threadpool, dnspython, or c-ares.

- Monkey patching utility to get 3rd party modules to become cooperative

- TCP/UDP/HTTP servers

- Subprocess support (through gevent.subprocess)

- Thread pools

(above are excerpted from [official website](https://www.gevent.org/))

`inspect` (built-in): The inspect module provides several useful functions to help get information about live objects such as modules, classes, methods, functions, tracebacks, frame objects, and code objects.

