"""
GPIO Controller Module
Unified GPIO control for various devices (buzzers, relays, motors, etc.)
Supports Raspberry Pi GPIO with safety features and monitoring
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import json

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    # Mock GPIO for development/testing on non-Pi systems
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        IN = 'IN'
        HIGH = 1
        LOW = 0
        PUD_UP = 'PUD_UP'
        PUD_DOWN = 'PUD_DOWN'

        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setwarnings(flag): pass
        @staticmethod
        def setup(pin, mode, initial=None, pull_up_down=None): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def input(pin): return 0
        @staticmethod
        def cleanup(pin=None): pass

    GPIO = MockGPIO()


class GPIODevice:
    """Represents a single GPIO-controlled device"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.pin = config['pin']
        self.mode = config.get('mode', 'OUTPUT')
        self.active_state = config.get('active_state', 'HIGH')
        self.initial_state = config.get('initial_state', 'LOW')
        self.description = config.get('description', '')
        self.device_type = config.get('device_type', 'generic')
        self.max_runtime = config.get('max_runtime', 300)  # seconds

        # Safety features
        self.safety = config.get('safety_features', {})
        self.cooldown_time = self.safety.get('cooldown_time', 0)
        self.max_cycles_per_hour = self.safety.get('max_cycles_per_hour', 0)

        # State tracking
        self.is_on = False
        self.last_turned_on = None
        self.last_turned_off = None
        self.current_session_start = None
        self.total_runtime = 0.0
        self.cycle_count = 0
        self.cycle_history = []

        # Auto-off timer
        self._timer = None
        self._lock = threading.Lock()

    def get_active_level(self) -> int:
        """Get GPIO level for active state"""
        return GPIO.HIGH if self.active_state == 'HIGH' else GPIO.LOW

    def get_inactive_level(self) -> int:
        """Get GPIO level for inactive state"""
        return GPIO.LOW if self.active_state == 'HIGH' else GPIO.HIGH

    def get_initial_level(self) -> int:
        """Get GPIO level for initial state"""
        return GPIO.HIGH if self.initial_state == 'HIGH' else GPIO.LOW


