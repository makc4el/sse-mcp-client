# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-slim AS uv

# Set the working directory
WORKDIR /app

# Copy the necessary files
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-editable

# Copy the rest of the application files
COPY . .

# Set environment variable for OPENAI_API_KEY
# This can be overridden at runtime
ENV OPENAI_API_KEY=your_api_key_here

# Default command to run the client
# Note: This requires a server URL to be provided as an argument
CMD ["uv", "run", "client.py", "http://localhost:8080/sse"]