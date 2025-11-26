#!/bin/bash

# Shoe Price Tracker - Daily Check Runner
# This script runs the price tracker and logs the output

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the tracker and append output to daily log
LOGFILE="logs/tracker_$(date +%Y%m%d).log"

echo "========================================" >> "$LOGFILE"
echo "Run started at: $(date)" >> "$LOGFILE"
echo "========================================" >> "$LOGFILE"

python3.12 shoe_price_tracker.py >> "$LOGFILE" 2>&1

echo "" >> "$LOGFILE"
echo "Run completed at: $(date)" >> "$LOGFILE"
echo "" >> "$LOGFILE"

# Keep only last 30 days of logs
find logs -name "tracker_*.log" -mtime +30 -delete
