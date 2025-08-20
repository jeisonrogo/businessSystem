"""
Interface del repositorio para la entidad UsuarioLocal en el sistema multi-tenant.

Define las operaciones de persistencia para gestionar permisos granulares
de usuarios por local específico.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.models.usuario_local import (
    UsuarioLocal, 
    UsuarioLocalCreate, 
    UsuarioLocalUpdate,
    PerfilPermiso
)


class IUsuarioLocalRepository(ABC):
    """
    Interface del repositorio para gestión de permisos usuario-local.
    
    Define las operaciones para asignar y gestionar permisos granulares
    de usuarios en locales específicos.
    """

    @abstractmethod
    async def create(self, usuario_local_data: UsuarioLocalCreate) -> UsuarioLocal:
        """
        Crea una nueva asignación de permisos usuario-local.

        Args:
            usuario_local_data: Datos para crear la asignación

        Returns:
            UsuarioLocal: La asignación creada

        Raises:
            ValueError: Si ya existe una asignación para el usuario-local
            ForeignKeyError: Si usuario o local no existen
        """
        pass

    @abstractmethod
    async def get_by_id(self, usuario_local_id: UUID) -> Optional[UsuarioLocal]:
        """
        Obtiene una asignación de permisos por su ID.

        Args:
            usuario_local_id: ID único de la asignación

        Returns:
            UsuarioLocal o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_usuario_and_local(
        self, 
        user_id: UUID, 
        local_id: UUID
    ) -> Optional[UsuarioLocal]:
        """
        Obtiene los permisos de un usuario en un local específico.

        Args:
            user_id: ID del usuario
            local_id: ID del local

        Returns:
            UsuarioLocal o None si no tiene asignación
        """
        pass

    @abstractmethod
    async def get_by_usuario(
        self, 
        user_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todas las asignaciones de permisos de un usuario.

        Args:
            user_id: ID del usuario
            incluir_inactivos: Si incluir asignaciones inactivas

        Returns:
            Lista de asignaciones del usuario
        """
        pass

    @abstractmethod
    async def get_by_local(
        self, 
        local_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todos los usuarios con permisos en un local.

        Args:
            local_id: ID del local
            incluir_inactivos: Si incluir asignaciones inactivas

        Returns:
            Lista de usuarios del local
        """
        pass

    @abstractmethod
    async def get_by_tienda(
        self, 
        tienda_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todas las asignaciones de una tienda.

        Args:
            tienda_id: ID de la tienda
            incluir_inactivos: Si incluir asignaciones inactivas

        Returns:
            Lista de asignaciones de la tienda
        """
        pass

    @abstractmethod
    async def update(
        self, 
        usuario_local_id: UUID, 
        usuario_local_data: UsuarioLocalUpdate
    ) -> Optional[UsuarioLocal]:
        """
        Actualiza los permisos de un usuario en un local.

        Args:
            usuario_local_id: ID de la asignación
            usuario_local_data: Datos a actualizar

        Returns:
            UsuarioLocal actualizado o None si no existe
        """
        pass

    @abstractmethod
    async def delete(self, usuario_local_id: UUID) -> bool:
        """
        Elimina (desactiva) una asignación de permisos.

        Args:
            usuario_local_id: ID de la asignación

        Returns:
            True si se eliminó, False si no existe
        """
        pass

    @abstractmethod
    async def asignar_perfil_permiso(
        self,
        user_id: UUID,
        local_id: UUID,
        perfil: PerfilPermiso,
        created_by: Optional[UUID] = None
    ) -> UsuarioLocal:
        """
        Asigna un perfil de permisos predefinido a un usuario en un local.

        Args:
            user_id: ID del usuario
            local_id: ID del local
            perfil: Perfil de permisos a asignar
            created_by: ID del usuario que crea la asignación

        Returns:
            UsuarioLocal con el perfil asignado

        Raises:
            ValueError: Si ya existe una asignación activa
        """
        pass

    @abstractmethod
    async def usuario_tiene_permiso(
        self,
        user_id: UUID,
        local_id: UUID,
        permiso: str
    ) -> bool:
        """
        Verifica si un usuario tiene un permiso específico en un local.

        Args:
            user_id: ID del usuario
            local_id: ID del local
            permiso: Nombre del permiso a verificar

        Returns:
            True si tiene el permiso, False si no
        """
        pass

    @abstractmethod
    async def get_usuarios_con_permiso(
        self,
        local_id: UUID,
        permiso: str
    ) -> List[UsuarioLocal]:
        """
        Obtiene usuarios que tienen un permiso específico en un local.

        Args:
            local_id: ID del local
            permiso: Permiso a buscar

        Returns:
            Lista de usuarios con el permiso
        """
        pass

    @abstractmethod
    async def get_responsables_local(self, local_id: UUID) -> List[UsuarioLocal]:
        """
        Obtiene los usuarios responsables de un local.

        Args:
            local_id: ID del local

        Returns:
            Lista de usuarios responsables
        """
        pass

    @abstractmethod
    async def get_locales_donde_usuario_es_responsable(self, user_id: UUID) -> List[UUID]:
        """
        Obtiene los locales donde un usuario es responsable.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de IDs de locales donde es responsable
        """
        pass

    @abstractmethod
    async def copiar_permisos_entre_locales(
        self,
        user_id: UUID,
        local_origen_id: UUID,
        local_destino_id: UUID,
        created_by: Optional[UUID] = None
    ) -> Optional[UsuarioLocal]:
        """
        Copia los permisos de un usuario de un local a otro.

        Args:
            user_id: ID del usuario
            local_origen_id: Local origen de los permisos
            local_destino_id: Local destino para copiar permisos
            created_by: ID del usuario que realiza la copia

        Returns:
            UsuarioLocal creado o None si el origen no existe

        Raises:
            ValueError: Si ya existe asignación en el destino
        """
        pass

    @abstractmethod
    async def get_usuarios_vendedores_local(self, local_id: UUID) -> List[UsuarioLocal]:
        """
        Obtiene usuarios que pueden vender en un local.

        Args:
            local_id: ID del local

        Returns:
            Lista de usuarios vendedores
        """
        pass

    @abstractmethod
    async def get_estadisticas_permisos_tienda(self, tienda_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas de permisos en una tienda.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Diccionario con estadísticas:
            - total_asignaciones: Total de asignaciones activas
            - usuarios_unicos: Usuarios únicos con permisos
            - responsables_por_local: Responsables por local
            - permisos_mas_asignados: Permisos más comunes
            - usuarios_sin_asignacion: Usuarios sin permisos en locales
        """
        pass

    @abstractmethod
    async def validar_limites_usuario(
        self,
        user_id: UUID,
        local_id: UUID,
        tipo_operacion: str,
        valor: float
    ) -> bool:
        """
        Valida si un usuario puede realizar una operación según sus límites.

        Args:
            user_id: ID del usuario
            local_id: ID del local
            tipo_operacion: 'descuento' o 'credito'
            valor: Valor de la operación

        Returns:
            True si está dentro de los límites, False si no
        """
        pass

    @abstractmethod
    async def buscar_usuarios_local(
        self,
        local_id: UUID,
        texto_busqueda: str
    ) -> List[UsuarioLocal]:
        """
        Busca usuarios en un local por nombre o email.

        Args:
            local_id: ID del local
            texto_busqueda: Texto a buscar

        Returns:
            Lista de usuarios que coinciden con la búsqueda
        """
        pass