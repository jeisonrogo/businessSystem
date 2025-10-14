#!/usr/bin/env python3
"""
Test Script for Auto-Selection Local Logic
==========================================

This script validates the automatic local selection functionality across the multi-tenant system.
It tests both backend API endpoints and simulates frontend flows.

Usage:
    python test_auto_selection.py

Requirements:
    - Backend server running on localhost:8000
    - Valid test user credentials
    - Test data populated (stores, locals, user assignments)
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
import time


class AutoSelectionTester:
    """Comprehensive tester for auto-selection functionality."""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.current_token = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        print()

    def authenticate(self, email: str = "admin@empresa.com", password: str = "admin123") -> bool:
        """Authenticate user and set token."""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json={
                "email": email,
                "password": password
            })

            if response.status_code == 200:
                data = response.json()
                self.current_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.current_token}"
                })
                self.log_test("User Authentication", True, f"Logged in as {email}")
                return True
            else:
                self.log_test("User Authentication", False, f"Login failed: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Authentication", False, f"Exception: {str(e)}")
            return False

    def test_locals_info_endpoint(self) -> bool:
        """Test the new /locales-info endpoint for auto-selection logic."""
        try:
            response = self.session.get(f"{self.base_url}/tenant-context/locales-info")

            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_locales", "should_auto_select", "requires_manual_selection"]

                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test("Locals Info Endpoint", False,
                                f"Missing fields: {missing_fields}")
                    return False

                # Validate logic consistency
                total_locales = data["total_locales"]
                should_auto_select = data["should_auto_select"]
                requires_manual_selection = data["requires_manual_selection"]

                if total_locales == 1 and not should_auto_select:
                    self.log_test("Locals Info Endpoint", False,
                                "Single local should trigger auto-selection")
                    return False

                if total_locales > 1 and not requires_manual_selection:
                    self.log_test("Locals Info Endpoint", False,
                                "Multiple locals should require manual selection")
                    return False

                self.log_test("Locals Info Endpoint", True,
                            f"Logic correct: {total_locales} locals, auto_select={should_auto_select}")
                return True
            else:
                self.log_test("Locals Info Endpoint", False,
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Locals Info Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_select_local_endpoint(self) -> bool:
        """Test the /select-local endpoint."""
        try:
            # First get available locals
            locals_response = self.session.get(f"{self.base_url}/tenant-context/mis-locales")
            if locals_response.status_code != 200:
                self.log_test("Select Local Endpoint", False, "Cannot get available locals")
                return False

            locals_data = locals_response.json()
            if not locals_data:
                self.log_test("Select Local Endpoint", False, "No locals available for testing")
                return False

            # Test local selection
            test_local_id = locals_data[0]["id"]
            response = self.session.post(f"{self.base_url}/tenant-context/select-local", json={
                "local_id": test_local_id
            })

            if response.status_code == 200:
                data = response.json()
                if data.get("local_id") == test_local_id:
                    self.log_test("Select Local Endpoint", True,
                                f"Successfully selected local: {test_local_id}")
                    return True
                else:
                    self.log_test("Select Local Endpoint", False,
                                "Selected local ID doesn't match request")
                    return False
            else:
                self.log_test("Select Local Endpoint", False,
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Select Local Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_context_persistence(self) -> bool:
        """Test that context persists across requests."""
        try:
            # Select a local
            locals_response = self.session.get(f"{self.base_url}/tenant-context/mis-locales")
            if locals_response.status_code != 200:
                self.log_test("Context Persistence", False, "Cannot get available locals")
                return False

            locals_data = locals_response.json()
            if not locals_data:
                self.log_test("Context Persistence", False, "No locals available")
                return False

            test_local_id = locals_data[0]["id"]

            # Select local
            select_response = self.session.post(f"{self.base_url}/tenant-context/select-local", json={
                "local_id": test_local_id
            })

            if select_response.status_code != 200:
                self.log_test("Context Persistence", False, "Failed to select local")
                return False

            # Simulate frontend by adding X-Local-ID header
            self.session.headers.update({"X-Local-ID": test_local_id})

            # Test multiple tenant-aware endpoints
            endpoints_to_test = [
                "/inventario/resumen/",
                "/facturas/",
                "/dashboard/kpis"
            ]

            persistence_success = True
            for endpoint in endpoints_to_test:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404]:  # 404 is acceptable if no data exists
                    self.log_test("Context Persistence", False,
                                f"Endpoint {endpoint} failed with status {response.status_code}")
                    persistence_success = False
                    break

            if persistence_success:
                self.log_test("Context Persistence", True,
                            "Context persisted across all tenant-aware endpoints")
                return True
            else:
                return False
        except Exception as e:
            self.log_test("Context Persistence", False, f"Exception: {str(e)}")
            return False

    def test_auto_selection_flow(self) -> bool:
        """Test the complete auto-selection flow."""
        try:
            # Step 1: Get locals info
            info_response = self.session.get(f"{self.base_url}/tenant-context/locales-info")
            if info_response.status_code != 200:
                self.log_test("Auto-Selection Flow", False, "Failed to get locals info")
                return False

            info_data = info_response.json()

            # Step 2: Simulate auto-selection logic
            if info_data.get("should_auto_select") and info_data.get("auto_select_local_id"):
                # Auto-select the recommended local
                auto_local_id = info_data["auto_select_local_id"]
                select_response = self.session.post(f"{self.base_url}/tenant-context/select-local", json={
                    "local_id": auto_local_id
                })

                if select_response.status_code != 200:
                    self.log_test("Auto-Selection Flow", False, "Auto-selection failed")
                    return False

                # Step 3: Verify context is set correctly
                context_response = self.session.get(f"{self.base_url}/tenant-context/current")
                if context_response.status_code != 200:
                    self.log_test("Auto-Selection Flow", False, "Failed to get current context")
                    return False

                context_data = context_response.json()
                if context_data.get("local_id") == auto_local_id:
                    self.log_test("Auto-Selection Flow", True,
                                f"Auto-selection completed successfully for local: {auto_local_id}")
                    return True
                else:
                    self.log_test("Auto-Selection Flow", False,
                                "Context doesn't match auto-selected local")
                    return False
            else:
                self.log_test("Auto-Selection Flow", True,
                            "Manual selection required (multiple locals detected)")
                return True
        except Exception as e:
            self.log_test("Auto-Selection Flow", False, f"Exception: {str(e)}")
            return False

    def test_navigation_persistence(self) -> bool:
        """Test that auto-selected context persists during navigation."""
        try:
            # Auto-select a local if possible
            info_response = self.session.get(f"{self.base_url}/tenant-context/locales-info")
            if info_response.status_code != 200:
                return False

            info_data = info_response.json()
            if info_data.get("should_auto_select"):
                auto_local_id = info_data["auto_select_local_id"]
                self.session.post(f"{self.base_url}/tenant-context/select-local", json={
                    "local_id": auto_local_id
                })
                self.session.headers.update({"X-Local-ID": auto_local_id})

            # Simulate navigation through different modules
            navigation_tests = [
                ("/inventario/resumen/", "Inventory Module"),
                ("/facturas/", "Invoice Module"),
                ("/dashboard/kpis", "Dashboard Module"),
                ("/tenant-context/current", "Tenant Context Check")
            ]

            for endpoint, module_name in navigation_tests:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code not in [200, 404]:
                    self.log_test("Navigation Persistence", False,
                                f"{module_name} failed with status {response.status_code}")
                    return False

            self.log_test("Navigation Persistence", True,
                        "Context persisted across all navigation scenarios")
            return True
        except Exception as e:
            self.log_test("Navigation Persistence", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all auto-selection tests."""
        print("🚀 Starting Auto-Selection Tests")
        print("=" * 50)
        print()

        # Authentication test
        if not self.authenticate():
            print("❌ Authentication failed. Cannot continue with tests.")
            return self.get_summary()

        # Core functionality tests
        self.test_locals_info_endpoint()
        self.test_select_local_endpoint()
        self.test_context_persistence()
        self.test_auto_selection_flow()
        self.test_navigation_persistence()

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()

        if failed_tests > 0:
            print("❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "details": self.test_results
        }


def main():
    """Main test execution."""
    tester = AutoSelectionTester()

    try:
        summary = tester.run_all_tests()

        # Exit with appropriate code
        if summary["failed_tests"] == 0:
            print("🎉 All tests passed!")
            sys.exit(0)
        else:
            print(f"⚠️ {summary['failed_tests']} test(s) failed.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()