from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    devices,
    metrics,
    websocket,
    system,
    cpu,
    memory,
    disk,
    network,
    temperature,
    users,
    gpio
)

api_router = APIRouter()

# Include all endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(cpu.router, prefix="/cpu", tags=["cpu"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(disk.router, prefix="/disk", tags=["disk"])
api_router.include_router(network.router, prefix="/network", tags=["network"])
api_router.include_router(temperature.router, prefix="/temperature", tags=["temperature"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(gpio.router, prefix="/gpio", tags=["gpio"])