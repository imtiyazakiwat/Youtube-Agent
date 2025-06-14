#!/bin/bash

# Instructions to make the script executable:
# 1. cd "/Users/imtiyazakiwat/Documents/R&D/Youtube-Agent"
# 2. chmod +x test_curl.sh

# Check if server is running
nc -z localhost 8000 || {
    echo "Error: Flask server is not running. Please start it first with:"
    echo "python script-to-srt.py"
    exit 1
}

echo "Testing OPTIONS request..."
curl -v -X OPTIONS \
  -H "Origin: http://localhost" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/generate-srt

echo "Testing POST request with valid data..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Origin: http://localhost" \
  --retry 3 \
  -d @- http://localhost:8000/generate-srt << 'EOF'
{
  "script": "This is a test script. It has multiple sentences. Testing SRT generation.",
  "filename": "test"
}
EOF

echo -e "\n\nTesting with invalid method (GET)..."
curl -X GET http://localhost:8000/generate-srt

echo -e "\n\nTesting with invalid content type..."
curl -X POST \
  -H "Content-Type: text/plain" \
  -d '{"script":"Test", "filename":"test"}' \
  http://localhost:8000/generate-srt
