"""
WebSocket Manager for real-time communication
"""
from typing import Dict, Set
from fastapi import WebSocket
import json
from datetime import datetime


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
                if user_id in self.user_devices:
                    del self.user_devices[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.append(connection)

            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

    async def broadcast_metrics(self, device_id: str, metrics: dict):
        for user_id, devices in self.user_devices.items():
            if device_id in devices:
                await self.send_personal_message(
                    json.dumps({
                        "type": "metrics",
                        "device_id": device_id,
                        "metrics": metrics,
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

    async def send_command_to_device(self, device_id: str, command: dict):
        """Send a command to a device (placeholder for now)"""
        # In a real implementation, this would send the command to the device agent
        # For now, return mock data based on command type
        command_type = command.get("type", "")

        if command_type == "get_system_info":
            return {
                "hostname": f"device-{device_id[:8]}",
                "os": "Linux",
                "kernel": "5.15.0",
                "arch": "aarch64",
                "uptime": 86400,
                "cpu_model": "ARM Cortex-A72",
                "cpu_cores": 4,
                "memory_total": 8192
            }
        elif command_type == "get_health":
            return {
                "status": "healthy",
                "cpu_temp": 45.5,
                "load_avg": [0.5, 0.6, 0.4],
                "services": ["ssh", "monitoring", "network"]
            }
        elif command_type == "get_performance":
            return {
                "cpu_usage": 35.5,
                "memory_usage": 62.3,
                "disk_io": {"read": 1024, "write": 512},
                "network_io": {"rx": 2048, "tx": 1024}
            }
        elif command_type == "get_uptime":
            return {
                "uptime_seconds": 86400,
                "boot_time": "2025-09-28T07:00:00Z",
                "users": 2,
                "load_average": [0.5, 0.6, 0.4]
            }
        # GPIO Control Commands
        elif command_type == "gpio_register_device":
            params = command.get("parameters", {})
            return {
                "success": True,
                "message": f"GPIO device '{params.get('device_name')}' registered (mock)",
                "device_info": params.get("config", {})
            }
        elif command_type == "gpio_list_devices":
            return {
                "success": True,
                "device_count": 2,
                "devices": [
                    {"name": "buzzer", "pin": 17, "device_type": "buzzer", "is_on": False},
                    {"name": "pump_relay", "pin": 27, "device_type": "relay", "is_on": False}
                ],
                "gpio_available": True
            }
        elif command_type == "gpio_get_device_info":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "name": device_name,
                "pin": 17 if device_name == "buzzer" else 27,
                "device_type": "buzzer" if device_name == "buzzer" else "relay",
                "description": f"Mock {device_name}",
                "active_state": "HIGH" if device_name == "buzzer" else "LOW",
                "max_runtime": 60 if device_name == "buzzer" else 300,
                "is_on": False
            }
        elif command_type == "gpio_turn_on":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "success": True,
                "message": f"Device '{device_name}' turned ON",
                "timestamp": datetime.utcnow().isoformat(),
                "status": {"device_name": device_name, "is_on": True}
            }
        elif command_type == "gpio_turn_off":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "success": True,
                "message": f"Device '{device_name}' turned OFF",
                "timestamp": datetime.utcnow().isoformat(),
                "session_runtime": 5.2,
                "status": {"device_name": device_name, "is_on": False}
            }
        elif command_type == "gpio_turn_on_duration":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            duration = params.get("duration", 10)
            return {
                "success": True,
                "message": f"Device '{device_name}' turned ON for {duration} seconds",
                "duration": duration,
                "auto_off_at": datetime.utcnow().isoformat(),
                "status": {"device_name": device_name, "is_on": True}
            }
        elif command_type == "gpio_get_status":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "device_name": device_name,
                "is_on": False,
                "pin": 17 if device_name == "buzzer" else 27,
                "device_type": "buzzer" if device_name == "buzzer" else "relay",
                "timestamp": datetime.utcnow().isoformat()
            }
        elif command_type == "gpio_get_statistics":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "device_name": device_name,
                "total_runtime": 125.5,
                "total_cycles": 15,
                "cycles_last_hour": 3,
                "current_session_runtime": 0,
                "is_on": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif command_type == "gpio_emergency_stop":
            params = command.get("parameters", {})
            device_name = params.get("device_name", "unknown")
            return {
                "success": True,
                "message": f"Emergency stop executed for '{device_name}'",
                "timestamp": datetime.utcnow().isoformat()
            }
        elif command_type == "gpio_emergency_stop_all":
            return {
                "success": True,
                "message": "All GPIO devices stopped",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {"status": "command_executed", "device_id": device_id}


ws_manager = ConnectionManager()