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
                    datos = msg.get("datos", {})
                    cliente_id = datos.get("cliente_id")
                    taller_id = datos.get("taller_id")
                    lat = datos.get("lat")
                    lng = datos.get("lng")
                    print(f"[WS Log] Recibido ACTUALIZAR_UBICACION -> Lat: {lat}, Lng: {lng} | Reenviando a Cliente {cliente_id} y Taller {taller_id}")
                    
                    payload = {
                        "evento": "UBICACION_MECANICO",
                        "datos": datos
                    }
                    
                    if cliente_id:
                        await socket_manager.send_to_user(cliente_id, payload)
                    if taller_id:
                        await socket_manager.send_to_taller(taller_id, payload)
            except Exception as e:
                print(f"Error procesando JSON de WS: {e}")

    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, taller_id)
    except Exception as e:
        print(f"Error en WebSocket {taller_id}: {e}")
        socket_manager.disconnect(websocket, taller_id)
