#!/usr/bin/env python3
"""
LangChain Agent with MCP Tools Example

This example demonstrates how to create a LangChain agent that uses
tools from an MCP server via our custom integration.
"""

import asyncio
import logging
from typing import List

# LangChain imports
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI  # You'll need: pip install langchain-openai

# Our MCP integration
from langchain_integration import MCPToolAdapter, create_mcp_tools
from mcp_client import SSEMCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Custom prompt template for the agent
REACT_PROMPT = """You are a helpful assistant with access to mathematical tools via an MCP server.
You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class MCPLangChainAgent:
    """
    LangChain agent that uses MCP tools
    
    This class creates and manages a LangChain agent that can use
    tools from an MCP server.
    """
    
    def __init__(self, 
                 mcp_server_url: str,
                 llm_model: str = "gpt-3.5-turbo",
                 openai_api_key: str = None):
        """
        Initialize the MCP LangChain agent
        
        Args:
            mcp_server_url: URL of the MCP server
            llm_model: OpenAI model to use
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.mcp_server_url = mcp_server_url
        self.llm_model = llm_model
        self.openai_api_key = openai_api_key
        
        self.mcp_adapter: MCPToolAdapter = None
        self.agent_executor: AgentExecutor = None
        self.llm = None
        
    async def initialize(self):
        """Initialize the agent with MCP tools"""
        try:
            # Initialize LLM
            logger.info(f"Initializing LLM: {self.llm_model}")
            self.llm = ChatOpenAI(
                model=self.llm_model,
                api_key=self.openai_api_key,
                temperature=0
            )
            
            # Connect to MCP server and load tools
            logger.info(f"Connecting to MCP server: {self.mcp_server_url}")
            self.mcp_adapter = MCPToolAdapter(self.mcp_server_url)
            await self.mcp_adapter.connect()
            tools = await self.mcp_adapter.load_tools()
            
            logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")
            
            # Create the prompt template
            prompt = PromptTemplate(
                template=REACT_PROMPT,
                input_variables=["input", "agent_scratchpad"],
                partial_variables={
                    "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
                    "tool_names": ", ".join([tool.name for tool in tools])
                }
            )
            
            # Create the ReAct agent
            agent = create_react_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=10,
                handle_parsing_errors=True
            )
            
            logger.info("Agent initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def run(self, query: str) -> str:
        """
        Run the agent with a query
        
        Args:
            query: User query/question
            
        Returns:
            Agent response
        """
        if not self.agent_executor:
            raise Exception("Agent not initialized. Call initialize() first.")
        
        try:
            logger.info(f"Running agent with query: {query}")
            result = await self.agent_executor.ainvoke({"input": query})
            return result["output"]
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.mcp_adapter:
            await self.mcp_adapter.disconnect()


async def demo_basic_usage():
    """Demonstrate basic usage of the MCP LangChain agent"""
    print("\n🤖 Basic MCP LangChain Agent Demo")
    print("=" * 40)
    
    # Note: You'll need to set OPENAI_API_KEY environment variable
    # or pass it as a parameter
    agent = MCPLangChainAgent("http://localhost:8000")
    
    try:
        await agent.initialize()
        
        # Test queries
        queries = [
            "What is 25 + 37?",
            "Find the maximum of 156 and 89",
            "Calculate the sum of 100 and 200, then find the maximum between that result and 250",
            "What's the larger number: the sum of 15+25 or the sum of 18+22?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n--- Query {i} ---")
            print(f"Question: {query}")
            
            try:
                response = await agent.run(query)
                print(f"Answer: {response}")
            except Exception as e:
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        
    finally:
        await agent.cleanup()


async def demo_interactive_mode():
    """Interactive demo mode"""
    print("\n💬 Interactive MCP LangChain Agent")
    print("=" * 40)
    print("Ask mathematical questions! Type 'quit' to exit.")
    
    agent = MCPLangChainAgent("http://localhost:8000")
    
    try:
        await agent.initialize()
        
        while True:
            try:
                query = input("\n🔢 Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    continue
                
                print("🤔 Thinking...")
                response = await agent.run(query)
                print(f"🤖 Answer: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except Exception as e:
        print(f"Failed to start interactive mode: {e}")
        
    finally:
        await agent.cleanup()


async def demo_without_openai():
    """Demo using MCP tools directly without LLM (for testing)"""
    print("\n🔧 Direct MCP Tools Demo (No LLM)")
    print("=" * 40)
    
    try:
        # Create MCP tools directly
        tools = await create_mcp_tools("http://localhost:8000")
        
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test tools directly
        for tool in tools:
            if tool.name == "add_numbers":
                result = await tool._arun(a=10, b=5)
                print(f"add_numbers(10, 5) = {result}")
            
            elif tool.name == "find_max":
                result = await tool._arun(a=42, b=17)
                print(f"find_max(42, 17) = {result}")
        
    except Exception as e:
        print(f"Direct tools demo failed: {e}")


async def main():
    """Main function to run demos"""
    print("🚀 MCP + LangChain Integration Demos")
    print("=" * 50)
    
    # Check if MCP server is running
    try:
        client = SSEMCPClient("http://localhost:8000")
        if not await client.health_check():
            print("❌ MCP server is not running!")
            print("Please start the server first:")
            print("cd ../sse-mcp-server && python main.py")
            return
        await client.disconnect()
        print("✅ MCP server is running")
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return
    
    # Run demos
    print("\nChoose a demo:")
    print("1. Direct MCP tools (no LLM required)")
    print("2. Basic agent demo (requires OpenAI API key)")  
    print("3. Interactive mode (requires OpenAI API key)")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            await demo_without_openai()
        elif choice == "2":
            await demo_basic_usage()
        elif choice == "3":
            await demo_interactive_mode()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
