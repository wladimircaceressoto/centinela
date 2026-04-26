"""
Modelos de datos para el sistema Centinela.
Definición de tablas y relaciones con SQLAlchemy.
"""

from typing import List

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database.database import Base


class Licitacion(Base):
    """
    Modelo para la tabla de licitaciones.
    Representa una licitación en el sistema Centinela.
    """
    __tablename__ = "licitaciones"
    __allow_unmapped__ = True

    codigo_externo: str = Column(String, primary_key=True, index=True)
    nombre: str = Column(String, nullable=False)
    estado: str = Column(String, nullable=False)
    monto_estimado: float = Column(Float, nullable=True)
    region_unidad: str = Column(String, nullable=False)
    fecha_adjudicacion: DateTime = Column(DateTime, nullable=True)

    # Relaciones
    items: List["Item"] = relationship("Item", back_populates="licitacion")
    adjudicaciones: List["Adjudicacion"] = relationship("Adjudicacion", back_populates="licitacion")


class Item(Base):
    """
    Modelo para la tabla de items.
    Representa un ítem dentro de una licitación.
    """
    __tablename__ = "items"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    codigo_licitacion: str = Column(String, ForeignKey("licitaciones.codigo_externo"), nullable=False)
    nombre_producto: str = Column(String, nullable=False)
    cantidad: int = Column(Integer, nullable=False)
    categoria: str = Column(String, nullable=True)

    # Relación inversa
    licitacion: Licitacion = relationship("Licitacion", back_populates="items")


class Adjudicacion(Base):
    """
    Modelo para la tabla de adjudicaciones.
    Representa una adjudicación de una licitación.
    """
    __tablename__ = "adjudicaciones"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    codigo_licitacion: str = Column(String, ForeignKey("licitaciones.codigo_externo"), nullable=False)
    rut_proveedor: str = Column(String, nullable=False)
    nombre_proveedor: str = Column(String, nullable=False)
    monto_ganador: float = Column(Float, nullable=False)

    # Relación inversa
    licitacion: Licitacion = relationship("Licitacion", back_populates="adjudicaciones")