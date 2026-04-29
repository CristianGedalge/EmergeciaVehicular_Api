from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.helpers.socket_manager import socket_manager
import asyncio
import json

router = APIRouter()

@router.websocket("/ws/{taller_id}")
async def websocket_endpoint(websocket: WebSocket, taller_id: int):
    """Endpoint para talleres, clientes y mecánicos."""
    await socket_manager.connect(websocket, taller_id)
    try:
        while True:
            data_text = await websocket.receive_text()
            
            # Keep-alive
            if data_text == "ping":
                await websocket.send_text("pong")
                continue
            
            # Procesar mensajes de rastreo (si vienen en formato JSON)
            try:
                msg = json.loads(data_text)
                if msg.get("evento") == "ACTUALIZAR_UBICACION":
                    cliente_id = msg.get("datos", {}).get("cliente_id")
                    if cliente_id:
                        # Reenviamos la ubi al cliente que está escuchando su propio socket
                        await socket_manager.send_to_user(cliente_id, {
                            "evento": "UBICACION_MECANICO",
                            "datos": msg.get("datos")
                        })
            except:
                pass # Si no es JSON (como un simple string), lo ignoramos

    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, taller_id)
    except Exception as e:
        print(f"Error en WebSocket {taller_id}: {e}")
        socket_manager.disconnect(websocket, taller_id)
