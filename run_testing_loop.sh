#!/bin/bash
# Simple script to run automated_testing.py every 2 minutes

echo "Starting automated testing loop at $(date)"
echo "Press Ctrl+C to stop the loop"
echo "--------------------------------------------"

while true; do
  echo "Running automated_testing.py at $(date)"
  python /home/ks/Desktop/project/test_llm/automated_testing.py
  
  echo "--------------------------------------------"
  echo "Waiting 2 minutes before next run..."
  echo "Next run will be at $(date -d '2 minutes')"
  echo "--------------------------------------------"
  
  sleep 120  # Sleep for 2 minutes
done
