import requests
import os
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

        Args:
            codigo_externo (str): Código externo de la licitación

        Returns:
            Dict[str, Any]: Detalle completo de la licitación
        """
        url: str = f"{self.base_url}/licitaciones/{codigo_externo}.json"
        params: Dict[str, str] = {"ticket": self.mp_ticket}

        logger.info(f"Obteniendo detalle de licitación: {codigo_externo}")
        return self._hacer_llamada_api(url, params)

    def _procesar_licitacion_para_email(self, licitacion_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Procesa los datos de una licitación para formatearlos según lo esperado por EmailService.

        Args:
            licitacion_data (Dict[str, Any]): Datos de la licitación desde la API

        Returns:
            List[Dict[str, str]]: Lista de diccionarios formateados para email
        """
        resultados: List[Dict[str, str]] = []

        # Extraer información básica de la licitación
        codigo_externo: str = licitacion_data.get("Listado", [{}])[0].get("CodigoExterno", "")
        nombre_licitacion: str = licitacion_data.get("Listado", [{}])[0].get("Nombre", "")

        # Procesar adjudicaciones
        adjudicaciones: List[Dict[str, Any]] = licitacion_data.get("Adjudicacion", [])

        for adjudicacion in adjudicaciones:
            empresa_ganadora: str = adjudicacion.get("NombreProveedor", "")
            rut: str = adjudicacion.get("RutProveedor", "")
            monto_adjudicado: str = str(adjudicacion.get("MontoEstimado", 0))

            # Solo incluir adjudicaciones con datos completos
            if empresa_ganadora and rut:
                resultados.append({
                    "codigo_externo": codigo_externo,
                    "nombre_licitacion": nombre_licitacion,
                    "empresa_ganadora": empresa_ganadora,
                    "rut": rut,
                    "monto_adjudicado": monto_adjudicado
                })

        return resultados

    def _guardar_licitacion_en_db(
        self,
        licitacion_data: Dict[str, Any],
        db: Session
    ) -> Licitacion:
        """
        Guarda una licitación completa en la base de datos.

        Args:
            licitacion_data (Dict[str, Any]): Datos de la licitación desde la API
            db (Session): Sesión de base de datos

        Returns:
            Licitacion: Instancia del modelo Licitacion guardado
        """
        # Extraer datos básicos de la licitación
        listado: List[Dict[str, Any]] = licitacion_data.get("Listado", [])
        if not listado:
            raise ValueError("Datos de licitación incompletos")

        lic_data: Dict[str, Any] = listado[0]

        # Crear instancia de Licitacion
        licitacion: Licitacion = Licitacion(
            codigo_externo=lic_data.get("CodigoExterno", ""),
            nombre=lic_data.get("Nombre", ""),
            estado=lic_data.get("Estado", ""),
            monto_estimado=lic_data.get("MontoEstimado", 0),
            region_unidad=lic_data.get("RegionUnidad", ""),
            fecha_adjudicacion=datetime.now() if lic_data.get("Estado") == "Adjudicada" else None
        )

        # Agregar items si existen
        items_data: List[Dict[str, Any]] = licitacion_data.get("Items", [])
        for item_data in items_data:
            item: Item = Item(
                codigo_licitacion=licitacion.codigo_externo,
                nombre_producto=item_data.get("NombreProducto", ""),
                cantidad=item_data.get("Cantidad", 0),
                categoria=item_data.get("Categoria", None)
            )
            licitacion.items.append(item)

        # Agregar adjudicaciones si existen
        adjudicaciones_data: List[Dict[str, Any]] = licitacion_data.get("Adjudicacion", [])
        for adj_data in adjudicaciones_data:
            adjudicacion: Adjudicacion = Adjudicacion(
                codigo_licitacion=licitacion.codigo_externo,
                rut_proveedor=adj_data.get("RutProveedor", ""),
                nombre_proveedor=adj_data.get("NombreProveedor", ""),
                monto_ganador=adj_data.get("MontoEstimado", 0)
            )
            licitacion.adjudicaciones.append(adjudicacion)

        # Validar con Pydantic antes de guardar
        try:
            LicitacionSchema.model_validate(licitacion)
        except Exception as e:
            logger.error(f"Error de validación en licitación {licitacion.codigo_externo}: {str(e)}")
            raise ValueError(f"Datos de licitación inválidos: {str(e)}")

        # Guardar en base de datos
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
                "estado": "8"  # Estado 8 = Adjudicadas
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