#!/usr/bin/env python3
"""
Test script to verify the LangGraph configuration error is fixed

This tests the LangChain integration without requiring OpenAI API key.
"""

import asyncio
import logging
from langchain_integration import MCPToolAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_langchain_imports():
    """Test that LangChain imports work without LangGraph errors"""
    print("🧪 Testing LangChain Imports (No LangGraph Dependencies)")
    print("=" * 60)
    
    try:
        # Test basic LangChain imports
        print("1️⃣ Testing basic LangChain imports...")
        from langchain.agents import initialize_agent, AgentType
        from langchain.tools import BaseTool
        print("   ✅ Basic LangChain imports successful")
        
        # Test OpenAI imports (should work even without API key)
        print("2️⃣ Testing LangChain OpenAI imports...")
        from langchain_openai import ChatOpenAI
        print("   ✅ LangChain OpenAI imports successful")
        
        # Test MCP tool integration
        print("3️⃣ Testing MCP tool integration...")
        adapter = MCPToolAdapter("http://localhost:8000")
        await adapter.connect()
        tools = await adapter.load_tools()
        print(f"   ✅ MCP integration successful - {len(tools)} tools loaded")
        
        # Test tool schema compatibility with LangChain
        print("4️⃣ Testing LangChain tool compatibility...")
        for tool in tools:
            assert isinstance(tool, BaseTool), f"Tool {tool.name} is not a BaseTool"
            assert hasattr(tool, 'name'), f"Tool missing name attribute"
            assert hasattr(tool, 'description'), f"Tool missing description attribute"
            print(f"   ✅ Tool {tool.name} is LangChain compatible")
        
        await adapter.disconnect()
        
        # Test agent creation (without LLM)
        print("5️⃣ Testing agent initialization structure...")
        # This tests the agent setup without actually creating it
        agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION
        print(f"   ✅ Agent type {agent_type} available")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ No LangGraph configuration errors")
        print("✅ LangChain integration working correctly")
        print("✅ MCP tools are LangChain compatible")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_execution():
    """Test actual tool execution through LangChain interface"""
    print("\n🔧 Testing Tool Execution via LangChain Interface")
    print("=" * 60)
    
    try:
        adapter = MCPToolAdapter("http://localhost:8000")
        await adapter.connect()
        tools = await adapter.load_tools()
        
        # Find and test the add_numbers tool
        add_tool = None
        for tool in tools:
            if tool.name == "add_numbers":
                add_tool = tool
                break
        
        if not add_tool:
            print("❌ add_numbers tool not found")
            return False
        
        print(f"1️⃣ Testing {add_tool.name} tool...")
        result = await add_tool._arun(a=15, b=25)
        print(f"   Input: a=15, b=25")
        print(f"   Output: {result}")
        
        # Verify the result contains expected value
        if "40" in str(result):
            print("   ✅ Tool execution successful")
        else:
            print(f"   ❌ Unexpected result: {result}")
            return False
        
        # Test find_max tool
        max_tool = None
        for tool in tools:
            if tool.name == "find_max":
                max_tool = tool
                break
        
        if max_tool:
            print(f"2️⃣ Testing {max_tool.name} tool...")
            result = await max_tool._arun(a=30, b=20)
            print(f"   Input: a=30, b=20")
            print(f"   Output: {result}")
            
            if "30" in str(result):
                print("   ✅ Tool execution successful")
            else:
                print(f"   ❌ Unexpected result: {result}")
                return False
        
        await adapter.disconnect()
        
        print("\n🎉 TOOL EXECUTION TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Tool execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 LangChain Integration Fix Verification")
    print("=" * 80)
    
    # Check server
    try:
        from mcp_client import SSEMCPClient
        client = SSEMCPClient("http://localhost:8000")
        if not await client.health_check():
            print("❌ MCP server not running. Start with: cd ../sse-mcp-server && python main.py")
            return
        await client.disconnect()
        print("✅ MCP server is running")
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return
    
    # Run tests
    test1_passed = await test_langchain_imports()
    test2_passed = await test_tool_execution()
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 80)
    print(f"✅ LangChain Import Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Tool Execution Test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 ALL TESTS PASSED - LangGraph Error Fixed!")
        print(f"💡 You can now use the LangChain agent with OpenAI API key:")
        print(f"   export OPENAI_API_KEY='your-key-here'")
        print(f"   python simple_langchain_agent.py")
    else:
        print(f"\n❌ Some tests failed. Check the output above.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
