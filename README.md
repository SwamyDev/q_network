# QNetwork
This project implements a method to perform secure communication using quantum key distribution.
Tested on Ubuntu 16.04.3.
For classical communication tinyIpcLib from fellow student uderos was used (https://github.com/uderos/tinyIpcLib).

## Docker images:
You can find a docker image of the project with all environment variables set up and dependencies installed here:
https://hub.docker.com/r/swamydev/qnetwork/

## Running examples
To run the exercise submission for the edx course perform the following steps:

- Start SimulaQron as described in the introductions pdf
- Start the ipcServer by opening a terminal in the tinyIpcLib folder and running the command python ipcServer.py
- Open a terminal in the QNetwork folder and run the following commands:
    $ export NETSIM=yourPath/SimulaQron
    $ export PYTHONPATH=yourpath:yourpath/tinyIpcLib:$PYTHONPATH
    $ sh run_exercise.sh

Alice and Bob are sharing 1000 qubits and try to generate a key bit from it. Eve is trying to eavesdrop by simply
measuring the qubit and sending it on to Bob. When n is small it can happen that no eaves dropping is detected,
because it just happened that states altered by Eve didn't end up in the states used for testing.

To run the competition submission perform the following steps:

- Start SimulaQron as described in the introductions pdf
- Start the ipcServer by opening a terminal in the tinyIpcLib folder and running the command python ipcServer.py
- Open a terminal in the QNetwork folder and run the following commands:
    $ export NETSIM=yourPath/SimulaQron
    $ export PYTHONPATH=yourpath:yourpath/tinyIpcLib:$PYTHONPATH
    $ sh run_submission.sh

Alice sends Bob a secure message "Hello, Bob!". First the system shares enough key to encode the message with the one
time pad, using the protocol specified in q_network.cfg. Currently only BB84 could be properly tested because DIQKD
required larger n to work and the setup on which this implementation was tested on was too slow. Currently, the DIQKD
implementation can be considered WIP or beeing in Alpha.

## File contents:
- QNetwork/examples/alice_q_network.py: Simple main sending a message to Bob
- QNetwork/examples/bob_q_network.py: Simple receiving a message from Alice

- QNetwork/qkd/bb84_qkd.py: Contains the implementation details of the BB84 protocol and implementations for sender and
                          receiver nodes
- QNetwork/qkd/diqkd.py: Contains the implementation details of the DIQKD protocol and implementations for sender and
                       receiver nodes. Currently, it is almost finished, but it couldn't be propely tested
- QNetwork/qkd/qkd.py: Contains shared implementations which can be used by different QKD protocols
- QNetwork/q_network_channels.py: Contains implementations to send data strings via quantum or classical channels
- QNetwork/q_network_impl.py: Contains the implementation of the context manger used for secure quantum communication
- QNetwork/q_network_config.py: Contains a factory that loads the right configuration specified by q_network.cfg
- QNetwork/q_network.cfg: Contains the configuration of the secure quantum communication
- QNetwork/q_network.py: Contains the implementation of the open_channel function used for secure communication
- QNetwork/tests/*: Contains unit tests suits for the projects implementations
- QNetwork/run_submission.sh: Run the submission
- QNetwork/run_exercise.sh: Run the exercise
