#! /bin/bash

function get_pid() {
  PID=$(ps aux | grep 'python server.py' | grep -v grep | awk '{print $2}')
}

get_pid
if [ "$PID" != "" ]; then
    echo "Please stop the running server (pid: $PID) first !!"
    exit 1
fi

if [ ! -f 'hmac.pem' ]; then
    python scripts/gen_hmac_key.py
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

function product_running_confirm()
{
    echo "Are you sure you want to run test on product? Running test will insert data into database"
    read -p "yes / no ?" ans
    if [ "$ans" == "yes" ]
    then
        echo "start to running test ..."
    else
        exit 1
    fi
}

function user_check()
{
    if [ "$(whoami)" == "root" ]; then
        product_running_confirm
    fi
}

user_check

bash start_redis.sh --test &
waiting 3 'Waiting for redis server ...'

python server.py --test > /dev/null 2>&1 &
waiting 3 'Waiting for user server loading data ...'

if [ -z $1 ]; then
    python -m unittest discover -s tests -p test_*.py -v
else
    python -m unittest discover -s tests -p $1 -v
fi

get_pid && kill $PID
redis-cli -p 6279 shutdown
svn revert central-redis-6279.rdb
