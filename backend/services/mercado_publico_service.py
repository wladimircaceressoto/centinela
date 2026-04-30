import requests
import os
import time
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from models.models import Licitacion, Item, Adjudicacion
from schemas.schemas import LicitacionSchema

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)


class MercadoPublicoService:
    """
    Servicio para interactuar con la API de Mercado Público.
    Maneja la obtención y procesamiento de licitaciones adjudicadas.
    """

    def __init__(self) -> None:
        """Inicializa el servicio con configuración de Mercado Público."""
        self.mp_ticket: str = os.getenv("MP_TICKET", "")
        if not self.mp_ticket:
            raise ValueError("La variable MP_TICKET no está configurada en .env")

        self.base_url: str = "https://api.mercadopublico.cl/servicios/v1/publico"
        self.headers: Dict[str, str] = {
            "User-Agent": "Centinela-PFJ-Printer/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Configuración de timeouts para las llamadas API
        self.timeout: int = 30

    def _hacer_llamada_api(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Método auxiliar para hacer llamadas a la API de Mercado Público.

        Args:
            url (str): URL completa de la API
            params (Optional[Dict[str, Any]]): Parámetros de consulta

        Returns:
            Dict[str, Any]: Respuesta JSON de la API

        Raises:
            Exception: Si hay error en la llamada a la API
        """
        try:
            response: requests.Response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            data: Dict[str, Any] = response.json()

            # Verificar si la respuesta tiene el formato esperado
            if "codigoError" in data and data["codigoError"] != 0:
                error_msg: str = data.get("mensajeError", "Error desconocido en API de Mercado Público")
                logger.error(f"Error en API de Mercado Público: {error_msg}")
                raise Exception(f"Error en API: {error_msg}")

            return data

        except requests.exceptions.Timeout:
            logger.error("Timeout en llamada a API de Mercado Público")
            raise Exception("Timeout en conexión con API de Mercado Público")

        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con API de Mercado Público")
            raise Exception("Error de conexión con API de Mercado Público")

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP en API de Mercado Público: {str(e)}")
            raise Exception(f"Error HTTP en API de Mercado Público: {str(e)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en solicitud a API de Mercado Público: {str(e)}")
            raise Exception(f"Error en solicitud a API de Mercado Público: {str(e)}")

        except ValueError as e:
            logger.error(f"Error al parsear respuesta JSON: {str(e)}")
            raise Exception(f"Error al procesar respuesta de API: {str(e)}")

    def _obtener_detalle_licitacion(self, codigo_externo: str) -> Dict[str, Any]:
        """
        Obtiene el detalle completo de una licitación incluyendo ítems y adjudicaciones.
        """
        # CORRECCIÓN: La URL base no lleva el código insertado
        url: str = f"{self.base_url}/licitaciones.json"
        
        # CORRECCIÓN: El código se envía como un parámetro adicional
        params: Dict[str, str] = {
            "ticket": self.mp_ticket,
            "codigo": codigo_externo
        }

        logger.info(f"Obteniendo detalle de licitación: {codigo_externo}")
        return self._hacer_llamada_api(url, params)

    def _procesar_licitacion_para_email(self, licitacion_data: Dict[str, Any]) -> List[Dict[str, str]]:
        resultados = []
        try:
            lic_data = licitacion_data.get("Listado", [{}])[0]
            if not lic_data: return resultados

            codigo_externo = lic_data.get("CodigoExterno", "")
            nombre_licitacion = lic_data.get("Nombre", "")
            
            # Vamos DIRECTO a los ítems, ignoramos la cabecera tramposa
            items = lic_data.get("Items", {}).get("Listado", [])
            ruts_encontrados = set()

            for item in items:
                adj_item = item.get("Adjudicacion")
                if isinstance(adj_item, dict):
                    rut = adj_item.get("RutProveedor", "")
                    empresa = adj_item.get("NombreProveedor", "")
                    monto = str(adj_item.get("MontoEstimado", lic_data.get("MontoEstimado", 0)))

                    # Si hay ganador y no lo hemos agregado ya al correo
                    if rut and empresa and rut not in ruts_encontrados:
                        resultados.append({
                            "codigo_externo": codigo_externo,
                            "nombre_licitacion": nombre_licitacion,
                            "empresa_ganadora": empresa,
                            "rut": rut,
                            "monto_adjudicado": monto
                        })
                        ruts_encontrados.add(rut)
        except Exception as e:
            logger.error(f"Error parseando email: {e}")
        return resultados

    def _guardar_licitacion_en_db(self, licitacion_data: Dict[str, Any], db: Session) -> Licitacion:
        listado = licitacion_data.get("Listado", [])
        if not listado:
            raise ValueError("Datos incompletos")

        lic_data = listado[0]
        licitacion = Licitacion(
            codigo_externo=lic_data.get("CodigoExterno", ""),
            nombre=lic_data.get("Nombre", ""),
            estado=lic_data.get("Estado", ""),
            monto_estimado=lic_data.get("MontoEstimado", 0),
            region_unidad=lic_data.get("RegionUnidad", ""),
            fecha_adjudicacion=datetime.now()
        )

        items_data = lic_data.get("Items", {}).get("Listado", [])
        ruts_guardados = set()

        # Vamos DIRECTO a los ítems a buscar a los ganadores
        for item_data in items_data:
            adj_data = item_data.get("Adjudicacion")
            if isinstance(adj_data, dict):
                rut = adj_data.get("RutProveedor", "")
                if rut and rut not in ruts_guardados:
                    adjudicacion = Adjudicacion(
                        codigo_licitacion=licitacion.codigo_externo,
                        rut_proveedor=rut,
                        nombre_proveedor=adj_data.get("NombreProveedor", ""),
                        monto_ganador=adj_data.get("MontoEstimado", lic_data.get("MontoEstimado", 0))
                    )
                    licitacion.adjudicaciones.append(adjudicacion)
                    ruts_guardados.add(rut)

        db.add(licitacion)
        db.commit()
        db.refresh(licitacion)
        logger.info(f"Licitación guardada exitosamente: {licitacion.codigo_externo}")
        return licitacion
    
    def obtener_licitaciones_adjudicadas(self, fecha: str, db: Session) -> List[Dict[str, str]]:
        """
        Obtiene licitaciones adjudicadas para una fecha específica desde Mercado Público.

        Args:
            fecha (str): Fecha en formato DDMMYYYY (ej: "01042026")
            db (Session): Sesión de base de datos SQLAlchemy

        Returns:
            List[Dict[str, str]]: Lista de licitaciones formateadas para EmailService
                Formato: [
                    {
                        "codigo_externo": str,
                        "nombre_licitacion": str,
                        "empresa_ganadora": str,
                        "rut": str,
                        "monto_adjudicado": str
                    },
                    ...
                ]
        """
        resultados: List[Dict[str, str]] = []

        try:
            # Primera llamada: obtener lista de licitaciones adjudicadas por fecha
            url_licitaciones: str = f"{self.base_url}/licitaciones.json"
            params: Dict[str, str] = {
                "ticket": self.mp_ticket,
                "fecha": fecha,
                "estado": "adjudicada"  
            }

            logger.info(f"Consultando licitaciones adjudicadas para fecha: {fecha}")
            response_licitaciones: Dict[str, Any] = self._hacer_llamada_api(url_licitaciones, params)

            # Procesar cada licitación encontrada
            licitaciones_list: List[Dict[str, Any]] = response_licitaciones.get("Listado", [])

            if not licitaciones_list:
                logger.info(f"No se encontraron licitaciones adjudicadas para la fecha {fecha}")
                return resultados

            logger.info(f"Se encontraron {len(licitaciones_list)} licitaciones adjudicadas")

            for lic_basica in licitaciones_list:
                codigo_externo: str = lic_basica.get("CodigoExterno", "")
                nombre_lic: str = lic_basica.get("Nombre", "").lower()

                # --- EL HACK DE LAS 1:30 AM ---
                # Si no tiene la palabra "impre", la saltamos
                if "impre" not in nombre_lic:
                    continue
                # ------------------------------

                if not codigo_externo:
                    logger.warning("Licitación sin código externo, omitiendo")
                    continue

                try:
                    # Verificar si ya existe en la base de datos
                    existe: Optional[Licitacion] = db.query(Licitacion).filter(
                        Licitacion.codigo_externo == codigo_externo
                    ).first()

                    if existe:
                        logger.info(f"Licitación {codigo_externo} ya existe en BD, procesando para email")
                        # Si existe, obtener datos para email desde BD
                        for adj in existe.adjudicaciones:
                            resultados.append({
                                "codigo_externo": existe.codigo_externo,
                                "nombre_licitacion": existe.nombre,
                                "empresa_ganadora": adj.nombre_proveedor,
                                "rut": adj.rut_proveedor,
                                "monto_adjudicado": str(adj.monto_ganador)
                            })
                        continue

                    # Si no existe, obtener detalle completo desde API
                    time.sleep(1.5)
                    detalle_licitacion: Dict[str, Any] = self._obtener_detalle_licitacion(codigo_externo)

                    # Guardar en base de datos
                    try:
                        self._guardar_licitacion_en_db(detalle_licitacion, db)
                        logger.info(f"Licitación {codigo_externo} guardada exitosamente en BD")
                    except Exception as e:
                        logger.error(f"Error al guardar licitación {codigo_externo} en BD: {str(e)}")
                        db.rollback()
                        continue

                    # Procesar para respuesta de email
                    licitaciones_email: List[Dict[str, str]] = self._procesar_licitacion_para_email(detalle_licitacion)
                    resultados.extend(licitaciones_email)

                except Exception as e:
                    logger.error(f"Error procesando licitación {codigo_externo}: {str(e)}")
                    continue

            logger.info(f"Procesamiento completado. Total licitaciones para email: {len(resultados)}")
            return resultados

        except Exception as e:
            logger.error(f"Error general en obtener_licitaciones_adjudicadas: {str(e)}")
            db.rollback()
            raise Exception(f"Error al obtener licitaciones adjudicadas: {str(e)}")


# Ejemplo de uso
if __name__ == "__main__":
    from database.database import SessionLocal

    try:
        service: MercadoPublicoService = MercadoPublicoService()
        db: Session = SessionLocal()

        # Ejemplo: obtener licitaciones del 1 de abril de 2026
        licitaciones: List[Dict[str, str]] = service.obtener_licitaciones_adjudicadas("24042026", db)

        print(f"Se encontraron {len(licitaciones)} licitaciones adjudicadas")
        for lic in licitaciones[:3]:  # Mostrar solo las primeras 3
            print(f"- {lic['codigo_externo']}: {lic['empresa_ganadora']} - ${lic['monto_adjudicado']}")

    except Exception as e:
        logger.error(f"Error en ejemplo de uso: {str(e)}")
    finally:
        db.close()