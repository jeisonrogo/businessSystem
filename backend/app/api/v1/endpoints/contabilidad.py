"""
Endpoints REST para el módulo de contabilidad.
Maneja las operaciones CRUD del plan de cuentas y asientos contables.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.application.use_cases.cuenta_contable_use_cases import (
    CreateCuentaContableUseCase,
    GetCuentaContableUseCase,
    GetCuentaContableByCodigoUseCase,
    ListCuentasContablesUseCase,
    UpdateCuentaContableUseCase,
    DeleteCuentaContableUseCase,
    GetPlanCuentasJerarquicoUseCase,
    GetSubcuentasUseCase,
    SeedPlanCuentasColombia,
    GetCuentasPrincipalesUseCase,
    CuentaContableNotFoundError,
    DuplicateCodigoError,
    InvalidHierarchyError,
    CuentaContableError
)
from app.api.v1.schemas import (
    CuentaContableCreateRequest,
    CuentaContableUpdateRequest,
    CuentaContableResponse,
    CuentaContableListResponse,
    PlanCuentasJerarquicoResponse,
    SeedPlanCuentasResponse,
    CuentasPrincipalesResponse,
    SubcuentasResponse,
    TipoCuenta,
    ErrorResponse,
    MessageResponse
)
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository


router = APIRouter()


def get_cuenta_repository(session: Session = Depends(get_session)) -> ICuentaContableRepository:
    """
    Función de dependencia para crear una instancia del repositorio de cuentas contables.
    
    Args:
        session: Sesión de base de datos inyectada
        
    Returns:
        ICuentaContableRepository: Instancia del repositorio
    """
    return SQLCuentaContableRepository(session)


@router.post(
    "/",
    response_model=CuentaContableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta contable",
    description="Crea una nueva cuenta contable en el plan de cuentas",
    responses={
        201: {"description": "Cuenta contable creada exitosamente"},
        400: {"model": ErrorResponse, "description": "Código duplicado o cuenta padre inválida"},
        422: {"description": "Error de validación en los datos de entrada"}
    }
)
async def create_cuenta_contable(
    cuenta_data: CuentaContableCreateRequest,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Crear una nueva cuenta contable."""
    use_case = CreateCuentaContableUseCase(cuenta_repository)
    
    try:
        cuenta = await use_case.execute(cuenta_data)
        return cuenta
    except DuplicateCodigoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidHierarchyError as e:
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
    response_model=CuentaContableListResponse,
    summary="Listar cuentas contables",
    description="Obtiene una lista paginada de cuentas contables con filtros opcionales",
    responses={
        200: {"description": "Lista de cuentas contables obtenida exitosamente"},
        422: {"description": "Parámetros de consulta inválidos"}
    }
)
async def list_cuentas_contables(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=500, description="Número de elementos por página"),
    tipo_cuenta: Optional[TipoCuenta] = Query(None, description="Filtrar por tipo de cuenta"),
    only_active: bool = Query(True, description="Solo cuentas activas"),
    only_main_accounts: bool = Query(False, description="Solo cuentas principales (sin padre)"),
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Listar cuentas contables con filtros y paginación."""
    use_case = ListCuentasContablesUseCase(cuenta_repository)
    
    try:
        result = await use_case.execute(
            page=page,
            limit=limit,
            tipo_cuenta=tipo_cuenta,
            only_active=only_active,
            only_main_accounts=only_main_accounts
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{cuenta_id}",
    response_model=CuentaContableResponse,
    summary="Obtener cuenta contable por ID",
    description="Obtiene una cuenta contable específica por su ID",
    responses={
        200: {"description": "Cuenta contable obtenida exitosamente"},
        404: {"model": ErrorResponse, "description": "Cuenta contable no encontrada"},
        422: {"description": "UUID inválido"}
    }
)
async def get_cuenta_contable(
    cuenta_id: UUID,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener una cuenta contable por su ID."""
    use_case = GetCuentaContableUseCase(cuenta_repository)
    
    try:
        cuenta = await use_case.execute(cuenta_id)
        return cuenta
    except CuentaContableNotFoundError as e:
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
    "/codigo/{codigo}",
    response_model=CuentaContableResponse,
    summary="Obtener cuenta contable por código",
    description="Obtiene una cuenta contable específica por su código único",
    responses={
        200: {"description": "Cuenta contable obtenida exitosamente"},
        404: {"model": ErrorResponse, "description": "Cuenta contable no encontrada"}
    }
)
async def get_cuenta_contable_by_codigo(
    codigo: str,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener una cuenta contable por su código."""
    use_case = GetCuentaContableByCodigoUseCase(cuenta_repository)
    
    try:
        cuenta = await use_case.execute(codigo)
        return cuenta
    except CuentaContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put(
    "/{cuenta_id}",
    response_model=CuentaContableResponse,
    summary="Actualizar cuenta contable",
    description="Actualiza una cuenta contable existente",
    responses={
        200: {"description": "Cuenta contable actualizada exitosamente"},
        400: {"model": ErrorResponse, "description": "Referencia circular o datos inválidos"},
        404: {"model": ErrorResponse, "description": "Cuenta contable no encontrada"},
        422: {"description": "Error de validación en los datos de entrada"}
    }
)
async def update_cuenta_contable(
    cuenta_id: UUID,
    cuenta_data: CuentaContableUpdateRequest,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Actualizar una cuenta contable existente."""
    use_case = UpdateCuentaContableUseCase(cuenta_repository)
    
    try:
        cuenta = await use_case.execute(cuenta_id, cuenta_data)
        return cuenta
    except CuentaContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidHierarchyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete(
    "/{cuenta_id}",
    response_model=MessageResponse,
    summary="Eliminar cuenta contable",
    description="Elimina una cuenta contable (soft delete). No se puede eliminar si tiene subcuentas o movimientos",
    responses={
        200: {"description": "Cuenta contable eliminada exitosamente"},
        400: {"model": ErrorResponse, "description": "No se puede eliminar - tiene subcuentas o movimientos"},
        404: {"model": ErrorResponse, "description": "Cuenta contable no encontrada"}
    }
)
async def delete_cuenta_contable(
    cuenta_id: UUID,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Eliminar una cuenta contable (soft delete)."""
    use_case = DeleteCuentaContableUseCase(cuenta_repository)
    
    try:
        await use_case.execute(cuenta_id)
        return MessageResponse(
            message="Cuenta contable eliminada exitosamente",
            success=True
        )
    except CuentaContableNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidHierarchyError as e:
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
    "/plan-jerarquico/",
    response_model=PlanCuentasJerarquicoResponse,
    summary="Obtener plan de cuentas jerárquico",
    description="Obtiene todo el plan de cuentas en formato jerárquico para visualización",
    responses={
        200: {"description": "Plan de cuentas jerárquico obtenido exitosamente"}
    }
)
async def get_plan_cuentas_jerarquico(
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener el plan de cuentas en formato jerárquico."""
    use_case = GetPlanCuentasJerarquicoUseCase(cuenta_repository)
    
    try:
        plan_cuentas = await use_case.execute()
        return PlanCuentasJerarquicoResponse(plan_cuentas=plan_cuentas)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/principales/",
    response_model=CuentasPrincipalesResponse,
    summary="Obtener cuentas principales",
    description="Obtiene cuentas principales (sin cuenta padre) opcionalmente filtradas por tipo",
    responses={
        200: {"description": "Cuentas principales obtenidas exitosamente"}
    }
)
async def get_cuentas_principales(
    tipo_cuenta: Optional[TipoCuenta] = Query(None, description="Filtrar por tipo de cuenta"),
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener cuentas principales (sin cuenta padre)."""
    use_case = GetCuentasPrincipalesUseCase(cuenta_repository)
    
    try:
        cuentas = await use_case.execute(tipo_cuenta)
        return CuentasPrincipalesResponse(
            cuentas=cuentas,
            tipo_cuenta=tipo_cuenta
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{cuenta_padre_id}/subcuentas/",
    response_model=SubcuentasResponse,
    summary="Obtener subcuentas",
    description="Obtiene todas las subcuentas de una cuenta padre específica",
    responses={
        200: {"description": "Subcuentas obtenidas exitosamente"},
        404: {"model": ErrorResponse, "description": "Cuenta padre no encontrada"}
    }
)
async def get_subcuentas(
    cuenta_padre_id: UUID,
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Obtener subcuentas de una cuenta padre."""
    use_case = GetSubcuentasUseCase(cuenta_repository)
    
    try:
        subcuentas = await use_case.execute(cuenta_padre_id)
        return SubcuentasResponse(
            subcuentas=subcuentas,
            cuenta_padre_id=cuenta_padre_id,
            total_subcuentas=len(subcuentas)
        )
    except CuentaContableNotFoundError as e:
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
    "/seed-colombia/",
    response_model=SeedPlanCuentasResponse,
    summary="Poblar plan de cuentas de Colombia",
    description="Carga el plan de cuentas estándar de Colombia. Es idempotente - no crea duplicados",
    responses={
        200: {"description": "Plan de cuentas poblado exitosamente"},
        500: {"model": ErrorResponse, "description": "Error al poblar el plan de cuentas"}
    }
)
async def seed_plan_cuentas_colombia(
    cuenta_repository: ICuentaContableRepository = Depends(get_cuenta_repository)
):
    """Poblar la base de datos con el plan de cuentas estándar de Colombia."""
    use_case = SeedPlanCuentasColombia(cuenta_repository)
    
    try:
        result = await use_case.execute()
        return result
    except CuentaContableError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )