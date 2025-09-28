import asyncio
import json
import os
import sys
from typing import Optional, Dict
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from openai import OpenAI
from dotenv import load_dotenv

# Import LangChain agent
from langchain_agent import LangChainAgent, MCPToolAdapter

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, use_langchain_agent: bool = True):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = OpenAI()
        
        # Initialize LangChain agent
        self.use_langchain_agent = use_langchain_agent
        self.langchain_agent: Optional[LangChainAgent] = None
        self.mcp_tool_adapter: Optional[MCPToolAdapter] = None
        
        if use_langchain_agent:
            self._setup_langchain_agent()

    def _setup_langchain_agent(self):
        """Setup the LangChain agent with configuration."""
        try:
            # Get configuration from environment variables
            model_name = os.getenv("LANGCHAIN_MODEL", "gpt-4o")
            temperature = float(os.getenv("LANGCHAIN_TEMPERATURE", "0.7"))
            use_langgraph_cloud = os.getenv("LANGGRAPH_CLOUD_ENABLED", "false").lower() == "true"
            cloud_deployment_id = os.getenv("LANGGRAPH_CLOUD_DEPLOYMENT_ID")
            
            self.langchain_agent = LangChainAgent(
                model_name=model_name,
                temperature=temperature,
                use_langgraph_cloud=use_langgraph_cloud,
                cloud_deployment_id=cloud_deployment_id
            )
            
            print("✅ LangChain agent initialized")
            
        except Exception as e:
            print(f"❌ Failed to setup LangChain agent: {e}")
            self.use_langchain_agent = False

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
        
        # Setup MCP tools for LangChain agent if enabled
        if self.use_langchain_agent and self.langchain_agent:
            try:
                self.mcp_tool_adapter = MCPToolAdapter(self.session)
                await self.mcp_tool_adapter.setup_mcp_tools(self.langchain_agent)
                print("✅ MCP tools integrated with LangChain agent")
            except Exception as e:
                print(f"⚠️ Failed to integrate MCP tools with LangChain agent: {e}")

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
        """Process a query using LangChain agent or fallback to OpenAI"""
        if self.use_langchain_agent and self.langchain_agent:
            try:
                # Use LangChain agent for advanced processing
                print("🤖 Using LangChain agent for processing...")
                response = await self.langchain_agent.process_query(query)
                return response
            except Exception as e:
                print(f"⚠️ LangChain agent failed, falling back to basic processing: {e}")
                return await self._process_query_basic(query)
        else:
            # Use basic OpenAI processing
            return await self._process_query_basic(query)
    
    async def _process_query_basic(self, query: str) -> str:
        """Basic query processing using OpenAI and MCP tools"""
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
    
    def get_agent_status(self) -> Dict:
        """Get the status of the LangChain agent"""
        if not self.use_langchain_agent or not self.langchain_agent:
            return {"enabled": False, "reason": "LangChain agent not enabled"}
        
        return {
            "enabled": True,
            "model": self.langchain_agent.model_name,
            "temperature": self.langchain_agent.temperature,
            "tools_available": len(self.langchain_agent.tools),
            "conversation_history_length": len(self.langchain_agent.get_conversation_history()),
            "langgraph_cloud_enabled": self.langchain_agent.use_langgraph_cloud
        }
    
    def clear_agent_memory(self):
        """Clear the LangChain agent's conversation memory"""
        if self.langchain_agent:
            self.langchain_agent.clear_memory()
            print("✅ Agent memory cleared")
        else:
            print("⚠️ LangChain agent not available")
    
    def export_conversation(self, filename: Optional[str] = None) -> str:
        """Export the conversation history"""
        if self.langchain_agent:
            return self.langchain_agent.export_conversation(filename)
        else:
            print("⚠️ LangChain agent not available for export")
            return ""

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("Special commands: 'status', 'clear', 'export', 'help'")
        
        while True:
            try:
                # Use asyncio to handle input in a non-blocking way
                import asyncio
                loop = asyncio.get_event_loop()
                query = await loop.run_in_executor(None, input, "\nQuery: ")
                query = query.strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'status':
                    status = self.get_agent_status()
                    print(f"\n📊 Agent Status: {json.dumps(status, indent=2)}")
                    continue
                elif query.lower() == 'clear':
                    self.clear_agent_memory()
                    continue
                elif query.lower() == 'export':
                    filename = self.export_conversation()
                    if filename:
                        print(f"📁 Conversation exported to: {filename}")
                    continue
                elif query.lower() == 'help':
                    print("\n🔧 Available commands:")
                    print("  status  - Show agent status and configuration")
                    print("  clear   - Clear conversation memory")
                    print("  export  - Export conversation to JSON file")
                    print("  help    - Show this help message")
                    print("  quit    - Exit the application")
                    continue
                    
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
    server_url = os.getenv('MCP_SERVER_URL')

    print(f"Connecting to MCP server: {server_url}")

    if not server_url:
        print("Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/sse)>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_sse_server(server_url)
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        await client.cleanup()


def create_langgraph_agent():
    """
    Create a LangGraph agent for deployment to LangGraph Cloud.
    This function is called by LangGraph Cloud to create the agent graph.
    """
    try:
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, AIMessage
        import os
        
        # Initialize the language model
        llm = ChatOpenAI(
            model=os.getenv("LANGCHAIN_MODEL", "gpt-4o"),
            temperature=float(os.getenv("LANGCHAIN_TEMPERATURE", "0.7")),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Define the state
        from typing import TypedDict, Annotated
        
        class AgentState(TypedDict):
            messages: Annotated[list, "The messages in the conversation"]
            user_input: str
            agent_response: str
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        def process_input(state: AgentState) -> AgentState:
            """Process user input and prepare for agent processing."""
            user_input = state["user_input"]
            messages = state.get("messages", [])
            
            # Add user message to conversation
            messages.append(HumanMessage(content=user_input))
            
            return {
                "messages": messages,
                "user_input": user_input,
                "agent_response": ""
            }
        
        def agent_reasoning(state: AgentState) -> AgentState:
            """Agent reasoning and response generation."""
            messages = state["messages"]
            
            # Get the last user message
            user_input = messages[-1].content if messages else ""
            
            # Generate response using the language model
            response = llm.invoke([HumanMessage(content=user_input)])
            
            # Add agent response to messages
            messages.append(AIMessage(content=response.content))
            
            return {
                "messages": messages,
                "agent_response": response.content,
                "user_input": state["user_input"]
            }
        
        def format_output(state: AgentState) -> AgentState:
            """Format the final output."""
            return {
                **state,
                "agent_response": f"Agent Response: {state['agent_response']}"
            }
        
        # Add nodes to the workflow
        workflow.add_node("process_input", process_input)
        workflow.add_node("agent_reasoning", agent_reasoning)
        workflow.add_node("format_output", format_output)
        
        # Add edges
        workflow.add_edge("process_input", "agent_reasoning")
        workflow.add_edge("agent_reasoning", "format_output")
        workflow.add_edge("format_output", END)
        
        # Set entry point
        workflow.set_entry_point("process_input")
        
        # Compile the graph
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        
        return app
        
    except ImportError as e:
        # Fallback for missing dependencies
        print(f"Warning: Missing dependencies for LangGraph agent: {e}")
        
        # Create a simple fallback agent
        from typing import TypedDict, Annotated
        
        class SimpleState(TypedDict):
            user_input: str
            agent_response: str
        
        def simple_agent(state: SimpleState) -> SimpleState:
            """Simple agent that echoes the input."""
            return {
                "user_input": state["user_input"],
                "agent_response": f"Echo: {state['user_input']}"
            }
        
        from langgraph.graph import StateGraph, END
        workflow = StateGraph(SimpleState)
        workflow.add_node("agent", simple_agent)
        workflow.add_edge("agent", END)
        workflow.set_entry_point("agent")
        
        return workflow.compile()


if __name__ == "__main__":
    import sys
    asyncio.run(main())