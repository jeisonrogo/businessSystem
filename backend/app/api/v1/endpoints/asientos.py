"""
Endpoints REST para la gestión de asientos contables manuales.
Maneja las operaciones CRUD de asientos contables y funcionalidades especiales.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.application.services.i_asiento_contable_repository import IAsientoContableRepository
from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.application.use_cases.asiento_contable_use_cases import (
    CreateAsientoContableUseCase,
    GetAsientoContableUseCase,
    GetAsientoContableByComprobanteUseCase,
    ListAsientosContablesUseCase,
    DeleteAsientoContableUseCase,
    ValidateAsientoContableBalanceUseCase,
    AsientoContableError,
    AsientoContableNotFoundError,
    DesequilibrioContableError,
    CuentaInactivaError,
    AsientoContableDuplicadoError
)
from app.api.v1.schemas import (
    AsientoContableCreateRequest,
    AsientoContableResponse,
    AsientoContableListResponse,
    ValidacionBalanceRequest,
    ValidacionBalanceResponse,
    BalanceCuentaResponse,
    LibroDiarioRequest,
    LibroDiarioResponse,
    MessageResponse,
    ErrorResponse
)
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.asiento_contable_repository import SQLAsientoContableRepository
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository


router = APIRouter()


def get_asiento_repository(session: Session = Depends(get_session)) -> IAsientoContableRepository:
    """Función de dependencia para crear una instancia del repositorio de asientos."""
    return SQLAsientoContableRepository(session)


def get_cuenta_repository(session: Session = Depends(get_session)) -> ICuentaContableRepository:
    """Función de dependencia para crear una instancia del repositorio de cuentas."""
    return SQLCuentaContableRepository(session)


@router.post(
    "/",
    response_model=AsientoContableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asiento contable manual",
    description="Crea un nuevo asiento contable manual con validación de doble partida",
    responses={
        201: {"description": "Asiento contable creado exitosamente"},
        400: {"model": ErrorResponse, "description": "Error de validación o balance contable"},
        422: {"description": "Error de validación en los datos de entrada"}
    }
)
async def create_asiento_contable(
    asiento_data: AsientoContableCreateRequest,
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository),
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Crear un nuevo asiento contable manual."""
    use_case = CreateAsientoContableUseCase(asiento_repository, cuenta_repository)
    
    try:
        asiento = await use_case.execute(asiento_data)
        return asiento
    except DesequilibrioContableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CuentaInactivaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AsientoContableDuplicadoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AsientoContableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/",
    response_model=AsientoContableListResponse,
    summary="Listar asientos contables",
    description="Obtiene una lista paginada de asientos contables con filtros opcionales",
    responses={
        200: {"description": "Lista de asientos contables obtenida exitosamente"},
        422: {"description": "Parámetros de consulta inválidos"}
    }
)
async def list_asientos_contables(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=500, description="Número de elementos por página"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    comprobante: Optional[str] = Query(None, description="Filtrar por comprobante"),
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository)
):
    """Listar asientos contables con filtros y paginación."""
    use_case = ListAsientosContablesUseCase(asiento_repository)
    
    try:
        # Convertir fechas si se proporcionan
        fecha_desde_date = None
        fecha_hasta_date = None
        
        if fecha_desde:
            fecha_desde_date = date.fromisoformat(fecha_desde)
        
        if fecha_hasta:
            fecha_hasta_date = date.fromisoformat(fecha_hasta)
        
        result = await use_case.execute(
            page=page,
            limit=limit,
            fecha_desde=fecha_desde_date,
            fecha_hasta=fecha_hasta_date,
            comprobante=comprobante
        )
        
        return AsientoContableListResponse(**result)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{asiento_id}",
    response_model=AsientoContableResponse,
    summary="Obtener asiento contable por ID",
    description="Obtiene un asiento contable específico por su ID",
    responses={
        200: {"description": "Asiento contable obtenido exitosamente"},
        404: {"model": ErrorResponse, "description": "Asiento contable no encontrado"},
        422: {"description": "UUID inválido"}
    }
)
async def get_asiento_contable(
    asiento_id: UUID,
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository)
):
    """Obtener un asiento contable por su ID."""
    use_case = GetAsientoContableUseCase(asiento_repository)
    
    try:
        asiento = await use_case.execute(asiento_id)
        return asiento
    except AsientoContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/comprobante/{comprobante}",
    response_model=AsientoContableResponse,
    summary="Obtener asiento contable por comprobante",
    description="Obtiene un asiento contable específico por su número de comprobante",
    responses={
        200: {"description": "Asiento contable obtenido exitosamente"},
        404: {"model": ErrorResponse, "description": "Asiento contable no encontrado"}
    }
)
async def get_asiento_contable_by_comprobante(
    comprobante: str,
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository)
):
    """Obtener un asiento contable por su comprobante."""
    use_case = GetAsientoContableByComprobanteUseCase(asiento_repository)
    
    try:
        asiento = await use_case.execute(comprobante)
        return asiento
    except AsientoContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete(
    "/{asiento_id}",
    response_model=MessageResponse,
    summary="Eliminar asiento contable",
    description="Elimina un asiento contable y todos sus detalles",
    responses={
        200: {"description": "Asiento contable eliminado exitosamente"},
        404: {"model": ErrorResponse, "description": "Asiento contable no encontrado"}
    }
)
async def delete_asiento_contable(
    asiento_id: UUID,
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository)
):
    """Eliminar un asiento contable."""
    use_case = DeleteAsientoContableUseCase(asiento_repository)
    
    try:
        await use_case.execute(asiento_id)
        return MessageResponse(
            message="Asiento contable eliminado exitosamente",
            success=True
        )
    except AsientoContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/validar-balance/",
    response_model=ValidacionBalanceResponse,
    summary="Validar balance de un asiento",
    description="Valida que un conjunto de detalles esté balanceado (débitos = créditos)",
    responses={
        200: {"description": "Validación completada exitosamente"},
        422: {"description": "Error de validación en los datos de entrada"}
    }
)
async def validar_balance_asiento(
    validacion_data: ValidacionBalanceRequest
):
    """Validar el balance de un conjunto de detalles de asiento."""
    use_case = ValidateAsientoContableBalanceUseCase()
    
    try:
        result = use_case.execute(validacion_data.detalles)
        return ValidacionBalanceResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/cuenta/{cuenta_id}/balance/",
    response_model=BalanceCuentaResponse,
    summary="Obtener balance de una cuenta",
    description="Calcula el balance de una cuenta contable hasta una fecha específica",
    responses={
        200: {"description": "Balance calculado exitosamente"},
        404: {"model": ErrorResponse, "description": "Cuenta no encontrada"},
        422: {"description": "Fecha inválida"}
    }
)
async def get_balance_cuenta(
    cuenta_id: UUID,
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository),
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener el balance de una cuenta contable."""
    try:
        # Verificar que la cuenta existe
        cuenta = await cuenta_repository.get_by_id(cuenta_id)
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuenta contable con ID {cuenta_id} no encontrada"
            )
        
        # Convertir fecha si se proporciona
        fecha_hasta_date = None
        if fecha_hasta:
            fecha_hasta_date = date.fromisoformat(fecha_hasta)
        
        # Calcular balance
        balance = await asiento_repository.get_balance_cuenta(cuenta_id, fecha_hasta_date)
        
        return BalanceCuentaResponse(
            cuenta_id=cuenta_id,
            fecha_hasta=fecha_hasta,
            **balance
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/libro-diario/",
    response_model=LibroDiarioResponse,
    summary="Obtener libro diario",
    description="Obtiene el libro diario para un rango de fechas específico",
    responses={
        200: {"description": "Libro diario obtenido exitosamente"},
        422: {"description": "Fechas inválidas"}
    }
)
async def get_libro_diario(
    request: LibroDiarioRequest,
    asiento_repository: IAsientoContableRepository = Depends(get_asiento_repository)
):
    """Obtener el libro diario para un rango de fechas."""
    try:
        # Convertir fechas
        fecha_desde = date.fromisoformat(request.fecha_desde)
        fecha_hasta = date.fromisoformat(request.fecha_hasta)
        
        # Validar rango de fechas
        if fecha_desde > fecha_hasta:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La fecha desde debe ser menor o igual a la fecha hasta"
            )
        
        # Obtener asientos
        asientos = await asiento_repository.get_libro_diario(fecha_desde, fecha_hasta)
        
        return LibroDiarioResponse(
            asientos=asientos,
            fecha_desde=request.fecha_desde,
            fecha_hasta=request.fecha_hasta,
            total_asientos=len(asientos)
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de fecha inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )