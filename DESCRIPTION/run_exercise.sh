#!/usr/bin/env bash

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python ../QNetwork/examples/alice_exercise.py &
python ../QNetwork/examples/bob_exercise.py &
python ../QNetwork/examples/eve_exercise.py &
