# Multi-Agent Framework

A scalable multi-agent framework for building and orchestrating AI agents with Planner, Builder/Executor, and Critic agents.

## Architecture

- **Backend**: Python with FastAPI for REST API and WebSocket support
- **Frontend**: React with TypeScript
- **Memory**: PostgreSQL (Supabase) + Graph Store (Neo4j)
- **LLM**: OpenAI API
- **Deployment**: Koyeb

## Features

- 🧠 **Multi-Agent System**: Planner, Builder/Executor, and Critic agents
- 💾 **Memory Architecture**: Graph store + PostgreSQL for scalable memory management
- 🔧 **MCP Server**: Integrated Model Context Protocol server with tools
- 📊 **Observability**: Real-time execution flow visualization and logging
- 💰 **Budget Guardrails**: Token usage tracking and budget enforcement
- 🧪 **Testing Tools**: Code writing, unit test generation, and script execution

## Project Structure

```
multi-agent-framework/
├── backend/           # Python backend (FastAPI)
│   ├── agents/       # Agent implementations
│   ├── api/          # API endpoints
│   ├── config/       # Configuration management
│   ├── core/         # Core utilities (logging, budget, exceptions)
│   ├── memory/       # Memory management (graph store + PostgreSQL)
│   └── mcp/          # MCP server and tools
├── frontend/         # React frontend
│   └── src/          # React source code
└── docs/             # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL (via Docker or Supabase)
- Neo4j (via Docker or cloud)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-agent-framework
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

5. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

6. **Run the backend**
   ```bash
   cd backend
   uvicorn api.main:app --reload
   ```

7. **Run the frontend**
   ```bash
   cd frontend
   npm run dev
   ```

## Development

The framework is organized into phases:

1. **Foundation & Infrastructure**: Core utilities, configuration, logging
2. **Memory Architecture**: PostgreSQL + Neo4j memory system
3. **Agent Framework**: Base agents, registry, executor
4. **MCP Server**: Tools for code writing, testing, execution
5. **Backend API**: REST API and WebSocket endpoints
6. **Frontend**: React UI with task management, observability, logs

## Testing

See `backend/tests/README.md` for testing instructions.

## Deployment

See `koyeb.toml` for Koyeb deployment configuration.

## License

See LICENSE file for details.
