#!/usr/bin/env python3
"""
Simple LangChain Agent with MCP Tools

A simplified version that avoids LangGraph dependencies and uses
the most basic LangChain agent setup.
"""

import asyncio
import logging
import os
from langchain.agents import create_structured_chat_agent, AgentExecutor
from langchain.agents.structured_chat.base import STRUCTURED_CHAT_PREFIX, STRUCTURED_CHAT_FORMAT_INSTRUCTIONS, STRUCTURED_CHAT_SUFFIX
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from mcp_client_lib.langchain_integration import MCPToolAdapter
from mcp_client_lib.config import MCPClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleMCPAgent:
    """
    Simple LangChain agent using MCP tools
    
    This is a minimal implementation that avoids complex dependencies
    and focuses on core functionality.
    """
    
    def __init__(self, mcp_server_url: str = None):
        self.mcp_server_url = mcp_server_url or MCPClientConfig.get_server_url()
        self.adapter = None
        self.agent = None
        self.llm = None
    
    async def setup(self):
        """Set up the agent with MCP tools"""
        try:
            # Check for OpenAI API key
            api_key = MCPClientConfig.get_openai_api_key()
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0
            )
            
            # Connect to MCP server and get tools
            self.adapter = MCPToolAdapter(self.mcp_server_url)
            await self.adapter.connect()
            tools = await self.adapter.load_tools()
            
            logger.info(f"Connected to MCP server, found {len(tools)} tools")
            
            # Create structured chat agent for LangChain 0.2+
            prompt = ChatPromptTemplate.from_messages([
                ("system", STRUCTURED_CHAT_PREFIX),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ])
            
            agent = create_structured_chat_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            
            self.agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            logger.info("Agent setup complete!")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def ask(self, question: str) -> str:
        """Ask the agent a question"""
        if not self.agent:
            raise Exception("Agent not set up. Call setup() first.")
        
        try:
            # Use the synchronous invoke method (LangChain handles async internally)
            result = self.agent.invoke({"input": question})
            return result.get("output", str(result))
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources"""
        if self.adapter:
            await self.adapter.disconnect()


async def test_simple_agent():
    """Test the simple agent with various questions"""
    print("🤖 Simple MCP Agent Test")
    print("=" * 40)
    
    agent = SimpleMCPAgent()
    
    try:
        # Setup
        print("Setting up agent...")
        if not await agent.setup():
            print("❌ Setup failed!")
            return
        
        # Test questions
        questions = [
            "What is 25 + 37?",
            "Which is larger: 42 or 17?",
            "Add 100 and 200, then tell me the result",
            "Find the maximum of 15 and 89"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n--- Question {i} ---")
            print(f"Q: {question}")
            
            try:
                answer = await agent.ask(question)
                print(f"A: {answer}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        await agent.cleanup()


async def interactive_mode():
    """Interactive chat mode"""
    print("💬 Interactive MCP Agent")
    print("=" * 40)
    print("Ask questions! Type 'quit' to exit.")
    
    agent = SimpleMCPAgent()
    
    try:
        if not await agent.setup():
            print("❌ Setup failed!")
            return
        
        while True:
            try:
                question = input("\n🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("🤖 Thinking...")
                answer = await agent.ask(question)
                print(f"💡 Answer: {answer}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Interactive mode failed: {e}")
        
    finally:
        await agent.cleanup()


async def main():
    """Main function"""
    print("🚀 Simple LangChain + MCP Integration")
    print("=" * 50)
    
    # Print current configuration
    MCPClientConfig.print_config()
    print()
    
    # Check if server is running
    server_url = MCPClientConfig.get_server_url()
    try:
        from mcp_client_lib.mcp_client import SSEMCPClient
        client = SSEMCPClient(server_url)
        if not await client.health_check():
            print(f"❌ MCP server is not running at {server_url}!")
            if MCPClientConfig.is_production():
                print("Railway server might be down. Check deployment status.")
            else:
                print("Start local server with: cd ../sse-mcp-server && python main.py")
            return
        await client.disconnect()
        print("✅ MCP server is running")
    except Exception as e:
        print(f"❌ Cannot connect to MCP server at {server_url}: {e}")
        return
    
    # Check OpenAI API key
    if not MCPClientConfig.get_openai_api_key():
        print("❌ OPENAI_API_KEY not set!")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    print("✅ OpenAI API key found")
    
    # Choose mode
    print("\nChoose mode:")
    print("1. Run test questions")
    print("2. Interactive chat")
    
    try:
        choice = input("\nEnter choice (1-2): ").strip()
        
        if choice == "1":
            await test_simple_agent()
        elif choice == "2":
            await interactive_mode()
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
