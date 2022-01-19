# set base image
FROM python:3.6

# Copy this whole folder.
# (Not necessary when bridging with -v {host}:/uc-contracts
COPY . /uc-contracts

# Set the workdir to a bridge to ece598-uc-contracts folder on host
WORKDIR /uc-contracts

RUN pip install -r "uc/requirements.txt"

RUN pip install -e .

CMD [ "bash" ]