# LangGraph Cloud Deployment Troubleshooting

This guide helps resolve common deployment issues with the MCP SSE Client on LangGraph Cloud.

## Common Issues and Solutions

### 1. Python Version Compatibility

**Issue**: `Python>=3.13 and mcp-sse-client==0.1.0 depends on Python>=3.13, we can conclude that mcp-sse-client==0.1.0 cannot be used.`

**Solution**: ✅ **FIXED** - Updated `pyproject.toml` to use `requires-python = ">=3.11"` to be compatible with LangGraph Cloud's Python 3.11 environment.

### 2. Missing Dependencies

**Issue**: Import errors for LangChain or LangGraph modules.

**Solution**: 
- Ensure all dependencies are listed in `pyproject.toml`
- Added `langchain-core` and `typing-extensions` for better compatibility
- The `create_langgraph_agent()` function includes fallback handling for missing dependencies

### 3. LangGraph Configuration Issues

**Issue**: Invalid `langgraph.json` configuration.

**Solution**: ✅ **FIXED** - Updated configuration with:
- Proper Python version specification (`"python_version": "3.11"`)
- Wolfi Linux distribution for security (`"image_distro": "wolfi"`)
- Complete configuration schema
- Proper metadata

### 4. Environment Variable Issues

**Issue**: Missing or incorrect environment variables.

**Solution**: 
- Use the provided `env.template` file
- Ensure all required variables are set:
  - `OPENAI_API_KEY`
  - `LANGCHAIN_MODEL`
  - `LANGCHAIN_TEMPERATURE`

### 5. Build Context Issues

**Issue**: Docker build failures due to large context or missing files.

**Solution**: 
- Ensure `.dockerignore` is properly configured
- Keep the project structure minimal
- Use the provided `langgraph.json` configuration

## Deployment Checklist

Before deploying to LangGraph Cloud:

- [ ] ✅ Python version set to `>=3.11` in `pyproject.toml`
- [ ] ✅ `langgraph.json` properly configured with Python 3.11
- [ ] ✅ All dependencies listed in `pyproject.toml`
- [ ] ✅ Environment variables configured
- [ ] ✅ `create_langgraph_agent()` function implemented
- [ ] ✅ Fallback handling for missing dependencies

## Configuration Files

### `langgraph.json`
```json
{
  "dependencies": ["."],
  "graphs": {
    "mcp-sse-agent": {
      "path": "client.py:create_langgraph_agent",
      "description": "MCP SSE Client with LangChain Agent",
      "config_schema": {
        "type": "object",
        "properties": {
          "model_name": {"type": "string", "default": "gpt-4o"},
          "temperature": {"type": "number", "default": 0.7},
          "max_tokens": {"type": "integer", "default": 4000},
          "memory_window": {"type": "integer", "default": 10}
        }
      }
    }
  },
  "env": ".env",
  "python_version": "3.11",
  "image_distro": "wolfi"
}
```

### `pyproject.toml`
```toml
[project]
name = "mcp-sse-client"
version = "0.1.0"
description = "SSE-based MCP Client for connecting to MCP servers"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.0.0",
    "mcp[cli]>=1.2.1",
    "python-dotenv>=1.0.1",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
    "langgraph>=0.2.0",
    "langgraph-cloud>=0.1.0",
    "httpx>=0.28.1",
    "pydantic>=2.0.0",
    "typing-extensions>=4.0.0",
]
```

## Testing Deployment

### Local Testing
```bash
# Test the agent function locally
python -c "from client import create_langgraph_agent; print('Agent created successfully')"
```

### Environment Testing
```bash
# Test with environment variables
export OPENAI_API_KEY=your_key_here
python -c "from client import create_langgraph_agent; agent = create_langgraph_agent(); print('Agent initialized')"
```

## Deployment Commands

### Deploy to LangGraph Cloud
```bash
# Using the deployment script
python deploy_langgraph.py

# Or manually using LangGraph CLI
langgraph deploy
```

### Check Deployment Status
```bash
# Check deployment status
langgraph status

# View logs
langgraph logs
```

## Troubleshooting Commands

### Check Dependencies
```bash
# Verify all dependencies are installed
uv sync

# Check for missing imports
python -c "import langchain, langgraph, openai; print('All imports successful')"
```

### Validate Configuration
```bash
# Validate langgraph.json
python -c "import json; json.load(open('langgraph.json')); print('Configuration valid')"
```

### Test Agent Function
```bash
# Test the agent creation function
python -c "from client import create_langgraph_agent; agent = create_langgraph_agent(); print('Agent created successfully')"
```

## Common Error Messages and Solutions

### 1. "Python>=3.13" Error
**Solution**: Change `requires-python = ">=3.11"` in `pyproject.toml`

### 2. "ImportError: No module named 'langchain'"
**Solution**: Add missing dependencies to `pyproject.toml`

### 3. "Invalid langgraph.json"
**Solution**: Validate JSON syntax and required fields

### 4. "Missing environment variables"
**Solution**: Set required environment variables in `.env` file

### 5. "Docker build failed"
**Solution**: Check `.dockerignore` and project structure

## Support

If you continue to experience issues:

1. Check the LangGraph Cloud documentation
2. Verify all configuration files
3. Test locally before deploying
4. Check the deployment logs for specific error messages
5. Ensure all dependencies are compatible with Python 3.11

## Recent Fixes Applied

- ✅ Updated Python version requirement to `>=3.11`
- ✅ Added `python_version: "3.11"` to `langgraph.json`
- ✅ Added `image_distro: "wolfi"` for security
- ✅ Simplified `create_langgraph_agent()` function
- ✅ Added fallback handling for missing dependencies
- ✅ Updated dependencies for better compatibility
