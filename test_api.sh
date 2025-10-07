#!/bin/bash
# Comprehensive API testing script
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="http://localhost:4187"

echo "=================================================="
echo "  AI Robot Speaker API - Test Suite"
echo "=================================================="
echo ""

# Test 1: Health Check
echo -e "${YELLOW}[1/7] Testing health endpoint...${NC}"
HEALTH=$(curl -s ${API_URL}/health)
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$HEALTH" | jq .
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "$HEALTH"
    exit 1
fi
echo ""

# Test 2: List Voice Presets
echo -e "${YELLOW}[2/7] Testing voice presets...${NC}"
VOICES=$(curl -s ${API_URL}/api/v1/voices)
echo "$VOICES" | jq .
if echo "$VOICES" | jq -e '.voices | length > 0' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Voice presets loaded${NC}"
else
    echo -e "${RED}✗ No voice presets found${NC}"
    exit 1
fi
echo ""

# Test 3: List Face Presets
echo -e "${YELLOW}[3/7] Testing face presets...${NC}"
FACES=$(curl -s ${API_URL}/api/v1/face/presets)
echo "$FACES" | jq .
if echo "$FACES" | jq -e '.presets | length > 0' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Face presets loaded${NC}"
else
    echo -e "${RED}✗ No face presets found${NC}"
    exit 1
fi
echo ""

# Test 4: Generate Face (optional if SDXL not available)
echo -e "${YELLOW}[4/7] Testing face generation (skipped if SDXL not available)...${NC}"
FACE_JOB=$(curl -s -X POST ${API_URL}/api/v1/face/generate \
  -H 'Content-Type: application/json' \
  -d '{"preset":"robot_mesh_hologram"}' 2>&1)

if echo "$FACE_JOB" | jq -e '.job_id' > /dev/null 2>&1; then
    FACE_JOB_ID=$(echo "$FACE_JOB" | jq -r '.job_id')
    echo -e "${GREEN}✓ Face generation job created: ${FACE_JOB_ID}${NC}"
    echo "$FACE_JOB" | jq .
else
    echo -e "${YELLOW}⚠ Face generation skipped (SDXL not available)${NC}"
fi
echo ""

# Test 5: Simple Speech Job
echo -e "${YELLOW}[5/7] Creating speech job...${NC}"
SPEECH_JOB=$(curl -s -X POST ${API_URL}/api/v1/speak \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "ทดสอบระบบพากย์เสียงอัตโนมัติ นี่คือการทดสอบความสามารถของระบบ",
    "lang": "th",
    "mode": "robot_only"
  }')

if echo "$SPEECH_JOB" | jq -e '.job_id' > /dev/null 2>&1; then
    JOB_ID=$(echo "$SPEECH_JOB" | jq -r '.job_id')
    echo -e "${GREEN}✓ Speech job created: ${JOB_ID}${NC}"
    echo "$SPEECH_JOB" | jq .
else
    echo -e "${RED}✗ Failed to create speech job${NC}"
    echo "$SPEECH_JOB"
    exit 1
fi
echo ""

# Test 6: Poll Job Status
echo -e "${YELLOW}[6/7] Polling job status...${NC}"
MAX_WAIT=300  # 5 minutes
WAIT_TIME=0
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    STATUS=$(curl -s ${API_URL}/api/v1/jobs/${JOB_ID})
    CURRENT_STATUS=$(echo "$STATUS" | jq -r '.status')
    PROGRESS=$(echo "$STATUS" | jq -r '.progress')
    
    echo -ne "\rStatus: ${CURRENT_STATUS} | Progress: ${PROGRESS}%"
    
    if [ "$CURRENT_STATUS" == "done" ]; then
        echo ""
        echo -e "${GREEN}✓ Job completed successfully${NC}"
        echo "$STATUS" | jq .
        break
    elif [ "$CURRENT_STATUS" == "error" ]; then
        echo ""
        echo -e "${RED}✗ Job failed${NC}"
        echo "$STATUS" | jq .
        exit 1
    fi
    
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}✗ Job timeout after ${MAX_WAIT} seconds${NC}"
    exit 1
fi
echo ""

# Test 7: Download Result
echo -e "${YELLOW}[7/7] Downloading result...${NC}"
OUTPUT_FILE="test_result_${JOB_ID}.mp4"
curl -s -o ${OUTPUT_FILE} ${API_URL}/api/v1/jobs/${JOB_ID}/result

if [ -f ${OUTPUT_FILE} ]; then
    FILE_SIZE=$(stat -f%z "${OUTPUT_FILE}" 2>/dev/null || stat -c%s "${OUTPUT_FILE}" 2>/dev/null)
    if [ "$FILE_SIZE" -gt 0 ]; then
        echo -e "${GREEN}✓ Result downloaded: ${OUTPUT_FILE} (${FILE_SIZE} bytes)${NC}"
    else
        echo -e "${RED}✗ Downloaded file is empty${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Failed to download result${NC}"
    exit 1
fi
echo ""

# Summary
echo "=================================================="
echo -e "${GREEN}  All tests passed! 🎉${NC}"
echo "=================================================="
echo ""
echo "Results:"
echo "  - Job ID: ${JOB_ID}"
echo "  - Output: ${OUTPUT_FILE}"
echo "  - Size: ${FILE_SIZE} bytes"
echo ""
echo "Play the result with:"
echo "  ffplay ${OUTPUT_FILE}"
echo "  # or"
echo "  vlc ${OUTPUT_FILE}"
echo ""
