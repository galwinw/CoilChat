# Coil.ai + LibreChat Setup Guide

## 🎯 Overview

This guide helps you run LibreChat with your Coil MCP server for HVAC business intelligence.

## 📁 Files Created

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API keys, secrets) |
| `librechat.yaml` | LibreChat config with MCP server connection |
| `docker-compose.override.yml` | Docker customizations |

---

## 🚀 Quick Start

### Step 1: Start Your MCP Server

First, start your Coil MCP server (runs on port 8123):

```powershell
# In a new terminal, navigate to your MCP server
cd C:\Users\galwi\Coil\coil.ai

# Start the SSE server
python coil_mcp_server.py
```

You should see:
```
[OK] Connection pool initialized (min=2, max=10)
[INFO] Starting MCP server in REMOTE mode on 0.0.0.0:8123
[INFO] Connect from Claude Desktop using: http://YOUR_EC2_IP:8123/sse
```

### Step 2: Configure Your .env File

Edit the `.env` file and add your API keys:

```powershell
# Open in notepad or your preferred editor
notepad .env
```

**Required changes:**
1. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (at least one)
2. Change `CREDS_KEY`, `CREDS_IV`, `JWT_SECRET` to random strings
3. Change `MEILI_MASTER_KEY` to a random string

**Tip:** Generate random strings at https://generate-secret.vercel.app/32

### Step 3: Start LibreChat

```powershell
# Navigate to LibreChat directory
cd C:\Users\galwi\Coil\Librechat

# Start all containers
docker compose up -d
```

### Step 4: Access LibreChat

Open your browser and go to:
```
http://localhost:3080
```

1. **Create an account** (first user becomes admin)
2. **Select an AI model** (OpenAI, Claude, etc.)
3. **Enable MCP tools** - Click the MCP dropdown below the chat input
4. **Select "coil"** - Your HVAC data tools are now available!

---

## 🛠️ Available MCP Tools

Once connected, the AI can use these tools:

| Tool | Description |
|------|-------------|
| `test_connection` | Verify database connectivity |
| `get_database_schema` | View all tables and columns |
| `get_table_info` | Analyze a specific table |
| `run_query_mcp` | Execute custom SQL |
| `get_estimates_overview` | Sales KPIs with filters |
| `get_top_sellers` | Salesperson leaderboard |
| `get_estimates_trend` | Daily trend analysis |
| `get_pipeline_analysis` | Open estimates pipeline |

### Example Prompts

Try asking:
- "Show me this month's estimates overview"
- "Who are the top 5 salespeople by revenue?"
- "What's the pipeline value for open estimates over 90 days old?"
- "Show me the daily trend for HVAC INSTALL estimates"

---

## 🔧 Troubleshooting

### MCP Server Not Connecting

1. **Check if MCP server is running:**
   ```powershell
   # In the coil.ai directory
   python coil_mcp_server.py
   ```

2. **Test the SSE endpoint:**
   ```powershell
   curl http://localhost:8123/sse
   ```

3. **Check Docker can reach host:**
   The `docker-compose.override.yml` includes `host.docker.internal` mapping.

### Database Connection Issues

1. **Verify PostgreSQL is running:**
   ```powershell
   # Check if Docker container is running
   docker ps | findstr postgres
   ```

2. **Check connection settings in coil_mcp_server.py:**
   - For local: `host: localhost`
   - For AWS RDS: `host: mcp-db.xxx.us-east-1.rds.amazonaws.com`

### LibreChat Not Starting

1. **Check container logs:**
   ```powershell
   docker compose logs api
   ```

2. **Rebuild containers:**
   ```powershell
   docker compose down
   docker compose up -d --build
   ```

---

## 🔐 Security Notes

### For Development
- MCP server runs on `localhost:8123`
- Docker accesses via `host.docker.internal`
- No authentication required

### For Production
Consider:
1. Running MCP server behind nginx with SSL
2. Adding API key authentication to MCP server
3. Restricting `allowedDomains` in `librechat.yaml`
4. Using proper secrets management

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Computer                            │
│                                                             │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │   Docker Desktop     │    │   Coil MCP Server        │  │
│  │                      │    │   (Python/FastMCP)       │  │
│  │  ┌────────────────┐  │    │                          │  │
│  │  │   LibreChat    │  │    │   Port: 8123             │  │
│  │  │   Port: 3080   │──┼────┼─► SSE Transport          │  │
│  │  └────────────────┘  │    │                          │  │
│  │                      │    └───────────┬──────────────┘  │
│  │  ┌────────────────┐  │                │                 │
│  │  │   MongoDB      │  │                │                 │
│  │  └────────────────┘  │                │                 │
│  │                      │                ▼                 │
│  │  ┌────────────────┐  │    ┌──────────────────────────┐  │
│  │  │   Meilisearch  │  │    │   PostgreSQL             │  │
│  │  └────────────────┘  │    │   (Local or AWS RDS)     │  │
│  └──────────────────────┘    │   - norm schema          │  │
│                              │   - ServiceTitan data    │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Stopping Services

```powershell
# Stop LibreChat
docker compose down

# Stop MCP server
# Press Ctrl+C in the terminal running coil_mcp_server.py
```

---

## 📚 Resources

- [LibreChat Documentation](https://www.librechat.ai/docs)
- [LibreChat MCP Guide](https://www.librechat.ai/docs/features/mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Built for HVAC businesses using Coil.ai 🔧**

