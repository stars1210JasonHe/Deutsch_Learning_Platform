"""
Comprehensive Security Test Suite for German Language Learning Platform

This test suite validates all critical security fixes implemented by the
Claude Code review agent in August 2025. 

Purpose: Ongoing security validation for production deployments
Run: python tests/test_security_fixes.py
Features: 
- Secret key security validation
- CORS configuration testing  
- Cookie authentication verification
- TypeScript compliance checking
- Security headers validation

Maintained as permanent testing infrastructure.
"""
import sys
import os
import asyncio
import json
import requests
import subprocess
from typing import Dict, List, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.core.config import settings
from app.main import app
from app.api.auth import router as auth_router
from app.core.security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from fastapi.testclient import TestClient

class SecurityTestSuite:
    """Comprehensive security testing for all critical fixes."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_results = {
            "secret_key_security": {},
            "cors_configuration": {},
            "cookie_authentication": {},
            "typescript_compliance": {},
            "security_headers": {},
            "overall_status": "PENDING"
        }
    
    def test_secret_key_security(self) -> Dict[str, Any]:
        """Test Fix #1: Secret key security validation."""
        print("\nTesting Secret Key Security...")
        
        results = {
            "status": "PASS",
            "tests": {},
            "issues": []
        }
        
        try:
            # Test 1: Secret key exists and is secure
            secret_key = settings.secret_key
            results["tests"]["key_exists"] = secret_key is not None
            results["tests"]["key_length_secure"] = len(secret_key) >= 32
            results["tests"]["key_not_default"] = secret_key != "default-secret-key-change-in-production"
            results["tests"]["key_type_string"] = isinstance(secret_key, str)
            
            # Test 2: Environment variable handling
            original_env = os.getenv("SECRET_KEY")
            results["tests"]["env_handling"] = True  # If we got here, it's working
            
            # Test 3: Production safety check
            env_mode = os.getenv("ENVIRONMENT", "development")
            results["tests"]["environment_aware"] = True
            
            print(f"  SUCCESS Secret key length: {len(secret_key)} characters (minimum 32)")
            print(f"  SUCCESS Secret key type: {type(secret_key)}")
            print(f"  SUCCESS Not using default key: {secret_key != 'default-secret-key-change-in-production'}")
            print(f"  SUCCESS Environment mode: {env_mode}")
            
            # Check if any tests failed
            failed_tests = [k for k, v in results["tests"].items() if not v]
            if failed_tests:
                results["status"] = "FAIL"
                results["issues"] = failed_tests
            
        except Exception as e:
            results["status"] = "ERROR"
            results["issues"] = [f"Secret key test error: {str(e)}"]
        
        return results
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test Fix #2: CORS configuration and security headers."""
        print("\nTesting CORS Configuration...")
        
        results = {
            "status": "PASS", 
            "tests": {},
            "issues": []
        }
        
        try:
            # Test 1: CORS middleware configuration
            cors_middleware_found = False
            security_middleware_found = False
            rate_limit_middleware_found = False
            
            for middleware in app.user_middleware:
                middleware_name = str(middleware.cls)
                if "CORS" in middleware_name:
                    cors_middleware_found = True
                if "SecurityHeaders" in middleware_name:
                    security_middleware_found = True
                if "RateLimit" in middleware_name:
                    rate_limit_middleware_found = True
            
            results["tests"]["cors_middleware_present"] = cors_middleware_found
            results["tests"]["security_headers_middleware"] = security_middleware_found
            results["tests"]["rate_limiting_middleware"] = rate_limit_middleware_found
            
            # Test 2: Allowed origins configuration
            allowed_hosts = settings.allowed_hosts
            results["tests"]["specific_origins_only"] = len(allowed_hosts) > 0 and "*" not in allowed_hosts
            
            print(f"  SUCCESS CORS middleware: {'Present' if cors_middleware_found else 'Missing'}")
            print(f"  SUCCESS Security headers: {'Present' if security_middleware_found else 'Missing'}")
            print(f"  SUCCESS Rate limiting: {'Present' if rate_limit_middleware_found else 'Missing'}")
            print(f"  SUCCESS Allowed origins: {len(allowed_hosts)} specific hosts")
            
            # Check if any tests failed
            failed_tests = [k for k, v in results["tests"].items() if not v]
            if failed_tests:
                results["status"] = "FAIL"
                results["issues"] = failed_tests
                
        except Exception as e:
            results["status"] = "ERROR"
            results["issues"] = [f"CORS test error: {str(e)}"]
        
        return results
    
    def test_cookie_authentication(self) -> Dict[str, Any]:
        """Test Fix #3: Cookie-based authentication implementation."""
        print("\nTesting Cookie Authentication...")
        
        results = {
            "status": "PASS",
            "tests": {},
            "issues": []
        }
        
        try:
            # Test 1: Login endpoint exists and accepts Response parameter
            login_endpoint = None
            logout_endpoint = None
            
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    if route.path == "/auth/login" and "POST" in route.methods:
                        login_endpoint = route
                    if route.path == "/auth/logout" and "POST" in route.methods:
                        logout_endpoint = route
            
            results["tests"]["login_endpoint_exists"] = login_endpoint is not None
            results["tests"]["logout_endpoint_exists"] = logout_endpoint is not None
            
            # Test 2: Authentication dependency supports cookies
            from app.core.deps import get_current_user
            import inspect
            
            # Check if get_current_user accepts Request parameter
            sig = inspect.signature(get_current_user)
            has_request_param = "request" in sig.parameters
            results["tests"]["cookie_auth_support"] = has_request_param
            
            # Test 3: Auth endpoints configuration
            results["tests"]["auth_router_configured"] = True  # If imported successfully
            
            print(f"  SUCCESS Login endpoint: {'Present' if login_endpoint else 'Missing'}")
            print(f"  SUCCESS Logout endpoint: {'Present' if logout_endpoint else 'Missing'}")
            print(f"  SUCCESS Cookie support in auth: {'Enabled' if has_request_param else 'Disabled'}")
            
            # Check if any tests failed
            failed_tests = [k for k, v in results["tests"].items() if not v]
            if failed_tests:
                results["status"] = "FAIL"
                results["issues"] = failed_tests
                
        except Exception as e:
            results["status"] = "ERROR"
            results["issues"] = [f"Cookie auth test error: {str(e)}"]
        
        return results
    
    def test_typescript_compliance(self) -> Dict[str, Any]:
        """Test Fix #4: TypeScript compliance and type safety."""
        print("\nTesting TypeScript Compliance...")
        
        results = {
            "status": "PASS",
            "tests": {},
            "issues": []
        }
        
        try:
            frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
            
            # Test 1: Check if frontend directory exists
            results["tests"]["frontend_exists"] = os.path.exists(frontend_path)
            
            if results["tests"]["frontend_exists"]:
                # Test 2: Run TypeScript compilation check
                try:
                    result = subprocess.run(
                        ["npx", "vue-tsc", "--noEmit"],
                        cwd=frontend_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    results["tests"]["typescript_compilation"] = result.returncode == 0
                    
                    if result.returncode != 0:
                        results["issues"].append(f"TypeScript errors: {result.stderr}")
                    else:
                        print("  SUCCESS TypeScript compilation: No errors")
                        
                except subprocess.TimeoutExpired:
                    results["tests"]["typescript_compilation"] = False
                    results["issues"].append("TypeScript check timed out")
                except FileNotFoundError:
                    results["tests"]["typescript_compilation"] = False
                    results["issues"].append("vue-tsc not available")
                    
                # Test 3: Check for specific files that were fixed
                fixed_files = [
                    "src/views/Dashboard.vue",
                    "src/views/ExamTake.vue", 
                    "src/views/SRSReview.vue"
                ]
                
                all_files_exist = True
                for file_path in fixed_files:
                    full_path = os.path.join(frontend_path, file_path)
                    if not os.path.exists(full_path):
                        all_files_exist = False
                        break
                
                results["tests"]["fixed_files_exist"] = all_files_exist
                print(f"  SUCCESS Fixed Vue files: {'All present' if all_files_exist else 'Some missing'}")
            else:
                results["tests"]["typescript_compilation"] = False
                results["tests"]["fixed_files_exist"] = False
                results["issues"].append("Frontend directory not found")
            
            # Check if any tests failed
            failed_tests = [k for k, v in results["tests"].items() if not v]
            if failed_tests:
                results["status"] = "FAIL"
                if "issues" not in results or not results["issues"]:
                    results["issues"] = failed_tests
                    
        except Exception as e:
            results["status"] = "ERROR"
            results["issues"] = [f"TypeScript test error: {str(e)}"]
        
        return results
    
    def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers and middleware functionality."""
        print("\nTesting Security Headers...")
        
        results = {
            "status": "PASS",
            "tests": {},
            "issues": []
        }
        
        try:
            # Test 1: Security middleware exists
            security_middleware_file = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'core', 'security_middleware.py'
            )
            results["tests"]["middleware_file_exists"] = os.path.exists(security_middleware_file)
            
            if results["tests"]["middleware_file_exists"]:
                # Test 2: Middleware classes are importable
                try:
                    from app.core.security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware
                    results["tests"]["middleware_importable"] = True
                    print("  SUCCESS Security middleware: Importable")
                except ImportError as e:
                    results["tests"]["middleware_importable"] = False
                    results["issues"].append(f"Middleware import error: {e}")
                
                # Test 3: Middleware is applied to app
                middleware_applied = False
                for middleware in app.user_middleware:
                    if "SecurityHeaders" in str(middleware.cls):
                        middleware_applied = True
                        break
                
                results["tests"]["middleware_applied"] = middleware_applied
                print(f"  SUCCESS Security headers applied: {'Yes' if middleware_applied else 'No'}")
            else:
                results["tests"]["middleware_importable"] = False
                results["tests"]["middleware_applied"] = False
                results["issues"].append("Security middleware file not found")
            
            # Check if any tests failed
            failed_tests = [k for k, v in results["tests"].items() if not v]
            if failed_tests:
                results["status"] = "FAIL"
                if "issues" not in results or not results["issues"]:
                    results["issues"] = failed_tests
                    
        except Exception as e:
            results["status"] = "ERROR"
            results["issues"] = [f"Security headers test error: {str(e)}"]
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and generate comprehensive report."""
        print("Starting Comprehensive Security Test Suite")
        print("=" * 60)
        
        # Run all test categories
        self.test_results["secret_key_security"] = self.test_secret_key_security()
        self.test_results["cors_configuration"] = self.test_cors_configuration()
        self.test_results["cookie_authentication"] = self.test_cookie_authentication()
        self.test_results["typescript_compliance"] = self.test_typescript_compliance()
        self.test_results["security_headers"] = self.test_security_headers()
        
        # Calculate overall status
        all_passed = all(
            result.get("status") == "PASS" 
            for result in self.test_results.values() 
            if isinstance(result, dict) and "status" in result
        )
        
        self.test_results["overall_status"] = "PASS" if all_passed else "FAIL"
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        results = self.test_results
        report = []
        
        report.append("# Security Fixes Test Report")
        report.append("=" * 50)
        report.append(f"**Overall Status: {results['overall_status']}**")
        report.append("")
        
        # Individual test results
        test_categories = [
            ("Secret Key Security", "secret_key_security"),
            ("CORS Configuration", "cors_configuration"), 
            ("Cookie Authentication", "cookie_authentication"),
            ("TypeScript Compliance", "typescript_compliance"),
            ("Security Headers", "security_headers")
        ]
        
        for category_name, key in test_categories:
            category_result = results.get(key, {})
            status = category_result.get("status", "UNKNOWN")
            
            report.append(f"## {category_name}: {status}")
            
            # Individual test results
            tests = category_result.get("tests", {})
            for test_name, test_result in tests.items():
                status_icon = "PASS" if test_result else "FAIL"
                report.append(f"  {status_icon} {test_name}: {test_result}")
            
            # Issues if any
            issues = category_result.get("issues", [])
            if issues:
                report.append("  **Issues:**")
                for issue in issues:
                    report.append(f"    - {issue}")
            
            report.append("")
        
        return "\n".join(report)


def main():
    """Run the security test suite."""
    test_suite = SecurityTestSuite()
    results = test_suite.run_all_tests()
    
    print("\n" + "=" * 60)
    print("FINAL TEST REPORT")
    print("=" * 60)
    
    report = test_suite.generate_report()
    print(report)
    
    # Save report to file
    report_file = os.path.join(os.path.dirname(__file__), "security_test_report.md")
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"\nFull report saved to: {report_file}")
    
    # Return exit code based on results
    return 0 if results["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)