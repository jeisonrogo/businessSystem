#!/usr/bin/env python3
"""
Test script to assign local with perfil to user
"""

import subprocess
import json
import uuid

def test_perfil_assignment():
    """Test assigning a local with perfil to user"""
    
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
            print(f"❌ Login failed: {login_result.stderr}")
            return
            
        login_data = json.loads(login_result.stdout)
        token = login_data['access_token']
        print(f"✅ Login successful")
        
        # Test assigning local with perfil (using a different local)
        user_id = '3e4b4e82-9b73-4bff-95b6-45cc31ceeec0'
        assignment_data = {
            "local_id": "39c473da-7004-472d-bf0d-a80f8eb3fb33",  # Almacén Principal
            "perfil": "VENDEDOR"
        }
        
        assign_cmd = [
            'curl', '-s', '-X', 'POST',
            f'http://localhost:8000/api/v1/users/{user_id}/locales/perfil',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {token}',
            '-d', json.dumps(assignment_data)
        ]
        
        assign_result = subprocess.run(assign_cmd, capture_output=True, text=True)
        print(f"Assignment response: {assign_result.stdout}")
        
        if assign_result.returncode == 0:
            try:
                response = json.loads(assign_result.stdout)
                if 'id' in response:
                    print("✅ Local assignment successful!")
                else:
                    print("❌ Unexpected response format")
            except Exception as e:
                print(f"❌ Error parsing response: {e}")
        else:
            print(f"❌ Assignment failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_perfil_assignment()