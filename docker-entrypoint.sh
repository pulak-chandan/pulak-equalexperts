#!/bin/sh

set -u

if [ ! -f /data/warehouse.db ]; then
    cp /app/warehouse.db /data/warehouse.db
fi

cp /data/warehouse.db /app/warehouse.db

exercise "$@"
status=$?

if [ -f /app/warehouse.db ]; then
    cp /app/warehouse.db /data/warehouse.db
fi

exit "$status"