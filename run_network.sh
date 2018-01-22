#!/usr/bin/env bash

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python examples/alice_diqkd.py &
python examples/bob_diqkd.py &