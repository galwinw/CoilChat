# 🔧 Coil.ai - HVAC Business Intelligence Platform

AI-powered business intelligence for HVAC companies, built on LibreChat with a custom MCP server for ServiceTitan data.

## ✨ Features

- **ServiceTitan Integration** - Query your HVAC business data directly
- **AI Chat Interface** - Natural language questions about your data
- **Claude & GPT Support** - Multiple AI model options
- **Document Chat** - Upload and analyze documents
- **Message Search** - Find past conversations quickly
- **Multi-User** - Team access with authentication
- **Speech Support** - Text-to-speech and speech-to-text

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Python 3.10+
- Anthropic or OpenAI API key

### 1. Start the MCP Server

```powershell
cd C:\Users\galwi\Coil\coil.ai
python coil_mcp_server_local.py --sse
```

### 2. Configure Environment

Copy the template and add your API keys:

```powershell
cp env.template .env
notepad .env
```

Fill in at least one API key (Anthropic or OpenAI) and change the security keys.

### 3. Start Coil.ai

```powershell
docker compose up -d
```

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
| coil-mongodb | Conversation storage | - |
| coil-meilisearch | Message search | - |
| coil-vectordb | Document embeddings | - |
| coil-rag-api | Document chat API | - |

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
└───────┬──────────────┬─────────────────┬─────────────────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌───────────────┐ ┌────────────┐ ┌─────────────────┐
│ coil-mongodb  │ │ coil-meili │ │   coil-rag-api  │
│               │ │  search    │ │                 │
│ Stores:       │ │            │ │ Processes:      │
│ • Users       │ │ Indexes:   │ │ • PDF uploads   │
│ • Chats       │ │ • Messages │ │ • Document Q&A  │
│ • Messages    │ │ for search │ │                 │
│ • Settings    │ └────────────┘ └────────┬────────┘
└───────────────┘                         │
                                          ▼
                                  ┌───────────────┐
                                  │ coil-vectordb │
                                  │               │
                                  │ Stores:       │
                                  │ • Embeddings  │
                                  │ • Vector data │
                                  └───────────────┘

                    ┌─────────────────────────────────┐
                    │       Coil MCP Server           │
                    │      (localhost:8123)           │
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
Coil/Librechat/
├── env.template            # Template for .env (copy to .env)
├── .env                    # Your API keys (not in git)
├── librechat.yaml          # Application configuration
├── docker-compose.yml      # Docker services
├── data-node/              # MongoDB data (not in git)
├── uploads/                # Uploaded files (not in git)
├── logs/                   # Application logs (not in git)
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
