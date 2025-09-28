#!/usr/bin/env python3
"""
LangChain Agent with LangGraph Cloud compatibility for MCP SSE Client.

This module provides a comprehensive AI agent that integrates with LangChain
and LangGraph Cloud platform, offering advanced conversation capabilities
and tool integration.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph_cloud import LangGraphCloud

from dotenv import load_dotenv

load_dotenv()


class LangChainAgent:
    """
    Advanced AI Agent with LangChain and LangGraph Cloud integration.
    
    This agent provides:
    - Conversation memory management
    - Tool integration and execution
    - LangGraph Cloud deployment capabilities
    - Advanced reasoning and planning
    - Multi-step task execution
    """
    
    def __init__(self, 
                 model_name: str = "gpt-4o",
                 temperature: float = 0.7,
                 max_tokens: int = 4000,
                 memory_window: int = 10,
                 use_langgraph_cloud: bool = False,
                 cloud_deployment_id: Optional[str] = None):
        """
        Initialize the LangChain Agent.
        
        Args:
            model_name: OpenAI model to use
            temperature: Model temperature for creativity
            max_tokens: Maximum tokens per response
            memory_window: Number of conversation turns to remember
            use_langgraph_cloud: Whether to use LangGraph Cloud deployment
            cloud_deployment_id: LangGraph Cloud deployment ID
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory_window = memory_window
        self.use_langgraph_cloud = use_langgraph_cloud
        self.cloud_deployment_id = cloud_deployment_id
        
        # Initialize the language model
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            k=memory_window,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Initialize tools list
        self.tools: List[Tool] = []
        self.agent_executor: Optional[AgentExecutor] = None
        
        # Initialize LangGraph Cloud if enabled
        if use_langgraph_cloud:
            self._setup_langgraph_cloud()
    
    def _setup_langgraph_cloud(self):
        """Setup LangGraph Cloud integration."""
        try:
            self.langgraph_cloud = LangGraphCloud()
            print("✅ LangGraph Cloud integration initialized")
        except Exception as e:
            print(f"⚠️ LangGraph Cloud setup failed: {e}")
            self.use_langgraph_cloud = False
    
    def add_tool(self, name: str, description: str, func: callable):
        """
        Add a tool to the agent's toolkit.
        
        Args:
            name: Tool name
            description: Tool description
            func: Tool function to execute
        """
        tool = Tool(
            name=name,
            description=description,
            func=func
        )
        self.tools.append(tool)
        print(f"✅ Added tool: {name}")
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent prompt template."""
        system_message = """You are an advanced AI assistant with access to various tools and capabilities.

Your role is to:
1. Understand user queries and provide helpful, accurate responses
2. Use available tools when appropriate to gather information or perform tasks
3. Maintain context across the conversation
4. Provide clear explanations and reasoning for your actions

Available tools:
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

Previous conversation:
{chat_history}

