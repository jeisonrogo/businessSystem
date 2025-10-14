#!/usr/bin/env python3
"""
Test script to call asignar_perfil_permiso method directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
from app.domain.models.usuario_local import PerfilPermiso
from uuid import UUID

def test_direct_assignment():
    """Test the method directly"""
    print("🔍 Testing asignar_perfil_permiso directly...")
    
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        
        user_id = UUID('3e4b4e82-9b73-4bff-95b6-45cc31ceeec0')
        local_id = UUID('95a4fc43-46ef-4512-8547-9215d61631fb')  # Sucursal Centro
        perfil = PerfilPermiso.VENDEDOR
        admin_id = UUID('6d3992f0-ff7b-49bc-86be-a1984919d4d5')  # admin@demoprincipal.com
        
        print(f"User ID: {user_id}")
        print(f"Local ID: {local_id}")
        print(f"Perfil: {perfil}")
        print(f"Created by: {admin_id}")
        
        result = usuario_local_repo.asignar_perfil_permiso(
            user_id=user_id,
            local_id=local_id,
            perfil=perfil,
            created_by=admin_id
        )
        
        print(f"✅ Assignment successful! ID: {result.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_direct_assignment()