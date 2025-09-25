# Environment Setup Guide for MCP Client

## 🎉 **SUCCESS! Your MCP + LangChain Integration is Working!**

The MCP client now supports both local development and Railway production environments with automatic configuration.

## 🌍 **Environment Configuration**

### **Quick Setup Commands**

```bash
# For LOCAL development
eval $(python switch_environment.py local --export)

# For RAILWAY production
eval $(python switch_environment.py railway --export)

```

### **Environment Variables**

The system automatically detects and uses these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `development` or `production` | `development` |
| `MCP_SERVER_URL` | Override server URL | Auto-detected |
| `OPENAI_API_KEY` | OpenAI API key for LangChain | Required |
| `MCP_CLIENT_TIMEOUT` | Request timeout in seconds | `30` |
| `MCP_CLIENT_VERBOSE` | Enable verbose logging | `false` |

### **Automatic URL Selection**

- **Local Development**: `http://localhost:8000`
- **Railway Production**: `https://web-production-b40eb.up.railway.app`

## 🧰 **Utility Scripts**

### **Environment Switcher**
```bash
# Show current configuration
python switch_environment.py current

# Switch to local
python switch_environment.py local

# Switch to Railway  
python switch_environment.py railway

# Test connection
python switch_environment.py test

# Export environment variables
eval $(python switch_environment.py local --export)
eval $(python switch_environment.py railway --export)
```

### **Configuration Module**
```python
from config import MCPClientConfig

# Get configured server URL
server_url = MCPClientConfig.get_server_url()

# Check if in production
is_prod = MCPClientConfig.is_production()

# Get OpenAI API key
api_key = MCPClientConfig.get_openai_api_key()

# Print current config
MCPClientConfig.print_config()
```

## ✅ **Working Examples**

### **1. Simple Demo**
```bash
export OPENAI_API_KEY="your-key-here"
eval $(python switch_environment.py local --export)
python demo.py
```

### **2. LangChain Agent**
```bash
export OPENAI_API_KEY="your-key-here"
eval $(python switch_environment.py local --export)
python simple_langchain_agent.py
```

### **3. Complete Integration Test**
```bash
export OPENAI_API_KEY="your-key-here"
eval $(python switch_environment.py local --export)
python complete_integration_test.py
```

## 🚀 **Test Results**

✅ **LOCAL ENVIRONMENT (WORKING)**
- Server URL: `http://localhost:8000`
- Connection: ✅ Healthy
- Tools discovered: ✅ 2 tools (`add_numbers`, `find_max`)
- LangChain integration: ✅ Working
- OpenAI API: ✅ Connected

**Example successful agent responses:**
- Q: "Which is larger: 42 or 17?" → A: "42" ✅
- Q: "Add 100 and 200" → A: "300" ✅
- Q: "Find the maximum of 15 and 89" → A: "89" ✅

⚠️ **RAILWAY ENVIRONMENT (DEPLOYMENT ISSUE)**
- Server URL: `https://web-production-b40eb.up.railway.app`
- Connection: ❌ 404 Not Found
- Status: Application not found on Railway

## 🐛 **Railway Deployment Status**

The Railway deployment is currently failing with "Application not found". This could be due to:

1. **Deployment failed** - Check Railway dashboard
2. **Domain not configured** - Verify Railway domain setup
3. **Service not running** - Check Railway logs
4. **Requirements conflict** - Verify dependency resolution

**Fixed dependency issues:**
- ✅ Removed conflicting `mcp==1.0.0` package
- ✅ Updated to compatible FastAPI/uvicorn versions
- ✅ Added explicit `anyio` version constraint

## 📋 **Development Workflow**

### **Local Development**
```bash
# Terminal 1: Start local MCP server
cd sse-mcp-server
python main.py

# Terminal 2: Use MCP client
cd sse-mcp-client
export OPENAI_API_KEY="your-key-here"
eval $(python switch_environment.py local --export)
python simple_langchain_agent.py
```

### **Production Testing**
```bash
# When Railway is fixed
export OPENAI_API_KEY="your-key-here"
eval $(python switch_environment.py railway --export)
python switch_environment.py test  # Check connection
python simple_langchain_agent.py   # Test agent
```

## 🔧 **Configuration Files**

### **config.py**
- Environment-aware configuration
- Automatic URL selection
- OpenAI API key management

### **switch_environment.py**
- Environment switching utility
- Connection testing
- Export commands for shell

### **Updated Client Files**
- `simple_langchain_agent.py` - Uses environment config
- `demo.py` - Environment-aware demo
- `langchain_integration.py` - Fixed event loop issues

## 🎯 **Next Steps**

1. **Fix Railway Deployment** - Debug the 404 error
2. **Test Railway Integration** - Once deployment works
3. **Production Monitoring** - Set up health checks
4. **Scale Testing** - Test with multiple concurrent users

Your MCP + LangChain integration is **working successfully locally** and ready for production once the Railway deployment is fixed! 🎉

