#!/usr/bin/env python3
import jwt
from datetime import datetime, timedelta

# Configuración del JWT
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

def create_test_token():
    # ID de usuario admin desde los logs
    user_id = "c03958af-e2f3-4bbd-a2c6-abf9ee7dab20"
    
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

if __name__ == "__main__":
    token = create_test_token()
    print(token)