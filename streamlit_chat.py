#!/usr/bin/env python3
"""
Streamlit Web Chat Interface for MCP AI Agent

Run with: streamlit run streamlit_chat.py
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_client_lib.config import MCPClientConfig
from simple_langchain_agent import SimpleMCPAgent


@st.cache_resource
def get_agent():
    """Get or create the MCP agent (cached)"""
    return SimpleMCPAgent()


async def initialize_agent():
    """Initialize the MCP agent"""
    agent = get_agent()
    return await agent.setup()


async def send_message_to_agent(message: str):
    """Send message to agent and get response"""
    agent = get_agent()
    return await agent.ask(message)


def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="MCP AI Agent Chat",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 MCP AI Agent Chat")
    st.markdown("Chat with your MCP-enabled AI agent that has access to mathematical tools!")
    
    # Sidebar with configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Show current config
        server_url = MCPClientConfig.get_server_url()
        api_key_set = bool(MCPClientConfig.get_openai_api_key())
        
        st.info(f"**MCP Server:** {server_url}")
        st.info(f"**OpenAI API Key:** {'✅ Set' if api_key_set else '❌ Not Set'}")
        
        if st.button("🔄 Refresh Config"):
            st.rerun()
        
        # Instructions
        st.header("📖 Instructions")
        st.markdown("""
        **Try asking:**
        - What is 25 + 37?
        - Which is larger: 42 or 17?
        - Add 100 and 200
        - Find the maximum of 15, 89, and 33
        """)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent_initialized" not in st.session_state:
        st.session_state.agent_initialized = False
    
    # Check prerequisites
    if not api_key_set:
        st.error("❌ OpenAI API key not set! Please set the OPENAI_API_KEY environment variable.")
        st.stop()
    
    # Initialize agent
    if not st.session_state.agent_initialized:
        with st.spinner("🤖 Initializing MCP AI Agent..."):
            try:
                # Run async initialization
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(initialize_agent())
                loop.close()
                
                if success:
                    st.session_state.agent_initialized = True
                    st.success("✅ Agent initialized successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to initialize agent. Check your MCP server connection.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Initialization error: {str(e)}")
                st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about math..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Run async agent call
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(send_message_to_agent(prompt))
                    loop.close()
                    
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Export chat history
    if st.session_state.messages:
        with st.sidebar:
            st.header("💾 Export")
            if st.button("📥 Download Chat History"):
                chat_data = {
                    "timestamp": datetime.now().isoformat(),
                    "messages": st.session_state.messages
                }
                json_str = json.dumps(chat_data, indent=2)
                st.download_button(
                    label="💾 Download JSON",
                    data=json_str,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()
