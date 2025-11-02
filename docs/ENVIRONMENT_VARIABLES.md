# Environment Variables Documentation

## Required Environment Variables

### 1. OpenAI API Key (REQUIRED)
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```
**Required**: Yes  
**Description**: Your OpenAI API key for LLM access. Get it from https://platform.openai.com/api-keys  
**No default**: This must be set or the application will fail to start

### 2. Database Configuration

#### PostgreSQL (Required)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/multi_agent_db
```
**Required**: Yes (if not using Docker Compose)  
**Description**: PostgreSQL connection string  
**Default**: `postgresql+asyncpg://postgres:postgres@localhost:5432/multi_agent_db`

#### Neo4j (Required)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
```
**Required**: Yes (if not using Docker Compose)  
**Description**: Neo4j graph database connection  
**Defaults**: 
- `NEO4J_URI=bolt://localhost:7687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=neo4j`

## Optional Environment Variables

### Application Settings
```bash
ENVIRONMENT=development          # development, staging, production
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

### Budget Settings
```bash
BUDGET_DAILY_LIMIT=100.00       # Daily budget limit in USD
BUDGET_TASK_LIMIT=10.00         # Per-task budget limit in USD
BUDGET_ENABLE_TRACKING=true     # Enable/disable budget tracking
BUDGET_WARNING_THRESHOLD=0.8    # Warning at 80% of limit
```

### OpenAI Model Settings
```bash
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=60
```

### MCP Server Settings
```bash
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8001
MCP_ENABLE_SANDBOX=true
```

### Frontend Settings
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Supabase (Optional)
```bash
SUPABASE_URL=https://pwwrzmwtgrsfdqykcomh.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

## Setup Scenarios

### Scenario 1: Local Development with Docker Compose
**Minimum required**: Only `OPENAI_API_KEY`
```bash
OPENAI_API_KEY=sk-your-key-here
```
Docker Compose handles database setup automatically.

### Scenario 2: Local Development without Docker
**Required**:
```bash
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

### Scenario 3: Production with Supabase
**Required**:
```bash
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=postgresql+asyncpg://postgres:password@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
NEO4J_URI=bolt://your-neo4j-instance.com:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
ENVIRONMENT=production
VITE_API_URL=https://your-backend.koyeb.app
VITE_WS_URL=wss://your-backend.koyeb.app
```

## Getting Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and add it to your `.env` file

## Getting Supabase Connection String

1. Go to https://supabase.com
2. Create a project or select existing
3. Go to Settings > Database
4. Copy the connection string (URI format)
5. Update `DATABASE_URL` in your `.env` file

## Security Notes

- **Never commit `.env` file to version control**
- Keep your API keys secure
- Use different keys for development and production
- Rotate keys regularly
- Use environment-specific budgets

