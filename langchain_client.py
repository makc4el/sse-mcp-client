import asyncio
import json
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from langchain.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv()


class MCPTool(BaseTool):
    """LangChain tool wrapper for MCP tools"""
    
    name: str
    description: str
    mcp_session: ClientSession
    input_schema: Dict[str, Any]
    
    def _run(self, **kwargs) -> str:
        """Synchronous run method - not used in async context"""
        raise NotImplementedError("Use async version")
    
    async def _arun(self, **kwargs) -> str:
        """Async run method for MCP tool execution"""
        try:
            result = await self.mcp_session.call_tool(self.name, kwargs)
            if result.content:
                return str(result.content[0].text)
            return "No result"
        except Exception as e:
            return f"Error: {str(e)}"


class LangChainMCPClient:
    """LangChain-compatible MCP client"""
    
    def __init__(self, server_url: str, model_name: str = "gpt-4o-mini"):
        self.server_url = server_url
        self.model_name = model_name
        self.session: Optional[ClientSession] = None
        self.tools: List[MCPTool] = []
        self.agent_executor: Optional[AgentExecutor] = None
        self._streams_context = None
        self._session_context = None
        
    async def connect(self):
        """Connect to the MCP server and initialize tools"""
        # Connect to MCP server
        self._streams_context = sse_client(url=self.server_url)
        streams = await self._streams_context.__aenter__()
        
        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()
        
        # Initialize session
        await self.session.initialize()
        
        # Get available tools
        response = await self.session.list_tools()
        mcp_tools = response.tools
        
        # Convert MCP tools to LangChain tools
        self.tools = []
        for tool in mcp_tools:
            langchain_tool = MCPTool(
                name=tool.name,
                description=tool.description,
                mcp_session=self.session,
                input_schema=tool.inputSchema if hasattr(tool, 'inputSchema') else {}
            )
            self.tools.append(langchain_tool)
        
        # Create LangChain agent
        self._create_agent()
        
        print(f"Connected to MCP server with {len(self.tools)} tools:")
        for tool in self.tools:
            print(f"  - {tool.name}: {tool.description}")
    
    def _create_agent(self):
        """Create LangChain agent with MCP tools"""
        # Initialize the LLM
        llm = ChatOpenAI(model=self.model_name, temperature=0)
        
        # Create memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with access to various tools. Use the available tools to help answer user questions."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_tools_agent(llm, self.tools, prompt)
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    async def chat(self, message: str) -> str:
        """Process a chat message using the agent"""
        if not self.agent_executor:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # Run the agent
        result = await self.agent_executor.ainvoke({"input": message})
        return result["output"]
    
    async def cleanup(self):
        """Clean up connections"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


async def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python langchain_client.py <SSE_SERVER_URL>")
        sys.exit(1)
    
    server_url = sys.argv[1]
    client = LangChainMCPClient(server_url)
    
    try:
        await client.connect()
        
        print("\nLangChain MCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                response = await client.chat(query)
                print(f"\nResponse: {response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()
    
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
