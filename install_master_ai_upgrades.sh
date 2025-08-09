# Step 1: Navigate to automation directory
cd ~/automation
# Step 2: Create watchdog script to shut down when idle
echo '#!/bin/bash
MAX_IDLE_MINUTES=15
IDLE_CHECK_INTERVAL=60
while true; do
  LAST_CMD_TIME=$(stat -c %Y ~/automation/logs/last_command.txt)
  NOW=$(date +%s)
  IDLE_TIME=$(( (NOW - LAST_CMD_TIME) / 60 ))
  if (( IDLE_TIME >= MAX_IDLE_MINUTES )); then
    echo "🛌 Master-AI idle for $IDLE_TIME mins, shutting down..."
    sudo shutdown -h now
  fi
  sleep $IDLE_CHECK_INTERVAL
done' > watchdog.sh
# Step 3: Make watchdog executable
chmod +x watchdog.sh
# Step 4: (Optional) Run watchdog in background
./watchdog.sh &
# Step 5: Download all AI-enhancing Python/logic files from predefined repository or input
# For now, these need to be manually added or use nano to create and paste the contents into:
# - log_thought_snippet.txt
# - inject_listener_snippet.txt
# - update_file_snippet.txt
# - enable_self_editing.py
# Example for creating enable_self_editing.py
nano enable_self_editing.py
# Then paste in the contents provided earlier