# Coil MCP Server - Docker Image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code (local version)
COPY coil_mcp_server_local.py .

# Expose SSE port
EXPOSE 8123

# Run in SSE mode
CMD ["python", "coil_mcp_server_local.py", "--sse"]

