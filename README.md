# 🔧 Coil.ai - HVAC Business Intelligence Platform

AI-powered business intelligence for HVAC companies, built on LibreChat with a custom MCP server for ServiceTitan data.

## ✨ Features

- **ServiceTitan Integration** - Query your HVAC business data directly
- **AI Chat Interface** - Natural language questions about your data
- **Claude & GPT Support** - Multiple AI model options
- **Message Search** - Find past conversations quickly
- **Multi-User** - Team access with authentication
- **Speech Support** - Text-to-speech and speech-to-text

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Python 3.10+
- Anthropic or OpenAI API key

### 1. Clone & Configure

```powershell
git clone https://github.com/galwinw/CoilChat.git
cd CoilChat
git checkout dev

# Create .env from template
cp env.template .env
notepad .env
```

Edit `.env`:
- Add your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Change all `CHANGE_ME` values to random strings

### 2. Configure MCP Server Database

```powershell
cd mcp-server
cp .env.template .env
notepad .env   # Fill in DB_HOST, DB_USER, DB_PASSWORD
cd ..
```

### 3. Start Everything

```powershell
docker compose up -d
```

This starts all services including the MCP server - no separate terminal needed!

### 4. Access the App

Open **http://localhost:3080** and create an account.

## 📊 Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_estimates_overview` | Sales KPIs with date/business unit filters |
| `get_top_sellers` | Salesperson leaderboard by revenue |
| `get_estimates_trend` | Daily trend analysis |
| `get_pipeline_analysis` | Open estimates pipeline |
| `get_database_schema` | View all tables and columns |
| `get_table_info` | Analyze specific tables |
| `run_query_mcp` | Execute custom SQL queries |
| `test_connection` | Verify database connectivity |

## 🐳 Docker Services

| Service | Purpose | Port |
|---------|---------|------|
| CoilAI | Main application | 3080 |
| coil-mcp-server | HVAC data tools | - |
| coil-mongodb | Conversation storage | - |
| coil-meilisearch | Message search | - |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOU (Browser)                            │
│                      localhost:3080                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                         CoilAI                                    │
│              (Main Application - LibreChat)                       │
│                                                                   │
│   Handles: UI, AI requests, MCP tools, user auth                  │
└───────┬──────────────┬────────────────────────────────────────────┘
        │              │
        ▼              ▼
┌───────────────┐ ┌────────────┐
│ coil-mongodb  │ │ coil-meili │
│               │ │  search    │
│ Stores:       │ │            │
│ • Users       │ │ Indexes:   │
│ • Chats       │ │ • Messages │
│ • Messages    │ │ for search │
│ • Settings    │ └────────────┘
└───────────────┘

┌─────────────────────────────────┐
│     coil-mcp-server             │
│   (Docker Container)            │
│                                 │
│  Your HVAC data tools:          │
│  • get_estimates_overview       │
│  • get_top_sellers              │
│  • get_pipeline_analysis        │
│  • run_query_mcp                │
└────────────────┬────────────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │  PostgreSQL (RDS)   │
      │  ServiceTitan Data  │
      └─────────────────────┘
```

## 🔧 Common Commands

```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs api --tail 50

# Restart after config changes
docker compose restart api

# Check status
docker compose ps
```

## 📁 Project Structure

```
CoilChat/
├── env.template              # Template for .env (copy to .env)
├── .env                      # Your API keys (not in git)
├── librechat.yaml            # Application configuration
├── docker-compose.yml        # Docker services
├── mcp-server/               # Coil MCP Server
│   ├── coil_mcp_server.py       # Remote version (AWS RDS)
│   ├── coil_mcp_server_local.py # Local version
│   ├── .env.template            # DB config template
│   ├── .env                     # Your DB credentials (not in git)
│   └── requirements.txt
├── data-node/                # MongoDB data (not in git)
├── uploads/                  # Uploaded files (not in git)
├── logs/                     # Application logs (not in git)
└── api/, client/, packages/  # Source code (for customization)
```

## 🔐 Security

For production deployment:
1. Change all keys in `.env` to random values
2. Enable HTTPS
3. Restrict network access
4. Set up proper authentication

## 📚 Resources

- [LibreChat Documentation](https://www.librechat.ai/docs)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [ServiceTitan API](https://developer.servicetitan.io/)

---

**Built for HVAC businesses using Coil.ai 🔧**
