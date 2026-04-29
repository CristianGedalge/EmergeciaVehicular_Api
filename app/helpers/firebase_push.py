"""
Helper para enviar notificaciones push usando Firebase Cloud Messaging (FCM).
Usa firebase-admin SDK con credenciales desde variable de entorno.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

# Inicializar Firebase solo una vez
_firebase_initialized = False

def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True
    
    try:
        # Leer credenciales desde variable de entorno (JSON string)
        creds_json = os.getenv("FIREBASE_CREDENTIALS")
        if not creds_json:
            print("⚠️ FIREBASE_CREDENTIALS no configurada. Push notifications deshabilitadas.")
            return False
        
        creds_dict = json.loads(creds_json)
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("✅ Firebase Admin SDK inicializado correctamente.")
        return True
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")
        return False


async def enviarPushNotification(fcm_token: str, titulo: str, cuerpo: str, data: dict = None):
    """
    Envía una notificación push a un dispositivo específico usando FCM.
    
    Args:
        fcm_token: Token FCM del dispositivo destino
        titulo: Título de la notificación
        cuerpo: Cuerpo/mensaje de la notificación
        data: Datos adicionales (opcional) que la app puede procesar
    """
    if not _init_firebase():
        print("⚠️ Firebase no inicializado. No se envió push notification.")
        return False
    
    if not fcm_token:
        print("⚠️ FCM token vacío. No se envió push notification.")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=cuerpo,
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        
        response = messaging.send(message)
        print(f"✅ Push notification enviada exitosamente. Message ID: {response}")
        return True
    except Exception as e:
        print(f"❌ Error enviando push notification: {e}")
        return False
