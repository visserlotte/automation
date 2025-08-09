#!/bin/bash
ENV_FILE=~/automation/.env

# Auto-set default fallback values if missing
declare -A defaults=(
  ["OPENAI_API_KEY"]="your-api-key"
  ["GMAIL_ADDRESS"]="your-email@gmail.com"
  ["GMAIL_PASSWORD"]="your-password"
  ["REPLY_TO"]="your-email@gmail.com"
  ["PROJECT"]="default"
  ["PORT"]="55555"
)

for key in "${!defaults[@]}"; do
  if grep -q "^$key=" "$ENV_FILE"; then
    echo "✅ $key already set"
  else
    echo "$key=${defaults[$key]}" >> "$ENV_FILE"
    echo "➕ Added missing $key"
  fi
done

echo "✅ .env update complete."
