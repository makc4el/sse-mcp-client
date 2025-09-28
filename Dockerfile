# LangChain Platform Dockerfile for MCP SSE Client
FROM ghcr.io/astral-sh/uv:python3.11-slim

WORKDIR /app

# Copy dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

# Copy application
COPY . .

# Set environment variables
ENV OPENAI_API_KEY=your_openai_api_key_here
ENV LANGCHAIN_TRACING_V2=true
ENV LANGCHAIN_PROJECT=mcp-sse-client
ENV MCP_SERVER_URL=https://web-production-b40eb.up.railway.app/sse

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Run the client
CMD ["uv", "run", "langchain_client.py"]