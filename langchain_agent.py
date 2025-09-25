"""
LangChain-compatible AI Agent with OpenAI LLM integration
"""
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
import asyncio
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    BaseMessage, 
    HumanMessage, 
    AIMessage, 
    SystemMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from config import get_config


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses"""
    
    def __init__(self, on_token_callback=None):
        self.on_token_callback = on_token_callback
        self.tokens = []
    
    def on_llm_new_token(
        self, 
        token: str, 
        *, 
        run_id: Any = None, 
        parent_run_id: Any = None, 
        **kwargs: Any
    ) -> Any:
        self.tokens.append(token)
        if self.on_token_callback:
            self.on_token_callback(token)


class OpenAILangChainAgent:
    """
    A LangChain-compatible AI agent that provides OpenAI LLM chat functionality.
    
    Features:
    - Full LangChain integration
    - Streaming support
    - Conversation memory
    - Customizable system prompts
    - Message history management
    """
    
    def __init__(self, config=None):
        """Initialize the agent with configuration"""
        self.config = config or get_config()
        self.conversation_history: List[BaseMessage] = []
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=self.config.openai_model,
            temperature=self.config.openai_temperature,
            max_tokens=self.config.openai_max_tokens,
            openai_api_key=self.config.openai_api_key,
            streaming=self.config.enable_streaming
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.system_message),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create the chain
        self.chain = (
            RunnablePassthrough.assign(
                history=RunnableLambda(self._get_history)
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        print(f"🤖 {self.config.agent_name} initialized with {self.config.openai_model}")
    
    def _get_history(self, inputs: Dict[str, Any]) -> List[BaseMessage]:
        """Get conversation history for the prompt"""
        # Limit history to prevent context overflow
        max_length = self.config.max_history_length
        if len(self.conversation_history) > max_length:
            return self.conversation_history[-max_length:]
        return self.conversation_history
    
    def add_system_message(self, message: str):
        """Add a system message to the conversation"""
        self.conversation_history.append(SystemMessage(content=message))
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        print("🗑️ Conversation history cleared")
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation history"""
        return {
            "total_messages": len(self.conversation_history),
            "human_messages": len([m for m in self.conversation_history if isinstance(m, HumanMessage)]),
            "ai_messages": len([m for m in self.conversation_history if isinstance(m, AIMessage)]),
            "system_messages": len([m for m in self.conversation_history if isinstance(m, SystemMessage)])
        }
    
    def chat(self, message: str, stream: bool = None) -> str:
        """
        Send a message to the agent and get a response
        
        Args:
            message: The user's message
            stream: Whether to stream the response (overrides config)
        
        Returns:
            The agent's response
        """
        if stream is None:
            stream = self.config.enable_streaming
        
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=message))
        
        try:
            if stream:
                return self._chat_streaming(message)
            else:
                return self._chat_sync(message)
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _chat_sync(self, message: str) -> str:
        """Synchronous chat without streaming"""
        response = self.chain.invoke({"input": message})
        
        # Add AI response to history
        self.conversation_history.append(AIMessage(content=response))
        
        return response
    
    def _chat_streaming(self, message: str) -> str:
        """Streaming chat with real-time token output"""
        full_response = ""
        
        print(f"\n🤖 {self.config.agent_name}: ", end="", flush=True)
        
        for token in self.chain.stream({"input": message}):
            print(token, end="", flush=True)
            full_response += token
        
        print()  # New line after response
        
        # Add AI response to history
        self.conversation_history.append(AIMessage(content=full_response))
        
        return full_response
    
    async def achat(self, message: str) -> str:
        """Async version of chat"""
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=message))
        
        try:
            response = await self.chain.ainvoke({"input": message})
            
            # Add AI response to history
            self.conversation_history.append(AIMessage(content=response))
            
            return response
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def astream(self, message: str) -> AsyncIterator[str]:
        """Async streaming chat"""
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=message))
        
        full_response = ""
        
        try:
            async for token in self.chain.astream({"input": message}):
                yield token
                full_response += token
            
            # Add AI response to history
            self.conversation_history.append(AIMessage(content=full_response))
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            yield error_msg
    
    def get_langchain_runnable(self):
        """Get the underlying LangChain runnable for advanced usage"""
        return self.chain
    
    def export_conversation(self) -> List[Dict[str, Any]]:
        """Export conversation history as JSON-serializable format"""
        return [
            {
                "type": type(msg).__name__,
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            }
            for msg in self.conversation_history
        ]
    
    def import_conversation(self, messages: List[Dict[str, Any]]):
        """Import conversation history from JSON format"""
        self.conversation_history.clear()
        
        for msg_data in messages:
            msg_type = msg_data["type"]
            content = msg_data["content"]
            
            if msg_type == "HumanMessage":
                self.conversation_history.append(HumanMessage(content=content))
            elif msg_type == "AIMessage":
                self.conversation_history.append(AIMessage(content=content))
            elif msg_type == "SystemMessage":
                self.conversation_history.append(SystemMessage(content=content))


def create_agent(config=None) -> OpenAILangChainAgent:
    """Factory function to create a new agent instance"""
    return OpenAILangChainAgent(config=config)


if __name__ == "__main__":
    # Quick test
    agent = create_agent()
    
    print(f"Testing {agent.config.agent_name}...")
    
    response = agent.chat("Hello! What can you help me with?")
    print(f"\nResponse: {response}")
    
    print(f"\nHistory summary: {agent.get_history_summary()}")
