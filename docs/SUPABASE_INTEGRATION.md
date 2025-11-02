# Supabase Integration Guide

## Overview

The Multi-Agent Framework supports Supabase for PostgreSQL database storage. Supabase provides a managed PostgreSQL database with additional features like real-time subscriptions, storage, and authentication.

## Setup

### 1. Get Your Supabase Credentials

1. Go to https://app.supabase.com
2. Create a new project or select an existing one
3. Navigate to **Settings > API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** or **service_role key** → `SUPABASE_KEY`

### 2. Get PostgreSQL Connection String

1. In Supabase dashboard, go to **Settings > Database**
2. Under **Connection string**, select **URI**
3. Copy the connection string
4. Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`
5. Replace `[PASSWORD]` with your database password
6. Update `DATABASE_URL` environment variable

### 3. Configure Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://pwwrzmwtgrsfdqykcomh.supabase.co
SUPABASE_KEY=your_supabase_anon_or_service_role_key

# PostgreSQL Connection (from Supabase dashboard)
DATABASE_URL=postgresql+asyncpg://postgres:your-password@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
```

## Usage

### Direct PostgreSQL Connection (Current Implementation)

The framework uses `asyncpg` to connect directly to Supabase's PostgreSQL database. This is the recommended approach for production:

```python
# In backend/api/main.py
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxx.supabase.co:5432/postgres
```

### Supabase Python Client (Optional)

The framework also includes the Supabase Python client for accessing Supabase-specific features:

```python
from backend.core.supabase import get_supabase_client

# Get Supabase client
supabase = get_supabase_client()

if supabase:
    # Use Supabase REST API
    result = supabase.table('memory_items').select('*').execute()
    
    # Access Storage
    file = supabase.storage.from_('bucket').download('file.txt')
    
    # Use Realtime subscriptions
    # etc.
```

## Connection String Format

### Supabase Connection String Format:
```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### For asyncpg (used in this framework):
```
postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

**Important**: Replace `[PASSWORD]` with your actual database password from Supabase dashboard.

## Security Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Use Service Role Key Carefully**: Service role key bypasses RLS (Row Level Security)
3. **Use Anon Key for Client-Side**: Only use anon key if needed for client-side operations
4. **Use Connection Pooling**: Supabase supports connection pooling - use connection pooler URL if available
5. **Enable SSL**: Supabase requires SSL connections

## Connection Pooling

Supabase provides connection pooling via `pgbouncer`. For better performance, use the pooler connection string:

```
postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:6543/postgres
```

Port `6543` is the pooler port (instead of `5432`).

## Example Configuration

### For Koyeb Deployment:

```bash
# Environment Variables in Koyeb
SUPABASE_URL=https://pwwrzmwtgrsfdqykcomh.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql+asyncpg://postgres:your-password@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
```

### For Local Development:

```bash
# .env file
SUPABASE_URL=https://pwwrzmwtgrsfdqykcomh.supabase.co
SUPABASE_KEY=your-anon-key
DATABASE_URL=postgresql+asyncpg://postgres:your-password@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
```

## Troubleshooting

### Connection Timeout
- Check if your IP is allowed in Supabase dashboard (Settings > Database > Connection Pooling)
- Verify connection string format
- Check SSL requirements

### Authentication Failed
- Verify database password is correct
- Check if using correct user (usually `postgres`)
- Ensure connection string includes password

### SSL Required
Supabase requires SSL connections. The `asyncpg` driver handles this automatically when connecting to Supabase.

## Additional Resources

- [Supabase Python Client Docs](https://github.com/supabase/supabase-py)
- [Supabase PostgreSQL Guide](https://supabase.com/docs/guides/database)
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

