#!/usr/bin/env python3
"""
Test if InfoEx accepts arrays of avalanche observations
Final version - using working configuration
"""

import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

def test_array_support():
    """Test if InfoEx accepts arrays of avalanche observations"""
    # Load environment
    load_dotenv()
    
    environment = os.getenv('ENVIRONMENT', 'staging').lower()
    
    if environment == 'staging':
        api_key = os.getenv('STAGING_API_KEY')
        operation_uuid = os.getenv('STAGING_OPERATION_UUID')
        base_url = os.getenv('STAGING_URL')
    else:
        api_key = os.getenv('PRODUCTION_API_KEY')
        operation_uuid = os.getenv('PRODUCTION_OPERATION_UUID')
        base_url = os.getenv('PRODUCTION_URL')
    
    print("🏔️ InfoEx Avalanche Array Support Test")
    print("=" * 60)
    print(f"🔧 Environment: {environment.upper()}")
    print(f"🔧 API Key: {api_key[:8]}...")
    
    # Get location UUID from the working payload
    with open('infoex-api-payloads/avalanche_observation.json', 'r') as f:
        data = json.load(f)
        template = data['AURORA_IDEAL_PAYLOAD']
        location_uuid = template['locationUUIDs'][0]
    
    url = f"{base_url}/observation/avalanche"
    headers = {
        'api_key': api_key,
        'operation': operation_uuid,
        'Content-Type': 'application/json'
    }
    
    # Test 1: Single observation (should work)
    print("\n🧪 TEST 1: Single Avalanche Observation")
    print("-" * 50)
    
    single_obs = {
        "obDate": datetime.now().strftime("%m/%d/%Y"),
        "obTime": "10:00",
        "num": "1",
        "trigger": "Sa",
        "character": "STORM_SLAB",
        "size": "2",
        "locationUUIDs": [location_uuid],
        "operationUUID": operation_uuid,
        "state": "IN_REVIEW"
    }
    
    response = requests.post(url, headers=headers, json=single_obs, timeout=30)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Single observation: SUCCESS")
        data = response.json()
        print(f"UUID: {data.get('uuid')}")
    else:
        print("❌ Single observation: FAILED")
        print(f"Error: {response.text[:200]}")
    
    # Test 2: Array of observations
    print("\n🧪 TEST 2: Array of Avalanche Observations")
    print("-" * 50)
    
    array_obs = [
        {
            "obDate": datetime.now().strftime("%m/%d/%Y"),
            "obTime": "09:00",
            "num": "1",
            "trigger": "Na",
            "character": "STORM_SLAB",
            "size": "2.5",
            "locationUUIDs": [location_uuid],
            "operationUUID": operation_uuid,
            "state": "IN_REVIEW"
        },
        {
            "obDate": datetime.now().strftime("%m/%d/%Y"),
            "obTime": "11:00",
            "num": "1",
            "trigger": "Sa",
            "character": "WIND_SLAB",
            "size": "2",
            "locationUUIDs": [location_uuid],
            "operationUUID": operation_uuid,
            "state": "IN_REVIEW"
        }
    ]
    
    response = requests.post(url, headers=headers, json=array_obs, timeout=30)
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Array submission: SUCCESS")
        print("🎉 InfoEx ACCEPTS arrays!")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:300]}...")
    else:
        print("❌ Array submission: FAILED") 
        print("InfoEx does NOT accept arrays")
        error = response.text[:300]
        if "Expected BEGIN_OBJECT but was BEGIN_ARRAY" in error:
            print("Error confirms: API expects single object, not array")
        print(f"Error: {error}")
    
    # Conclusion
    print("\n" + "=" * 60)
    print("📊 CONCLUSION")
    print("=" * 60)
    
    if response.status_code != 200:
        print("❌ InfoEx requires individual avalanche submissions")
        print("\n📐 Architecture Decision:")
        print("  - Store avalanches as array in JSONB field (single row)")
        print("  - InfoEx service iterates and submits each separately")
        print("  - Each avalanche gets its own UUID from InfoEx")
    else:
        print("✅ InfoEx accepts arrays of avalanches")
        print("  - Can submit multiple at once")

if __name__ == "__main__":
    test_array_support()
