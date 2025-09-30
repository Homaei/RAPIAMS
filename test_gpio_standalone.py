#!/usr/bin/env python3
"""
Standalone GPIO Controller Test
Tests the GPIO module independently without other dependencies
"""

import sys
import time
import json
from pathlib import Path

# Direct import
sys.path.insert(0, str(Path(__file__).parent / "agent" / "modules"))

# Import just the GPIO controller
from gpio_controller import GPIOController


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(result):
    """Print result in formatted JSON"""
    print(json.dumps(result, indent=2))


def test_basic_functionality():
    """Test basic GPIO controller functionality"""
    print_header("BASIC FUNCTIONALITY TEST")

    controller = GPIOController()

    # Test 1: Register buzzer
    print("\n✓ Test 1: Register Buzzer")
    buzzer_config = {
        "pin": 17,
        "mode": "OUTPUT",
        "active_state": "HIGH",
        "initial_state": "LOW",
        "description": "Test buzzer",
        "max_runtime": 60,
        "device_type": "buzzer"
    }
    result = controller.register_device("buzzer", buzzer_config)
    print_result(result)
    assert result.get("success"), "Failed to register buzzer"

    # Test 2: Register pump relay
    print("\n✓ Test 2: Register Pump Relay")
    pump_config = {
        "pin": 27,
        "active_state": "LOW",
        "max_runtime": 300,
        "device_type": "relay",
        "safety_features": {
            "cooldown_time": 60,
            "max_cycles_per_hour": 10
        }
    }
    result = controller.register_device("pump_relay", pump_config)
    print_result(result)
    assert result.get("success"), "Failed to register pump"

    # Test 3: List devices
    print("\n✓ Test 3: List All Devices")
    result = controller.list_devices()
    print_result(result)
    assert result.get("device_count") == 2, "Should have 2 devices"

    # Test 4: Get device info
    print("\n✓ Test 4: Get Buzzer Info")
    result = controller.get_device_info("buzzer")
    print_result(result)
    assert result.get("pin") == 17, "Buzzer should be on pin 17"

    # Test 5: Turn buzzer on
    print("\n✓ Test 5: Turn Buzzer ON")
    result = controller.turn_on("buzzer")
    print_result(result)
    assert result.get("success"), "Failed to turn on buzzer"

    # Test 6: Get status
    print("\n✓ Test 6: Get Buzzer Status (should be ON)")
    result = controller.get_status("buzzer")
    print_result(result)
    assert result.get("is_on") == True, "Buzzer should be ON"

    time.sleep(1)

    # Test 7: Turn buzzer off
    print("\n✓ Test 7: Turn Buzzer OFF")
    result = controller.turn_off("buzzer")
    print_result(result)
    assert result.get("success"), "Failed to turn off buzzer"

    # Test 8: Get status again
    print("\n✓ Test 8: Get Buzzer Status (should be OFF)")
    result = controller.get_status("buzzer")
    print_result(result)
    assert result.get("is_on") == False, "Buzzer should be OFF"

    # Test 9: Timed operation
    print("\n✓ Test 9: Turn ON for 3 seconds (with timer)")
    result = controller.turn_on_duration("buzzer", 3)
    print_result(result)
    assert result.get("success"), "Failed to turn on with duration"

    print("  Waiting for auto-off...")
    for i in range(4):
        time.sleep(1)
        status = controller.get_status("buzzer")
        print(f"  [{i+1}s] Is ON: {status.get('is_on')}")

    # Test 10: Get statistics
    print("\n✓ Test 10: Get Buzzer Statistics")
    result = controller.get_statistics("buzzer")
    print_result(result)
    assert result.get("total_cycles") >= 2, "Should have at least 2 cycles"

    # Test 11: Emergency stop
    print("\n✓ Test 11: Emergency Stop")
    controller.turn_on("pump_relay")
    time.sleep(0.5)
    result = controller.emergency_stop("pump_relay")
    print_result(result)
    assert result.get("success"), "Emergency stop failed"

    # Test 12: Emergency stop all
    print("\n✓ Test 12: Emergency Stop All")
    controller.turn_on("buzzer")
    time.sleep(0.5)
    result = controller.emergency_stop_all()
    print_result(result)
    assert result.get("success"), "Emergency stop all failed"

    controller.cleanup()

    print("\n" + "=" * 60)
    print("  ✅ ALL TESTS PASSED!")
    print("=" * 60)
    return True


