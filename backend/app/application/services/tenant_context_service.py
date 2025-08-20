"""
Servicio para gestión del contexto de tenant en el sistema multi-tenant.

Maneja la creación, validación y propagación del contexto de tenant
a través de toda la aplicación.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from app.domain.models.tenant_context import (
    TenantContext, 
    TenantContextType,
    PermisoInsuficienteError,
    ContextoInvalidoError
)
from app.domain.models.user import User
from app.domain.models.tienda import Tienda
from app.domain.models.local import Local
from app.domain.models.usuario_local import UsuarioLocal

from app.application.services.i_tienda_repository import ITiendaRepository
from app.application.services.i_local_repository import ILocalRepository
from app.application.services.i_usuario_local_repository import IUsuarioLocalRepository


class TenantContextService:
    """
    Servicio para gestión del contexto de tenant.
    
    Proporciona funcionalidades para crear, validar y gestionar
    el contexto de tenant que se propaga por toda la aplicación.
    """

    def __init__(
        self,
        tienda_repository: ITiendaRepository,
        local_repository: ILocalRepository,
        usuario_local_repository: IUsuarioLocalRepository
    ):
        self.tienda_repository = tienda_repository
        self.local_repository = local_repository
        self.usuario_local_repository = usuario_local_repository

    def crear_contexto_para_usuario(
        self,
        usuario: User,
        local_id: Optional[UUID] = None
    ) -> TenantContext:
        """
        Crea el contexto de tenant para un usuario.

        Args:
            usuario: Usuario autenticado
            local_id: Local específico (opcional)

        Returns:
            TenantContext: Contexto creado para el usuario

        Raises:
            ContextoInvalidoError: Si el usuario no tiene acceso a la tienda/local
        """
        if not usuario.tienda_id:
            raise ContextoInvalidoError("Usuario no tiene tienda asignada")

        # Obtener tienda del usuario
        tienda = self.tienda_repository.get_by_id(usuario.tienda_id)
        if not tienda or not tienda.is_active:
            raise ContextoInvalidoError("Tienda no existe o está inactiva")

        # Obtener permisos del usuario por local
        permisos_locales = self.usuario_local_repository.get_by_usuario(usuario.id)
        permisos_dict = {}
        
        for permiso_local in permisos_locales:
            if permiso_local.is_active:
                local_key = str(permiso_local.local_id)
                permisos_dict[local_key] = permiso_local.get_permisos_activos()

        # Crear contexto base
        contexto = TenantContext(
            tienda_id=tienda.id,
            tienda_codigo=tienda.codigo,
            tienda_nombre=tienda.nombre,
            user_id=usuario.id,
            user_nombre=usuario.nombre,
            user_rol=usuario.rol,
            permisos_locales=permisos_dict,
            tipo_contexto=TenantContextType.TIENDA_ONLY
        )

        # Si se especifica local, validar y configurar contexto de local
        if local_id:
            self._configurar_contexto_local(contexto, local_id, usuario.id)

        return contexto

    def _configurar_contexto_local(
        self,
        contexto: TenantContext,
        local_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Configura el contexto para un local específico.

        Args:
            contexto: Contexto base a configurar
            local_id: ID del local
            user_id: ID del usuario

        Raises:
            ContextoInvalidoError: Si el local no existe o usuario no tiene acceso
        """
        # Verificar que el local existe y pertenece a la tienda
        local = self.local_repository.get_by_id(local_id)
        if not local or not local.is_active:
            raise ContextoInvalidoError("Local no existe o está inactivo")

        if local.tienda_id != contexto.tienda_id:
            raise ContextoInvalidoError("Local no pertenece a la tienda del usuario")

        # Verificar que el usuario tiene permisos en el local
        permisos_local = self.usuario_local_repository.get_by_usuario_and_local(
            user_id, local_id
        )
        if not permisos_local or not permisos_local.is_active:
            raise ContextoInvalidoError("Usuario no tiene permisos en el local especificado")

        # Configurar contexto de local
        contexto.cambiar_contexto_local(local.id, local.codigo, local.nombre)

    def validar_permiso_operacion(
        self,
        contexto: TenantContext,
        operacion: str,
        local_id: Optional[UUID] = None
    ) -> bool:
        """
        Valida si el usuario puede realizar una operación en el contexto dado.

        Args:
            contexto: Contexto actual del usuario
            operacion: Operación a validar
            local_id: Local específico (si difiere del contexto)

        Returns:
            bool: True si tiene permisos, False si no

        Raises:
            PermisoInsuficienteError: Si no tiene permisos suficientes
        """
        # Si se especifica local diferente, validar en ese local
        if local_id and local_id != contexto.local_id:
            if not contexto.tiene_permiso_en_local(local_id, operacion):
                raise PermisoInsuficienteError(operacion, local_id)
            return True

        # Validar en el contexto actual
        if not contexto.validar_operacion_en_contexto_actual(operacion):
            raise PermisoInsuficienteError(operacion, contexto.local_id)

        return True

    def cambiar_contexto_local(
        self,
        contexto: TenantContext,
        nuevo_local_id: Optional[UUID]
    ) -> TenantContext:
        """
        Cambia el contexto activo a un local diferente.

        Args:
            contexto: Contexto actual
            nuevo_local_id: ID del nuevo local (None para contexto solo tienda)

        Returns:
            TenantContext: Contexto actualizado

        Raises:
            ContextoInvalidoError: Si no puede cambiar al nuevo local
        """
        if nuevo_local_id is None:
            # Cambiar a contexto solo tienda
            contexto.limpiar_contexto_local()
            return contexto

        # Configurar nuevo contexto de local
        self._configurar_contexto_local(contexto, nuevo_local_id, contexto.user_id)
        return contexto

    def get_locales_disponibles_usuario(
        self,
        user_id: UUID,
        tienda_id: UUID
    ) -> List[Local]:
        """
        Obtiene los locales disponibles para un usuario.

        Args:
            user_id: ID del usuario
            tienda_id: ID de la tienda

        Returns:
            Lista de locales donde el usuario tiene permisos
        """
        # Obtener asignaciones activas del usuario en la tienda
        asignaciones = self.usuario_local_repository.get_by_usuario(user_id)
        local_ids = [asig.local_id for asig in asignaciones if asig.is_active]

        if not local_ids:
            return []

        # Obtener los locales de la tienda donde tiene permisos
        locales_tienda = self.local_repository.get_by_tienda(tienda_id)
        locales_disponibles = [
            local for local in locales_tienda 
            if local.id in local_ids and local.is_active
        ]

        return locales_disponibles

    def get_contexto_disponible_usuario(self, user_id: UUID) -> Dict[str, Any]:
        """
        Obtiene toda la información de contexto disponible para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de contexto disponible
        """
        # Obtener usuario con tienda
        from app.application.services.i_user_repository import IUserRepository
        # Nota: En implementación real, inyectar UserRepository en constructor
        
        # Por ahora, simulamos la respuesta básica
        return {
            "tiendas_disponibles": [],
            "locales_por_tienda": {},
            "contexto_actual": None
        }

    def crear_filtros_consulta(
        self,
        contexto: TenantContext,
        incluir_local: bool = False
    ) -> Dict[str, Any]:
        """
        Crea filtros para consultas basados en el contexto.

        Args:
            contexto: Contexto actual
            incluir_local: Si incluir filtro por local

        Returns:
            Diccionario con filtros para aplicar en consultas
        """
        if incluir_local and contexto.tiene_contexto_local:
            return contexto.get_filters_con_local()
        else:
            return contexto.get_filters_base()

    def validar_acceso_recurso(
        self,
        contexto: TenantContext,
        recurso_tienda_id: UUID,
        recurso_local_id: Optional[UUID] = None
    ) -> bool:
        """
        Valida si el usuario tiene acceso a un recurso específico.

        Args:
            contexto: Contexto del usuario
            recurso_tienda_id: Tienda del recurso
            recurso_local_id: Local del recurso (opcional)

        Returns:
            bool: True si tiene acceso, False si no

        Raises:
            PermisoInsuficienteError: Si no tiene acceso
        """
        # Verificar acceso a la tienda
        if recurso_tienda_id != contexto.tienda_id:
            raise PermisoInsuficienteError("acceso_tienda")

        # Si el recurso tiene local, verificar acceso
        if recurso_local_id:
            if not contexto.puede_ver_stock_local(recurso_local_id):
                raise PermisoInsuficienteError("acceso_local", recurso_local_id)

        return True

    def serializar_contexto(self, contexto: TenantContext) -> Dict[str, Any]:
        """
        Serializa el contexto para almacenamiento en sesión/token.

        Args:
            contexto: Contexto a serializar

        Returns:
            Diccionario serializado
        """
        return contexto.to_dict()

    def deserializar_contexto(self, data: Dict[str, Any]) -> TenantContext:
        """
        Deserializa el contexto desde datos almacenados.

        Args:
            data: Datos serializados del contexto

        Returns:
            TenantContext: Contexto deserializado
        """
        return TenantContext.from_dict(data)

    def refrescar_permisos_usuario(
        self,
        contexto: TenantContext
    ) -> TenantContext:
        """
        Refresca los permisos del usuario en el contexto.

        Args:
            contexto: Contexto a refrescar

        Returns:
            TenantContext: Contexto con permisos actualizados
        """
        # Obtener permisos actualizados
        permisos_locales = self.usuario_local_repository.get_by_usuario(
            contexto.user_id
        )
        
        permisos_dict = {}
        for permiso_local in permisos_locales:
            if permiso_local.is_active:
                local_key = str(permiso_local.local_id)
                permisos_dict[local_key] = permiso_local.get_permisos_activos()

        # Actualizar permisos en el contexto
        contexto.permisos_locales = permisos_dict
        return contexto