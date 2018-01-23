#!/usr/bin/env bash

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python examples/alice_q_network.py &
python examples/bob_q_network.py &