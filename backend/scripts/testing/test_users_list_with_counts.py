#!/usr/bin/env python3
"""
Test script to get users list with local assignment counts
"""

import subprocess
import json

def test_users_list_with_counts():
    """Test getting users list with local assignment counts"""
    
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
        
        # Get users list
        users_cmd = [
            'curl', '-s', '-X', 'GET',
            f'http://localhost:8000/api/v1/users/',
            '-H', f'Authorization: Bearer {token}'
        ]
        
        users_result = subprocess.run(users_cmd, capture_output=True, text=True)
        print(f"Users list response:")
        
        if users_result.returncode == 0:
            try:
                users = json.loads(users_result.stdout)
                
                # Check if users have local assignment counts
                print(f"Found {len(users)} users:")
                for user in users:
                    total_locals = user.get('total_locales_asignados', 'MISSING')
                    print(f"   - {user.get('nombre', 'N/A')} ({user.get('email', 'N/A')}): {total_locals} locales")
                
                # Focus on the problematic user
                vendedor2 = next((u for u in users if u.get('email') == 'vendedor2@demoprincipal.com'), None)
                if vendedor2:
                    print(f"\n📋 Usuario vendedor2 details:")
                    print(f"   ID: {vendedor2.get('id')}")
                    print(f"   Email: {vendedor2.get('email')}")
                    print(f"   Total locales: {vendedor2.get('total_locales_asignados')}")
                    
                    if vendedor2.get('total_locales_asignados', 0) > 0:
                        print("✅ Local assignment count is working correctly!")
                    else:
                        print("❌ Local assignment count still showing 0")
                else:
                    print("⚠️  Usuario vendedor2 not found in response")
                    
            except Exception as e:
                print(f"❌ Error parsing response: {e}")
                print(f"Raw response: {users_result.stdout}")
        else:
            print(f"❌ Request failed")
            print(f"Response: {users_result.stdout}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_users_list_with_counts()