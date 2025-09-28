import asyncio
import json
import os
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
        if hasattr(self, '_session_context') and self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, '_streams_context') and self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    def convert_mcp_tools_to_openai(self, mcp_tools):
        """Convert MCP tool format to OpenAI function calling format"""
        openai_tools = []
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        mcp_tools = response.tools
        # Convert to OpenAI format
        openai_tools = self.convert_mcp_tools_to_openai(mcp_tools)

        # Initial OpenAI API call
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",  # Fixed model name
            max_tokens=1000,
            messages=messages,
            tools=openai_tools if openai_tools else None
        )

        # Get the response message
        response_message = response.choices[0].message
        final_text = []

        # Check if there's text content
        if response_message.content:
            final_text.append(response_message.content)

        # Handle tool calls if any
        if response_message.tool_calls:
            # Add assistant message to conversation
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"Calling tool: {tool_name} with args: {tool_args}")
                
                try:
                    # Execute tool call via MCP
                    result = await self.session.call_tool(tool_name, tool_args)
                    
                    # Add tool result to conversation
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(result.content[0].text) if result.content else "No result"
                    })
                    
                except Exception as e:
                    print(f"Tool call error: {e}")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": f"Error: {str(e)}"
                    })

            # Get final response from OpenAI with tool results
            final_response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1000,
                messages=messages,
            )
            
            final_message = final_response.choices[0].message
            if final_message.content:
                final_text.append(final_message.content)

        return "\n".join(final_text)
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print(f"\nResponse: {response}")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()


async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/sse)>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url=sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())