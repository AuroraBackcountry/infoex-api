#!/usr/bin/env python3
"""
Test script for InfoEx Persistent Weak Layer (PWL) submission
Two-step process:
1. GET /pwl/operation/{operationUUID} - Check existing PWLs
2. POST /pwl - Create new PWL (only if doesn't exist)
"""

import json
import requests
import os
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

def check_existing_pwls(env_vars):
    """Step 1: Check for existing PWLs"""
    url = f"{env_vars['base_url']}/pwl/operation?operationUUID={env_vars['operation_uuid']}"
    headers = {
        'api_key': env_vars['api_key'],
        'operation': env_vars['operation_uuid'],
        'Content-Type': 'application/json'
    }
    
    print(f"\n📋 Step 1: Checking Existing PWLs")
    print(f"🚀 URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            pwls = response.json()
            print(f"✅ Found {len(pwls)} existing PWL(s)")
            
            if pwls:
                print("\n📋 Existing PWLs:")
                for i, pwl in enumerate(pwls, 1):
                    print(f"   {i}. {pwl.get('name')} (UUID: {pwl.get('uuid', 'N/A')[:8]}...)")
                    print(f"      Created: {pwl.get('creationDate')}")
                    print(f"      Color: {pwl.get('color')}")
                    print(f"      Assessments: {len(pwl.get('assessment', []))}")
            else:
                print("   No PWLs found for this operation")
            
            return pwls
        else:
            print(f"⚠️ Could not retrieve PWLs: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return []

def create_pwl(env_vars):
    """Step 2: Create new PWL"""
    url = f"{env_vars['base_url']}/pwl"
    headers = {
        'api_key': env_vars['api_key'],
        'operation': env_vars['operation_uuid'],
        'Content-Type': 'application/json'
    }
    
    try:
        with open('infoex-api-payloads/pwl_persistent_weak_layer.json', 'r') as f:
            data = json.load(f)
            payload = data['AURORA_IDEAL_PAYLOAD']
    except FileNotFoundError:
        print("❌ Error: pwl_persistent_weak_layer.json not found in infoex-api-payloads/")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
        return False
    except KeyError:
        print("❌ Error: AURORA_IDEAL_PAYLOAD not found in JSON file")
        return False
    
    print(f"\n🧪 Step 2: Creating New PWL")
    print(f"🚀 URL: {url}")
    print(f"📛 Name: {payload.get('name')}")
    print(f"📅 Creation Date: {payload.get('creationDate')}")
    print(f"🎨 Color: {payload.get('color')}")
    if payload.get('assessment'):
        print(f"🔬 Crystal Type: {payload.get('assessment', [{}])[0].get('crystalType')}")
        print(f"📏 Depth Range: {payload.get('assessment', [{}])[0].get('depthMin')}-{payload.get('assessment', [{}])[0].get('depthMax')}cm")
        print(f"📊 Status: {payload.get('assessment', [{}])[0].get('status')}")
    
    print(f"\n📋 Full Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 SUCCESS: PWL created!")
            try:
                response_data = response.json()
                print("📋 Response Data:")
                print(json.dumps(response_data, indent=2))
                
                if 'uuid' in response_data:
                    print(f"\n✅ PWL UUID: {response_data['uuid']}")
                if 'assessment' in response_data and response_data['assessment']:
                    print(f"✅ Assessment Count: {len(response_data['assessment'])}")
                    
            except json.JSONDecodeError:
                print("📋 Response Text:")
                print(response.text)
            return True
        else:
            print("❌ Submission failed")
            print(f"📋 Response: {response.text}")
            
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
    print("❄️ InfoEx Persistent Weak Layer (PWL) Test")
    print("=" * 60)
    
    try:
        env_vars = load_environment()
        
        # Step 1: Check existing PWLs
        existing_pwls = check_existing_pwls(env_vars)
        
        # Step 2: Create new PWL
        print("\n" + "=" * 60)
        print("📝 Proceeding with PWL creation test...")
        
        success = create_pwl(env_vars)
        
        if success:
            print("\n🎉 PWL creation successful!")
            print("✅ Ready to review on InfoEx UI")
            print("\n⚠️ REMINDER: Only create 2-3 PWLs per season!")
            print("⚠️ Add assessments to existing PWLs instead of creating duplicates")
        else:
            print("\n🔧 Need to debug PWL format")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
