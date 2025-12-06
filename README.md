# Supabase Cloud Data Export for Free Accounts (working as December 2025)

A practical solution for exporting data from Supabase free-tier projects when standard export methods are unavailable.

## The Challenge

Supabase free accounts face several data export limitations:

1. **IPv6-only database connections** - Direct PostgreSQL connections fail on many systems (especially Docker on Windows)
2. **No Just-In-Time Recovery** - Database backups require a paid plan
3. **Limited UI export options** - The dashboard provides minimal export functionality
4. **Connection pooler restrictions** - Some projects encounter "Tenant or user not found" errors

These constraints make it difficult to export your own data, even though you own it.

## The Solution

This project uses the **Supabase Management API** to extract data directly through authenticated API calls. This approach:

- Works reliably regardless of IPv6 connectivity issues
- Requires only your API token (no direct database connection needed)
- Extracts complete database structure and data
- Generates both JSON and SQL formats for flexibility

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- Supabase API Token (from https://supabase.com/dashboard/account/tokens)
- Your Project ID (from your project URL: `https://supabase.com/dashboard/project/{PROJECT_ID}`)

## Getting Your API Token

1. Visit https://supabase.com/dashboard/account/tokens
2. Click "Generate new token"
3. Give it a descriptive name
4. Copy the token (starts with `sbp_`)

## Usage

1. Set environment variables:
   ```bash
   export SUPABASE_PROJECT_ID="your-project-id"
   export SUPABASE_API_TOKEN="sbp_your_api_token_here"
   ```

2. Run the script:
   ```bash
   python extract_supabase_data_template.py
   ```

3. Find your exports in the `backups/` folder:
   - `supabase_complete_backup_{project_id}_{timestamp}.json` - Complete JSON backup
   - `supabase_schema_dump_{project_id}_{timestamp}.sql` - SQL dump with schema and data

## What Gets Exported

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

## API Details

The script uses the Supabase Management API endpoint:

```
POST https://api.supabase.com/v1/projects/{project_id}/database/query
Authorization: Bearer {api_token}
Content-Type: application/json

{"query": "SELECT * FROM your_table"}
```

**Note:** This endpoint returns HTTP 201 for successful queries (not 200).

## Limitations

- Storage files (actual binary content) are not downloaded - only metadata
- Very large tables may timeout (120 second limit per query)
- Rate limits may apply for very large databases

## Troubleshooting

**"Error executing query: 401"**
- Your API token is invalid or expired. Generate a new one from the dashboard.

**"Error executing query: 404"**
- Project ID is incorrect. Verify it matches your project URL.

**Timeout errors**
- For very large tables, modify the script to use pagination with `LIMIT` and `OFFSET`.

## Files

- `extract_supabase_data_template.py` - Main extraction script (use this for public sharing)
- `backups/` - Output directory for backup files

## Author

Jimmy Lin
