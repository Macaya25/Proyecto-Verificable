#!/usr/bin/env bash

TRY_LOOP="20"

: "${MYSQL_HOST:="db"}"
: "${MYSQL_PORT:="3306"}"

wait_for_port() {
  local name="$1" host="$2" port="$3"
  local j=0
  while ! nc -z "$host" "$port" >/dev/null 2>&1 < /dev/null; do
    j=$((j+1))
    if [ $j -ge $TRY_LOOP ]; then
      echo >&2 "$(date) - $host:$port still not reachable, giving up"
      exit 1
    fi
    echo "$(date) - waiting for $name... $j/$TRY_LOOP"
    sleep 5
  done
}

echo "$MYSQL_HOST" "$MYSQL_PORT"
wait_for_port "MySQL" "$MYSQL_HOST" "$MYSQL_PORT"

echo "Starting Software_verificable app..."

python seed.py

python app.py
