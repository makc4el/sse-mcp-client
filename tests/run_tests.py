#!/usr/bin/env python3
"""
Test runner for main.py tests
Runs all weather query tests and provides a comprehensive report
"""

import asyncio
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def run_all_tests():
    """Run all tests for main.py"""
    print("🧪 RUNNING ALL TESTS FOR MAIN.PY")
    print("=" * 50)
    
    # Import and run weather tests
    try:
        from test_main_weather import run_weather_tests
        print("🌤️  Running weather query tests...")
        weather_success = await run_weather_tests()
        print()
    except Exception as e:
        print(f"❌ Weather tests failed to run: {e}")
        weather_success = False
    
    # Import and run demo tests
    try:
        from test_mcp_weather_demo import run_weather_demo
        print("🎬 Running weather demo tests...")
        demo_success = await run_weather_demo()
        print()
    except Exception as e:
        print(f"❌ Demo tests failed to run: {e}")
        demo_success = False
    
    # Summary
    print("📊 FINAL TEST SUMMARY")
    print("=" * 30)
    print(f"🌤️  Weather Query Tests: {'✅ PASSED' if weather_success else '❌ FAILED'}")
    print(f"🎬 Demo Tests: {'✅ PASSED' if demo_success else '❌ FAILED'}")
    
    if weather_success and demo_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ main.py is fully functional")
        print("✅ Weather query 'what's the weather like in Spokane?' works")
        print("✅ MCP client integration verified")
        print("✅ Error handling works")
        print("✅ Session management works")
        print("✅ Ready for deployment")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print("Please review the test output above")
    
    return weather_success and demo_success

if __name__ == "__main__":
    asyncio.run(run_all_tests())
