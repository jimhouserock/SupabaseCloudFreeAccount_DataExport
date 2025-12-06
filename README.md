# Supabase Cloud Data Extraction (Free Method)

Extract all your data from Supabase Cloud without paying for the database export feature.

## Method: Supabase Management API

This method uses the **Supabase Management API** to execute SQL queries directly against your database, bypassing the need for direct PostgreSQL connections (which are IPv6-only and often inaccessible).

### Why This Works

1. **Direct database connections fail** because Supabase databases use IPv6-only addresses, which many systems (especially Docker on Windows) cannot reach
2. **Connection pooler fails** with "Tenant or user not found" errors for some projects
3. **Management API works** because it routes through Supabase's infrastructure, handling the IPv6 connectivity internally

### Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- Supabase API Token (from https://supabase.com/dashboard/account/tokens)
- Your Project ID (from project URL: `https://supabase.com/dashboard/project/{PROJECT_ID}`)

### How to Get Your API Token

1. Go to https://supabase.com/dashboard/account/tokens
2. Click "Generate new token"
3. Give it a name and copy the token (starts with `sbp_`)

### Usage

1. Edit `extract_supabase_data.py` and update these values:
   ```python
   PROJECT_ID = "your-project-id"
   API_TOKEN = "sbp_your_api_token_here"
   ```

2. Run the script:
   ```bash
   python extract_supabase_data.py
   ```

3. Find your backups in the `backups/` folder:
   - `supabase_complete_backup_{project_id}_{timestamp}.json` - Complete JSON backup
   - `supabase_schema_dump_{project_id}_{timestamp}.sql` - SQL dump with schema and data

### What Gets Exported

| Data Type | Description |
|-----------|-------------|
| Tables | All tables in `public` schema with full data |
| Schemas | Column definitions, types, defaults, constraints |
| Auth Users | User accounts from `auth.users` (excluding passwords) |
| Storage Buckets | Bucket configurations |
| Storage Objects | File metadata (not actual files) |
| Functions | Custom database functions |
| Triggers | Database triggers |
| RLS Policies | Row Level Security policies |
| Indexes | Table indexes |
| Foreign Keys | Foreign key relationships |

### API Endpoint Used

```
POST https://api.supabase.com/v1/projects/{project_id}/database/query
Authorization: Bearer {api_token}
Content-Type: application/json

{"query": "SELECT * FROM your_table"}
```

**Note:** This endpoint returns HTTP 201 for successful queries (not 200).

### Limitations

- Storage files (actual binary content) are not downloaded - only metadata
- Very large tables may timeout (120 second limit per query)
- Rate limits may apply for very large databases

### Troubleshooting

**"Error executing query: 401"**
- Your API token is invalid or expired. Generate a new one.

**"Error executing query: 404"**
- Project ID is incorrect. Check your project URL.

**Timeout errors**
- For very large tables, modify the script to use pagination with `LIMIT` and `OFFSET`.

## Files

- `extract_supabase_data_template.py` - Main extraction script (use this for public sharing)
- `backups/` - Output directory for backup files

## Author

Jimmy Lin