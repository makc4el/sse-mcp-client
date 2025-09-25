# 🤖 MCP AI Agent Chat Interfaces

Multiple ways to chat with your MCP-enabled AI agent that has access to mathematical tools!

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have:
- ✅ **MCP Server running** (locally or on Railway)
- ✅ **OpenAI API key** set as environment variable
- ✅ **Dependencies installed**: `pip install -r requirements.txt`

**Check your setup:**
```bash
# Check if MCP server is running
curl http://localhost:8000/health  # for local
# OR check your Railway URL/health

# Check if API key is set
echo $OPENAI_API_KEY
```

### 2. Choose Your Chat Interface

## 🖥️ **Option 1: Simple Terminal Chat** (Recommended)

**Easiest to use - just run and chat!**

```bash
python simple_chat.py
```

**Features:**
- ✅ Clean, easy-to-read interface
- ✅ Response time tracking
- ✅ Simple commands (quit, exit)
- ✅ No extra dependencies

**Example session:**
```
🤔 You: What is 25 + 37?
🤖 Agent: I'll help you add those numbers! Using the add_numbers tool...
          The sum of 25 and 37 is 62.
   ⏱️  Response time: 2.3s
```

## 💻 **Option 2: Advanced Terminal Chat**

**Full-featured with history and commands**

```bash
python chat_interface.py
```

**Features:**
- ✅ Chat history (`/history`)
- ✅ Save conversations (`/save`)
- ✅ Clear screen (`/clear`)
- ✅ Help system (`/help`)
- ✅ JSON export of conversations

**Commands:**
- `/help` - Show available commands
- `/history` - Display chat history
- `/save` - Save chat to JSON file
- `/clear` - Clear terminal screen
- `/quit` - Exit chat

## 🌐 **Option 3: Web Interface** (Streamlit)

**Beautiful web-based chat interface**

```bash
# Install Streamlit (if not already installed)
pip install streamlit

# Run the web interface
streamlit run streamlit_chat.py
```

**Features:**
- ✅ Modern web UI
- ✅ Real-time chat
- ✅ Sidebar with configuration
- ✅ Download chat history
- ✅ Copy/paste friendly
- ✅ Mobile responsive

**Access:** Opens automatically in your browser (usually http://localhost:8501)

## 🎯 **What You Can Ask**

Your AI agent has access to mathematical tools via MCP:

### ➕ **Addition Questions**
- "What is 25 + 37?"
- "Add 100 and 200"
- "Sum of 15, 23, and 45"

### 📊 **Comparison Questions**
- "Which is larger: 42 or 17?"
- "Find the maximum of 15, 89, and 33"
- "What's the biggest number: 123, 456, or 789?"

### 🧮 **Complex Math**
- "Calculate 123 + 456 and tell me if it's greater than 500"
- "Add 25 and 37, then compare the result with 60"

## 🔧 **Troubleshooting**

### ❌ "Agent setup failed"
```bash
# Check MCP server
curl http://localhost:8000/health

# Start local server if needed
cd ../sse-mcp-server
python main.py
```

### ❌ "OpenAI API key not set"
```bash
# Set API key (choose one method)
export OPENAI_API_KEY='your-key-here'

# OR create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
```

### ❌ "Import errors"
```bash
# Install dependencies
pip install -r requirements.txt

# For web interface
pip install streamlit
```

### ❌ "Connection refused"
- **Local**: Make sure MCP server is running on port 8000
- **Railway**: Check if your Railway deployment is up and running

## 📝 **Examples**

### Simple Math Conversation
```
🤔 You: What is 25 + 37?
🤖 Agent: I'll add those numbers for you! 25 + 37 = 62

🤔 You: Is 62 greater than 60?
🤖 Agent: Yes! 62 is greater than 60.
```

### Complex Query
```
🤔 You: Add 123 and 456, then tell me if the result is bigger than 500
🤖 Agent: Let me calculate this step by step:
         First, I'll add 123 + 456 = 579
         Then I'll compare 579 with 500.
         Yes, 579 is greater than 500!
```

## 🎉 **Tips for Best Experience**

1. **Start Simple**: Begin with basic math questions
2. **Be Specific**: "Add 25 and 37" works better than "do some math"
3. **Ask Follow-ups**: The agent remembers context within a conversation
4. **Try Different Interfaces**: Each has unique features
5. **Save Important Chats**: Use `/save` command or web download feature

## 🔄 **Switching Between Interfaces**

You can use different interfaces for different needs:
- **Quick questions**: Simple terminal chat
- **Long conversations**: Advanced terminal with history
- **Presentations/demos**: Web interface
- **Development/testing**: Any interface with verbose output

Enjoy chatting with your MCP-powered AI agent! 🚀
