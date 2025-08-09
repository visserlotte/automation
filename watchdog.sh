#!/bin/bash
MAX_IDLE_MINUTES=15
IDLE_CHECK_INTERVAL=60

while true; do
  LAST_CMD_TIME=$(stat -c %Y ~/automation/logs/last_command.txt)
  NOW=$(date +%s)
  IDLE_TIME=$(( (NOW - LAST_CMD_TIME) / 60 ))

  if (( IDLE_TIME >= MAX_IDLE_MINUTES )); then
    echo "🛌 Idle for $IDLE_TIME mins. (Would shut down here)"
    # Uncomment below line to enable shutdown
    # sudo shutdown -h now
    break
  fi
  sleep $IDLE_CHECK_INTERVAL
done
