#!/usr/bin/env python3
"""
Test HTTP endpoint with curl command
"""

import subprocess
import json

def test_endpoint():
    """Test the endpoint via HTTP"""
    
    try:
        # First, get a token
        login_cmd = [
            'curl', '-s', '-X', 'POST', 
            'http://localhost:8000/api/v1/auth/login',
            '-H', 'Content-Type: application/json',
            '-d', '{"email": "admin@demoprincipal.com", "password": "admin123"}'
        ]
        
        login_result = subprocess.run(login_cmd, capture_output=True, text=True)
        if login_result.returncode != 0:
            print(f"❌ Login command failed: {login_result.stderr}")
            return
            
        try:
            login_data = json.loads(login_result.stdout)
            token = login_data['access_token']
            print(f"✅ Login successful, got token")
        except Exception as e:
            print(f"❌ Failed to parse login response: {e}")
            print(f"Response: {login_result.stdout}")
            return
        
        # Now test the endpoint
        user_id = '3e4b4e82-9b73-4bff-95b6-45cc31ceeec0'
        endpoint_cmd = [
            'curl', '-s', '-X', 'GET',
            f'http://localhost:8000/api/v1/users/{user_id}/locales/disponibles',
            '-H', f'Authorization: Bearer {token}'
        ]
        
        endpoint_result = subprocess.run(endpoint_cmd, capture_output=True, text=True)
        print(f"Status: {endpoint_result.returncode}")
        print(f"Response: {endpoint_result.stdout}")
        
        if endpoint_result.stderr:
            print(f"Stderr: {endpoint_result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()