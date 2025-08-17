"""
Endpoints de autenticación.
Maneja las rutas para login, registro y obtención del usuario actual.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from app.api.v1.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    UserResponse, ErrorResponse, ProfileUpdateRequest, ChangePasswordRequest,
    MessageResponse
)
from app.application.use_cases.auth_use_cases import (
    LoginUseCase, RegisterUseCase, GetCurrentUserUseCase,
    UpdateProfileUseCase, ChangePasswordUseCase,
    AuthenticationError, RegistrationError
)
from app.infrastructure.repositories.user_repository import SQLUserRepository
from app.infrastructure.database.session import get_session
from app.domain.models.user import UserCreate


router = APIRouter(tags=["Autenticación"])
security = HTTPBearer()


def get_user_repository(session: Session = Depends(get_session)) -> SQLUserRepository:
    """
    Dependency injection para el repositorio de usuarios.
    
    Args:
        session (Session): Sesión de base de datos
        
    Returns:
        SQLUserRepository: Instancia del repositorio de usuarios
    """
    return SQLUserRepository(session)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica un usuario y retorna un token JWT",
    responses={
        200: {"description": "Login exitoso"},
        401: {"model": ErrorResponse, "description": "Credenciales inválidas"},
        422: {"description": "Error de validación"}
    }
)
async def login(
    login_data: LoginRequest,
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Endpoint para iniciar sesión.
    
    Args:
        login_data (LoginRequest): Credenciales de login
        user_repository (SQLUserRepository): Repositorio de usuarios
        
    Returns:
        LoginResponse: Token JWT y datos del usuario
        
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    try:
        login_use_case = LoginUseCase(user_repository)
        result = await login_use_case.execute(login_data.email, login_data.password)
        return LoginResponse(**result)
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description="Crea un nuevo usuario en el sistema",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"model": ErrorResponse, "description": "Error en los datos de registro"},
        409: {"model": ErrorResponse, "description": "Email ya existe"},
        422: {"description": "Error de validación"}
    }
)
async def register(
    register_data: RegisterRequest,
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Endpoint para registrar un nuevo usuario.
    
    Args:
        register_data (RegisterRequest): Datos de registro
        user_repository (SQLUserRepository): Repositorio de usuarios
        
    Returns:
        RegisterResponse: Token JWT y datos del usuario creado
        
    Raises:
        HTTPException: Si hay errores en el registro
    """
    try:
        # Convertir datos del request a modelo de dominio
        user_create = UserCreate(
            email=register_data.email,
            nombre=register_data.nombre,
            rol=register_data.rol,
            password=register_data.password
        )
        
        register_use_case = RegisterUseCase(user_repository)
        result = await register_use_case.execute(user_create)
        return RegisterResponse(**result)
        
    except RegistrationError as e:
        # Determinar el código de estado apropiado
        if "Ya existe un usuario" in str(e):
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Usuario actual",
    description="Obtiene la información del usuario autenticado actual",
    responses={
        200: {"description": "Información del usuario actual"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
        404: {"model": ErrorResponse, "description": "Usuario no encontrado"}
    }
)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Endpoint para obtener información del usuario actual.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Credenciales Bearer token
        user_repository (SQLUserRepository): Repositorio de usuarios
        
    Returns:
        UserResponse: Información del usuario actual
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    try:
        token = credentials.credentials
        get_current_user_use_case = GetCurrentUserUseCase(user_repository)
        result = await get_current_user_use_case.execute(token)
        return UserResponse(**result)
        
    except AuthenticationError as e:
        if "Usuario no encontrado" in str(e):
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil",
    description="Actualiza el perfil del usuario autenticado actual",
    responses={
        200: {"description": "Perfil actualizado exitosamente"},
        400: {"model": ErrorResponse, "description": "Error en los datos del perfil"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
        409: {"model": ErrorResponse, "description": "Email ya existe"}
    }
)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Endpoint para actualizar el perfil del usuario actual.
    
    Args:
        profile_data (ProfileUpdateRequest): Datos del perfil a actualizar
        credentials (HTTPAuthorizationCredentials): Credenciales Bearer token
        user_repository (SQLUserRepository): Repositorio de usuarios
        
    Returns:
        UserResponse: Información del usuario actualizado
        
    Raises:
        HTTPException: Si hay errores en la actualización
    """
    try:
        token = credentials.credentials
        update_profile_use_case = UpdateProfileUseCase(user_repository)
        result = await update_profile_use_case.execute(
            token, 
            {"nombre": profile_data.nombre, "email": profile_data.email}
        )
        return UserResponse(**result)
        
    except RegistrationError as e:
        if "Ya existe un usuario" in str(e):
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except AuthenticationError as e:
        if "Usuario no encontrado" in str(e):
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña",
    description="Cambia la contraseña del usuario autenticado actual",
    responses={
        200: {"description": "Contraseña cambiada exitosamente"},
        400: {"model": ErrorResponse, "description": "Contraseña actual incorrecta"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"}
    }
)
async def change_password(
    password_data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Endpoint para cambiar la contraseña del usuario actual.
    
    Args:
        password_data (ChangePasswordRequest): Datos para cambio de contraseña
        credentials (HTTPAuthorizationCredentials): Credenciales Bearer token
        user_repository (SQLUserRepository): Repositorio de usuarios
        
    Returns:
        MessageResponse: Mensaje de confirmación
        
    Raises:
        HTTPException: Si hay errores en el cambio de contraseña
    """
    try:
        token = credentials.credentials
        change_password_use_case = ChangePasswordUseCase(user_repository)
        await change_password_use_case.execute(
            token,
            password_data.current_password,
            password_data.new_password
        )
        
        return MessageResponse(
            message="Contraseña cambiada exitosamente",
            success=True
        )
        
    except AuthenticationError as e:
        if "Usuario no encontrado" in str(e):
            status_code = status.HTTP_404_NOT_FOUND
        elif "Contraseña actual incorrecta" in str(e):
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_401_UNAUTHORIZED
            
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        ) 