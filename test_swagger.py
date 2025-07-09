#!/usr/bin/env python3
"""
Test script to verify Swagger docs accessibility
"""

import requests
import sys
import time

def test_swagger_endpoints(base_url="http://localhost:8000"):
    """Test if Swagger endpoints are accessible"""
    
    endpoints = [
        "/docs",
        "/redoc", 
        "/openapi.json"
    ]
    
    print(f"🔍 Testing Swagger endpoints at {base_url}")
    print("=" * 50)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - Status: {response.status_code}")
                if endpoint == "/openapi.json":
                    # Check if it's valid JSON
                    try:
                        response.json()
                        print("   📄 Valid JSON response")
                    except:
                        print("   ❌ Invalid JSON response")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection refused (server not running?)")
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint} - Timeout")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
        
        print()
    
    print("=" * 50)
    print("🎯 Test completed!")

if __name__ == "__main__":
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_swagger_endpoints(base_url) 