"""
Implementación concreta del repositorio para la entidad UsuarioLocal.

Maneja la persistencia de permisos granulares de usuarios por local
usando SQLAlchemy/SQLModel con validaciones de negocio.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, UTC
from sqlmodel import Session
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.domain.models.usuario_local import (
    UsuarioLocal, 
    UsuarioLocalCreate, 
    UsuarioLocalUpdate,
    PerfilPermiso
)
from app.application.services.i_usuario_local_repository import IUsuarioLocalRepository


class UsuarioLocalRepository(IUsuarioLocalRepository):
    """
    Implementación del repositorio de permisos usuario-local usando SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, usuario_local_data: UsuarioLocalCreate) -> UsuarioLocal:
        """
        Crea una nueva asignación de permisos usuario-local.
        """
        # Verificar que no exista ya una asignación activa
        existing = self.get_by_usuario_and_local(
            usuario_local_data.user_id, 
            usuario_local_data.local_id
        )
        if existing and existing.is_active:
            raise ValueError(
                "Ya existe una asignación activa para este usuario en el local"
            )

        # Crear asignación
        usuario_local = UsuarioLocal(**usuario_local_data.model_dump())
        self.session.add(usuario_local)
        self.session.commit()
        self.session.refresh(usuario_local)
        
        return usuario_local

    def get_by_id(self, usuario_local_id: UUID) -> Optional[UsuarioLocal]:
        """
        Obtiene una asignación de permisos por su ID.
        """
        result = self.session.exec(
            select(UsuarioLocal).where(UsuarioLocal.id == usuario_local_id)
        )
        return result.scalar_one_or_none()

    def get_by_usuario_and_local(
        self, 
        user_id: UUID, 
        local_id: UUID
    ) -> Optional[UsuarioLocal]:
        """
        Obtiene los permisos de un usuario en un local específico.
        """
        result = self.session.exec(
            select(UsuarioLocal).where(
                and_(
                    UsuarioLocal.user_id == user_id,
                    UsuarioLocal.local_id == local_id,
                    UsuarioLocal.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    def get_by_usuario(
        self, 
        user_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todas las asignaciones de permisos de un usuario.
        """
        query = select(UsuarioLocal).where(UsuarioLocal.user_id == user_id)
        
        if not incluir_inactivos:
            query = query.where(UsuarioLocal.is_active == True)
        
        query = query.order_by(UsuarioLocal.created_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def get_by_local(
        self, 
        local_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todos los usuarios con permisos en un local.
        """
        query = select(UsuarioLocal).where(UsuarioLocal.local_id == local_id)
        
        if not incluir_inactivos:
            query = query.where(UsuarioLocal.is_active == True)
        
        query = query.order_by(UsuarioLocal.created_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def get_by_tienda(
        self, 
        tienda_id: UUID, 
        incluir_inactivos: bool = False
    ) -> List[UsuarioLocal]:
        """
        Obtiene todas las asignaciones de una tienda.
        """
        from app.domain.models.local import Local

        query = (
            select(UsuarioLocal)
            .join(Local, UsuarioLocal.local_id == Local.id)
            .where(Local.tienda_id == tienda_id)
        )
        
        if not incluir_inactivos:
            query = query.where(UsuarioLocal.is_active == True)
        
        query = query.order_by(UsuarioLocal.created_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def update(
        self, 
        usuario_local_id: UUID, 
        usuario_local_data: UsuarioLocalUpdate
    ) -> Optional[UsuarioLocal]:
        """
        Actualiza los permisos de un usuario en un local.
        """
        usuario_local = self.get_by_id(usuario_local_id)
        if not usuario_local:
            return None

        # Actualizar campos
        update_data = usuario_local_data.model_dump(exclude_unset=True)
        if update_data:
            usuario_local.updated_at = datetime.now(UTC)
            for field, value in update_data.items():
                setattr(usuario_local, field, value)

        self.session.commit()
        self.session.refresh(usuario_local)
        return usuario_local

    def delete(self, usuario_local_id: UUID) -> bool:
        """
        Elimina (desactiva) una asignación de permisos.
        """
        usuario_local = self.get_by_id(usuario_local_id)
        if not usuario_local:
            return False

        usuario_local.is_active = False
        usuario_local.updated_at = datetime.now(UTC)
        self.session.commit()
        return True

    def asignar_perfil_permiso(
        self,
        user_id: UUID,
        local_id: UUID,
        perfil: PerfilPermiso,
        created_by: Optional[UUID] = None
    ) -> UsuarioLocal:
        """
        Asigna un perfil de permisos predefinido a un usuario en un local.
        """
        # Verificar que no exista asignación activa
        existing = self.get_by_usuario_and_local(user_id, local_id)
        if existing:
            raise ValueError("Ya existe una asignación activa para este usuario en el local")

        # Crear datos según el perfil
        usuario_local_data = UsuarioLocalCreate(
            user_id=user_id,
            local_id=local_id,
            created_by=created_by,
            **perfil.get_permisos()
        )

        return self.create(usuario_local_data)

    def usuario_tiene_permiso(
        self,
        user_id: UUID,
        local_id: UUID,
        permiso: str
    ) -> bool:
        """
        Verifica si un usuario tiene un permiso específico en un local.
        """
        usuario_local = self.get_by_usuario_and_local(user_id, local_id)
        if not usuario_local:
            return False

        return usuario_local.tiene_permiso(permiso)

    def get_usuarios_con_permiso(
        self,
        local_id: UUID,
        permiso: str
    ) -> List[UsuarioLocal]:
        """
        Obtiene usuarios que tienen un permiso específico en un local.
        """
        usuarios_local = self.get_by_local(local_id)
        
        return [
            usuario_local 
            for usuario_local in usuarios_local 
            if usuario_local.tiene_permiso(permiso)
        ]

    def get_responsables_local(self, local_id: UUID) -> List[UsuarioLocal]:
        """
        Obtiene los usuarios responsables de un local.
        """
        result = self.session.exec(
            select(UsuarioLocal).where(
                and_(
                    UsuarioLocal.local_id == local_id,
                    UsuarioLocal.es_responsable == True,
                    UsuarioLocal.is_active == True
                )
            ).order_by(UsuarioLocal.created_at.asc())
        )
        return list(result.scalars().all())

    def get_locales_donde_usuario_es_responsable(self, user_id: UUID) -> List[UUID]:
        """
        Obtiene los locales donde un usuario es responsable.
        """
        result = self.session.exec(
            select(UsuarioLocal.local_id).where(
                and_(
                    UsuarioLocal.user_id == user_id,
                    UsuarioLocal.es_responsable == True,
                    UsuarioLocal.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    def copiar_permisos_entre_locales(
        self,
        user_id: UUID,
        local_origen_id: UUID,
        local_destino_id: UUID,
        created_by: Optional[UUID] = None
    ) -> Optional[UsuarioLocal]:
        """
        Copia los permisos de un usuario de un local a otro.
        """
        # Obtener permisos en local origen
        usuario_local_origen = self.get_by_usuario_and_local(user_id, local_origen_id)
        if not usuario_local_origen:
            return None

        # Verificar que no exista asignación en destino
        existing_destino = self.get_by_usuario_and_local(user_id, local_destino_id)
        if existing_destino:
            raise ValueError("Ya existe una asignación en el local destino")

        # Crear nueva asignación con los mismos permisos
        nueva_asignacion_data = UsuarioLocalCreate(
            user_id=user_id,
            local_id=local_destino_id,
            puede_vender=usuario_local_origen.puede_vender,
            puede_ver_stock=usuario_local_origen.puede_ver_stock,
            puede_transferir=usuario_local_origen.puede_transferir,
            es_responsable=False,  # No copiar responsabilidad por seguridad
            puede_modificar_precios=usuario_local_origen.puede_modificar_precios,
            puede_aplicar_descuentos=usuario_local_origen.puede_aplicar_descuentos,
            puede_ver_reportes=usuario_local_origen.puede_ver_reportes,
            puede_gestionar_usuarios=usuario_local_origen.puede_gestionar_usuarios,
            limite_descuento_porcentaje=usuario_local_origen.limite_descuento_porcentaje,
            limite_credito_monto=usuario_local_origen.limite_credito_monto,
            created_by=created_by
        )

        return self.create(nueva_asignacion_data)

    def get_usuarios_vendedores_local(self, local_id: UUID) -> List[UsuarioLocal]:
        """
        Obtiene usuarios que pueden vender en un local.
        """
        result = self.session.exec(
            select(UsuarioLocal).where(
                and_(
                    UsuarioLocal.local_id == local_id,
                    UsuarioLocal.puede_vender == True,
                    UsuarioLocal.is_active == True
                )
            ).order_by(UsuarioLocal.created_at.asc())
        )
        return list(result.scalars().all())

    def get_estadisticas_permisos_tienda(self, tienda_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas de permisos en una tienda.
        """
        from app.domain.models.local import Local
        from app.domain.models.user import User

        # Total de asignaciones activas
        result_total = self.session.exec(
            select(func.count(UsuarioLocal.id))
            .join(Local, UsuarioLocal.local_id == Local.id)
            .where(
                and_(
                    Local.tienda_id == tienda_id,
                    UsuarioLocal.is_active == True
                )
            )
        )
        total_asignaciones = result_total.scalar() or 0

        # Usuarios únicos con permisos
        result_usuarios = self.session.exec(
            select(func.count(func.distinct(UsuarioLocal.user_id)))
            .join(Local, UsuarioLocal.local_id == Local.id)
            .where(
                and_(
                    Local.tienda_id == tienda_id,
                    UsuarioLocal.is_active == True
                )
            )
        )
        usuarios_unicos = result_usuarios.scalar() or 0

        # Responsables por local
        result_responsables = self.session.exec(
            select(
                Local.nombre,
                func.count(UsuarioLocal.id)
            )
            .join(Local, UsuarioLocal.local_id == Local.id)
            .where(
                and_(
                    Local.tienda_id == tienda_id,
                    UsuarioLocal.es_responsable == True,
                    UsuarioLocal.is_active == True
                )
            )
            .group_by(Local.id, Local.nombre)
        )
        responsables_por_local = dict(result_responsables.all())

        # Usuarios sin asignación en la tienda
        result_sin_asignacion = self.session.exec(
            select(func.count(User.id))
            .outerjoin(UsuarioLocal, User.id == UsuarioLocal.user_id)
            .outerjoin(Local, UsuarioLocal.local_id == Local.id)
            .where(
                and_(
                    User.tienda_id == tienda_id,
                    User.is_active == True,
                    or_(
                        UsuarioLocal.id.is_(None),
                        and_(
                            Local.tienda_id == tienda_id,
                            UsuarioLocal.is_active == False
                        )
                    )
                )
            )
        )
        usuarios_sin_asignacion = result_sin_asignacion.scalar() or 0

        return {
            "total_asignaciones": total_asignaciones,
            "usuarios_unicos": usuarios_unicos,
            "responsables_por_local": responsables_por_local,
            "permisos_mas_asignados": {},  # Se puede implementar contando permisos individuales
            "usuarios_sin_asignacion": usuarios_sin_asignacion
        }

    def validar_limites_usuario(
        self,
        user_id: UUID,
        local_id: UUID,
        tipo_operacion: str,
        valor: float
    ) -> bool:
        """
        Valida si un usuario puede realizar una operación según sus límites.
        """
        usuario_local = self.get_by_usuario_and_local(user_id, local_id)
        if not usuario_local:
            return False

        if tipo_operacion == "descuento":
            if usuario_local.limite_descuento_porcentaje is None:
                return True  # Sin límite
            return valor <= usuario_local.limite_descuento_porcentaje

        elif tipo_operacion == "credito":
            if usuario_local.limite_credito_monto is None:
                return True  # Sin límite
            return valor <= usuario_local.limite_credito_monto

        return False

    def buscar_usuarios_local(
        self,
        local_id: UUID,
        texto_busqueda: str
    ) -> List[UsuarioLocal]:
        """
        Busca usuarios en un local por nombre o email.
        """
        from app.domain.models.user import User

        texto_busqueda = f"%{texto_busqueda}%"
        
        result = self.session.exec(
            select(UsuarioLocal)
            .join(User, UsuarioLocal.user_id == User.id)
            .where(
                and_(
                    UsuarioLocal.local_id == local_id,
                    UsuarioLocal.is_active == True,
                    or_(
                        User.nombre.ilike(texto_busqueda),
                        User.email.ilike(texto_busqueda)
                    )
                )
            )
            .order_by(User.nombre)
        )
        return list(result.scalars().all())