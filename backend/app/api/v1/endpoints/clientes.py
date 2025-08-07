"""
Endpoints API para la gestión de clientes.

Proporciona endpoints REST para operaciones CRUD de clientes,
incluyendo búsqueda, filtros y estadísticas.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from uuid import UUID

from app.application.use_cases.cliente_use_cases import (
    CreateClienteUseCase,
    GetClienteUseCase,
    GetClienteByDocumentoUseCase,
    ListClientesUseCase,
    UpdateClienteUseCase,
    DeleteClienteUseCase,
    SearchClientesUseCase,
    GetClientesFrecuentesUseCase,
    GetEstadisticasClienteUseCase,
    ActivateClienteUseCase,
    GetClientesByTipoUseCase,
    # Excepciones
    ClienteNotFoundError,
    DuplicateDocumentError,
    ClienteInUseError,
    ClienteError
)
from app.application.services.i_cliente_repository import IClienteRepository
from app.infrastructure.repositories.cliente_repository import SQLClienteRepository
from app.domain.models.facturacion import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    TipoCliente,
    TipoDocumento
)
from app.infrastructure.database.session import get_session
from app.api.v1.endpoints.auth import get_current_user
from app.domain.models.user import User
from sqlmodel import Session

router = APIRouter(tags=["Clientes"])


def get_cliente_repository(session: Session = Depends(get_session)) -> IClienteRepository:
    """Dependencia para obtener el repositorio de clientes."""
    return SQLClienteRepository(session)


@router.post("/", response_model=ClienteResponse, status_code=201)
async def crear_cliente(
    cliente_data: ClienteCreate,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """
    Crear un nuevo cliente.
    
    - **nombre_completo**: Nombre completo del cliente
    - **tipo_documento**: Tipo de documento (CC, NIT, etc.)
    - **numero_documento**: Número de documento (único)
    - **email**: Email del cliente (opcional)
    - **telefono**: Teléfono de contacto (opcional)
    - **direccion**: Dirección del cliente (opcional)
    - **tipo_cliente**: Tipo de cliente (PERSONA_NATURAL, EMPRESA)
    """
    try:
        use_case = CreateClienteUseCase(cliente_repo)
        cliente = await use_case.execute(cliente_data)
        return cliente
    
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClienteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(
    cliente_id: UUID,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Obtener un cliente por su ID."""
    try:
        use_case = GetClienteUseCase(cliente_repo)
        cliente = await use_case.execute(cliente_id)
        return cliente
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/documento/{numero_documento}", response_model=ClienteResponse)
async def obtener_cliente_por_documento(
    numero_documento: str,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Obtener un cliente por su número de documento."""
    try:
        use_case = GetClienteByDocumentoUseCase(cliente_repo)
        cliente = await use_case.execute(numero_documento)
        return cliente
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/", response_model=dict)
async def listar_clientes(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    tipo_cliente: Optional[TipoCliente] = Query(None, description="Filtrar por tipo de cliente"),
    only_active: bool = Query(True, description="Solo clientes activos"),
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """
    Listar clientes con paginación y filtros.
    
    - **page**: Número de página (inicia en 1)
    - **limit**: Número de registros por página (máximo 100)
    - **search**: Buscar en nombre, documento, email
    - **tipo_cliente**: Filtrar por tipo (PERSONA_NATURAL, EMPRESA)
    - **only_active**: Solo incluir clientes activos
    """
    try:
        use_case = ListClientesUseCase(cliente_repo)
        result = await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            tipo_cliente=tipo_cliente,
            only_active=only_active
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def actualizar_cliente(
    cliente_id: UUID,
    cliente_data: ClienteUpdate,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Actualizar un cliente existente."""
    try:
        use_case = UpdateClienteUseCase(cliente_repo)
        cliente = await use_case.execute(cliente_id, cliente_data)
        return cliente
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClienteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{cliente_id}")
async def eliminar_cliente(
    cliente_id: UUID,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """
    Eliminar (desactivar) un cliente.
    
    Nota: Los clientes no se eliminan físicamente, solo se desactivan.
    No se puede eliminar un cliente que tenga facturas asociadas.
    """
    try:
        use_case = DeleteClienteUseCase(cliente_repo)
        await use_case.execute(cliente_id)
        return {"message": "Cliente eliminado exitosamente"}
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ClienteInUseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClienteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/{cliente_id}/activate")
async def reactivar_cliente(
    cliente_id: UUID,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Reactivar un cliente previamente desactivado."""
    try:
        use_case = ActivateClienteUseCase(cliente_repo)
        await use_case.execute(cliente_id)
        return {"message": "Cliente reactivado exitosamente"}
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/search/quick", response_model=List[ClienteResponse])
async def buscar_clientes_rapido(
    term: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=50, description="Número máximo de resultados"),
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """
    Búsqueda rápida de clientes.
    
    Útil para autocompletado en formularios.
    """
    try:
        use_case = SearchClientesUseCase(cliente_repo)
        clientes = await use_case.execute(term, limit)
        return clientes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/frecuentes/top", response_model=List[ClienteResponse])
async def obtener_clientes_frecuentes(
    limit: int = Query(10, ge=1, le=50, description="Número de clientes"),
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Obtener los clientes más frecuentes basado en número de facturas."""
    try:
        use_case = GetClientesFrecuentesUseCase(cliente_repo)
        clientes = await use_case.execute(limit)
        return clientes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{cliente_id}/estadisticas", response_model=dict)
async def obtener_estadisticas_cliente(
    cliente_id: UUID,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """
    Obtener estadísticas de un cliente.
    
    Incluye totales de facturas, montos, promedio de compra, etc.
    """
    try:
        use_case = GetEstadisticasClienteUseCase(cliente_repo)
        estadisticas = await use_case.execute(cliente_id)
        return estadisticas
    
    except ClienteNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/tipo/{tipo_cliente}", response_model=List[ClienteResponse])
async def obtener_clientes_por_tipo(
    tipo_cliente: TipoCliente,
    current_user: User = Depends(get_current_user),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository)
):
    """Obtener todos los clientes de un tipo específico."""
    try:
        use_case = GetClientesByTipoUseCase(cliente_repo)
        clientes = await use_case.execute(tipo_cliente)
        return clientes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")