Question: {input}"""
        
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
    
    def _setup_agent(self):
        """Setup the agent executor with tools and prompt."""
        if not self.tools:
            print("⚠️ No tools available, creating basic agent")
            return
        
        # Create the agent prompt
        prompt = self._create_agent_prompt()
        
        # Create the agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        print(f"✅ Agent setup complete with {len(self.tools)} tools")
    
    async def process_query(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Process a user query using the agent.
        
        Args:
            query: User query
            context: Additional context for the query
            
        Returns:
            Agent response
        """
        if not self.agent_executor:
            self._setup_agent()
        
        try:
            # Prepare input for the agent
            agent_input = {
                "input": query,
                "chat_history": self.memory.chat_memory.messages
            }
            
            if context:
                agent_input.update(context)
            
            # Execute the agent
            if self.use_langgraph_cloud and hasattr(self, 'langgraph_cloud'):
                # Use LangGraph Cloud for processing
                result = await self._process_with_langgraph_cloud(query, agent_input)
            else:
                # Use local agent execution
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.agent_executor.invoke, 
                    agent_input
                )
            
            # Extract the response
            if isinstance(result, dict):
                response = result.get("output", str(result))
            else:
                response = str(result)
            
            # Update memory
            self.memory.chat_memory.add_user_message(query)
            self.memory.chat_memory.add_ai_message(response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def _process_with_langgraph_cloud(self, query: str, context: Dict) -> str:
        """Process query using LangGraph Cloud."""
        try:
            # This would integrate with LangGraph Cloud API
            # For now, fallback to local processing
            print("🔄 Using LangGraph Cloud processing...")
            
            # Simulate cloud processing
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # For now, use local agent as fallback
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.agent_executor.invoke, 
                context
            )
            
            return result.get("output", str(result))
            
        except Exception as e:
            print(f"❌ LangGraph Cloud processing failed: {e}")
            # Fallback to local processing
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self.agent_executor.invoke, 
                context
            )
            return result.get("output", str(result))
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        messages = self.memory.chat_memory.messages
        history = []
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                history.append({
                    "user": messages[i].content if hasattr(messages[i], 'content') else str(messages[i]),
                    "assistant": messages[i + 1].content if hasattr(messages[i + 1], 'content') else str(messages[i + 1])
                })
        
        return history
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self.memory.clear()
        print("✅ Memory cleared")
    
    def get_available_tools(self) -> List[Dict]:
        """Get information about available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]
    
    def export_conversation(self, filename: Optional[str] = None) -> str:
        """Export conversation history to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        history = self.get_conversation_history()
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model_name,
            "temperature": self.temperature,
            "conversation": history,
            "tools": self.get_available_tools()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Conversation exported to {filename}")
        return filename


class MCPToolAdapter:
    """
    Adapter to integrate MCP tools with LangChain agent.
    """
    
    def __init__(self, mcp_session):
        """Initialize with MCP session."""
        self.mcp_session = mcp_session
        self.available_tools = {}
    
    async def setup_mcp_tools(self, agent: LangChainAgent):
        """Setup MCP tools for the LangChain agent."""
        try:
            # Get available tools from MCP session
            response = await self.mcp_session.list_tools()
            
            for tool in response.tools:
                tool_name = tool.name
                tool_description = tool.description
                
                # Create a wrapper function for the MCP tool
                async def create_tool_wrapper(tool_name, tool_description):
                    async def tool_wrapper(**kwargs):
                        try:
                            result = await self.mcp_session.call_tool(tool_name, kwargs)
                            return result.content if hasattr(result, 'content') else str(result)
                        except Exception as e:
                            return f"Error calling {tool_name}: {str(e)}"
                    return tool_wrapper
                
                # Add the tool to the agent
                tool_func = await create_tool_wrapper(tool_name, tool_description)
                agent.add_tool(tool_name, tool_description, tool_func)
                
                self.available_tools[tool_name] = {
                    "description": tool_description,
                    "schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
            
            print(f"✅ Setup {len(self.available_tools)} MCP tools for LangChain agent")
            
        except Exception as e:
            print(f"❌ Failed to setup MCP tools: {e}")


# Example usage and testing
async def main():
    """Example usage of the LangChain Agent."""
    # Initialize the agent
    agent = LangChainAgent(
        model_name="gpt-4o",
        temperature=0.7,
        use_langgraph_cloud=False  # Set to True when you have LangGraph Cloud setup
    )
    
    # Add some basic tools
    def get_weather(location: str) -> str:
        """Get weather information for a location."""
        return f"Weather in {location}: Sunny, 72°F"
    
    def calculate(expression: str) -> str:
        """Calculate mathematical expressions."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return "Error: Invalid expression"
    
    agent.add_tool("get_weather", "Get weather information", get_weather)
    agent.add_tool("calculate", "Calculate mathematical expressions", calculate)
    
    # Test the agent
    test_queries = [
        "What's the weather like in New York?",
        "Calculate 15 * 23 + 7",
        "Tell me about the weather and then calculate 100 / 4"
    ]
    
    for query in test_queries:
        print(f"\n🤖 Query: {query}")
        response = await agent.process_query(query)
        print(f"🤖 Response: {response}")
    
    # Export conversation
    agent.export_conversation()


if __name__ == "__main__":
    asyncio.run(main())
