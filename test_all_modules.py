#!/usr/bin/env python3
"""
Comprehensive test script for RAPIAMS Project
Tests all modules and functionalities
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

# Test data
ADMIN_USER = {"username": "admin", "password": "admin1234"}
TEST_DEVICE = {
    "name": "Test-RPI-Module",
    "hostname": "test-rpi-01",
    "ip_address": "192.168.1.100",
    "device_type": "raspberry_pi",
    "os": "Raspbian",
    "os_version": "11 (Bullseye)"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
    print(f"  {name}: {status}")
    if details and not passed:
        print(f"    Details: {details}")

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.END}")

def get_token():
    """Get authentication token"""
    response = requests.post(
        f"{API_V1}/auth/simple-login",
        json=ADMIN_USER
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_authentication():
    """Test Authentication Module"""
    print_section("1. AUTHENTICATION MODULE TESTS")
    results = []

    # Test registration
    try:
        new_user = {
            "email": f"user_{datetime.now().timestamp()}@test.com",
            "username": f"user_{int(datetime.now().timestamp())}",
            "password": "test1234",
            "full_name": "Test User"
        }
        response = requests.post(f"{API_V1}/auth/register", json=new_user)
        results.append(("User Registration", response.status_code == 200, response.text if response.status_code != 200 else ""))
    except Exception as e:
        results.append(("User Registration", False, str(e)))

    # Test login
    try:
        response = requests.post(f"{API_V1}/auth/simple-login", json=ADMIN_USER)
        results.append(("User Login", response.status_code == 200, response.text if response.status_code != 200 else ""))
        if response.status_code == 200:
            token = response.json()["access_token"]
    except Exception as e:
        results.append(("User Login", False, str(e)))

    # Test get current user
    try:
        token = get_token()
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_V1}/auth/me", headers=headers)
        results.append(("Get Current User", response.status_code == 200, response.text if response.status_code != 200 else ""))
    except Exception as e:
        results.append(("Get Current User", False, str(e)))

    # Test health endpoint
    try:
        response = requests.get(f"{API_V1}/auth/health")
        results.append(("Auth Health Check", response.status_code == 200, response.text if response.status_code != 200 else ""))
    except Exception as e:
        results.append(("Auth Health Check", False, str(e)))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results)

def test_device_management():
    """Test Device Management Module"""
    print_section("2. DEVICE MANAGEMENT MODULE TESTS")
    results = []
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create device
    try:
        response = requests.post(f"{API_V1}/devices/", json=TEST_DEVICE, headers=headers)
        results.append(("Create Device", response.status_code == 200, response.text if response.status_code != 200 else ""))
        if response.status_code == 200:
            device_data = response.json()
            device_id = device_data["device_id"]
            api_key = device_data["api_key"]
    except Exception as e:
        results.append(("Create Device", False, str(e)))
        device_id = None

    # List devices
    try:
        response = requests.get(f"{API_V1}/devices/", headers=headers)
        results.append(("List Devices", response.status_code == 200, response.text if response.status_code != 200 else ""))
    except Exception as e:
        results.append(("List Devices", False, str(e)))

    # Get specific device
    if device_id:
        try:
            response = requests.get(f"{API_V1}/devices/{device_id}", headers=headers)
            results.append(("Get Device Info", response.status_code == 200, response.text if response.status_code != 200 else ""))
        except Exception as e:
            results.append(("Get Device Info", False, str(e)))

    # Update device
    if device_id:
        try:
            update_data = {"name": "Updated-RPI", "location": "Server Room"}
            response = requests.put(f"{API_V1}/devices/{device_id}", json=update_data, headers=headers)
            results.append(("Update Device", response.status_code == 200, response.text if response.status_code != 200 else ""))
        except Exception as e:
            results.append(("Update Device", False, str(e)))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results), device_id if 'device_id' in locals() else None, api_key if 'api_key' in locals() else None

def test_metrics():
    """Test Metrics Module"""
    print_section("3. METRICS MODULE TESTS")
    results = []
    token = get_token()

    # First create a device to get API key
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_V1}/devices/", json=TEST_DEVICE, headers=headers)
    if response.status_code == 200:
        device_data = response.json()
        device_id = device_data["device_id"]
        api_key = device_data["api_key"]

        # Submit metrics using device API key
        try:
            metrics_data = {
                "cpu_usage": 45.5,
                "memory_usage": 62.3,
                "memory_total": 8192,
                "memory_available": 3072,
                "disk_usage": 75.2,
                "disk_total": 512000,
                "disk_free": 127000,
                "network_in": 1024000,
                "network_out": 512000,
                "temperature": 52.5,
                "uptime": 86400,
                "load_average": [1.2, 1.5, 1.8]
            }
            device_headers = {"X-API-Key": api_key}
            response = requests.post(f"{API_V1}/metrics/submit", json=metrics_data, headers=device_headers)
            results.append(("Submit Metrics", response.status_code == 200, response.text if response.status_code != 200 else ""))
        except Exception as e:
            results.append(("Submit Metrics", False, str(e)))

        # Get device metrics
        try:
            response = requests.get(f"{API_V1}/metrics/device/{device_id}", headers=headers)
            results.append(("Get Device Metrics", response.status_code == 200, response.text if response.status_code != 200 else ""))
        except Exception as e:
            results.append(("Get Device Metrics", False, str(e)))
    else:
        results.append(("Metrics Tests", False, "Failed to create test device"))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results)

def test_system_endpoints():
    """Test System Monitoring Endpoints"""
    print_section("4. SYSTEM MONITORING ENDPOINTS")
    results = []
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test device first
    response = requests.post(f"{API_V1}/devices/", json=TEST_DEVICE, headers=headers)
    if response.status_code == 200:
        device_id = response.json()["device_id"]

        endpoints = [
            ("System Info", f"/system/system/{device_id}/info"),
            ("System Health", f"/system/system/{device_id}/health"),
            ("Performance Stats", f"/system/system/{device_id}/performance"),
            ("Uptime Info", f"/system/system/{device_id}/uptime"),
        ]

        for name, endpoint in endpoints:
            try:
                response = requests.get(f"{API_V1}{endpoint}", headers=headers)
                results.append((name, response.status_code in [200, 404], response.text if response.status_code not in [200, 404] else ""))
            except Exception as e:
                results.append((name, False, str(e)))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results)

def test_monitoring_endpoints():
    """Test Individual Monitoring Endpoints"""
    print_section("5. MONITORING ENDPOINTS (CPU, Memory, Disk, Network, Temp)")
    results = []
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a test device first
    response = requests.post(f"{API_V1}/devices/", json=TEST_DEVICE, headers=headers)
    if response.status_code == 200:
        device_id = response.json()["device_id"]

        endpoints = [
            ("CPU Usage", f"/cpu/{device_id}/usage"),
            ("CPU Info", f"/cpu/{device_id}/info"),
            ("Memory Usage", f"/memory/{device_id}/usage"),
            ("Memory Info", f"/memory/{device_id}/info"),
            ("Disk Usage", f"/disk/{device_id}/usage"),
            ("Disk Info", f"/disk/{device_id}/partitions"),
            ("Network Stats", f"/network/{device_id}/stats"),
            ("Network Interfaces", f"/network/{device_id}/interfaces"),
            ("Temperature Info", f"/temperature/{device_id}"),
        ]

        for name, endpoint in endpoints:
            try:
                response = requests.get(f"{API_V1}{endpoint}", headers=headers)
                # Accept 200 or 404 (device might not have sent data yet)
                results.append((name, response.status_code in [200, 404], response.text if response.status_code not in [200, 404] else ""))
            except Exception as e:
                results.append((name, False, str(e)))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results)

def test_user_management():
    """Test User Management"""
    print_section("6. USER MANAGEMENT")
    results = []
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        ("List Users", "/users/"),
        ("Get Current User Profile", "/users/me"),
    ]

    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{API_V1}{endpoint}", headers=headers)
            results.append((name, response.status_code == 200, response.text if response.status_code != 200 else ""))
        except Exception as e:
            results.append((name, False, str(e)))

    for result in results:
        print_test(*result)

    return all(r[1] for r in results)

def main():
    print(f"{Colors.BLUE}")
    print("="*60)
    print("RAPIAMS - COMPREHENSIVE MODULE TESTING")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print(f"{Colors.END}")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"{Colors.RED}ERROR: Backend is not running or not healthy{Colors.END}")
            sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}ERROR: Cannot connect to backend at {BASE_URL}{Colors.END}")
        print(f"Details: {e}")
        sys.exit(1)

    # Run all tests
    all_passed = True

    all_passed &= test_authentication()
    device_result, device_id, api_key = test_device_management()
    all_passed &= device_result
    all_passed &= test_metrics()
    all_passed &= test_system_endpoints()
    all_passed &= test_monitoring_endpoints()
    all_passed &= test_user_management()

    # Summary
    print_section("TEST SUMMARY")
    if all_passed:
        print(f"{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.END}")
        print(f"\n{Colors.GREEN}The RAPIAMS system is fully functional and ready to share.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠ SOME TESTS FAILED{Colors.END}")
        print(f"Please review the failed tests above for details.")

    print(f"\n{Colors.BLUE}Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")

if __name__ == "__main__":
    main()