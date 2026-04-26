"""
Configuración y utilidad para envío de emails.
Usa SMTP con las credenciales del .env.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

#  Configuración SMTP 
MAIL_FROM: str = os.getenv("MAIL_FROM", "")
MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")


def enviarEmail(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    """
    Envía un email usando SMTP.
    Retorna True si se envió correctamente, False si falló.
    """
    try:
        mensaje = MIMEMultipart("alternative")
        mensaje["From"] = MAIL_FROM
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto

        # Adjuntar body HTML
        mensaje.attach(MIMEText(cuerpo_html, "html"))

        # Conectar y enviar
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_FROM, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, destinatario, mensaje.as_string())

        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False


def generarEmailReset(nombre: str, reset_url: str) -> str:
    """Genera el HTML del email de recuperación de contraseña."""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 10px;">
            <h2 style="color: #333;">🔐 Recuperar contraseña</h2>
            <p>Hola <strong>{nombre}</strong>,</p>
            <p>Recibimos una solicitud para restablecer tu contraseña. Hacé clic en el botón:</p>
            <a href="{reset_url}" 
               style="display: inline-block; padding: 12px 24px; background-color: #007bff; 
                      color: white; text-decoration: none; border-radius: 5px; margin: 15px 0;">
                Restablecer contraseña
            </a>
            <p style="color: #888; font-size: 12px;">
                Este enlace expira en 30 minutos. Si no solicitaste esto, ignorá este email.
            </p>
        </div>
    </body>
    </html>
    """
