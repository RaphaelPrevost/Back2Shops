#! /bin/bash

PORT=6379

echo "Shutting Down central-redis"
redis-cli -p $PORT shutdown
echo "Running central-redis"
redis-server central-redis.conf
echo "DONE"

