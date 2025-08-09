#!/bin/bash
# Simple chat client to send messages to Master-AI via socket

PORT=55555
MESSAGE="$*"

if [ -z "$MESSAGE" ]; then
  echo "Usage: $0 your message here"
  exit 1
fi

exec 3<>/dev/tcp/127.0.0.1/$PORT
if [ $? -ne 0 ]; then
  echo "❌ Cannot connect to Master-AI on port $PORT"
  exit 2
fi

echo "$MESSAGE" >&3
cat <&3
exec 3>&-
exec 3<&-
