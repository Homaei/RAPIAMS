"""
Network Monitoring API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.api.deps import get_current_user
from app.core.websocket_manager import ws_manager

router = APIRouter(prefix="/network", tags=["network"])
logger = logging.getLogger(__name__)


@router.get("/{device_id}/interfaces")
async def get_network_interfaces(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get network interface information"""
    try:
        command = {
            "type": "get_network_interfaces",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting network interfaces for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/io-stats")
async def get_network_io_stats(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get network I/O statistics"""
    try:
        command = {
            "type": "get_network_io_stats",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting network I/O stats for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/connections")
async def get_network_connections(
    device_id: str,
    current_user = Depends(get_current_user),
    kind: str = Query("inet", description="Connection type (inet, inet4, inet6, tcp, udp)")
) -> Dict[str, Any]:
    """Get network connections"""
    try:
        command = {
            "type": "get_network_connections",
            "device_id": device_id,
            "parameters": {
                "kind": kind
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting network connections for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/connectivity-test")
async def test_connectivity(
    device_id: str,
    current_user = Depends(get_current_user),
    hosts: List[str] = Query(["8.8.8.8", "google.com"], description="Hosts to test connectivity")
) -> Dict[str, Any]:
    """Test network connectivity to various hosts"""
    try:
        command = {
            "type": "test_connectivity",
            "device_id": device_id,
            "parameters": {
                "hosts": hosts
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error testing connectivity for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/speed-test")
async def network_speed_test(
    device_id: str,
    current_user = Depends(get_current_user),
    interface: Optional[str] = Query(None, description="Specific interface to test")
) -> Dict[str, Any]:
    """Perform network speed test"""
    try:
        command = {
            "type": "network_speed_test",
            "device_id": device_id,
            "parameters": {
                "interface": interface
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error performing speed test for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/scan-local-network")
async def scan_local_network(
    device_id: str,
    current_user = Depends(get_current_user),
    network: Optional[str] = Query(None, description="Network CIDR to scan (auto-detect if not provided)")
) -> Dict[str, Any]:
    """Scan local network for active hosts"""
    try:
        command = {
            "type": "scan_local_network",
            "device_id": device_id,
            "parameters": {
                "network": network
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error scanning local network for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/alerts")
async def get_network_alerts(
    device_id: str,
    current_user = Depends(get_current_user),
    high_traffic_threshold_mbps: float = Query(50.0, ge=0, description="High traffic threshold in Mbps"),
    connection_threshold: int = Query(1000, ge=1, description="High connection count threshold")
) -> Dict[str, Any]:
    """Get network-related alerts"""
    try:
        command = {
            "type": "get_network_alerts",
            "device_id": device_id,
            "parameters": {
                "high_traffic_threshold_mbps": high_traffic_threshold_mbps,
                "connection_threshold": connection_threshold
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error getting network alerts for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/start")
async def start_network_monitoring(
    device_id: str,
    current_user = Depends(get_current_user),
    interval: float = Query(1.0, ge=0.1, le=60.0, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """Start network monitoring"""
    try:
        command = {
            "type": "start_network_monitoring",
            "device_id": device_id,
            "parameters": {
                "interval": interval
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Network monitoring started",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error starting network monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/stop")
async def stop_network_monitoring(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop network monitoring"""
    try:
        command = {
            "type": "stop_network_monitoring",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "Network monitoring stopped",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error stopping network monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))