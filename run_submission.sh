#!/usr/bin/env bash

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python examples/alice_exercise.py &
python examples/bob_exercise.py &
python examples/eve_exercise.py &