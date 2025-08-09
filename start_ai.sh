#!/usr/bin/env bash
cd ~/automation || exit 1
source venv/bin/activate

echo "Projects:"
select P in $(ls projects); do
  [ -n "$P" ] && break
done
[ -z "$P" ] && echo "No project." && exit 1

PORT=55555
tmux kill-session -t ai 2>/dev/null
tmux new-session  -d -s ai \
  "PROJECT=$P PORT=$PORT python3 master_ai.py"
sleep 1
tmux split-window -h -t ai \
  "~/automation/chat_client.sh $PORT"
tmux select-pane -t ai:0.1
tmux attach -t ai
