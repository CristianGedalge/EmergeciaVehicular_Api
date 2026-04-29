from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.helpers.socket_manager import socket_manager
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/{taller_id}")
async def websocket_endpoint(websocket: WebSocket, taller_id: int):
    """Endpoint para que los talleres se conecten y reciban notificaciones en tiempo real."""
    await socket_manager.connect(websocket, taller_id)
    try:
        while True:
            # Recibir mensaje del cliente (incluye pings de keep-alive)
            data = await websocket.receive_text()
            # Si el cliente envía un ping, respondemos con pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, taller_id)
    except Exception as e:
        print(f"Error en WebSocket taller {taller_id}: {e}")
        socket_manager.disconnect(websocket, taller_id)
