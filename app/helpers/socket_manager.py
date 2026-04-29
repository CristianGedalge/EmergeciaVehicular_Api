from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Diccionario para mapear taller_id -> lista de conexiones activas (pueden ser múltiples pestañas)
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, taller_id: int):
        await websocket.accept()
        if taller_id not in self.active_connections:
            self.active_connections[taller_id] = []
        self.active_connections[taller_id].append(websocket)
        print(f"✅ Taller {taller_id} conectado por WebSocket")

    def disconnect(self, websocket: WebSocket, taller_id: int):
        if taller_id in self.active_connections:
            if websocket in self.active_connections[taller_id]:
                self.active_connections[taller_id].remove(websocket)
                if not self.active_connections[taller_id]:
                    del self.active_connections[taller_id]
        print(f"❌ Taller {taller_id} desconectado")

    async def send_to_taller(self, taller_id: int, message: dict):
        """Envía un mensaje JSON a todas las conexiones activas de un taller específico."""
        print(f"DEBUG_SOCKET: Intentando enviar a taller {taller_id}. Conexiones actuales en memoria: {list(self.active_connections.keys())}")
        if taller_id in self.active_connections:
            for connection in self.active_connections[taller_id]:
                try:
                    await connection.send_json(message)
                    print(f"DEBUG_SOCKET: Mensaje JSON enviado con éxito a taller {taller_id}")
                except Exception as e:
                    print(f"Error enviando mensaje a taller {taller_id}: {e}")
        else:
            print(f"DEBUG_SOCKET: El taller {taller_id} NO está conectado en este momento.")

socket_manager = ConnectionManager()
