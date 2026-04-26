"""
Centinela API - Motor de Inteligencia Comercial
Sistema principal de la aplicación backend.
"""

import os
from typing import Dict, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from database.database import engine, Base
from models import models

# Esta es la línea que crea las tablas mágicamente si no existen
Base.metadata.create_all(bind=engine)
# Cargar variables de entorno
load_dotenv()

# Inicializar aplicación FastAPI
app: FastAPI = FastAPI(
    title="Centinela API",
    description="Motor de Inteligencia Comercial",
    version="1.0.0"
)


@app.get("/", response_class=JSONResponse)
async def health_check() -> Dict[str, Any]:
    """
    Health Check - Endpoint raíz para verificar el estado del sistema.
    
    Returns:
        Dict[str, Any]: Estado actual del sistema Centinela
    """
    return {
        "sistema": "Centinela",
        "estado": "En línea y vigilando",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
