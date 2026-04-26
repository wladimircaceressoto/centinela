"""
Esquemas Pydantic para validación de datos en el sistema Centinela.
Validación de entrada y salida de datos de las tablas principales.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemSchema(BaseModel):
    """
    Esquema para validación de items en licitaciones.
    Representa un ítem que es parte de una licitación.
    """
    codigo_licitacion: str = Field(..., description="Código externo de la licitación")
    nombre_producto: str = Field(..., description="Nombre del producto o servicio")
    cantidad: int = Field(..., gt=0, description="Cantidad solicitada (debe ser mayor a 0)")
    categoria: Optional[str] = Field(None, description="Categoría opcional del producto")

    model_config = ConfigDict(from_attributes=True)


class AdjudicacionSchema(BaseModel):
    """
    Esquema para validación de adjudicaciones.
    Representa la asignación de un contrato a un proveedor en una licitación.
    """
    codigo_licitacion: str = Field(..., description="Código externo de la licitación")
    rut_proveedor: str = Field(..., description="RUT del proveedor adjudicado")
    nombre_proveedor: str = Field(..., description="Nombre comercial del proveedor")
    monto_ganador: float = Field(..., gt=0, description="Monto del contrato (debe ser mayor a 0)")

    model_config = ConfigDict(from_attributes=True)


class LicitacionSchema(BaseModel):
    """
    Esquema para validación de licitaciones.
    Representa una licitación completa con sus items y adjudicaciones.
    """
    codigo_externo: str = Field(..., description="Código único externo de la licitación")
    nombre: str = Field(..., description="Nombre descriptivo de la licitación")
    estado: str = Field(..., description="Estado actual de la licitación")
    monto_estimado: Optional[float] = Field(None, ge=0, description="Monto estimado del proceso (debe ser >= 0)")
    region_unidad: str = Field(..., description="Región o unidad responsable")
    fecha_adjudicacion: Optional[datetime] = Field(None, description="Fecha de adjudicación del contrato")
    items: List[ItemSchema] = Field(default=[], description="Lista de items asociados a la licitación")
    adjudicaciones: List[AdjudicacionSchema] = Field(default=[], description="Lista de adjudicaciones de la licitación")

    model_config = ConfigDict(from_attributes=True)
