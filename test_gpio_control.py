#!/usr/bin/env python3
"""
GPIO Control Test Script
Tests buzzer and pump relay control through the GPIO module
"""

import sys
import time
import json
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent / "agent"))

from modules.gpio_controller import GPIOController


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(result):
    """Print result in formatted JSON"""
    print(json.dumps(result, indent=2))


def test_buzzer_control():
    """Test buzzer control functions"""
    print_header("BUZZER CONTROL TEST")

    controller = GPIOController()

    # Register buzzer
    print("\n1. Registering Buzzer...")
    buzzer_config = {
        "pin": 17,
        "mode": "OUTPUT",
        "active_state": "HIGH",
        "initial_state": "LOW",
        "description": "Test buzzer for GPIO verification",
        "max_runtime": 60,
        "device_type": "buzzer",
        "safety_features": {
            "cooldown_time": 0,
            "max_cycles_per_hour": 0
        }
    }
    result = controller.register_device("buzzer", buzzer_config)
    print_result(result)

    if not result.get("success"):
        print("\n❌ Failed to register buzzer. Exiting.")
        return False

    # Get device info
    print("\n2. Getting Buzzer Info...")
    result = controller.get_device_info("buzzer")
    print_result(result)

    # Turn buzzer on
    print("\n3. Turning Buzzer ON...")
    result = controller.turn_on("buzzer")
    print_result(result)

    if result.get("success"):
        print("✅ Buzzer should be ON now!")
        print("Waiting 2 seconds...")
        time.sleep(2)

        # Get status
        print("\n4. Getting Buzzer Status...")
        result = controller.get_status("buzzer")
        print_result(result)

        # Turn buzzer off
        print("\n5. Turning Buzzer OFF...")
        result = controller.turn_off("buzzer")
        print_result(result)

        if result.get("success"):
            print("✅ Buzzer should be OFF now!")

    # Test timed operation
    print("\n6. Testing Timed Operation (5 seconds)...")
    result = controller.turn_on_duration("buzzer", 5)
    print_result(result)

    if result.get("success"):
        print("✅ Buzzer will auto-off after 5 seconds...")
        print("Monitoring status...")

        for i in range(6):
            time.sleep(1)
            status = controller.get_status("buzzer")
            print(f"  [{i+1}s] Is ON: {status.get('is_on')}, Runtime: {status.get('current_runtime', 0):.1f}s")

    # Get statistics
    print("\n7. Getting Buzzer Statistics...")
    result = controller.get_statistics("buzzer")
    print_result(result)

    # Cleanup
    controller.cleanup()

    print("\n✅ Buzzer test completed!")
    return True


def test_pump_relay_control():
    """Test pump relay control functions"""
    print_header("PUMP RELAY CONTROL TEST")

    controller = GPIOController()

    # Register pump relay
    print("\n1. Registering Pump Relay...")
    pump_config = {
        "pin": 27,
        "mode": "OUTPUT",
        "active_state": "LOW",  # Relay modules are usually active LOW
        "initial_state": "HIGH",
        "description": "Water pump relay (JQC3F-05VDC-C)",
        "max_runtime": 300,
        "device_type": "relay",
        "safety_features": {
            "cooldown_time": 60,
            "max_cycles_per_hour": 10
        }
    }
    result = controller.register_device("pump_relay", pump_config)
    print_result(result)

    if not result.get("success"):
        print("\n❌ Failed to register pump relay. Exiting.")
        return False

    # Get device info
    print("\n2. Getting Pump Relay Info...")
    result = controller.get_device_info("pump_relay")
    print_result(result)

    # Turn pump on
    print("\n3. Turning Pump ON...")
    result = controller.turn_on("pump_relay")
    print_result(result)

    if result.get("success"):
        print("✅ Pump should be ON now!")
        print("Waiting 3 seconds...")
        time.sleep(3)

        # Get status
        print("\n4. Getting Pump Status...")
        result = controller.get_status("pump_relay")
        print_result(result)

        # Turn pump off
        print("\n5. Turning Pump OFF...")
        result = controller.turn_off("pump_relay")
        print_result(result)

        if result.get("success"):
            print("✅ Pump should be OFF now!")

    # Test cooldown
    print("\n6. Testing Cooldown (try to turn on immediately)...")
    result = controller.turn_on("pump_relay")
    print_result(result)

    if not result.get("success") and "cooldown" in result.get("error", "").lower():
        print("✅ Cooldown protection working!")

        # Wait for cooldown
        print("\nWaiting for cooldown period (10 seconds for testing)...")
        time.sleep(10)

        print("\n7. Trying again after cooldown...")
        result = controller.turn_on("pump_relay")
        print_result(result)

        if result.get("success"):
            print("✅ Pump turned on after cooldown!")
            time.sleep(2)
            controller.turn_off("pump_relay")

    # Get statistics
    print("\n8. Getting Pump Statistics...")
    result = controller.get_statistics("pump_relay")
    print_result(result)

    # Emergency stop test
    print("\n9. Testing Emergency Stop...")
    controller.turn_on("pump_relay")
    time.sleep(1)
    result = controller.emergency_stop("pump_relay")
    print_result(result)

    if result.get("success"):
        print("✅ Emergency stop working!")

    # Cleanup
    controller.cleanup()

    print("\n✅ Pump relay test completed!")
    return True


def test_list_devices():
    """Test listing all devices"""
    print_header("LIST ALL DEVICES TEST")

    controller = GPIOController()

    # Register multiple devices
    print("\n1. Registering Multiple Devices...")

    buzzer_config = {
        "pin": 17,
        "device_type": "buzzer",
        "description": "Test buzzer",
        "max_runtime": 60
    }
    controller.register_device("buzzer", buzzer_config)

    pump_config = {
        "pin": 27,
        "active_state": "LOW",
        "device_type": "relay",
        "description": "Water pump relay",
        "max_runtime": 300,
        "safety_features": {
            "cooldown_time": 60,
            "max_cycles_per_hour": 10
        }
    }
    controller.register_device("pump_relay", pump_config)

    backup_config = {
        "pin": 22,
        "active_state": "LOW",
        "device_type": "relay",
        "description": "Backup relay",
        "max_runtime": 600
    }
    controller.register_device("backup_relay", backup_config)

    # List all devices
    print("\n2. Listing All Registered Devices...")
    result = controller.list_devices()
    print_result(result)

    # Cleanup
    controller.cleanup()

    print("\n✅ List devices test completed!")
    return True


def main():
    """Main test function"""
    print_header("GPIO CONTROLLER TEST SUITE")
    print("\nThis script tests GPIO control for buzzer and pump relay.")
    print("\n⚠️  WARNING: Make sure you have:")
    print("   1. Buzzer connected to GPIO 17 (Physical Pin 11)")
    print("   2. Pump relay connected to GPIO 27 (Physical Pin 13)")
    print("   3. Proper power supply and connections")
    print("\n   Press Ctrl+C to abort at any time.")

    try:
        input("\n➡️  Press ENTER to start tests, or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user.")
        return

    tests = [
        ("List Devices", test_list_devices),
        ("Buzzer Control", test_buzzer_control),
        ("Pump Relay Control", test_pump_relay_control),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n\n{'=' * 60}")
            print(f"  Running: {test_name}")
            print(f"{'=' * 60}")

            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name}: FAILED")

        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user!")
            break

        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()

    # Final summary
    print_header("TEST SUMMARY")
    print(f"\nTotal Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) FAILED!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user. Cleaning up...")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ Cleanup completed. Goodbye!")