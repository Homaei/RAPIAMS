from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Set
import json
import asyncio
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_token
from app.models.device import Device
from app.models.metrics import Metrics
from app.models.user import User

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_devices: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, device_ids: Set[str]):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        self.user_devices[user_id] = device_ids
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.user_devices[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass
    
    async def send_device_update(self, device_id: str, data: dict):
        for user_id, devices in self.user_devices.items():
            if device_id in devices:
                await self.send_personal_message(
                    json.dumps({
                        "type": "device_update",
                        "device_id": device_id,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    user_id
                )
    
    async def broadcast_alert(self, device_id: str, alert: dict):
        for user_id, devices in self.user_devices.items():
            if device_id in devices:
                await self.send_personal_message(
                    json.dumps({
                        "type": "alert",
                        "device_id": device_id,
                        "alert": alert,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    user_id
                )

manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008)
            return
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return
        
        devices_result = await db.execute(
            select(Device.id).where(Device.owner_id == user_id)
        )
        device_ids = {str(device_id) for device_id, in devices_result}
        
        await manager.connect(websocket, str(user_id), device_ids)
        
        try:
            while True:
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps({
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        )
                    
                    elif message.get("type") == "subscribe":
                        device_id = message.get("device_id")
                        if device_id:
                            device_check = await db.execute(
                                select(Device).where(
                                    Device.id == device_id,
                                    Device.owner_id == user_id
                                )
                            )
                            if device_check.scalar_one_or_none():
                                if str(user_id) in manager.user_devices:
                                    manager.user_devices[str(user_id)].add(device_id)
                                
                                await websocket.send_text(
                                    json.dumps({
                                        "type": "subscribed",
                                        "device_id": device_id,
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                                )
                    
                    elif message.get("type") == "unsubscribe":
                        device_id = message.get("device_id")
                        if device_id and str(user_id) in manager.user_devices:
                            manager.user_devices[str(user_id)].discard(device_id)
                            
                            await websocket.send_text(
                                json.dumps({
                                    "type": "unsubscribed",
                                    "device_id": device_id,
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            )
                
                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    )
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, str(user_id))
    
    except Exception as e:
        await websocket.close(code=1011)
        return


@router.websocket("/device/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008)
            return
        
        device_result = await db.execute(
            select(Device).where(
                Device.id == device_id,
                Device.owner_id == user_id
            )
        )
        device = device_result.scalar_one_or_none()
        
        if not device:
            await websocket.close(code=1008)
            return
        
        await websocket.accept()
        
        try:
            while True:
                latest_metrics = await db.execute(
                    select(Metrics)
                    .where(Metrics.device_id == device_id)
                    .order_by(Metrics.timestamp.desc())
                    .limit(1)
                )
                metrics = latest_metrics.scalar_one_or_none()
                
                if metrics:
                    await websocket.send_text(
                        json.dumps({
                            "type": "metrics",
                            "data": {
                                "cpu_percent": metrics.cpu_percent,
                                "memory_percent": metrics.memory_percent,
                                "disk_percent": metrics.disk_percent,
                                "temperature": metrics.cpu_temperature,
                                "is_online": device.is_online,
                                "last_seen": device.last_seen.isoformat() if device.last_seen else None
                            },
                            "timestamp": metrics.timestamp.isoformat()
                        })
                    )
                
                await asyncio.sleep(5)
        
        except WebSocketDisconnect:
            pass
    
    except Exception:
        await websocket.close(code=1011)