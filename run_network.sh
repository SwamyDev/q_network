#!/usr/bin/env bash

ps aux | grep python | grep Test | awk {'print $2'} | xargs kill -9

python alice.py &
python bob.py &
python eve.py &