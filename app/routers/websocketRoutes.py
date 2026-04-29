from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.helpers.socket_manager import socket_manager

router = APIRouter()

@router.websocket("/ws/{taller_id}")
async def websocket_endpoint(websocket: WebSocket, taller_id: int):
    """Endpoint para que los talleres se conecten y reciban notificaciones en tiempo real."""
    await socket_manager.connect(websocket, taller_id)
    try:
        while True:
            # Esperar mensajes (opcional, sirve para keep-alive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, taller_id)
