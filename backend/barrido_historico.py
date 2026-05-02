"""
Barrido Histórico de Licitaciones - Mercado Público

Script autónomo que recorre un rango de fechas día por día, consultando la API de
Mercado Público para guardar licitaciones históricas adjudicadas en la base de datos.

Características:
- Itera desde 01/01/2026 hasta la fecha actual
- Respeta límites de rate limiting con pausas de 5 segundos entre peticiones
- Manejo robusto de errores: continúa ejecutándose aunque un día falle
- Logging detallado para auditoría y debugging
- Cierre seguro de recursos

Uso:
    python barrido_historico.py
"""

import logging
from datetime import datetime, timedelta
import time
import os
from services.email_service import EmailService

from database.database import SessionLocal
from services.mercado_publico_service import MercadoPublicoService


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('barrido_historico.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def formatear_fecha_api(fecha: datetime) -> str:
    """
    Formatea una fecha de datetime al formato requerido por la API de Mercado Público.
    
    Args:
        fecha (datetime): Fecha a formatear
        
    Returns:
        str: Fecha en formato DDMMYYYY (ej: "01012026")
    """
    return fecha.strftime("%d%m%Y")


def ejecutar_barrido_historico() -> None:
    """
    Ejecuta el barrido histórico completo desde 01/01/2026 hasta hoy.
    
    Itera día por día, llamando a la API de Mercado Público y guardando
    licitaciones adjudicadas en la base de datos. Incluye pausas de 5 segundos
    entre peticiones para respetar los límites de rate limiting.
    
    Raises:
        Exception: Se capturan y registran todos los errores, pero no se lanzan
                   para permitir continuidad del proceso
    """
    # Definir rango de fechas
    fecha_inicio = datetime(2026, 1, 1)
    fecha_fin = datetime.now()
    
    logger.info("=" * 80)
    logger.info(f"Iniciando barrido histórico de licitaciones")
    logger.info(f"Rango de fechas: {fecha_inicio.date()} a {fecha_fin.date()}")
    logger.info("=" * 80)
    
    # Inicializar base de datos y servicio
    db = None
    service = None
    contador_exito = 0
    contador_error = 0
    contador_total = 0
    todas_las_licitaciones_encontradas = []
    
    try:
        db = SessionLocal()
        service = MercadoPublicoService()
        
        # Iterar día por día
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            contador_total += 1
            fecha_formateada = formatear_fecha_api(fecha_actual)
            
            try:
                logger.info(f"\n[{contador_total}] Procesando fecha: {fecha_actual.date()} ({fecha_formateada})")
                
                # Llamar al servicio para obtener licitaciones adjudicadas
                licitaciones = service.obtener_licitaciones_adjudicadas(fecha_formateada, db)
                
                contador_exito += 1
                logger.info(f"✓ Éxito: Se procesaron {len(licitaciones)} licitaciones para {fecha_actual.date()}")
                todas_las_licitaciones_encontradas.extend(licitaciones)

            except Exception as e:
                contador_error += 1
                logger.error(f"✗ Error procesando fecha {fecha_actual.date()}: {str(e)}")
                logger.error(f"  Continuando con el siguiente día...")
                # No relanzamos la excepción para permitir continuidad
            
            finally:
                # Protección de API: pausa de 5 segundos entre peticiones
                if fecha_actual < fecha_fin:
                    logger.debug("Aguardando 5 segundos antes de siguiente petición (rate limiting)...")
                    time.sleep(5)
            
            # Avanzar al siguiente día
            fecha_actual += timedelta(days=1)
        
        if todas_las_licitaciones_encontradas:
            logger.info(f"Preparando Reporte Maestro con {len(todas_las_licitaciones_encontradas)} licitaciones en total...")
            try:
                email_service = EmailService()
                email_destino = os.getenv("EMAIL_DAVID") # O pon directamente "stecnico@pfj-printer.cl" si prefieres
                email_service.enviar_reporte_adjudicaciones(email_destino, todas_las_licitaciones_encontradas)
                logger.info("¡Reporte Maestro enviado exitosamente!")
            except Exception as e:
                logger.error(f"Error al enviar el Reporte Maestro: {str(e)}")
                
        # Resumen final
        logger.info("\n" + "=" * 80)
        logger.info("BARRIDO HISTÓRICO COMPLETADO")
        logger.info(f"Total de días procesados: {contador_total}")
        logger.info(f"Días exitosos: {contador_exito}")
        logger.info(f"Días con error: {contador_error}")
        logger.info(f"Tasa de éxito: {(contador_exito/contador_total*100):.1f}%")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.critical(f"Error crítico durante el barrido histórico: {str(e)}")
        logger.critical("El proceso ha sido interrumpido.")
        raise
        
    finally:
        # Cierre seguro de la sesión de base de datos
        if db:
            try:
                db.close()
                logger.info("Sesión de base de datos cerrada exitosamente")
            except Exception as e:
                logger.error(f"Error al cerrar sesión de base de datos: {str(e)}")


if __name__ == "__main__":
    try:
        ejecutar_barrido_historico()
    except KeyboardInterrupt:
        logger.warning("Barrido histórico interrumpido por el usuario")
    except Exception as e:
        logger.critical(f"Barrido histórico falló: {str(e)}")
        exit(1)
