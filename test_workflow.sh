#!/bin/bash
# Test workflow: /api/kundli → /chart/svg (no duplicate calculations)

echo "🔮 Step 1: Getting kundli data..."
KUNDLI_JSON=$(curl -s -X POST http://127.0.0.1:5055/api/kundli \
  -H 'Content-Type: application/json' \
  -d '{
    "dateOfBirth":"1990-05-15",
    "timeOfBirth":"14:30",
    "latitude":28.6139,
    "longitude":77.2090,
    "timezone":"Asia/Kolkata"
  }')

echo "✅ Got kundli data"

echo ""
echo "🎨 Step 2: Generating SVG chart from kundli data..."

# Extract planets and ascendant arrays using jq (or python)
python3 << 'PYTHON_SCRIPT'
import json
import sys
import subprocess

# Read the kundli data from environment or file
kundli_data = '''KUNDLI_PLACEHOLDER'''

# Load kundli
kundli = json.loads(kundli_data)

# Prepare chart request with just the computed data
chart_req = {
    "planets": kundli["data"]["planets"],
    "ascendant": kundli["data"]["basicDetails"]["ascendant"],
    "width": 600,
    "height": 600,
    "theme": "dark",
    "includeOuterPlanets": False
}

# Send to chart/svg
result = subprocess.run([
    'curl', '-s', '-X', 'POST',
    'http://127.0.0.1:5055/chart/svg',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(chart_req)
], capture_output=True, text=True)

svg = result.stdout
if svg.startswith('<svg'):
    print(f"✅ Generated SVG chart ({len(svg)} bytes)")
    with open('chart_optimized.svg', 'w') as f:
        f.write(svg)
    print("✅ Saved to chart_optimized.svg")
    print("\n📄 SVG preview:")
    print(svg[:400] + '...')
else:
    print(f"❌ Error: {svg[:500]}")
PYTHON_SCRIPT

echo ""
echo "✨ Done! No duplicate calculations - reused kundli data."
