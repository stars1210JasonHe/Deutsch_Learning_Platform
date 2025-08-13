#!/usr/bin/env python3
"""
Phase 2 Test Suite Runner
Choose between backend tests, API tests, or both
"""
import sys
import os
import asyncio
import argparse


def print_banner():
    """Print test suite banner"""
    print("🚀" + "=" * 58 + "🚀")
    print("🌌  VIBE DEUTSCH - PHASE 2 TEST SUITE  🌌")
    print("🚀" + "=" * 58 + "🚀")
    print("")


async def run_backend_tests():
    """Run backend service tests"""
    print("🔧 Running Backend Service Tests...")
    try:
        from test_phase2_backend import Phase2BackendTester
        tester = Phase2BackendTester()
        await tester.run_all_tests()
    except Exception as e:
        print(f"❌ Backend tests failed: {e}")
        return False
    return True


async def run_api_tests():
    """Run API endpoint tests"""
    print("🌐 Running API Endpoint Tests...")
    try:
        from test_phase2_api import Phase2APITester
        tester = Phase2APITester()
        await tester.run_all_tests()
    except Exception as e:
        print(f"❌ API tests failed: {e}")
        return False
    return True


async def run_database_migration():
    """Run database migration for Phase 2"""
    print("🗄️ Running Phase 2 Database Migration...")
    try:
        from migrate_phase2 import migrate_database
        success = migrate_database()
        if success:
            print("✅ Database migration completed")
        else:
            print("❌ Database migration failed")
        return success
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import fastapi
        import sqlalchemy
        import pydantic
        import httpx
    except ImportError as e:
        missing_deps.append(str(e))
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nPlease install dependencies:")
        print("   pip install fastapi sqlalchemy pydantic httpx uvicorn")
        return False
    
    return True


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Phase 2 Test Suite")
    parser.add_argument(
        "test_type", 
        nargs="?", 
        choices=["backend", "api", "all", "migrate"], 
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--migrate", 
        action="store_true", 
        help="Run database migration first"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Run migration if requested
    if args.migrate or args.test_type == "migrate":
        success = await run_database_migration()
        if not success:
            print("❌ Migration failed, stopping tests")
            return
        if args.test_type == "migrate":
            return
    
    # Run tests based on type
    backend_success = True
    api_success = True
    
    if args.test_type in ["backend", "all"]:
        backend_success = await run_backend_tests()
        print("")
    
    if args.test_type in ["api", "all"]:
        api_success = await run_api_tests()
        print("")
    
    # Summary
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    if args.test_type in ["backend", "all"]:
        status = "✅ PASSED" if backend_success else "❌ FAILED"
        print(f"Backend Tests: {status}")
    
    if args.test_type in ["api", "all"]:
        status = "✅ PASSED" if api_success else "❌ FAILED"
        print(f"API Tests: {status}")
    
    overall_success = backend_success and api_success
    
    print("")
    if overall_success:
        print("🎉 ALL TESTS PASSED! Phase 2 is ready for use.")
        print("")
        print("🚀 You can now:")
        print("   - Generate AI-powered exams")
        print("   - Use spaced repetition system")
        print("   - Track learning analytics")
        print("   - Auto-grade with fuzzy matching")
    else:
        print("💥 SOME TESTS FAILED! Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())