"""
User Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from datetime import datetime
from uuid import UUID

from app.api.deps import get_current_user, get_current_active_superuser, get_db
from app.models.user import User
from app.schemas.auth import UserResponse
from app.core.websocket_manager import ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()

    return [UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    ) for user in users]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get specific user (admin only)"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/{device_id}/all")
async def get_all_users(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all system users"""
    try:
        command = {
            "type": "get_all_users",
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
        logger.error(f"Error getting all users for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/active")
async def get_active_users(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get currently logged in users"""
    try:
        command = {
            "type": "get_active_users",
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
        logger.error(f"Error getting active users for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/details/{username}")
async def get_user_details(
    device_id: str,
    username: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific user"""
    try:
        command = {
            "type": "get_user_details",
            "device_id": device_id,
            "parameters": {
                "username": username
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
        logger.error(f"Error getting user details for {username} on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/groups")
async def get_user_groups(
    device_id: str,
    current_user = Depends(get_current_user),
    username: Optional[str] = Query(None, description="Get groups for specific user")
) -> Dict[str, Any]:
    """Get user groups information"""
    try:
        command = {
            "type": "get_user_groups",
            "device_id": device_id,
            "parameters": {
                "username": username
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
        logger.error(f"Error getting user groups for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/login-history")
async def get_login_history(
    device_id: str,
    current_user = Depends(get_current_user),
    username: Optional[str] = Query(None, description="Get history for specific user"),
    days: int = Query(7, ge=1, le=30, description="Number of days of history")
) -> Dict[str, Any]:
    """Get login history"""
    try:
        command = {
            "type": "get_login_history",
            "device_id": device_id,
            "parameters": {
                "username": username,
                "days": days
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
        logger.error(f"Error getting login history for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}/security-info")
async def get_user_security_info(
    device_id: str,
    current_user = Depends(get_current_user),
    username: Optional[str] = Query(None, description="Get security info for specific user")
) -> Dict[str, Any]:
    """Get security-related information about users"""
    try:
        command = {
            "type": "get_user_security_info",
            "device_id": device_id,
            "parameters": {
                "username": username
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
        logger.error(f"Error getting user security info for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/create")
async def create_user(
    device_id: str,
    user_data: Dict[str, Any],
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new user (requires root privileges)"""
    try:
        command = {
            "type": "create_user",
            "device_id": device_id,
            "parameters": user_data,
            "timestamp": datetime.utcnow().isoformat(),
            "initiated_by": current_user.get("username", "unknown")
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
        logger.error(f"Error creating user on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{device_id}/{username}")
async def delete_user(
    device_id: str,
    username: str,
    current_user = Depends(get_current_user),
    remove_home: bool = Query(False, description="Remove user's home directory")
) -> Dict[str, Any]:
    """Delete a user (requires root privileges)"""
    try:
        command = {
            "type": "delete_user",
            "device_id": device_id,
            "parameters": {
                "username": username,
                "remove_home": remove_home
            },
            "timestamp": datetime.utcnow().isoformat(),
            "initiated_by": current_user.get("username", "unknown")
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
        logger.error(f"Error deleting user {username} on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/start")
async def start_user_monitoring(
    device_id: str,
    current_user = Depends(get_current_user),
    interval: float = Query(60.0, ge=1.0, le=3600.0, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """Start user activity monitoring"""
    try:
        command = {
            "type": "start_user_monitoring",
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
                "message": "User monitoring started",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error starting user monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/monitoring/stop")
async def stop_user_monitoring(
    device_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Stop user activity monitoring"""
    try:
        command = {
            "type": "stop_user_monitoring",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await ws_manager.send_command_to_device(device_id, command)

        if response:
            return {
                "success": True,
                "message": "User monitoring stopped",
                "data": response,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Device not connected or command failed"
            )

    except Exception as e:
        logger.error(f"Error stopping user monitoring for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))