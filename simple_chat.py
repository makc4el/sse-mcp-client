#!/usr/bin/env python3
"""
Simple Terminal Chat with MCP AI Agent

A lightweight chat interface that's easy to run and use.
"""

import asyncio
import sys
from datetime import datetime

from mcp_client_lib.config import MCPClientConfig
from simple_langchain_agent import SimpleMCPAgent


def print_header():
    """Print chat header"""
    print("\n" + "=" * 60)
    print("🤖 MCP AI Agent - Simple Chat")
    print("=" * 60)
    print("💡 Tips:")
    print("  • Ask math questions like 'What is 25 + 37?'")
    print("  • Try 'Which is larger: 42 or 17?'")
    print("  • Type 'quit' or 'exit' to end the chat")
    print("  • Press Ctrl+C to force quit")
    print("=" * 60)


async def check_system():
    """Quick system check"""
    print("🔍 Checking system...")
    
    # Check API key
    if not MCPClientConfig.get_openai_api_key():
        print("❌ OpenAI API key not found!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    print("✅ OpenAI API key found")
    
    # Check MCP server
    server_url = MCPClientConfig.get_server_url()
    print(f"🌐 Using MCP server: {server_url}")
    
    return True


async def chat_loop():
    """Main chat loop"""
    print_header()
    
    # System check
    if not await check_system():
        return
    
    # Initialize agent
    print("\n🤖 Starting up agent...")
    agent = SimpleMCPAgent()
    
    try:
        if not await agent.setup():
            print("❌ Failed to initialize agent!")
            return
        
        print("✅ Agent ready! Start chatting...\n")
        
        # Chat loop
        message_count = 0
        while True:
            try:
                # Get user input
                user_input = input("🤔 You: ").strip()
                
                # Handle exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    print("💭 Please type a message or 'quit' to exit.")
                    continue
                
                # Send to agent
                print("🤖 Agent: ", end="", flush=True)
                start_time = datetime.now()
                
                response = await agent.ask(user_input)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(response)
                print(f"   ⏱️  Response time: {duration:.1f}s")
                
                message_count += 1
                
                # Add some spacing for readability
                if message_count % 3 == 0:
                    print("\n" + "-" * 40 + "\n")
                else:
                    print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Chat ended. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("🔄 Try again or type 'quit' to exit.\n")
    
    except Exception as e:
        print(f"❌ Setup error: {e}")
    
    finally:
        # Cleanup
        try:
            await agent.cleanup()
            print("🧹 Cleaned up resources")
        except:
            pass


async def main():
    """Main function"""
    try:
        await chat_loop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
