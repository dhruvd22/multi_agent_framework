# Quick Supabase Setup Guide

## For Your Project

Based on your Supabase URL (`https://pwwrzmwtgrsfdqykcomh.supabase.co`), here's how to configure:

### 1. Environment Variables

Add to your `.env` file or Koyeb environment variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://pwwrzmwtgrsfdqykcomh.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# PostgreSQL Connection String
# Get this from: Supabase Dashboard > Settings > Database > Connection string > URI
# Replace [PASSWORD] with your actual database password
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
```

### 2. Getting Your Credentials

1. **Project URL**: Already have it - `https://pwwrzmwtgrsfdqykcomh.supabase.co`
2. **API Key**: 
   - Go to https://app.supabase.com/project/[your-project]/settings/api
   - Copy the `anon` `public` key (for client-side) or `service_role` key (for server-side)
3. **Database Password**:
   - Go to Settings > Database
   - If you don't know it, you can reset it
   - Use this password in the connection string

### 3. Connection String Format

Your Supabase PostgreSQL connection string should be:
```
postgresql+asyncpg://postgres:YOUR_PASSWORD@db.pwwrzmwtgrsfdqykcomh.supabase.co:5432/postgres
```

For connection pooling (recommended for production):
```
postgresql+asyncpg://postgres:YOUR_PASSWORD@db.pwwrzmwtgrsfdqykcomh.supabase.co:6543/postgres
```
(Note: Port 6543 is the pooler port)

### 4. Test Connection

After setting environment variables, the framework will:
- Connect to Supabase PostgreSQL automatically
- Initialize the Supabase Python client (if URL and key are provided)
- Create necessary database tables

### 5. Using Supabase Client

If you need to use Supabase-specific features (Storage, Auth, Realtime), you can access the client:

```python
from backend.core.supabase import get_supabase_client

supabase = get_supabase_client()
if supabase:
    # Use Supabase REST API
    result = supabase.table('memory_items').select('*').execute()
```

## Important Notes

- **Password**: The password in the connection string is your database password, NOT your Supabase account password
- **SSL**: Supabase requires SSL - `asyncpg` handles this automatically
- **Connection Pooling**: Use port 6543 for connection pooling (better for production)
- **Security**: Use environment variables, never commit credentials to git

