#!/usr/bin/env python3
"""
Test script to get user local assignments with local names
"""

import subprocess
import json

def test_user_locales_with_names():
    """Test getting user local assignments with local information"""
    
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
        
        # Get user local assignments
        user_id = '3e4b4e82-9b73-4bff-95b6-45cc31ceeec0'
        assignments_cmd = [
            'curl', '-s', '-X', 'GET',
            f'http://localhost:8000/api/v1/users/{user_id}/locales',
            '-H', f'Authorization: Bearer {token}'
        ]
        
        assignments_result = subprocess.run(assignments_cmd, capture_output=True, text=True)
        print(f"User local assignments response:")
        
        if assignments_result.returncode == 0:
            try:
                assignments = json.loads(assignments_result.stdout)
                print(json.dumps(assignments, indent=2))
                
                # Check if local_nombre and local_codigo are present
                if assignments and len(assignments) > 0:
                    first_assignment = assignments[0]
                    if 'local_nombre' in first_assignment and 'local_codigo' in first_assignment:
                        print(f"✅ Local information successfully included:")
                        for assignment in assignments:
                            print(f"   - {assignment.get('local_nombre', 'N/A')} ({assignment.get('local_codigo', 'N/A')})")
                    else:
                        print("❌ Local information missing from response")
                        print(f"Available keys: {list(first_assignment.keys())}")
                else:
                    print("ℹ️  No assignments found for user")
                    
            except Exception as e:
                print(f"❌ Error parsing response: {e}")
                print(f"Raw response: {assignments_result.stdout}")
        else:
            print(f"❌ Request failed")
            print(f"Response: {assignments_result.stdout}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_user_locales_with_names()