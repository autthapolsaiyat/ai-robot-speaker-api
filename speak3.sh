#!/bin/bash
echo "Text: "
read TEXT

JOB=$(curl -s -X POST http://192.168.1.59:4187/api/v1/speak \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"$TEXT\",\"lang\":\"en\",\"mode\":\"robot_only\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

echo "Job: $JOB - Waiting..."
sleep 8

curl -s http://192.168.1.59:4187/api/v1/jobs/$JOB/result -o output_$JOB.mp4
echo "Saved: output_$JOB.mp4"
open output_$JOB.mp4 2>/dev/null || echo "Video ready at: $(pwd)/output_$JOB.mp4"
