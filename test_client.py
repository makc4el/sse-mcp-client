#!/usr/bin/env python3
"""
Simple test for the SSE MCP Client

Run this with the SSE MCP server running on localhost:8000
"""

import asyncio
import sys
from mcp_client import SSEMCPClient, quick_tool_call


async def test_health_check():
    """Test server health check"""
    print("🏥 Testing health check...")
    client = SSEMCPClient("http://localhost:8000")
    
    try:
        is_healthy = await client.health_check()
        if is_healthy:
            print("✅ Server is healthy")
            return True
        else:
            print("❌ Server is not healthy")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    finally:
        await client.disconnect()


async def test_basic_connection():
    """Test basic connection and initialization"""
    print("🔗 Testing basic connection...")
    
    async with SSEMCPClient("http://localhost:8000") as client:
        try:
            # Connect
            if not await client.connect():
                print("❌ Failed to connect")
                return False
                
            # Initialize
            if not await client.initialize():
                print("❌ Failed to initialize")
                return False
                
            print("✅ Connection and initialization successful")
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


async def test_tool_operations():
    """Test tool listing and calling"""
    print("🛠️ Testing tool operations...")
    
    async with SSEMCPClient("http://localhost:8000") as client:
        try:
            await client.connect()
            await client.initialize()
            
            # List tools
            tools = await client.list_tools()
            print(f"📋 Found {len(tools)} tools: {[t.name for t in tools]}")
            
            if len(tools) == 0:
                print("❌ No tools found")
                return False
            
            # Test add_numbers tool
            if any(t.name == "add_numbers" for t in tools):
                result = await client.call_tool("add_numbers", {"a": 10, "b": 5})
                print(f"🧮 add_numbers(10, 5) = {result}")
                
            # Test find_max tool  
            if any(t.name == "find_max" for t in tools):
                result = await client.call_tool("find_max", {"a": 7, "b": 12})
                print(f"📊 find_max(7, 12) = {result}")
            
            print("✅ Tool operations successful")
            return True
            
        except Exception as e:
            print(f"❌ Tool operations failed: {e}")
            return False


async def test_quick_call():
    """Test quick tool call helper"""
    print("🚀 Testing quick tool call...")
    
    try:
        result = await quick_tool_call(
            "http://localhost:8000",
            "add_numbers",
            {"a": 100, "b": 200}
        )
        print(f"🏃 Quick call result: {result}")
        print("✅ Quick tool call successful")
        return True
        
    except Exception as e:
        print(f"❌ Quick tool call failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 SSE MCP Client Tests")
    print("=" * 30)
    
    tests = [
        ("Health Check", test_health_check),
        ("Basic Connection", test_basic_connection),
        ("Tool Operations", test_tool_operations),
        ("Quick Tool Call", test_quick_call),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)
