#!/usr/bin/env python3
"""
Test workflow for chart SVG generation:
1. Call /api/kundli to get computed planet and house data
2. Pass that data to /chart/svg to generate SVG image
"""
import subprocess
import json

BASE_URL = "http://127.0.0.1:5055"

# Step 1: Get kundli data (planet positions, houses, ascendant)
kundli_request = {
    "dateOfBirth": "1990-05-15",
    "timeOfBirth": "14:30",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "timezone": "Asia/Kolkata",
    "houseSystem": "W",
    "nodeMode": "mean"
}

print("📊 Step 1: Fetching kundli data from /api/kundli...")
result = subprocess.run([
    'curl', '-s', '-X', 'POST',
    f'{BASE_URL}/api/kundli',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(kundli_request)
], capture_output=True, text=True)

kundli_response = json.loads(result.stdout)
kundli_data = kundli_response['data']

print(f"✅ Got {len(kundli_data['planets'])} planets")
print(f"✅ Ascendant: {kundli_data['basicDetails']['ascendant']['sign']} at {kundli_data['basicDetails']['ascendant']['degree']:.2f}°")

# Step 2: Generate SVG chart from the computed data
chart_request = {
    "planets": kundli_data["planets"],
    "ascendant": kundli_data["basicDetails"]["ascendant"],
    "width": 600,
    "height": 600,
    "theme": "dark",
    "includeOuterPlanets": False
}

print("\n🎨 Step 2: Generating SVG chart from /chart/svg...")
result2 = subprocess.run([
    'curl', '-s', '-X', 'POST',
    f'{BASE_URL}/chart/svg',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(chart_request)
], capture_output=True, text=True)

svg_content = result2.stdout

if svg_content.startswith('<?xml') or svg_content.startswith('<svg'):
    print(f"✅ Generated SVG ({len(svg_content)} bytes)")
    
    # Save to file
    output_file = "chart_optimized.svg"
    with open(output_file, "w") as f:
        f.write(svg_content)
    print(f"✅ Saved to {output_file}")
    
    # Show first few lines
    print("\n📄 SVG preview:")
    lines = svg_content.split('\n')
    for i, line in enumerate(lines[:8]):
        print(f"  {line[:100]}{'...' if len(line) > 100 else ''}")
else:
    print(f"❌ Error response:")
    print(svg_content[:500])

print("\n✨ Workflow complete! No duplicate calculations.")
print("💡 Frontend should: /api/kundli → store data → /chart/svg when needed")
