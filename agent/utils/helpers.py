"""
Helper Functions - Utility functions for the enhanced monitoring system
Adapted from Telegram monitoring system
"""

import os
import re
import json
import subprocess
import logging
import socket
import time
import shlex
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any, Union
from functools import wraps

logger = logging.getLogger('monitoring.utils')

# Constants
BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
TIME_UNITS = [
    ('year', 365 * 24 * 3600),
    ('month', 30 * 24 * 3600),
    ('week', 7 * 24 * 3600),
    ('day', 24 * 3600),
    ('hour', 3600),
    ('minute', 60),
    ('second', 1)
]


def safe_execute(func):
    """Decorator for safe function execution with error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return None
    return wrapper


def run_command(command: Union[str, List[str]],
                shell: bool = False,
                timeout: int = 30,
                check: bool = False) -> Tuple[str, str, int]:
    """
    Execute system command safely with timeout

    Args:
        command: Command to execute (string or list)
        shell: Whether to use shell execution
        timeout: Command timeout in seconds
        check: Whether to raise exception on non-zero return code

    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    try:
        # Security: Avoid shell=True when possible
        if isinstance(command, str) and not shell:
            command = shlex.split(command)

        # Validate command to prevent injection
        if shell:
            logger.warning(f"Shell execution requested for: {command}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=shell,
            timeout=timeout,
            check=check
        )

        return result.stdout.strip(), result.stderr.strip(), result.returncode

    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout after {timeout}s: {command}")
        return "", f"Command timeout after {timeout} seconds", 124

    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {command}")
        return e.stdout or "", e.stderr or str(e), e.returncode

    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return "", str(e), 1


def format_bytes(bytes_value: Union[int, float], precision: int = 2) -> str:
    """
    Format bytes into human readable format

    Args:
        bytes_value: Number of bytes
        precision: Decimal precision

    Returns:
        Formatted string (e.g., "1.23 GB")
    """
    if bytes_value == 0:
        return "0 B"

    try:
        bytes_value = float(bytes_value)
        if bytes_value < 0:
            return "Invalid"

        for i, unit in enumerate(BYTE_UNITS):
            if bytes_value < 1024.0 or i == len(BYTE_UNITS) - 1:
                return f"{bytes_value:.{precision}f} {unit}"
            bytes_value /= 1024.0

        return f"{bytes_value:.{precision}f} {BYTE_UNITS[-1]}"

    except (ValueError, TypeError):
        return "Invalid"


def format_time(seconds: Union[int, float]) -> str:
    """
    Format seconds into human readable time format

    Args:
        seconds: Number of seconds

    Returns:
        Formatted string (e.g., "2 days, 3 hours, 45 minutes")
    """
    try:
        seconds = int(float(seconds))
        if seconds <= 0:
            return "0 seconds"

        parts = []
        for name, count in TIME_UNITS:
            value = seconds // count
            if value:
                plural = 's' if value != 1 else ''
                parts.append(f"{value} {name}{plural}")
                seconds %= count
                if len(parts) >= 3:  # Limit to 3 most significant units
                    break

        return ", ".join(parts) if parts else "0 seconds"

    except (ValueError, TypeError):
        return "Invalid"


def format_uptime(boot_time: datetime) -> str:
    """
    Format system uptime

    Args:
        boot_time: System boot time

    Returns:
        Formatted uptime string
    """
    try:
        uptime = datetime.now() - boot_time
        return format_time(uptime.total_seconds())
    except Exception:
        return "Unknown"


def get_hostname() -> str:
    """
    Get system hostname

    Returns:
        System hostname
    """
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def get_system_uptime() -> Optional[float]:
    """
    Get system uptime in seconds

    Returns:
        Uptime in seconds or None if unavailable
    """
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return uptime.total_seconds()
    except Exception:
        return None


def get_load_average() -> Optional[Tuple[float, float, float]]:
    """
    Get system load average

    Returns:
        Tuple of (1min, 5min, 15min) load averages or None
    """
    try:
        return os.getloadavg()
    except Exception:
        return None


def validate_input(input_string: str, input_type: str) -> bool:
    """
    Validate input string based on type

    Args:
        input_string: String to validate
        input_type: Type of validation to perform

    Returns:
        True if valid, False otherwise
    """
    if not input_string or not isinstance(input_string, str):
        return False

    input_string = input_string.strip()

    validation_patterns = {
        'service_name': r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$',
        'process_name': r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$',
        'filename': r'^[a-zA-Z0-9][a-zA-Z0-9._/-]*$',
        'hostname': r'^[a-zA-Z0-9][a-zA-Z0-9.-]*$',
        'ip_address': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
        'mac_address': r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'numeric': r'^\d+$'
    }

    pattern = validation_patterns.get(input_type)
    if not pattern:
        return False

    return bool(re.match(pattern, input_string))


