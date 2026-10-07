#!/bin/bash
# Minimize any AI2-THOR window every 3s. Needs one-time Accessibility grant.
while true; do
  osascript -e '
    tell application "System Events"
      repeat with p in (every process whose name contains "thor" or name contains "AI2")
        try
          set value of attribute "AXMinimized" of every window of p to true
        end try
      end repeat
    end tell' 2>/dev/null
  sleep 3
done
