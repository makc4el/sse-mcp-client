#!/usr/bin/env python3
"""
Simple demo of the SSE MCP Client

This demonstrates how to use the client to connect to the SSE MCP server
and perform basic operations.

Make sure the SSE MCP server is running on localhost:8000 before running this demo.
"""

import asyncio
import logging
from mcp_client import SSEMCPClient, ConnectionState

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


async def demo():
    """Run a simple demo of the MCP client"""
    print("🚀 SSE MCP Client Demo")
    print("=" * 30)
    
    # Create the client
    client = SSEMCPClient("http://localhost:8000")
    
    # Set up event handlers
    def on_notification(notification):
        params = notification.get("params", {})
        data = params.get("data", "")
        print(f"📢 Server: {data}")
    
    def on_state_change(state: ConnectionState):
        print(f"🔗 Connection: {state.value}")
    
    client.set_notification_handler(on_notification)
    client.set_connection_state_handler(on_state_change)
    
    try:
        print("\n1️⃣ Connecting to server...")
        if not await client.connect():
            print("❌ Failed to connect!")
            return
        
        print("\n2️⃣ Initializing MCP session...")
        if not await client.initialize():
            print("❌ Failed to initialize!")
            return
        
        print("\n3️⃣ Discovering tools...")
        tools = await client.list_tools()
        print(f"🛠️ Available tools:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description}")
        
        print("\n4️⃣ Testing tools...")
        
        # Test addition
        print("🧮 Testing add_numbers...")
        result = await client.call_tool("add_numbers", {"a": 42, "b": 58})
        print(f"   Result: {result}")
        
        # Test max
        print("🔢 Testing find_max...")
        result = await client.call_tool("find_max", {"a": 123, "b": 456})
        print(f"   Result: {result}")
        
        print("\n5️⃣ Waiting for any final notifications...")
        await asyncio.sleep(1)
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        
    finally:
        print("\n6️⃣ Disconnecting...")
        await client.disconnect()
        print("👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo crashed: {e}")