def sanitize_input(input_string: str) -> str:
    """
    Sanitize input string by removing dangerous characters

    Args:
        input_string: String to sanitize

    Returns:
        Sanitized string
    """
    if not isinstance(input_string, str):
        return ""

    # Remove potentially dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '{', '}', '[', ']', '<', '>']
    sanitized = input_string

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())

    return sanitized.strip()


def is_valid_json(json_string: str) -> bool:
    """
    Check if string is valid JSON

    Args:
        json_string: String to validate

    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely load JSON with default fallback

    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def ensure_directory(directory_path: Union[str, Path]) -> bool:
    """
    Ensure directory exists, create if necessary

    Args:
        directory_path: Path to directory

    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """
    Get file size in bytes

    Args:
        file_path: Path to file

    Returns:
        File size in bytes or None if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return None


def get_file_age(file_path: Union[str, Path]) -> Optional[float]:
    """
    Get file age in seconds

    Args:
        file_path: Path to file

    Returns:
        File age in seconds or None if file doesn't exist
    """
    try:
        stat = Path(file_path).stat()
        return time.time() - stat.st_mtime
    except Exception:
        return None


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def get_raspberry_pi_model() -> str:
    """
    Get Raspberry Pi model information

    Returns:
        Pi model string or 'Unknown'
    """
    try:
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('Model'):
                        return line.split(':', 1)[1].strip()
        return "Unknown Raspberry Pi"
    except Exception:
        return "Unknown"


def get_raspberry_pi_serial() -> Optional[str]:
    """
    Get Raspberry Pi serial number

    Returns:
        Serial number or None
    """
    try:
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('Serial'):
                        return line.split(':', 1)[1].strip()
        return None
    except Exception:
        return None


def format_percentage(value: float, precision: int = 1) -> str:
    """
    Format percentage with proper precision

    Args:
        value: Percentage value
        precision: Decimal precision

    Returns:
        Formatted percentage string
    """
    try:
        return f"{float(value):.{precision}f}%"
    except (ValueError, TypeError):
        return "0.0%"


def get_memory_usage_color(percentage: float) -> str:
    """
    Get color indicator for memory usage

    Args:
        percentage: Memory usage percentage

    Returns:
        Color indicator (green, yellow, orange, red)
    """
    if percentage < 50:
        return "green"
    elif percentage < 75:
        return "yellow"
    elif percentage < 90:
        return "orange"
    else:
        return "red"


def get_temperature_color(celsius: float) -> str:
    """
    Get color indicator for temperature

    Args:
        celsius: Temperature in Celsius

    Returns:
        Color indicator (green, yellow, orange, red)
    """
    if celsius < 50:
        return "green"
    elif celsius < 65:
        return "yellow"
    elif celsius < 80:
        return "orange"
    else:
        return "red"


def calculate_percentage(used: Union[int, float], total: Union[int, float]) -> float:
    """
    Calculate percentage safely

    Args:
        used: Used amount
        total: Total amount

    Returns:
        Percentage value
    """
    try:
        if total == 0:
            return 0.0
        return (float(used) / float(total)) * 100.0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def get_network_interface_speed(interface: str) -> Optional[int]:
    """
    Get network interface speed

    Args:
        interface: Network interface name

    Returns:
        Interface speed in Mbps or None
    """
    try:
        import psutil
        stats = psutil.net_if_stats()
        if interface in stats:
            return stats[interface].speed
        return None
    except Exception:
        return None


def format_network_speed(bytes_per_second: Union[int, float]) -> str:
    """
    Format network speed in human readable format

    Args:
        bytes_per_second: Speed in bytes per second

    Returns:
        Formatted speed string
    """
    try:
        # Convert to bits per second
        bits_per_second = float(bytes_per_second) * 8
        
        units = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
        
        for i, unit in enumerate(units):
            if bits_per_second < 1000.0 or i == len(units) - 1:
                return f"{bits_per_second:.2f} {unit}"
            bits_per_second /= 1000.0
        
        return f"{bits_per_second:.2f} {units[-1]}"
    
    except (ValueError, TypeError):
        return "0 bps"


def is_process_running(process_name: str) -> bool:
    """
    Check if a process is running

    Args:
        process_name: Name of the process

    Returns:
        True if process is running
    """
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False
    except Exception:
        return False


def get_process_count() -> int:
    """
    Get total number of running processes

    Returns:
        Number of processes
    """
    try:
        import psutil
        return len(psutil.pids())
    except Exception:
        return 0