# SSE MCP Client

A Python client for connecting to MCP (Model Context Protocol) servers that use Server-Sent Events (SSE) for real-time communication.

## Overview

This client implements the MCP specification for HTTP with SSE transport, allowing you to:

- Connect to MCP servers via Server-Sent Events
- Initialize MCP sessions
- Discover and call tools on the server
- Receive real-time notifications from the server
- Handle connection state changes

## Installation

1. Clone or download this client
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
import asyncio
from mcp_client import SSEMCPClient

async def main():
    # Create client
    client = SSEMCPClient("http://localhost:8000")
    
    try:
        # Connect and initialize
        await client.connect()
        await client.initialize()
        
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Call a tool
        result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
        print(f"Result: {result}")
        
    finally:
        await client.disconnect()

asyncio.run(main())
```

### Using Context Manager (Recommended)

```python
async def main():
    async with SSEMCPClient("http://localhost:8000") as client:
        await client.connect()
        await client.initialize()
        
        result = await client.call_tool("add_numbers", {"a": 10, "b": 20})
        print(f"Result: {result}")
        # Automatically disconnects when exiting the context

asyncio.run(main())
```

### Quick Tool Call Helper

For simple one-off tool calls:

```python
from mcp_client import quick_tool_call

async def main():
    result = await quick_tool_call(
        "http://localhost:8000",
        "find_max",
        {"a": 15, "b": 42}
    )
    print(f"Max: {result}")

asyncio.run(main())
```

## API Reference

### SSEMCPClient

The main client class for connecting to SSE MCP servers.

#### Constructor

```python
SSEMCPClient(server_url: str, timeout: int = 30)
```

- `server_url`: Base URL of the MCP server (e.g., "http://localhost:8000")
- `timeout`: Request timeout in seconds (default: 30)

#### Methods

##### Connection Management

- `async connect() -> bool`: Connect to the server via SSE
- `async disconnect()`: Disconnect from the server
- `async initialize() -> bool`: Initialize the MCP session

##### Tool Operations

- `async list_tools() -> List[Tool]`: Get available tools from server
- `async call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]`: Call a tool

##### Utilities

- `async health_check() -> bool`: Check if server is healthy
- `set_notification_handler(handler: Callable)`: Set notification event handler
- `set_connection_state_handler(handler: Callable)`: Set connection state change handler

#### Properties

- `state: ConnectionState`: Current connection state
- `session_id: Optional[str]`: Current session ID
- `tools: List[Tool]`: Cached list of available tools
- `initialized: bool`: Whether the MCP session is initialized

### Helper Functions

#### create_client()

```python
async def create_client(server_url: str, timeout: int = 30) -> SSEMCPClient
```

Creates a connected and initialized client in one call.

#### quick_tool_call()

```python
async def quick_tool_call(server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]
```

Connects, calls a tool, and disconnects automatically.

### Event Handlers

#### Notification Handler

Handle server notifications:

```python
def notification_handler(notification):
    params = notification.get("params", {})
    level = params.get("level", "info")
    data = params.get("data", "")
    print(f"Server says [{level}]: {data}")

client.set_notification_handler(notification_handler)
```

#### Connection State Handler

Handle connection state changes:

```python
from mcp_client import ConnectionState

def state_handler(state: ConnectionState):
    print(f"Connection state: {state.value}")

client.set_connection_state_handler(state_handler)
```

Connection states:
- `DISCONNECTED`: Not connected
- `CONNECTING`: Establishing connection
- `CONNECTED`: Connected and ready
- `ERROR`: Connection error occurred

## Example Server

This client is designed to work with the SSE MCP server in the `../sse-mcp-server/` directory. The server provides these tools:

- `add_numbers`: Calculate the sum of two numbers
- `find_max`: Find the larger of two numbers

To start the server:

```bash
cd ../sse-mcp-server
pip install -r requirements.txt
python main.py
```

The server will start on `http://localhost:8000`.

## Examples

Run the example script to see the client in action:

```bash
python example.py
```

This will demonstrate:
- Basic connection and tool calling
- Context manager usage
- Quick tool calls
- Error handling
- Health checking

## Error Handling

The client handles various error conditions:

```python
try:
    async with SSEMCPClient("http://localhost:8000") as client:
        await client.connect()
        await client.initialize()
        
        result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
        
except Exception as e:
    print(f"Error: {e}")
```

Common errors:
- Connection failures
- Invalid tool names
- Missing or invalid tool arguments
- Server errors
- Network timeouts

## Logging

The client uses Python's standard logging. To see debug information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Log levels:
- `INFO`: Connection events, tool calls
- `DEBUG`: Detailed protocol messages
- `ERROR`: Error conditions

## Protocol Details

This client implements the MCP specification for HTTP with SSE transport:

1. **Connection**: GET `/connect` establishes SSE connection
2. **Endpoint Event**: Server sends endpoint URI with session ID
3. **Messages**: POST to message endpoint for MCP requests
4. **Notifications**: Real-time notifications via SSE

### Message Flow

```
Client                    Server
  |                         |
  |-- GET /connect -------->|
  |<-- SSE endpoint event --|
  |                         |
  |-- POST /messages ------>|  (initialize)
  |<-- response ------------|
  |                         |
  |-- POST /messages ------>|  (tools/list)
  |<-- response ------------|
  |                         |
  |-- POST /messages ------>|  (tools/call)
  |<-- response ------------|
  |<-- SSE notification ----|  (optional)
```

## Requirements

- Python 3.7+
- httpx for HTTP requests
- asyncio for async operations

See `requirements.txt` for specific versions.

## License

This client is provided as-is for educational and development purposes.
# LangGraph deployment trigger - Thu Sep 25 23:00:31 EEST 2025
