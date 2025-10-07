#!/bin/bash
echo "Text: "
read TEXT
echo "Lang (en/th): "
read LANG

JOB=$(curl -s -X POST http://192.168.1.59:4187/api/v1/speak \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"$TEXT\",\"lang\":\"$LANG\",\"mode\":\"robot_only\"}" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

echo "Job ID: $JOB"
echo "Waiting..."

while true; do
  sleep 3
  STATUS=$(curl -s http://192.168.1.59:4187/api/v1/jobs/$JOB | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    echo "Done! Download: http://192.168.1.59:4187/api/v1/jobs/$JOB/result"
    break
  fi
done
