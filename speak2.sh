#!/bin/bash
echo "Text: "
read TEXT

echo "Submitting..."
RESPONSE=$(curl -s -X POST http://192.168.1.59:4187/api/v1/speak \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"$TEXT\",\"lang\":\"en\",\"mode\":\"robot_only\"}")

echo "Response: $RESPONSE"

JOB=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB"
echo "Video will be at: http://192.168.1.59:4187/api/v1/jobs/$JOB/result"
