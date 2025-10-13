#!/usr/bin/env python3
"""Simple script to extract planets and ascendant from kundli JSON and prepare chart request."""
import json
import sys

with open('/tmp/kundli_data.json', 'r') as f:
    kundli = json.load(f)

chart_request = {
    "planets": kundli["planets"],
    "ascendant": kundli["ascendant"],
    "width": 600,
    "theme": "light",
    "includeOuterPlanets": True
}

print(json.dumps(chart_request))
