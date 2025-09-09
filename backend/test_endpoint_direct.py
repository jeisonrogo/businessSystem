#!/usr/bin/env python3
"""
Test script to call the locales disponibles endpoint directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.user_repository import SQLUserRepository
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
from app.api.v1.endpoints.users import get_available_locals_for_user
from uuid import UUID

def test_endpoint():
    """Test the endpoint directly"""
    print("🔍 Testing endpoint directly...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        # Get admin user using sync method
        from sqlmodel import select
        from app.domain.models.user import User
        admin = session.exec(select(User).where(User.email == "admin@demoprincipal.com")).first()
        
        if not admin:
            print("❌ Admin user not found")
            return
            
        print(f"👤 Admin found: {admin.email}")
        
        # Test with the problematic user ID
        user_id = UUID('3e4b4e82-9b73-4bff-95b6-45cc31ceeec0')
        
        try:
            result = get_available_locals_for_user(
                user_id=user_id,
                current_user=admin,
                session=session
            )
            print(f"✅ Success! Found {len(result)} available locals")
            for local in result:
                print(f"   - {local}")
        except Exception as e:
            print(f"❌ Error calling endpoint: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
    finally:
        session.close()

if __name__ == "__main__":
    test_endpoint()