#!/usr/bin/env python3
"""
Test InfoEx Avalanche Summary Endpoint
"""

import os
import json
import requests
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    
    environment = os.getenv('ENVIRONMENT', 'staging').lower()
    
    if environment == 'staging':
        api_key = os.getenv('STAGING_API_KEY')
        operation_uuid = os.getenv('STAGING_OPERATION_UUID')
        base_url = os.getenv('STAGING_URL')
        env_name = "STAGING"
    elif environment == 'production':
        api_key = os.getenv('PRODUCTION_API_KEY')
        operation_uuid = os.getenv('PRODUCTION_OPERATION_UUID')
        base_url = os.getenv('PRODUCTION_URL')
        env_name = "PRODUCTION"
    else:
        raise ValueError(f"Invalid ENVIRONMENT value: {environment}")
    
    print(f"🔧 Environment: {env_name}")
    print(f"🔧 Using API Key: {api_key[:8]}...")
    print(f"🔧 Using Operation: {operation_uuid[:8]}...")
    print(f"🔧 Using Base URL: {base_url}")
    
    return {
        'api_key': api_key,
        'operation_uuid': operation_uuid,
        'base_url': base_url,
        'environment': environment
    }

def test_avalanche_summary(env_vars):
    """Test avalanche summary submission"""
    url = f"{env_vars['base_url']}/observation/avalancheSummary"
    headers = {
        'api_key': env_vars['api_key'],
        'operation': env_vars['operation_uuid'],
        'Content-Type': 'application/json'
    }
    
    try:
        with open('infoex-api-payloads/avalanche_summary.json', 'r') as f:
            data = json.load(f)
            # Extract the Aurora ideal payload
            payload = data['AURORA_IDEAL_PAYLOAD']
    except FileNotFoundError:
        print("❌ Error: avalanche_summary.json not found in markdown-examples/infoex-api-payloads/")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
        return False
    except KeyError:
        print("❌ Error: AURORA_IDEAL_PAYLOAD not found in JSON file")
        return False
    
    print(f"\n🧪 Testing Avalanche Summary Submission")
    print(f"🚀 URL: {url}")
    print(f"📅 Date: {payload.get('obDate')}")
    print(f"📊 Avalanches Observed: {payload.get('avalanchesObserved')}")
    print(f"📏 Area Observed: {payload.get('percentAreaObserved')}%")
    print(f"💥 Explosive Records: {len(payload.get('explosivesRecords', []))} entries")
    print(f"📍 Location: Whistler/Blackcomb")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS: Avalanche summary submitted!")
            try:
                response_data = response.json()
                print("📋 Response Data:")
                print(json.dumps(response_data, indent=2))
                
                # Extract UUID if available
                if 'uuid' in response_data:
                    print(f"\n✅ Summary UUID: {response_data['uuid']}")
                    
            except json.JSONDecodeError:
                print("📋 Response Text:")
                print(response.text)
            return True
        else:
            print("❌ Submission failed")
            print(f"📋 Response: {response.text}")
            
            # Parse validation errors
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    print("\n📋 Validation Errors:")
                    for error in error_data['errors']:
                        field = error.get('field', 'Unknown')
                        details = error.get('errorDetails', error.get('error', 'Unknown error'))
                        print(f"   ❌ {field}: {details}")
                elif 'message' in error_data:
                    print(f"\n📋 Error Message: {error_data['message']}")
            except json.JSONDecodeError:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("=" * 60)
    print("📊 InfoEx Avalanche Summary Test")
    print("=" * 60)
    
    try:
        env_vars = load_environment()
        success = test_avalanche_summary(env_vars)
        
        if success:
            print("\n🎉 Avalanche summary submission successful!")
            print("✅ Ready to integrate into Aurora workflow system")
        else:
            print("\n🔧 Need to debug avalanche summary format")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
