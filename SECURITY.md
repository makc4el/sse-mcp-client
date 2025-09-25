# Security Guidelines for MCP Client

## 🔐 **Sensitive Data Protection**

### **Environment Variables**
Never commit these sensitive values to version control:

- `OPENAI_API_KEY` - Your OpenAI API key
- `MCP_SERVER_URL` - Production server URLs (if they contain secrets)
- Any authentication tokens or credentials

### **Protected Files**
The following files are excluded from git commits via `.gitignore`:

```
.env                    # Environment variables with real values
__pycache__/           # Python cache files
*.pyc                  # Python compiled files
*.pyo                  # Python optimized files
.env.local             # Local environment overrides
.env.production        # Production environment files
*.log                  # Log files that might contain sensitive data
```

## 🛡️ **Setup Instructions**

### **1. Environment Variables Setup**
```bash
# Copy the template
cp env.template .env

# Edit .env with your actual values
# NEVER commit .env to git!
```

### **2. Required Environment Variables**
```bash
# In your .env file:
OPENAI_API_KEY=your-actual-openai-api-key-here
MCP_SERVER_URL=your-server-url-here
ENVIRONMENT=development
```

### **3. Shell Environment Setup**
```bash
# Load environment variables
source .env

# Or use the switch utility
eval $(python switch_environment.py local --export)
```

## ⚠️ **Security Checklist**

Before committing any changes:

- [ ] No API keys in code files
- [ ] No credentials in configuration files
- [ ] `.env` file is in `.gitignore`
- [ ] `__pycache__/` is excluded
- [ ] Log files are excluded
- [ ] Use `env.template` for sharing configuration structure

## 🔍 **Security Verification**

### **Check for sensitive data before commit:**
```bash
# Search for OpenAI API keys
git diff --cached | grep -i "sk-proj"

# Search all staged files
git grep -n "sk-proj" $(git diff --cached --name-only)

# Check what's being committed
git status
git diff --cached
```

### **Emergency: If you accidentally commit secrets:**
```bash
# If not pushed yet
git reset --soft HEAD~1
git reset HEAD .env

# If already pushed, contact your team immediately
# and rotate the compromised credentials
```

## 🔄 **Environment Management**

### **Local Development**
```bash
export OPENAI_API_KEY="your-key"
export ENVIRONMENT="development"
export MCP_SERVER_URL="http://localhost:8000"
```

### **Production Deployment**
```bash
export OPENAI_API_KEY="your-production-key"
export ENVIRONMENT="production"
export MCP_SERVER_URL="https://your-production-server.com"
```

### **Railway Deployment**
Set environment variables in Railway dashboard:
- `OPENAI_API_KEY` = your API key
- `ENVIRONMENT` = production
- `MCP_SERVER_URL` = auto-detected

## 🚨 **What to do if credentials are compromised:**

1. **Immediately rotate the API key** at OpenAI
2. **Update all deployments** with the new key
3. **Review git history** for other exposures
4. **Update team** about the incident

## ✅ **Safe Sharing**

### **DO:**
- Use `env.template` to show required variables
- Document environment setup in README
- Use environment variable names in code
- Store secrets in deployment platforms securely

### **DON'T:**
- Commit `.env` files
- Put secrets in code comments
- Share credentials in chat/email
- Include secrets in docker images
- Log sensitive values

Your security is important! Always double-check before committing. 🔒
