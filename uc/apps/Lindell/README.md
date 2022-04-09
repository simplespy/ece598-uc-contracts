## Test cases
1. `env_crupt_committer.py`: the committer is corrupt
2. `env_crupt_receiver.py`: the receiver is corrupt
3. `env_honest.py`, `env_bangfcom.py`: same as the Pedersen example


Note: Distinguisher in my test cases is revised to check deterministic information like type and sender/receiver of each message in transcripts, so it will output `same` when these information matches.