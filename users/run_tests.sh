#! /bin/bash

function get_pid() {
  PID=$(ps aux | grep 'python server.py' | grep -v grep | awk '{print $2}')
}

get_pid
if [ "$PID" != "" ]; then
    echo "Please stop the running server (pid: $PID) first !!"
    exit 1
fi

python server.py > /dev/null 2>&1 &
python -m unittest discover -s tests -p test_*.py -v

get_pid && kill $PID
