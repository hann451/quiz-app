#!/bin/bash
set -u
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=/bin/true
cd /home/miyamoto/myapp || exit 1
LOG=/home/miyamoto/myapp/deploy.log
BEFORE=$(git rev-parse HEAD)
timeout 60 git fetch origin main --quiet || { echo "$(date -Is) FETCH FAILED" >> "$LOG"; exit 1; }
if ! git merge --ff-only origin/main --quiet; then
  echo "$(date -Is) FF-ONLY FAILED (local changes or diverged history)" >> "$LOG"
  exit 1
fi
AFTER=$(git rev-parse HEAD)
[ "$BEFORE" != "$AFTER" ] && echo "$(date -Is) UPDATED $BEFORE -> $AFTER" >> "$LOG"
exit 0