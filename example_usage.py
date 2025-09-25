#!/usr/bin/env python3
"""
Example usage of the OpenAI LangChain Agent
"""
import asyncio
from langchain_agent import create_agent, OpenAILangChainAgent
from config import AgentConfig, get_config


def basic_usage_example():
    """Basic usage example"""
    print("🔄 Basic Usage Example")
    print("=" * 50)
    
    # Create agent with default configuration
    agent = create_agent()
    
    # Simple chat
    response = agent.chat("Hello! What can you help me with?")
    print(f"Agent: {response}\n")
    
    # Chat with custom streaming setting
    print("Streaming response:")
    agent.chat("Tell me a fun fact about Python programming", stream=True)
    print("\n")


def custom_configuration_example():
    """Example with custom configuration"""
    print("🔄 Custom Configuration Example")
    print("=" * 50)
    
    # Create custom configuration
    config = AgentConfig(
        openai_api_key=get_config().openai_api_key,  # Use existing key
        openai_model="gpt-3.5-turbo",
        openai_temperature=0.9,
        agent_name="Creative Assistant",
        system_message="You are a creative writing assistant. Help users with storytelling, poetry, and creative writing.",
        max_history_length=10
    )
    
    # Create agent with custom config
    agent = OpenAILangChainAgent(config=config)
    
    response = agent.chat("Write a short poem about artificial intelligence")
    print(f"Creative Assistant: {response}\n")


async def async_usage_example():
    """Async usage example"""
    print("🔄 Async Usage Example")
    print("=" * 50)
    
    agent = create_agent()
    
    # Async chat
    response = await agent.achat("Explain the concept of async programming in Python")
    print(f"Agent: {response}\n")
    
    # Async streaming
    print("Async streaming response:")
    full_response = ""
    async for token in agent.astream("What are the benefits of using LangChain?"):
        print(token, end="", flush=True)
        full_response += token
    print("\n")


def conversation_management_example():
    """Example of conversation management features"""
    print("🔄 Conversation Management Example")
    print("=" * 50)
    
    agent = create_agent()
    
    # Multiple messages to build history
    agent.chat("My name is Alice and I'm a software engineer")
    agent.chat("What programming languages do you recommend for beginners?")
    agent.chat("Can you remember my name and profession?")
    
    # Show conversation statistics
    stats = agent.get_history_summary()
    print(f"Conversation stats: {stats}")
    
    # Export conversation
    conversation_data = agent.export_conversation()
    print(f"Exported {len(conversation_data)} messages")
    
    # Clear and import
    agent.clear_history()
    print("History cleared")
    
    agent.import_conversation(conversation_data)
    print("History restored")
    
    # Verify restoration worked
    final_stats = agent.get_history_summary()
    print(f"Restored stats: {final_stats}\n")


def langchain_integration_example():
    """Example of LangChain ecosystem integration"""
    print("🔄 LangChain Integration Example")
    print("=" * 50)
    
    agent = create_agent()
    
    # Get the underlying LangChain runnable
    chain = agent.get_langchain_runnable()
    
    print(f"Chain type: {type(chain)}")
    
    # Use the chain directly with LangChain methods
    result = chain.invoke({"input": "What is LangChain?"})
    print(f"Direct chain invocation: {result}")
    
    # Stream using LangChain streaming
    print("\nDirect chain streaming:")
    for token in chain.stream({"input": "Explain machine learning in simple terms"}):
        print(token, end="", flush=True)
    print("\n")


def error_handling_example():
    """Example of error handling"""
    print("🔄 Error Handling Example")
    print("=" * 50)
    
    agent = create_agent()
    
    try:
        # This should work normally
        response = agent.chat("Hello")
        print(f"Normal response: {response}")
        
        # Demonstrate graceful handling of potential issues
        very_long_message = "Tell me everything about " + "artificial intelligence " * 100
        response = agent.chat(very_long_message)
        print(f"Long message handled: {len(response)} chars")
        
    except Exception as e:
        print(f"Error caught and handled: {e}")
    
    print()


def specialized_agent_example():
    """Example of creating specialized agents"""
    print("🔄 Specialized Agent Example")
    print("=" * 50)
    
    # Python coding assistant
    coding_config = AgentConfig(
        openai_api_key=get_config().openai_api_key,
        openai_model="gpt-4",
        agent_name="Python Coding Assistant",
        system_message="""You are a Python programming expert. You help users write better Python code, 
        explain programming concepts, debug issues, and provide best practices. Always provide practical, 
        working code examples when possible.""",
        openai_temperature=0.3  # Lower temperature for more focused coding help
    )
    
    coding_agent = OpenAILangChainAgent(config=coding_config)
    response = coding_agent.chat("How do I implement a decorator in Python?")
    print(f"Coding Assistant: {response}\n")
    
    # Creative writing assistant
    creative_config = AgentConfig(
        openai_api_key=get_config().openai_api_key,
        openai_model="gpt-4",
        agent_name="Creative Writing Assistant",
        system_message="""You are a creative writing mentor. You help users with storytelling, 
        character development, plot creation, and writing techniques. Be encouraging and provide 
        constructive feedback to help improve their writing skills.""",
        openai_temperature=0.9  # Higher temperature for creativity
    )
    
    creative_agent = OpenAILangChainAgent(config=creative_config)
    response = creative_agent.chat("Help me create an interesting character for a sci-fi story")
    print(f"Creative Assistant: {response}\n")


async def main():
    """Run all examples"""
    print("🤖 OpenAI LangChain Agent - Usage Examples")
    print("=" * 60)
    print()
    
    try:
        # Run sync examples
        basic_usage_example()
        custom_configuration_example()
        conversation_management_example()
        langchain_integration_example()
        error_handling_example()
        specialized_agent_example()
        
        # Run async example
        await async_usage_example()
        
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if configuration is valid before running examples
    from config import validate_config
    
    if not validate_config():
        print("❌ Configuration validation failed.")
        print("Please run 'python main.py setup' to configure the application.")
    else:
        asyncio.run(main())
