#!/bin/bash

source ./dbconf.sh

if [ "$#" = "1" ]; then
    DBNAME=$1
    dropdb $DBNAME -U $DBUSER && echo 'DB '$DBNAME' dropped'
fi

# Create database
createdb $DBNAME -U $DBUSER
echo 'Database '$DBNAME' created'

echo > "$SETUPDB_LOG"

# Create schema
$DBSHELL -v 'ON_ERROR_STOP=on' -d $DBNAME -U $DBUSER -f ./schema.sql > "$SETUPDB_LOG"
echo "Database creation done."

# initialize data
$DBSHELL -v 'ON_ERROR_STOP=on' -d $DBNAME -U $DBUSER -f ./data.sql > "$SETUPDB_LOG"
echo "Data loaded done."

