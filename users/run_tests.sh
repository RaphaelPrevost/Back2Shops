#! /bin/bash

function get_pid() {
  PID=$(ps aux | grep 'python server.py' | grep -v grep | awk '{print $2}')
}

get_pid
if [ "$PID" != "" ]; then
    echo "Please stop the running server (pid: $PID) first !!"
    exit 1
fi

function waiting()
{
    sec=$1
    msg=$2
    while [ $sec -gt 0 ]
    do
      sec=`expr $sec - 1`
      echo $msg $sec
      sleep 1
    done
}

bash start_redis.sh --test
waiting 3 'Waiting for redis server ...'

python server.py --test > /dev/null 2>&1 &
waiting 3 'Waiting for user server loading data ...'

python -m unittest discover -s tests -p test_*.py -v

get_pid && kill $PID
