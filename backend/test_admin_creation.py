#!/usr/bin/env python3
"""
Test script to create new ADMINISTRADOR user and verify automatic local assignment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess
import json
import uuid

def test_admin_creation():
    """Test creating a new admin user and check local assignments"""
    
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
        
        # Create a new ADMINISTRADOR user
        random_email = f"testadmin{uuid.uuid4().hex[:8]}@demoprincipal.com"
        user_data = {
            "email": random_email,
            "nombre": "Test Admin User",
            "password": "testpass123",
            "rol": "administrador"
        }
        
        create_user_cmd = [
            'curl', '-s', '-X', 'POST',
            'http://localhost:8000/api/v1/users/',
            '-H', 'Content-Type: application/json',
            '-H', f'Authorization: Bearer {token}',
            '-d', json.dumps(user_data)
        ]
        
        create_result = subprocess.run(create_user_cmd, capture_output=True, text=True)
        print(f"Create user response: {create_result.stdout}")
        
        if create_result.returncode == 0:
            try:
                created_user = json.loads(create_result.stdout)
                user_id = created_user['id']
                print(f"✅ User created with ID: {user_id}")
                
                # Check local assignments for this user
                assignments_cmd = [
                    'curl', '-s', '-X', 'GET',
                    f'http://localhost:8000/api/v1/users/{user_id}/locales',
                    '-H', f'Authorization: Bearer {token}'
                ]
                
                assignments_result = subprocess.run(assignments_cmd, capture_output=True, text=True)
                print(f"Local assignments response: {assignments_result.stdout}")
                
                if assignments_result.returncode == 0:
                    assignments = json.loads(assignments_result.stdout)
                    print(f"📋 Found {len(assignments)} local assignments for new admin")
                    
                    if len(assignments) == 0:
                        print("❌ ISSUE: New ADMINISTRADOR user has no local assignments!")
                    else:
                        print("✅ New ADMINISTRADOR user has automatic local assignments")
                        
            except Exception as e:
                print(f"❌ Error parsing create response: {e}")
        else:
            print(f"❌ Failed to create user: {create_result.stdout}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_admin_creation()