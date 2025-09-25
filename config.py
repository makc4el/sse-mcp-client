"""
Configuration module for the OpenAI LangChain Agent
"""
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables
load_dotenv()


class AgentConfig(BaseSettings):
    """Configuration settings for the AI agent"""
    
    # OpenAI settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: Optional[int] = Field(default=None, env="OPENAI_MAX_TOKENS")
    
    # Agent settings
    agent_name: str = Field(default="OpenAI Assistant", env="AGENT_NAME")
    system_message: str = Field(
        default="You are a helpful AI assistant powered by OpenAI. You can help with various tasks, answer questions, and have conversations.",
        env="SYSTEM_MESSAGE"
    )
    
    # Chat settings
    max_history_length: int = Field(default=20, env="MAX_HISTORY_LENGTH")
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")
    
    # LangSmith (optional monitoring)
    langsmith_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="openai-langchain-agent", env="LANGSMITH_PROJECT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> AgentConfig:
    """Get the application configuration"""
    return AgentConfig()


def validate_config() -> bool:
    """Validate that all required configuration is present"""
    try:
        config = get_config()
        if not config.openai_api_key:
            print("❌ OPENAI_API_KEY is required")
            return False
        print("✅ Configuration validated successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


if __name__ == "__main__":
    # Test configuration
    if validate_config():
        config = get_config()
        print(f"Agent: {config.agent_name}")
        print(f"Model: {config.openai_model}")
        print(f"Temperature: {config.openai_temperature}")
