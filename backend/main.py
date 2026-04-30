"""
Centinela API - Motor de Inteligencia Comercial
Sistema principal de la aplicación backend.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Generator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import SessionLocal, engine
from models.models import Base
from services.mercado_publico_service import MercadoPublicoService
from services.email_service import EmailService
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cargar variables de entorno
load_dotenv()

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Inicializar aplicación FastAPI
app: FastAPI = FastAPI(title="API Centinela")


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión de base de datos para dependencias de FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    return {"estado": "Centinela API en línea"}


@app.post("/api/v1/ejecutar-centinela")
def ejecutar_centinela(
    fecha: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ejecuta el proceso principal de búsqueda y notificación de licitaciones adjudicadas."""
    try:
        if not fecha:
            fecha_obj: datetime = datetime.now() - timedelta(days=1)
            fecha = fecha_obj.strftime("%d%m%Y")

        service_mp = MercadoPublicoService()
        licitaciones = service_mp.obtener_licitaciones_adjudicadas(fecha, db)

        email_destino: Optional[str] = os.getenv("EMAIL_DAVID")
        if not email_destino:
            raise ValueError("La variable EMAIL_DAVID no está configurada en .env")

        email_service = EmailService()
        email_service.enviar_reporte_adjudicaciones(email_destino, licitaciones)

        return {
            "estado": "éxito",
            "fecha_procesada": fecha,
            "total_licitaciones_encontradas": len(licitaciones)
        }

    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar Centinela: {str(exc)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
