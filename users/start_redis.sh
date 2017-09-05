#! /bin/bash

PASSWORD="setpassforsafety"

if [ "$1" == "--test" ]; then
  echo "Start redis server for test..."
  PORT=6279
  CONF="central-redis-test.conf"
else
  echo "Start redis server ..."
  PORT=6379
  CONF="central-redis.conf"
fi

echo "Shutting Down central-redis"
redis-cli -p $PORT -a $PASSWORD shutdown
echo "Running central-redis"
redis-server $CONF
echo "DONE"

