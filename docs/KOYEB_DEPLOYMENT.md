# Multi-Agent Framework - Koyeb Deployment Guide

## Prerequisites

1. Koyeb account (sign up at https://www.koyeb.com)
2. Docker installed locally (for testing)
3. Environment variables configured

## Deployment Steps

### Option 1: Deploy via Koyeb Dashboard (Recommended)

1. **Push your code to GitHub/GitLab**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create a new app on Koyeb**
   - Go to https://app.koyeb.com/apps
   - Click "Create App"
   - Select your Git repository
   - Koyeb will detect the Dockerfile automatically

3. **Configure Environment Variables**
   In Koyeb dashboard, add these environment variables:
   
   **Required:**
   ```
   OPENAI_API_KEY=sk-your-key-here
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
   NEO4J_URI=bolt://your-neo4j-host:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   ```
   
   **Optional:**
   ```
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   PORT=8000
   BUDGET_DAILY_LIMIT=100.00
   BUDGET_TASK_LIMIT=10.00
   ```

4. **Deploy**
   - Click "Deploy"
   - Koyeb will build and deploy your application
   - Your app will be available at `https://your-app-name.koyeb.app`

### Option 2: Deploy via Koyeb CLI

1. **Install Koyeb CLI**
   ```bash
   curl -fsSL https://cli.koyeb.com/install.sh | sh
   ```

2. **Login**
   ```bash
   koyeb login
   ```

3. **Create App**
   ```bash
   koyeb app create multi-agent-framework
   ```

4. **Set Environment Variables**
   ```bash
   koyeb secret create openai-api-key --value "sk-your-key"
   koyeb secret create database-url --value "postgresql+asyncpg://..."
   koyeb secret create neo4j-uri --value "bolt://..."
   koyeb secret create neo4j-user --value "neo4j"
   koyeb secret create neo4j-password --value "your-password"
   ```

5. **Deploy**
   ```bash
   koyeb service create \
     --app multi-agent-framework \
     --name backend \
     --dockerfile Dockerfile \
     --env OPENAI_API_KEY=$(koyeb secret get openai-api-key) \
     --env DATABASE_URL=$(koyeb secret get database-url) \
     --env NEO4J_URI=$(koyeb secret get neo4j-uri) \
     --env NEO4J_USER=$(koyeb secret get neo4j-user) \
     --env NEO4J_PASSWORD=$(koyeb secret get neo4j-password)
   ```

## Testing Locally

Before deploying, test the Dockerfile locally:

```bash
# Build the image
docker build -t multi-agent-framework .

# Run with environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e NEO4J_URI=bolt://... \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your-password \
  multi-agent-framework

# Test health endpoint
curl http://localhost:8000/health
```

## Database Setup

### Option 1: Use Koyeb Managed Databases

Koyeb offers managed PostgreSQL and can connect to external Neo4j:

1. Create PostgreSQL database in Koyeb
2. Get connection string
3. Set `DATABASE_URL` environment variable
4. Use external Neo4j instance (AuraDB, Neo4j Cloud, etc.)

### Option 2: Use External Databases

1. **Supabase (PostgreSQL)**
   - Create project at https://supabase.com
   - Get connection string from Settings > Database
   - Set `DATABASE_URL` environment variable

2. **Neo4j Aura (Neo4j)**
   - Create instance at https://neo4j.com/cloud/aura/
   - Get connection URI and credentials
   - Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

## Environment Variables Reference

See `env.template` and `docs/ENVIRONMENT_VARIABLES.md` for complete list.

### Minimum Required for Koyeb:
- `OPENAI_API_KEY`
- `DATABASE_URL`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

## Post-Deployment

1. **Update Frontend Environment Variables**
   After deployment, update these in your frontend build (or rebuild):
   ```
   VITE_API_URL=https://your-app-name.koyeb.app
   VITE_WS_URL=wss://your-app-name.koyeb.app
   ```

2. **Test the Application**
   - Visit `https://your-app-name.koyeb.app`
   - Check `/health` endpoint
   - Test API endpoints at `/api/tasks`

3. **Monitor Logs**
   ```bash
   koyeb logs tail --app multi-agent-framework
   ```

## Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Ensure all files are in correct locations
- Verify Node.js and Python versions

### Runtime Errors
- Check environment variables are set correctly
- Verify database connections
- Check logs: `koyeb logs tail`

### Frontend Not Loading
- Verify static files are copied to `/app/static`
- Check FastAPI static file mounting
- Ensure Vite build output is correct

## Dockerfile Structure

The Dockerfile uses multi-stage build:
1. **Stage 1**: Build React frontend (Node.js)
2. **Stage 2**: Build Python backend and copy static files

This results in a single, optimized production image.

