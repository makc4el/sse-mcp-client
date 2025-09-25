#!/usr/bin/env python3
"""
Example usage of the SSE MCP Client

This script demonstrates how to:
1. Connect to an MCP server
2. Initialize the session
3. List available tools
4. Call tools with arguments
5. Handle notifications from the server
"""

import asyncio
import logging
from mcp_client import SSEMCPClient, ConnectionState, create_client, quick_tool_call

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def notification_handler(notification):
    """Handle notifications from the server"""
    params = notification.get("params", {})
    level = params.get("level", "info")
    data = params.get("data", "")
    print(f"🔔 Server notification [{level}]: {data}")


def connection_state_handler(state: ConnectionState):
    """Handle connection state changes"""
    print(f"🔗 Connection state: {state.value}")


async def example_basic_usage():
    """Example of basic client usage"""
    print("\n=== Basic Usage Example ===")
    
    # Create client
    client = SSEMCPClient("http://localhost:8000")
    
    # Set event handlers
    client.set_notification_handler(notification_handler)
    client.set_connection_state_handler(connection_state_handler)
    
    try:
        # Connect to server
        print("1. Connecting to server...")
        if not await client.connect():
            print("❌ Failed to connect")
            return
        print("✅ Connected!")
        
        # Initialize MCP session
        print("\n2. Initializing MCP session...")
        if not await client.initialize():
            print("❌ Failed to initialize")
            return
        print("✅ Initialized!")
        
        # List available tools
        print("\n3. Listing available tools...")
        tools = await client.list_tools()
        print(f"📋 Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Call the add_numbers tool
        print("\n4. Calling add_numbers tool...")
        result = await client.call_tool("add_numbers", {"a": 15, "b": 25})
        print(f"🧮 Add result: {result}")
        
        # Call the find_max tool
        print("\n5. Calling find_max tool...")
        result = await client.call_tool("find_max", {"a": 42, "b": 17})
        print(f"📊 Max result: {result}")
        
        # Wait a bit to see any final notifications
        print("\n6. Waiting for final notifications...")
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Disconnect
        print("\n7. Disconnecting...")
        await client.disconnect()
        print("✅ Disconnected!")


async def example_context_manager():
    """Example using context manager for automatic cleanup"""
    print("\n=== Context Manager Example ===")
    
    try:
        async with SSEMCPClient("http://localhost:8000") as client:
            client.set_notification_handler(notification_handler)
            
            # Connect and initialize
            await client.connect()
            await client.initialize()
            
            # Get tools and call one
            tools = await client.list_tools()
            print(f"📋 Available tools: {[t.name for t in tools]}")
            
            # Call a tool
            result = await client.call_tool("add_numbers", {"a": 100, "b": 200})
            print(f"🧮 Result: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("✅ Automatically disconnected!")


async def example_quick_tool_call():
    """Example using quick tool call helper"""
    print("\n=== Quick Tool Call Example ===")
    
    try:
        # One-line tool call
        result = await quick_tool_call(
            "http://localhost:8000",
            "find_max", 
            {"a": 999, "b": 1000}
        )
        print(f"🚀 Quick call result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_health_check():
    """Example of health checking the server"""
    print("\n=== Health Check Example ===")
    
    client = SSEMCPClient("http://localhost:8000")
    
    try:
        # Check if server is healthy before connecting
        print("🏥 Checking server health...")
        is_healthy = await client.health_check()
        
        if is_healthy:
            print("✅ Server is healthy!")
        else:
            print("❌ Server is not healthy!")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    finally:
        await client.disconnect()


async def example_error_handling():
    """Example of error handling"""
    print("\n=== Error Handling Example ===")
    
    client = SSEMCPClient("http://localhost:8000")
    
    try:
        await client.connect()
        await client.initialize()
        
        # Try to call a non-existent tool
        print("🧪 Testing error handling with invalid tool...")
        try:
            result = await client.call_tool("nonexistent_tool", {})
            print(f"Unexpected result: {result}")
        except Exception as e:
            print(f"✅ Caught expected error: {e}")
        
        # Try to call a tool with missing arguments
        print("🧪 Testing error handling with missing arguments...")
        try:
            result = await client.call_tool("add_numbers", {"a": 5})  # Missing 'b'
            print(f"Unexpected result: {result}")
        except Exception as e:
            print(f"✅ Caught expected error: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        await client.disconnect()


async def main():
    """Run all examples"""
    print("🚀 SSE MCP Client Examples")
    print("=" * 40)
    
    # Check server health first
    await example_health_check()
    
    # Run examples
    await example_basic_usage()
    await example_context_manager()
    await example_quick_tool_call()
    await example_error_handling()
    
    print("\n🎉 All examples completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
