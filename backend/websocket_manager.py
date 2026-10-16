import json
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """
    Gerenciador de conexões WebSocket para o Telão da Gincana.
    Mantém registro de todas as telas conectadas e dispara atualizações simultâneas.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📡 [WebSocket] Nova tela conectada! Total de telas ativas: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 [WebSocket] Tela desconectada. Restantes: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Envia uma mensagem JSON para todas as telas conectadas.
        Se alguma tela falhar (ex: navegador fechado sem handshake), remove com segurança.
        """
        payload = json.dumps(message, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                print(f"⚠️ [WebSocket] Erro ao enviar para cliente: {e}")
                disconnected.append(connection)

        # Remove conexões mortas
        for dead_conn in disconnected:
            self.disconnect(dead_conn)

# Instância única global para ser compartilhada em toda a aplicação
ws_manager = ConnectionManager()
