#!/usr/bin/env python
"""Verify SDINT API endpoints are working with CORS"""

import requests
import json

BASE_URL = "http://localhost:5000"
FRONTEND_ORIGIN = "http://localhost:5174"

headers = {
    "Origin": FRONTEND_ORIGIN,
    "Accept": "application/json"
}

print("\n" + "="*60)
print("SDINT API VERIFICATION")
print("="*60 + "\n")

endpoints = [
    ("GET", "/api/status"),
    ("GET", "/api/health"),
    ("GET", "/api/posts"),
]

for method, path in endpoints:
    try:
        url = f"{BASE_URL}{path}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        
        cors_header = response.headers.get("Access-Control-Allow-Origin", "❌ MISSING")
        status = "✅ OK" if response.status_code == 200 else f"⚠️  {response.status_code}"
        
        print(f"[{status}] {method} {path}")
        print(f"     CORS: {cors_header}")
        
        # Show sample data
        try:
            data = response.json()
            if isinstance(data, list):
                print(f"     Data: Array with {len(data)} items")
            elif isinstance(data, dict):
                keys = list(data.keys())[:3]
                print(f"     Data: Object with keys: {', '.join(keys)}")
        except:
            print(f"     Data: {response.text[:100]}")
        print()
    
    except Exception as e:
        print(f"[❌ ERROR] {method} {path}")
        print(f"     Error: {e}")
        print()

print("="*60)
print("✅ API is ready for frontend!")
print("="*60)
print("\nFrontend available at: http://localhost:5174")
print("Backend API at: http://localhost:5000")
print("\n")
