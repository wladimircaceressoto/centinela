# Bitácora de Desarrollo - Proyecto Centinela (Día 1)
**Fecha:** 25 de abril de 2026 
**Fase Actual:** Fase 1 (Estudio de Mercado Histórico)

## Hitos Logrados:
1. **Descubrimiento de API (El Eslabón Perdido):** - Se analizó la API de Mercado Público y se descubrió que no es necesario consultar el endpoint de Órdenes de Compra para el estudio de mercado. La información de adjudicación (RUT, ganador, y montos) viene integrada directamente en el detalle de la Licitación (`Estado 8`). 
   - *Nota de negocio:* Se detectó una adjudicación real de venta de tóners por más de 12 millones de pesos, validando la rentabilidad del proyecto para PFJ-Printer.
2. **Modelado de Datos (DER):** - Se diseñó la arquitectura relacional (1:N) con tres entidades principales: `Licitaciones`, `Items` y `Adjudicaciones`.
3. **Infraestructura Backend:** - Se inicializó el proyecto con `FastAPI` y tipado estricto.
   - Se configuró la conexión a la base de datos `PostgreSQL` (`centinela_db`) mediante `SQLAlchemy`, superando conflictos de versiones de sintaxis (transición a SQLAlchemy 2.0).
   - Las tablas fueron generadas exitosamente en pgAdmin.
4. **Validación de Datos:** - Se implementó la capa de validación usando `Pydantic V2` (`schemas.py`) para asegurar la integridad de los datos antes de su inserción en la base de datos.