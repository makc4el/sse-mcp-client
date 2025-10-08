import asyncio
import json
import os
import sys
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def cleanup(self):
        """Properly clean up the session and streams"""
        try:
            if hasattr(self, '_session_context') and self._session_context:
                await self._session_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error cleaning up session: {e}")
        
        try:
            if hasattr(self, '_streams_context') and self._streams_context:
                await self._streams_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"Error cleaning up streams: {e}")

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema if tool.inputSchema else {}
            }
        } for tool in response.tools]

        # Initial OpenAI API call
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []
        
        message = response.choices[0].message
        
        if message.content:
            final_text.append(message.content)
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": message.content or ""
                })
                messages.append({
                    "role": "user", 
                    "content": result.content
                })

                # Get next response from OpenAI
                response = self.openai.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.choices[0].message.content or "")

        return "\n".join(final_text)
    

    async def list_resources(self) -> list:
        """List available MCP resources/tools"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.list_tools()
            resources = []
            for tool in response.tools:
                resources.append({
                    "name": tool.name,
                    "description": tool.description,
                    "server": "mcp_server",  # Default server name
                    "uri": f"mcp://{tool.name}"  # Default URI format
                })
            return resources
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                # Use asyncio to handle input in a non-blocking way
                import asyncio
                loop = asyncio.get_event_loop()
                query = await loop.run_in_executor(None, input, "\nQuery: ")
                query = query.strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nInput stream closed. Exiting...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")


async def main():
    mcp_server_url = os.getenv("MCP_SERVER_URL")

    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url=mcp_server_url)
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        await client.cleanup()


# Synchronous wrapper function for use in main.py
def list_mcp_resources() -> list:
    """
    Synchronous wrapper to list MCP resources.
    This function is used by main.py to initialize MCP tools.
    """
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    if not mcp_server_url:
        raise ValueError("MCP_SERVER_URL environment variable is required")
    
    async def _async_list_resources():
        client = MCPClient()
        try:
            await client.connect_to_sse_server(server_url=mcp_server_url)
            resources = await client.list_resources()
            return resources
        finally:
            await client.cleanup()
    
    # Run the async function in a new event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to handle this differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _async_list_resources())
                return future.result()
        else:
            return asyncio.run(_async_list_resources())
    except RuntimeError:
        # No event loop running, create a new one
        return asyncio.run(_async_list_resources())


if __name__ == "__main__":
    import sys
    asyncio.run(main())