class GPIOController:
    """
    Unified GPIO Controller for managing multiple GPIO devices
    Features:
    - Multi-device management
    - Safety features (max runtime, cooldown, cycle limits)
    - Automatic timers
    - Usage statistics
    - Thread-safe operations
    """

    def __init__(self, history_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.devices: Dict[str, GPIODevice] = {}
        self.history_size = history_size
        self._initialized = False
        self._lock = threading.Lock()

        # Initialize GPIO if available
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                self._initialized = True
                self.logger.info("GPIO Controller initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize GPIO: {e}")
                self._initialized = False
        else:
            self.logger.warning("RPi.GPIO not available - running in mock mode")
            self._initialized = True  # Allow mock mode for testing

    def register_device(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new GPIO device"""
        try:
            with self._lock:
                if name in self.devices:
                    return {
                        "success": False,
                        "error": f"Device '{name}' already registered"
                    }

                # Create device instance
                device = GPIODevice(name, config)

                # Setup GPIO pin
                if self._initialized:
                    GPIO.setup(
                        device.pin,
                        GPIO.OUT,
                        initial=device.get_initial_level()
                    )

                self.devices[name] = device

                self.logger.info(f"Registered GPIO device: {name} on pin {device.pin}")

                return {
                    "success": True,
                    "message": f"Device '{name}' registered successfully",
                    "device_info": self.get_device_info(name)
                }

        except Exception as e:
            self.logger.error(f"Error registering device '{name}': {e}")
            return {"success": False, "error": str(e)}

    def turn_on(self, device_name: str) -> Dict[str, Any]:
        """Turn on a device"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"success": False, "error": f"Device '{device_name}' not found"}

            with device._lock:
                # Check if already on
                if device.is_on:
                    return {
                        "success": False,
                        "error": f"Device '{device_name}' is already ON"
                    }

                # Check cooldown
                if not self._check_cooldown(device):
                    time_left = self._get_cooldown_remaining(device)
                    return {
                        "success": False,
                        "error": f"Device in cooldown period. Wait {time_left:.1f} seconds"
                    }

                # Check cycle limit
                if not self._check_cycle_limit(device):
                    return {
                        "success": False,
                        "error": f"Max cycles per hour ({device.max_cycles_per_hour}) reached"
                    }

                # Turn on the device
                GPIO.output(device.pin, device.get_active_level())

                device.is_on = True
                device.last_turned_on = datetime.now()
                device.current_session_start = datetime.now()
                device.cycle_count += 1
                device.cycle_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'turned_on'
                })

                # Keep only recent history
                if len(device.cycle_history) > self.history_size:
                    device.cycle_history = device.cycle_history[-self.history_size:]

                self.logger.info(f"Device '{device_name}' turned ON")

                return {
                    "success": True,
                    "message": f"Device '{device_name}' turned ON",
                    "timestamp": datetime.now().isoformat(),
                    "status": self.get_status(device_name)
                }

        except Exception as e:
            self.logger.error(f"Error turning on device '{device_name}': {e}")
            return {"success": False, "error": str(e)}

    def turn_off(self, device_name: str) -> Dict[str, Any]:
        """Turn off a device"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"success": False, "error": f"Device '{device_name}' not found"}

            with device._lock:
                # Cancel any running timer
                if device._timer:
                    device._timer.cancel()
                    device._timer = None

                # Check if already off
                if not device.is_on:
                    return {
                        "success": False,
                        "error": f"Device '{device_name}' is already OFF"
                    }

                # Calculate session runtime
                if device.current_session_start:
                    session_time = (datetime.now() - device.current_session_start).total_seconds()
                    device.total_runtime += session_time

                # Turn off the device
                GPIO.output(device.pin, device.get_inactive_level())

                device.is_on = False
                device.last_turned_off = datetime.now()
                device.current_session_start = None
                device.cycle_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'turned_off',
                    'session_time': session_time if device.current_session_start else 0
                })

                self.logger.info(f"Device '{device_name}' turned OFF")

                return {
                    "success": True,
                    "message": f"Device '{device_name}' turned OFF",
                    "timestamp": datetime.now().isoformat(),
                    "session_runtime": session_time if device.current_session_start else 0,
                    "status": self.get_status(device_name)
                }

        except Exception as e:
            self.logger.error(f"Error turning off device '{device_name}': {e}")
            return {"success": False, "error": str(e)}

    def turn_on_duration(self, device_name: str, duration: float) -> Dict[str, Any]:
        """Turn on device for specified duration (seconds)"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"success": False, "error": f"Device '{device_name}' not found"}

            # Validate duration
            if duration <= 0:
                return {"success": False, "error": "Duration must be greater than 0"}

            if duration > device.max_runtime:
                return {
                    "success": False,
                    "error": f"Duration exceeds max runtime ({device.max_runtime}s)"
                }

            # Turn on the device
            result = self.turn_on(device_name)
            if not result.get('success'):
                return result

            # Set auto-off timer
            with device._lock:
                device._timer = threading.Timer(duration, self._auto_turn_off, args=[device_name])
                device._timer.start()

            self.logger.info(f"Device '{device_name}' will auto-off in {duration}s")

            return {
                "success": True,
                "message": f"Device '{device_name}' turned ON for {duration} seconds",
                "duration": duration,
                "auto_off_at": (datetime.now() + timedelta(seconds=duration)).isoformat(),
                "status": self.get_status(device_name)
            }

        except Exception as e:
            self.logger.error(f"Error in turn_on_duration for '{device_name}': {e}")
            return {"success": False, "error": str(e)}

    def _auto_turn_off(self, device_name: str):
        """Automatically turn off device (called by timer)"""
        self.logger.info(f"Auto-turning off device '{device_name}'")
        self.turn_off(device_name)

    def get_status(self, device_name: str) -> Dict[str, Any]:
        """Get current status of a device"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"error": f"Device '{device_name}' not found"}

            status = {
                "device_name": device_name,
                "is_on": device.is_on,
                "pin": device.pin,
                "device_type": device.device_type,
                "timestamp": datetime.now().isoformat()
            }

            if device.is_on and device.current_session_start:
                runtime = (datetime.now() - device.current_session_start).total_seconds()
                status["current_runtime"] = runtime
                status["time_remaining"] = max(0, device.max_runtime - runtime)

            if device.last_turned_on:
                status["last_turned_on"] = device.last_turned_on.isoformat()

            if device.last_turned_off:
                status["last_turned_off"] = device.last_turned_off.isoformat()
                if device.cooldown_time > 0:
                    cooldown_remaining = self._get_cooldown_remaining(device)
                    status["cooldown_remaining"] = max(0, cooldown_remaining)

            return status

        except Exception as e:
            self.logger.error(f"Error getting status for '{device_name}': {e}")
            return {"error": str(e)}

    def get_statistics(self, device_name: str) -> Dict[str, Any]:
        """Get usage statistics for a device"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"error": f"Device '{device_name}' not found"}

            current_runtime = 0
            if device.is_on and device.current_session_start:
                current_runtime = (datetime.now() - device.current_session_start).total_seconds()

            # Calculate cycles in last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_cycles = sum(
                1 for entry in device.cycle_history
                if entry['action'] == 'turned_on' and
                datetime.fromisoformat(entry['timestamp']) > one_hour_ago
            )

            return {
                "device_name": device_name,
                "total_runtime": device.total_runtime + current_runtime,
                "total_cycles": device.cycle_count,
                "cycles_last_hour": recent_cycles,
                "current_session_runtime": current_runtime,
                "is_on": device.is_on,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics for '{device_name}': {e}")
            return {"error": str(e)}

    def get_device_info(self, device_name: str) -> Dict[str, Any]:
        """Get detailed device information"""
        try:
            device = self._get_device(device_name)
            if not device:
                return {"error": f"Device '{device_name}' not found"}

            return {
                "name": device.name,
                "pin": device.pin,
                "device_type": device.device_type,
                "description": device.description,
                "active_state": device.active_state,
                "max_runtime": device.max_runtime,
                "cooldown_time": device.cooldown_time,
                "max_cycles_per_hour": device.max_cycles_per_hour,
                "is_on": device.is_on
            }

        except Exception as e:
            self.logger.error(f"Error getting device info for '{device_name}': {e}")
            return {"error": str(e)}

    def list_devices(self) -> Dict[str, Any]:
        """List all registered devices"""
        try:
            devices_list = []
            for name, device in self.devices.items():
                devices_list.append({
                    "name": name,
                    "pin": device.pin,
                    "device_type": device.device_type,
                    "description": device.description,
                    "is_on": device.is_on
                })

            return {
                "success": True,
                "device_count": len(devices_list),
                "devices": devices_list,
                "gpio_available": GPIO_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
            return {"success": False, "error": str(e)}

    def emergency_stop(self, device_name: str) -> Dict[str, Any]:
        """Emergency stop - immediately turn off device"""
        self.logger.warning(f"EMERGENCY STOP for device '{device_name}'")
        return self.turn_off(device_name)

    def emergency_stop_all(self) -> Dict[str, Any]:
        """Emergency stop all devices"""
        self.logger.warning("EMERGENCY STOP ALL devices")
        results = {}
        for device_name in self.devices.keys():
            results[device_name] = self.turn_off(device_name)

        return {
            "success": True,
            "message": "All devices stopped",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    def _get_device(self, device_name: str) -> Optional[GPIODevice]:
        """Get device by name"""
        return self.devices.get(device_name)

    def _check_cooldown(self, device: GPIODevice) -> bool:
        """Check if device is out of cooldown period"""
        if device.cooldown_time == 0:
            return True

        if not device.last_turned_off:
            return True

        time_since_off = (datetime.now() - device.last_turned_off).total_seconds()
        return time_since_off >= device.cooldown_time

    def _get_cooldown_remaining(self, device: GPIODevice) -> float:
        """Get remaining cooldown time in seconds"""
        if device.cooldown_time == 0 or not device.last_turned_off:
            return 0

        time_since_off = (datetime.now() - device.last_turned_off).total_seconds()
        remaining = device.cooldown_time - time_since_off
        return max(0, remaining)

    def _check_cycle_limit(self, device: GPIODevice) -> bool:
        """Check if device hasn't exceeded cycle limit"""
        if device.max_cycles_per_hour == 0:
            return True

        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_cycles = sum(
            1 for entry in device.cycle_history
            if entry['action'] == 'turned_on' and
            datetime.fromisoformat(entry['timestamp']) > one_hour_ago
        )

        return recent_cycles < device.max_cycles_per_hour

    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            # Turn off all devices
            for device_name in self.devices.keys():
                self.turn_off(device_name)

            # Cleanup GPIO
            if GPIO_AVAILABLE and self._initialized:
                GPIO.cleanup()

            self.logger.info("GPIO Controller cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor - cleanup on deletion"""
        self.cleanup()


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create controller
    controller = GPIOController()

    # Register buzzer
    buzzer_config = {
        "pin": 17,
        "mode": "OUTPUT",
        "active_state": "HIGH",
        "initial_state": "LOW",
        "description": "Test buzzer",
        "max_runtime": 60,
        "device_type": "buzzer"
    }

    print("=== Registering Buzzer ===")
    result = controller.register_device("buzzer", buzzer_config)
    print(json.dumps(result, indent=2))

    # Register pump relay
    pump_config = {
        "pin": 27,
        "mode": "OUTPUT",
        "active_state": "LOW",
        "initial_state": "HIGH",
        "description": "Water pump relay",
        "max_runtime": 300,
        "device_type": "relay",
        "safety_features": {
            "cooldown_time": 60,
            "max_cycles_per_hour": 10
        }
    }

    print("\n=== Registering Pump Relay ===")
    result = controller.register_device("pump_relay", pump_config)
    print(json.dumps(result, indent=2))

    # List devices
    print("\n=== List All Devices ===")
    result = controller.list_devices()
    print(json.dumps(result, indent=2))

    # Turn on buzzer for 5 seconds
    print("\n=== Turn On Buzzer for 5 seconds ===")
    result = controller.turn_on_duration("buzzer", 5)
    print(json.dumps(result, indent=2))

    # Get status
    print("\n=== Get Buzzer Status ===")
    time.sleep(1)
    result = controller.get_status("buzzer")
    print(json.dumps(result, indent=2))

    # Wait for auto-off
    print("\nWaiting for auto-off...")
    time.sleep(5)

    # Get statistics
    print("\n=== Get Buzzer Statistics ===")
    result = controller.get_statistics("buzzer")
    print(json.dumps(result, indent=2))

    # Cleanup
    controller.cleanup()