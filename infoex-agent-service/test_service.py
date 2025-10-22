#!/usr/bin/env python3
"""Simple test script for the InfoEx Claude Agent Service"""

import requests
import json
import sys
from datetime import datetime

# Service URL (adjust if needed)
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Service status: {data['status']}")
        print(f"   Checks: {data['checks']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        sys.exit(1)

def test_conversation():
    """Test a simple conversation flow"""
    session_id = f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Fixed values for testing
    fixed_values = {
        "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
        "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
        "zone_name": "Whistler Blackcomb",
        "date": datetime.now().strftime("%m/%d/%Y"),
        "guide_names": ["Test Guide"]
    }
    
    print(f"\n💬 Starting conversation (session: {session_id})...")
    
    # First message
    message1 = "I observed a size 2 storm slab avalanche today"
    print(f"\n👤 User: {message1}")
    
    response = requests.post(
        f"{BASE_URL}/api/process-report",
        json={
            "session_id": session_id,
            "message": message1,
            "fixed_values": fixed_values
        }
    )
    
    if response.status_code == 200:
        claude_response = response.json()["response"]
        print(f"🤖 Claude: {claude_response}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return
    
    # Second message with more details
    message2 = "It was on a north aspect at 1800m, triggered by a skier"
    print(f"\n👤 User: {message2}")
    
    response = requests.post(
        f"{BASE_URL}/api/process-report",
        json={
            "session_id": session_id,
            "message": message2,
            "fixed_values": fixed_values
        }
    )
    
    if response.status_code == 200:
        claude_response = response.json()["response"]
        print(f"🤖 Claude: {claude_response}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return
    
    # Check session status
    print(f"\n📊 Checking session status...")
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/status")
    
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Session status: {status['status']}")
        print(f"   Ready payloads: {status['payloads_ready']}")
        print(f"   Missing data: {status['missing_data']}")
        print(f"   Conversation length: {status['conversation_length']}")
    else:
        print(f"❌ Status check failed: {response.status_code}")

def test_locations():
    """Test locations endpoint"""
    print("\n📍 Testing locations endpoint...")
    response = requests.get(f"{BASE_URL}/api/locations")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} locations")
        if data['locations']:
            print(f"   First location: {data['locations'][0].get('name', 'Unknown')}")
    else:
        print(f"❌ Locations request failed: {response.status_code}")

def main():
    """Run all tests"""
    print("🧪 Testing InfoEx Claude Agent Service")
    print("=" * 50)
    
    try:
        test_health()
        test_conversation()
        test_locations()
        
        print("\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to service. Is it running?")
        print("   Start with: docker-compose up")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
