"""Modelos ORM (PLAN §2)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import Categoria, EstadoPlaca, EstadoRenta, Rol, Tarifa, Ubicacion


def enum_col(E, name: Optional[str] = None):
    """Enum guardado como VARCHAR (valor string) sin tipo nativo."""
    return sa.Enum(
        E,
        native_enum=False,
        values_callable=lambda e: [x.value for x in e],
        length=40,
        validate_strings=True,
        name=name or E.__name__.lower(),
    )


def _uuid_pk():
    return mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4, server_default=sa.text("gen_random_uuid()")
    )


def _created_at():
    return mapped_column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        sa.Index("uq_usuarios_username_lower", sa.text("lower(username)"), unique=True),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    username: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    rol: Mapped[Rol] = mapped_column(enum_col(Rol), nullable=False)
    activo: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=True, server_default=sa.true()
    )
    created_at: Mapped[datetime] = _created_at()


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    __table_args__ = (sa.CheckConstraint("cilindrada > 0", name="ck_vehiculos_cilindrada"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    marca: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    modelo: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    imagen: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    cilindrada: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    categoria: Mapped[Categoria] = mapped_column(enum_col(Categoria), nullable=False)
    created_at: Mapped[datetime] = _created_at()

    precios: Mapped[list["Precio"]] = relationship(
        back_populates="vehiculo", cascade="all, delete-orphan", passive_deletes=True
    )
    placas: Mapped[list["Placa"]] = relationship(
        back_populates="vehiculo", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def cantidad(self) -> int:
        return len(self.placas)


class Precio(Base):
    __tablename__ = "precios"
    __table_args__ = (
        sa.UniqueConstraint("vehiculo_id", "tarifa", name="uq_precios_vehiculo_tarifa"),
        sa.CheckConstraint("monto > 0", name="ck_precios_monto"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False
    )
    tarifa: Mapped[Tarifa] = mapped_column(enum_col(Tarifa), nullable=False)
    monto: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)

    vehiculo: Mapped[Vehiculo] = relationship(back_populates="precios")


class Placa(Base):
    __tablename__ = "placas"
    __table_args__ = (
        sa.CheckConstraint(
            "((estado = 'Rentada') = (fecha_hora_finalizacion IS NOT NULL))",
            name="ck_placas_estado_fecha",
        ),
        sa.Index(
            "uq_placas_placa",
            sa.text("upper(placa)"),
            unique=True,
            postgresql_where=sa.text("upper(placa) <> 'NUEVA'"),
        ),
        sa.Index("ix_placas_vehiculo_id", "vehiculo_id"),
        sa.Index("ix_placas_estado", "estado"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    placa: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default="NUEVA", server_default="NUEVA"
    )
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("vehiculos.id", ondelete="CASCADE"), nullable=False
    )
    estado: Mapped[EstadoPlaca] = mapped_column(
        enum_col(EstadoPlaca),
        nullable=False,
        default=EstadoPlaca.DISPONIBLE,
        server_default=EstadoPlaca.DISPONIBLE.value,
    )
    ubicacion_actual: Mapped[Ubicacion] = mapped_column(
        enum_col(Ubicacion),
        nullable=False,
        default=Ubicacion.TALLER_NICO,
        server_default=Ubicacion.TALLER_NICO.value,
    )
    fecha_hora_finalizacion: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = _created_at()

    vehiculo: Mapped[Vehiculo] = relationship(back_populates="placas")


class Renta(Base):
    __tablename__ = "rentas"
    __table_args__ = (
        sa.Index("ix_rentas_estado", "estado"),
        sa.Index("ix_rentas_fin_programado", "fin_programado"),
        sa.Index("ix_rentas_inicio", "inicio"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    placa_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("placas.id"), nullable=False)
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("vehiculos.id"), nullable=False)
    usuario_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("usuarios.id"), nullable=False)
    inicio: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    fin_programado: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    fin_real: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    monto: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    desglose: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    estado: Mapped[EstadoRenta] = mapped_column(
        enum_col(EstadoRenta),
        nullable=False,
        default=EstadoRenta.ACTIVA,
        server_default=EstadoRenta.ACTIVA.value,
    )
    ubicacion_recibida: Mapped[Optional[Ubicacion]] = mapped_column(
        enum_col(Ubicacion, name="ubicacion_recibida"), nullable=True
    )
    recibida_por: Mapped[Optional[uuid.UUID]] = mapped_column(
        sa.ForeignKey("usuarios.id"), nullable=True
    )
    recibida_en: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = _created_at()

    placa: Mapped[Placa] = relationship(foreign_keys=[placa_id])
    vehiculo: Mapped[Vehiculo] = relationship(foreign_keys=[vehiculo_id])
    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id])
    recibida_por_usuario: Mapped[Optional[Usuario]] = relationship(foreign_keys=[recibida_por])
