#!/usr/bin/env python3
"""
LangGraph-compatible MCP Agent

This module provides a LangGraph-compatible graph definition for deployment
with LangGraph Server.
"""

import asyncio
import logging
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from mcp_client_lib.langchain_integration import MCPToolAdapter
from mcp_client_lib.config import MCPClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the MCP agent graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    mcp_server_url: Optional[str]
    tools_available: bool


class MCPGraphAgent:
    """MCP agent implemented as a LangGraph graph"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.mcp_server_url = self.config.get('mcp_server_url', MCPClientConfig.get_server_url())
        self.llm_model = self.config.get('llm_model', 'gpt-3.5-turbo')
        self.max_iterations = self.config.get('max_iterations', 10)
        self.verbose = self.config.get('verbose', True)
        
        self.llm = None
        self.adapter = None
        self.tools = []
        self.graph = None
    
    async def setup_tools(self, state: AgentState) -> AgentState:
        """Set up MCP tools"""
        try:
            if not self.adapter:
                self.adapter = MCPToolAdapter(self.mcp_server_url)
                await self.adapter.connect()
                self.tools = await self.adapter.load_tools()
                
                # Create LLM with tools
                self.llm = ChatOpenAI(
                    model=self.llm_model,
                    temperature=0
                ).bind_tools(self.tools)
                
                logger.info(f"Connected to MCP server, loaded {len(self.tools)} tools")
            
            state['tools_available'] = True
            return state
            
        except Exception as e:
            logger.error(f"Failed to setup tools: {e}")
            state['tools_available'] = False
            
            # Fallback to basic LLM without tools
            self.llm = ChatOpenAI(
                model=self.llm_model,
                temperature=0
            )
            return state
    
    async def call_model(self, state: AgentState) -> AgentState:
        """Call the language model"""
        try:
            messages = state['messages']
            
            # Call the model
            response = await self.llm.ainvoke(messages)
            
            # If there are tool calls, execute them
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Execute tool calls
                for tool_call in response.tool_calls:
                    try:
                        # Find the tool
                        tool = next((t for t in self.tools if t.name == tool_call['name']), None)
                        if tool:
                            result = await tool._arun(**tool_call['args'])
                            # Add tool result as a message
                            state['messages'].append(AIMessage(
                                content=f"Used tool {tool_call['name']}: {result}"
                            ))
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        state['messages'].append(AIMessage(
                            content=f"Tool {tool_call['name']} failed: {str(e)}"
                        ))
            
            # Add the response
            state['messages'].append(response)
            return state
            
        except Exception as e:
            logger.error(f"Model call failed: {e}")
            state['messages'].append(AIMessage(
                content=f"I encountered an error: {str(e)}"
            ))
            return state
    
    def should_continue(self, state: AgentState) -> str:
        """Determine if we should continue or end"""
        messages = state['messages']
        
        # Check if we've hit max iterations
        if len(messages) > self.max_iterations * 2:  # *2 for human+ai pairs
            return END
        
        # Check if the last message has tool calls
        if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
            return "tools"
        
        return END
    
    def create_graph(self) -> StateGraph:
        """Create the LangGraph graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("setup", self.setup_tools)
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.call_model)  # Same function handles tools
        
        # Add edges
        workflow.set_entry_point("setup")
        workflow.add_edge("setup", "agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()


# Global agent instance for LangGraph deployment
_agent_instance = None


async def get_agent(config: dict = None) -> MCPGraphAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MCPGraphAgent(config)
    return _agent_instance


async def create_graph(config: dict = None):
    """Create and return the MCP agent graph for LangGraph deployment"""
    agent = await get_agent(config)
    return agent.create_graph()


# This is the entry point that LangGraph will use
def graph_factory(config: dict = None):
    """Factory function for creating the graph (sync wrapper for LangGraph)"""
    # LangGraph expects a sync function, so we need to handle async
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(create_graph(config))


# Alternative sync entry point for LangGraph
def mcp_agent_graph(config: dict = None):
    """Direct graph creation for LangGraph deployment"""
    return graph_factory(config)


# Entry point that LangGraph expects
graph = graph_factory


if __name__ == "__main__":
    # Test the graph locally
    import asyncio
    
    async def test_graph():
        """Test the graph locally"""
        print("🔧 Testing LangGraph MCP Agent")
        
        try:
            # Create graph
            graph = await create_graph()
            
            # Test with a simple input
            initial_state = {
                "messages": [HumanMessage(content="What is 25 + 37?")],
                "mcp_server_url": MCPClientConfig.get_server_url(),
                "tools_available": False
            }
            
            result = await graph.ainvoke(initial_state)
            
            print("Graph execution result:")
            for msg in result['messages']:
                print(f"- {type(msg).__name__}: {msg.content}")
                
        except Exception as e:
            print(f"❌ Graph test failed: {e}")
    
    asyncio.run(test_graph())
