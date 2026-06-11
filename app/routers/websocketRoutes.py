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
                    print(f"===== DEBUG WS =====")
                    print(f"[WS Log] Recibido ACTUALIZAR_UBICACION -> Lat: {lat}, Lng: {lng} | Cliente_id: {cliente_id}, Taller_id: {taller_id}")
                    print(f"[WS Log] Conexiones activas en este servidor: {list(socket_manager.active_connections.keys())}")
                    
                    payload = {
                        "evento": "UBICACION_MECANICO",
                        "datos": datos
                    }
                    
                    if cliente_id:
                        if cliente_id in socket_manager.active_connections:
                            print(f"[WS Log] Enviando a Cliente {cliente_id}")
                        else:
                            print(f"[WS Log] Cliente {cliente_id} NO está conectado a este servidor.")
                        await socket_manager.send_to_user(cliente_id, payload)
                        
                    if taller_id:
                        if taller_id in socket_manager.active_connections:
                            print(f"[WS Log] Enviando a Taller {taller_id}")
                        else:
                            print(f"[WS Log] Taller {taller_id} NO está conectado a este servidor.")
                        await socket_manager.send_to_taller(taller_id, payload)
                    else:
                        print(f"[WS Log] ADVERTENCIA: taller_id es Nulo o Vacío en el mensaje del mecánico.")
                    print(f"====================")
            except Exception as e:
                print(f"Error procesando JSON de WS: {e}")

    except WebSocketDisconnect:
        socket_manager.disconnect(websocket, taller_id)
    except Exception as e:
        print(f"Error en WebSocket {taller_id}: {e}")
        socket_manager.disconnect(websocket, taller_id)
