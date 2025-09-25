"""
LangGraph-compatible agent implementation with OpenAI LLM
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from config import get_config


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    user_info: Dict[str, Any]
    conversation_metadata: Dict[str, Any]


class OpenAILangGraphAgent:
    """
    LangGraph-powered conversational agent with OpenAI LLM integration.
    
    Features:
    - State management with LangGraph
    - Persistent conversation memory
    - Checkpoint support for resuming conversations
    - Tool integration capabilities
    - Full LangGraph deployment compatibility
    """
    
    def __init__(self, config=None):
        """Initialize the LangGraph agent"""
        self.config = config or get_config()
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=self.config.openai_model,
            temperature=self.config.openai_temperature,
            max_tokens=self.config.openai_max_tokens,
            openai_api_key=self.config.openai_api_key,
            streaming=self.config.enable_streaming
        )
        
        # Create the conversation prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.system_message),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the chain
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        # Build the graph
        self.graph = self._build_graph()
        
        print(f"🔗 {self.config.agent_name} (LangGraph) initialized with {self.config.openai_model}")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation graph"""
        
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("conversation", self._conversation_node)
        workflow.add_node("update_metadata", self._update_metadata_node)
        
        # Set entry point
        workflow.set_entry_point("conversation")
        
        # Add edges
        workflow.add_edge("conversation", "update_metadata")
        workflow.add_edge("update_metadata", END)
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    def _conversation_node(self, state: AgentState) -> Dict[str, Any]:
        """Main conversation processing node"""
        
        # Get the last human message
        messages = state["messages"]
        if not messages or not isinstance(messages[-1], HumanMessage):
            return {"messages": [AIMessage(content="I'm ready to help! Please send me a message.")]}
        
        try:
            # Generate response using the chain
            response = self.chain.invoke({"messages": messages})
            
            # Return AI message
            return {"messages": [AIMessage(content=response)]}
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            return {"messages": [AIMessage(content=error_msg)]}
    
    def _update_metadata_node(self, state: AgentState) -> Dict[str, Any]:
        """Update conversation metadata"""
        
        metadata = state.get("conversation_metadata", {})
        messages = state["messages"]
        
        # Update metadata
        metadata.update({
            "last_updated": datetime.now().isoformat(),
            "total_messages": len(messages),
            "human_messages": len([m for m in messages if isinstance(m, HumanMessage)]),
            "ai_messages": len([m for m in messages if isinstance(m, AIMessage)]),
        })
        
        return {"conversation_metadata": metadata}
    
    def chat(self, message: str, thread_id: str = "default") -> str:
        """
        Send a message to the agent and get a response
        
        Args:
            message: The user's message
            thread_id: Thread ID for conversation persistence
            
        Returns:
            The agent's response
        """
        
        # Create initial state with user message
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_info": {},
            "conversation_metadata": {}
        }
        
        # Configure thread
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Run the graph
            result = self.graph.invoke(initial_state, config=config)
            
            # Extract the AI response
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                return ai_messages[-1].content
            else:
                return "I apologize, but I couldn't generate a response."
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def achat(self, message: str, thread_id: str = "default") -> str:
        """Async version of chat"""
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_info": {},
            "conversation_metadata": {}
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = await self.graph.ainvoke(initial_state, config=config)
            
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            if ai_messages:
                return ai_messages[-1].content
            else:
                return "I apologize, but I couldn't generate a response."
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def stream_chat(self, message: str, thread_id: str = "default"):
        """Stream chat responses"""
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_info": {},
            "conversation_metadata": {}
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            for event in self.graph.stream(initial_state, config=config, stream_mode="values"):
                if "messages" in event:
                    messages = event["messages"]
                    for msg in messages:
                        if isinstance(msg, AIMessage):
                            yield msg.content
                            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_conversation_history(self, thread_id: str = "default") -> List[BaseMessage]:
        """Get conversation history for a thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = self.graph.get_state(config)
            return state.values.get("messages", [])
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    def get_conversation_metadata(self, thread_id: str = "default") -> Dict[str, Any]:
        """Get conversation metadata for a thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = self.graph.get_state(config)
            return state.values.get("conversation_metadata", {})
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return {}
    
    def clear_conversation(self, thread_id: str = "default"):
        """Clear conversation history for a thread"""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Reset state by creating empty initial state
            empty_state = {
                "messages": [],
                "user_info": {},
                "conversation_metadata": {}
            }
            self.graph.update_state(config, empty_state)
            print(f"🗑️ Conversation {thread_id} cleared")
        except Exception as e:
            print(f"Error clearing conversation: {e}")
    
    def get_graph_visualization(self) -> str:
        """Get a text representation of the graph structure"""
        try:
            return self.graph.get_graph().draw_ascii()
        except Exception as e:
            return f"Could not generate graph visualization: {e}"
    
    def get_runnable(self):
        """Get the compiled LangGraph runnable for deployment"""
        return self.graph


def create_langgraph_agent(config=None) -> OpenAILangGraphAgent:
    """
    Factory function to create a new LangGraph agent instance.
    This is the callable referenced in langgraph.json
    """
    return OpenAILangGraphAgent(config=config)


# For LangGraph server deployment
def create_graph():
    """Create and return the compiled graph for server deployment"""
    agent = create_langgraph_agent()
    return agent.get_runnable()


if __name__ == "__main__":
    # Quick test
    agent = create_langgraph_agent()
    
    print(f"Testing {agent.config.agent_name}...")
    print("\nGraph structure:")
    print(agent.get_graph_visualization())
    
    # Test conversation
    response = agent.chat("Hello! Can you remember this conversation?")
    print(f"\nResponse: {response}")
    
    # Test memory
    response2 = agent.chat("What did I just ask you?")
    print(f"Follow-up: {response2}")
    
    # Show metadata
    metadata = agent.get_conversation_metadata()
    print(f"\nMetadata: {metadata}")
