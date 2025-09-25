#!/usr/bin/env python3
"""
Interactive Chat Interface for MCP AI Agent

A simple chat interface to interact with the MCP-enabled AI agent.
Supports both command-line and web-based chat.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

from mcp_client_lib.config import MCPClientConfig
from simple_langchain_agent import SimpleMCPAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatSession:
    """Manages a chat session with the MCP agent"""
    
    def __init__(self):
        self.agent = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chat_history = []
        self.setup_complete = False
    
    async def initialize(self):
        """Initialize the MCP agent"""
        try:
            print("🤖 Initializing MCP AI Agent...")
            self.agent = SimpleMCPAgent()
            
            if await self.agent.setup():
                self.setup_complete = True
                print("✅ Agent ready! You can start chatting.")
                return True
            else:
                print("❌ Agent setup failed!")
                return False
                
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False
    
    async def send_message(self, message: str) -> str:
        """Send a message to the agent and get response"""
        if not self.setup_complete or not self.agent:
            return "❌ Agent not initialized. Please restart the chat."
        
        try:
            # Add user message to history
            self.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Get agent response
            response = await self.agent.ask(message)
            
            # Add agent response to history
            self.chat_history.append({
                "role": "agent", 
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Error processing message: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def cleanup(self):
        """Clean up resources"""
        if self.agent:
            await self.agent.cleanup()
    
    def save_history(self, filename: str = None):
        """Save chat history to file"""
        if not filename:
            filename = f"chat_history_{self.session_id}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.chat_history, f, indent=2)
            print(f"💾 Chat history saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save history: {e}")


async def cli_chat():
    """Command-line chat interface"""
    print("💬 MCP AI Agent - Interactive Chat")
    print("=" * 50)
    print("Commands:")
    print("  /help    - Show this help")
    print("  /history - Show chat history")
    print("  /save    - Save chat history")
    print("  /clear   - Clear screen")
    print("  /quit    - Exit chat")
    print("=" * 50)
    
    # Show current configuration
    MCPClientConfig.print_config()
    print()
    
    # Initialize chat session
    session = ChatSession()
    if not await session.initialize():
        return
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("\n🤔 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input == '/quit':
                        print("👋 Goodbye!")
                        break
                    elif user_input == '/help':
                        print("\nAvailable commands:")
                        print("  /help    - Show this help")
                        print("  /history - Show chat history")
                        print("  /save    - Save chat history")
                        print("  /clear   - Clear screen")
                        print("  /quit    - Exit chat")
                    elif user_input == '/history':
                        print("\n📜 Chat History:")
                        for i, msg in enumerate(session.chat_history, 1):
                            role = "🤔 You" if msg["role"] == "user" else "🤖 Agent"
                            print(f"{i}. {role}: {msg['content']}")
                    elif user_input == '/save':
                        session.save_history()
                    elif user_input == '/clear':
                        import os
                        os.system('clear' if os.name == 'posix' else 'cls')
                    else:
                        print("❌ Unknown command. Type /help for available commands.")
                    continue
                
                # Send message to agent
                print("🤖 Agent: ", end="", flush=True)
                response = await session.send_message(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted by user")
                break
            except EOFError:
                print("\n\n👋 Chat ended")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                continue
    
    finally:
        await session.cleanup()


async def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check MCP server
    server_url = MCPClientConfig.get_server_url()
    try:
        from mcp_client_lib.mcp_client import SSEMCPClient
        client = SSEMCPClient(server_url)
        if not await client.health_check():
            print(f"❌ MCP server is not running at {server_url}")
            if MCPClientConfig.is_production():
                print("   Railway server might be down. Check deployment status.")
            else:
                print("   Start local server with: cd ../sse-mcp-server && python main.py")
            return False
        await client.disconnect()
        print(f"✅ MCP server is running at {server_url}")
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return False
    
    # Check OpenAI API key
    if not MCPClientConfig.get_openai_api_key():
        print("❌ OPENAI_API_KEY not set!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print("   Or create a .env file with: OPENAI_API_KEY=your-key-here")
        return False
    
    print("✅ OpenAI API key found")
    return True


def create_web_interface():
    """Create a simple web interface using Streamlit (if available)"""
    try:
        import streamlit as st
        
        st.title("🤖 MCP AI Agent Chat")
        st.write("Interactive chat with your MCP-enabled AI agent")
        
        # Initialize session state
        if 'session' not in st.session_state:
            st.session_state.session = None
            st.session_state.initialized = False
        
        # Initialize agent
        if not st.session_state.initialized:
            with st.spinner("Initializing agent..."):
                # This would need to be adapted for Streamlit's async handling
                st.session_state.session = ChatSession()
                # Note: Streamlit doesn't handle async well, would need additional setup
                st.warning("Web interface requires additional setup for async support.")
                return
        
        # Chat interface
        user_input = st.text_input("Your message:", key="user_input")
        
        if st.button("Send") and user_input:
            # This would need async handling
            st.write("Web interface coming soon! Use CLI version for now.")
            
    except ImportError:
        print("📝 Streamlit not available. Install with: pip install streamlit")
        print("   Then run: streamlit run chat_interface.py")


async def main():
    """Main function"""
    print("🚀 MCP AI Agent Chat Interface")
    print("=" * 50)
    
    # Check prerequisites
    if not await check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return
    
    print("\n✅ All prerequisites met!")
    
    # Choose interface
    if len(sys.argv) > 1 and sys.argv[1] == '--web':
        create_web_interface()
    else:
        await cli_chat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
