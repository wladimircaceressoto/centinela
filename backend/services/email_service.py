import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from typing import List, Dict
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio de email para Centinela.
    Utiliza SMTP_SSL (puerto 465) para conexiones seguras.
    """

    def __init__(self) -> None:
        """Inicializa el servicio de email con variables de entorno."""
        self.smtp_server: str = os.getenv("SMTP_SERVER", "")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user: str = os.getenv("SMTP_USER", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")

        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            raise ValueError(
                "Las variables de configuración SMTP no están configuradas correctamente en .env"
            )

    def _enviar_correo(
        self, destinatario: str, asunto: str, cuerpo_html: str
    ) -> bool:
        """
        Método privado para enviar correos electrónicos.

        Args:
            destinatario (str): Dirección de correo del destinatario
            asunto (str): Asunto del correo
            cuerpo_html (str): Cuerpo del correo en formato HTML

        Returns:
            bool: True si el correo se envió exitosamente, False en caso contrario

        Raises:
            Exception: Si hay un error en la conexión o envío del correo
        """
        try:
            # Crear conexión SMTP_SSL (puerto 465 - conexión segura desde el inicio)
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                # Realizar login
                server.login(self.smtp_user, self.smtp_password)

                # Crear mensaje MIME
                mensaje: MIMEMultipart = MIMEMultipart("alternative")
                mensaje["Subject"] = asunto
                mensaje["From"] = self.smtp_user
                mensaje["To"] = destinatario

                # Adjuntar cuerpo HTML
                parte_html: MIMEText = MIMEText(cuerpo_html, "html", "utf-8")
                mensaje.attach(parte_html)

                # Enviar correo
                server.sendmail(self.smtp_user, destinatario, mensaje.as_string())

                logger.info(
                    f"Correo enviado exitosamente a {destinatario} - Asunto: {asunto}"
                )
                return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"Error de autenticación SMTP: Verifique usuario y contraseña. {str(e)}"
            )
            raise Exception(
                f"Error de autenticación: Credenciales SMTP inválidas"
            ) from e

        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP al enviar correo a {destinatario}: {str(e)}")
            raise Exception(f"Error SMTP: {str(e)}") from e

        except Exception as e:
            logger.error(f"Error inesperado al enviar correo a {destinatario}: {str(e)}")
            raise Exception(f"Error al enviar correo: {str(e)}") from e

    def enviar_correo_prueba(self, destinatario: str) -> bool:
        """
        Envía un correo de prueba formal para verificar la conexión SMTP.

        Args:
            destinatario (str): Dirección de correo del destinatario

        Returns:
            bool: True si el correo se envió exitosamente

        Raises:
            Exception: Si hay un error en el envío del correo
        """
        asunto: str = "Centinela Inicializado"

        cuerpo_html: str = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #1a3a52 0%, #2d5a7b 100%);
                    color: #ffffff;
                    padding: 30px 20px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }
                .header p {
                    margin: 8px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }
                .content {
                    padding: 40px 30px;
                    color: #333333;
                }
                .content h2 {
                    color: #1a3a52;
                    font-size: 20px;
                    margin: 0 0 15px 0;
                }
                .content p {
                    line-height: 1.6;
                    margin: 15px 0;
                    font-size: 14px;
                }
                .status-badge {
                    display: inline-block;
                    background-color: #d4edda;
                    color: #155724;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 600;
                    margin: 15px 0;
                    font-size: 13px;
                }
                .footer {
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                    font-size: 12px;
                    color: #666666;
                }
                .divider {
                    height: 2px;
                    background: linear-gradient(90deg, transparent, #2d5a7b, transparent);
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Centinela</h1>
                    <p>Sistema de Inteligencia Comercial para PFJ-Printer</p>
                </div>
                <div class="content">
                    <h2>Hola,</h2>
                    <p>Soy <strong>Centinela de PFJ-Printer</strong> y este es mi primer correo de prueba.</p>
                    <p>
                        <span class="status-badge">✓ Sistema Activo</span>
                    </p>
                    <p>
                        El sistema de inteligencia comercial está <strong>en línea</strong> y a la espera de instrucciones.
                    </p>
                    <div class="divider"></div>
                    <p style="font-size: 13px; color: #666666; margin-top: 25px;">
                        Este es un correo automatizado de prueba. Por favor, no responda a este mensaje.
                    </p>
                </div>
                <div class="footer">
                    <p>Centinela • Sistema de Inteligencia Comercial</p>
                    <p>© 2024 PFJ-Printer. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self._enviar_correo(destinatario, asunto, cuerpo_html)

    def enviar_reporte_adjudicaciones(
        self, destinatario: str, licitaciones: List[Dict[str, any]]
    ) -> bool:
        """
        Envía un reporte de licitaciones adjudicadas encontradas.

        Args:
            destinatario (str): Dirección de correo del destinatario
            licitaciones (List[Dict[str, any]]): Lista de diccionarios con información de licitaciones.
                Esperado: [
                    {
                        "codigo_externo": str,
                        "nombre_licitacion": str,
                        "empresa_ganadora": str,
                        "rut": str,
                        "monto_adjudicado": float|str
                    },
                    ...
                ]

        Returns:
            bool: True si el correo se envió exitosamente

        Raises:
            Exception: Si hay un error en el envío del correo
        """
        asunto: str = "Reporte Centinela: Nuevas Licitaciones Adjudicadas Encontradas"

        # Generar tabla HTML con las licitaciones
        cantidad_licitaciones: int = len(licitaciones)

        filas_tabla: str = ""
        for idx, licitacion in enumerate(licitaciones, 1):
            codigo_externo: str = str(licitacion.get("codigo_externo", "N/A"))
            nombre_licitacion: str = str(licitacion.get("nombre_licitacion", "N/A"))
            empresa_ganadora: str = str(licitacion.get("empresa_ganadora", "N/A"))
            rut: str = str(licitacion.get("rut", "N/A"))
            monto_adjudicado: str = str(licitacion.get("monto_adjudicado", "N/A"))

            # Aplicar formato de moneda si es posible
            try:
                monto_numerico: float = float(
                    monto_adjudicado.replace("$", "").replace(".", "").replace(",", ".")
                    if isinstance(monto_adjudicado, str)
                    else monto_adjudicado
                )
                monto_formateado: str = f"${monto_numerico:,.0f}".replace(",", ".")
            except (ValueError, AttributeError):
                monto_formateado: str = monto_adjudicado

            # Alternar colores de fila para mejor legibilidad
            color_fondo: str = "#f9f9f9" if idx % 2 == 0 else "#ffffff"

            filas_tabla += f"""
            <tr style="background-color: {color_fondo};">
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #1a3a52; font-weight: 500;">{codigo_externo}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #333333;">{nombre_licitacion}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #333333;">{empresa_ganadora}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #333333;">{rut}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #27ae60; font-weight: 600; text-align: right;">{monto_formateado}</td>
            </tr>
            """

        cuerpo_html: str = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 900px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #1a3a52 0%, #2d5a7b 100%);
                    color: #ffffff;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }}
                .header p {{
                    margin: 8px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                    color: #333333;
                }}
                .content h2 {{
                    color: #1a3a52;
                    font-size: 20px;
                    margin: 0 0 10px 0;
                }}
                .content p {{
                    line-height: 1.6;
                    margin: 15px 0;
                    font-size: 14px;
                }}
                .badge {{
                    display: inline-block;
                    background-color: #e3f2fd;
                    color: #1a3a52;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: 600;
                    margin: 15px 0;
                    font-size: 13px;
                }}
                .table-wrapper {{
                    margin: 25px 0;
                    border-radius: 6px;
                    overflow: hidden;
                    border: 1px solid #e0e0e0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                thead {{
                    background: linear-gradient(135deg, #2d5a7b 0%, #1a3a52 100%);
                    color: #ffffff;
                }}
                th {{
                    padding: 14px 12px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 13px;
                    letter-spacing: 0.5px;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #e0e0e0;
                    font-size: 13px;
                }}
                tbody tr:last-child td {{
                    border-bottom: none;
                }}
                .summary {{
                    background-color: #f0f4f8;
                    padding: 15px;
                    border-left: 4px solid #2d5a7b;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .summary p {{
                    margin: 5px 0;
                    font-size: 13px;
                }}
                .summary strong {{
                    color: #1a3a52;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                    font-size: 12px;
                    color: #666666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Centinela</h1>
                    <p>Reporte de Licitaciones Adjudicadas</p>
                </div>
                <div class="content">
                    <h2>Hola,</h2>
                    <p>
                        Soy <strong>Centinela de PFJ-Printer</strong> y he encontrado <span class="badge">{cantidad_licitaciones} licitación(es)</span> adjudicada(s) dentro del plazo de búsqueda establecido, de acuerdo al siguiente detalle:
                    </p>

                    <div class="summary">
                        <p><strong>Total de licitaciones:</strong> {cantidad_licitaciones}</p>
                        <p><strong>Fecha de reporte:</strong> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>

                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Código Externo</th>
                                    <th>Nombre de Licitación</th>
                                    <th>Empresa Ganadora</th>
                                    <th>RUT</th>
                                    <th style="text-align: right;">Monto Adjudicado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filas_tabla}
                            </tbody>
                        </table>
                    </div>

                    <p style="font-size: 13px; color: #666666; margin-top: 25px;">
                        Este es un correo automatizado. Por favor, no responda a este mensaje. Para más información, acceda al sistema Centinela.
                    </p>
                </div>
                <div class="footer">
                    <p>Centinela • Sistema de Inteligencia Comercial</p>
                    <p>© 2024 PFJ-Printer. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self._enviar_correo(destinatario, asunto, cuerpo_html)


# Ejemplo de uso
if __name__ == "__main__":
    try:
        email_service: EmailService = EmailService()
        email_service.enviar_correo_prueba("wladimircaceressoto@gmail.com")
        # email_service.enviar_reporte_adjudicaciones("correo@ejemplo.com", [...])
    except Exception as e:
        logger.error(f"Error en email_service: {str(e)}")