def test_safety_features():
    """Test safety features"""
    print_header("SAFETY FEATURES TEST")

    controller = GPIOController()

    # Register pump with cooldown
    pump_config = {
        "pin": 27,
        "active_state": "LOW",
        "max_runtime": 300,
        "device_type": "relay",
        "safety_features": {
            "cooldown_time": 5,  # 5 seconds for testing
            "max_cycles_per_hour": 3
        }
    }
    controller.register_device("pump_relay", pump_config)

    # Test cooldown
    print("\n✓ Test 1: Cooldown Protection")
    controller.turn_on("pump_relay")
    time.sleep(1)
    controller.turn_off("pump_relay")

    print("  Trying to turn on immediately (should fail)...")
    result = controller.turn_on("pump_relay")
    print_result(result)
    assert not result.get("success"), "Should be blocked by cooldown"
    assert "cooldown" in result.get("error", "").lower(), "Should mention cooldown"

    print("\n  Waiting for cooldown (6 seconds)...")
    time.sleep(6)

    print("  Trying again after cooldown...")
    result = controller.turn_on("pump_relay")
    print_result(result)
    assert result.get("success"), "Should work after cooldown"
    controller.turn_off("pump_relay")

    # Test max runtime
    print("\n✓ Test 2: Max Runtime Validation")
    result = controller.turn_on_duration("pump_relay", 500)  # More than max_runtime
    print_result(result)
    assert not result.get("success"), "Should fail due to max runtime"

    controller.cleanup()

    print("\n" + "=" * 60)
    print("  ✅ SAFETY TESTS PASSED!")
    print("=" * 60)
    return True


def test_error_handling():
    """Test error handling"""
    print_header("ERROR HANDLING TEST")

    controller = GPIOController()

    # Test 1: Non-existent device
    print("\n✓ Test 1: Non-existent Device")
    result = controller.turn_on("non_existent")
    print_result(result)
    assert not result.get("success"), "Should fail for non-existent device"

    # Test 2: Duplicate registration
    print("\n✓ Test 2: Duplicate Registration")
    config = {"pin": 17, "device_type": "buzzer"}
    controller.register_device("buzzer", config)
    result = controller.register_device("buzzer", config)
    print_result(result)
    assert not result.get("success"), "Should fail for duplicate"

    # Test 3: Turn off already off device
    print("\n✓ Test 3: Turn OFF Already OFF Device")
    result = controller.turn_off("buzzer")
    print_result(result)
    assert not result.get("success"), "Should fail when already off"

    # Test 4: Turn on already on device
    print("\n✓ Test 4: Turn ON Already ON Device")
    controller.turn_on("buzzer")
    result = controller.turn_on("buzzer")
    print_result(result)
    assert not result.get("success"), "Should fail when already on"

    controller.cleanup()

    print("\n" + "=" * 60)
    print("  ✅ ERROR HANDLING TESTS PASSED!")
    print("=" * 60)
    return True


def main():
    """Run all tests"""
    print_header("GPIO CONTROLLER STANDALONE TEST SUITE")
    print("\n⚠️  Note: Running in MOCK mode (no physical GPIO required)")
    print("This tests the GPIO controller logic and API.\n")

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Safety Features", test_safety_features),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{'=' * 60}")
            print(f"  Running: {test_name}")
            print(f"{'=' * 60}")

            if test_func():
                passed += 1
            else:
                failed += 1

        except AssertionError as e:
            failed += 1
            print(f"\n❌ TEST FAILED: {e}")

        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Final summary
    print("\n" + "=" * 60)
    print("  FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"\nTotal Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! GPIO module is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) FAILED!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)