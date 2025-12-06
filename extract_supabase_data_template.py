#!/usr/bin/env python3
"""
Supabase Complete Data Extraction Script
Extracts all data from Supabase cloud using the Management API

Configuration: Set environment variables before running:
  - SUPABASE_PROJECT_ID: Your Supabase project ID
  - SUPABASE_API_TOKEN: Your Supabase Management API token (from https://supabase.com/dashboard/account/tokens)
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration from environment variables
PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID")
API_TOKEN = os.getenv("SUPABASE_API_TOKEN")

# Validate configuration
if not PROJECT_ID or not API_TOKEN:
    print("Error: Missing required environment variables")
    print("Please set:")
    print("  - SUPABASE_PROJECT_ID")
    print("  - SUPABASE_API_TOKEN")
    print("\nGet your API token from: https://supabase.com/dashboard/account/tokens")
    sys.exit(1)

MANAGEMENT_API_URL = "https://api.supabase.com/v1"
PROJECT_URL = f"https://{PROJECT_ID}.supabase.co"

def run_sql_query(query):
    """Execute SQL query via Management API"""
    url = f"{MANAGEMENT_API_URL}/projects/{PROJECT_ID}/database/query"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json={"query": query}, timeout=120)
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error executing query: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_all_tables():
    """Get list of all tables in public schema"""
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
    """
    result = run_sql_query(query)
    if result:
        return [row['table_name'] for row in result]
    return []

def get_table_schema(table_name):
    """Get column information for a table"""
    query = f"""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    return run_sql_query(query)

def get_table_data(table_name):
    """Get all data from a table"""
    query = f"SELECT * FROM public.{table_name}"
    return run_sql_query(query)

def get_auth_users():
    """Get auth.users data"""
    query = """
    SELECT id, email, phone, created_at, updated_at, last_sign_in_at,
           raw_user_meta_data, raw_app_meta_data, role,
           email_confirmed_at, phone_confirmed_at, confirmation_sent_at,
           confirmed_at, recovery_sent_at, invited_at, is_sso_user, deleted_at
    FROM auth.users
    """
    return run_sql_query(query)

def get_storage_buckets():
    """Get storage buckets"""
    query = "SELECT * FROM storage.buckets"
    return run_sql_query(query)

def get_storage_objects():
    """Get storage objects metadata"""
    query = "SELECT * FROM storage.objects"
    return run_sql_query(query)

def get_database_functions():
    """Get all custom functions"""
    query = """
    SELECT routine_name, routine_type, routine_definition, data_type
    FROM information_schema.routines 
    WHERE routine_schema = 'public'
    """
    return run_sql_query(query)

def get_database_triggers():
    """Get all triggers"""
    query = """
    SELECT trigger_name, event_manipulation, event_object_table, action_statement
    FROM information_schema.triggers 
    WHERE trigger_schema = 'public'
    """
    return run_sql_query(query)

def get_rls_policies():
    """Get Row Level Security policies"""
    query = """
    SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
    FROM pg_policies 
    WHERE schemaname = 'public'
    """
    return run_sql_query(query)

def get_indexes():
    """Get all indexes"""
    query = """
    SELECT indexname, tablename, indexdef
    FROM pg_indexes 
    WHERE schemaname = 'public'
    """
    return run_sql_query(query)

def get_foreign_keys():
    """Get foreign key constraints"""
    query = """
    SELECT
        tc.table_name, 
        kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema = 'public'
    """
    return run_sql_query(query)

def get_full_schema_dump():
    """Get complete schema as SQL"""
    # Get CREATE TABLE statements
    query = """
    SELECT 
        'CREATE TABLE IF NOT EXISTS public.' || table_name || ' (' ||
        string_agg(
            column_name || ' ' || 
            data_type || 
            CASE WHEN character_maximum_length IS NOT NULL 
                THEN '(' || character_maximum_length || ')' 
                ELSE '' 
            END ||
            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
            CASE WHEN column_default IS NOT NULL 
                THEN ' DEFAULT ' || column_default 
                ELSE '' 
            END,
            ', '
            ORDER BY ordinal_position
        ) || ');' as create_statement
    FROM information_schema.columns
    WHERE table_schema = 'public'
    GROUP BY table_name
    ORDER BY table_name
    """
    return run_sql_query(query)

def main():
    """Main extraction workflow"""
    print("=" * 70)
    print("Supabase Complete Data Extraction")
    print("=" * 70)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Create backup directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize backup data structure
    backup_data = {
        "project_id": PROJECT_ID,
        "exported_at": datetime.now().isoformat(),
        "tables": {},
        "schemas": {},
        "auth": {},
        "storage": {},
        "functions": [],
        "triggers": [],
        "policies": [],
        "indexes": [],
        "foreign_keys": []
    }
    
    # Step 1: Get all tables
    print("\n[1/10] Fetching table list...")
    tables = get_all_tables()
    print(f"       Found {len(tables)} tables: {', '.join(tables)}")
    
    # Step 2: Export each table's schema and data
    print("\n[2/10] Exporting table schemas and data...")
    for table in tables:
        print(f"       Exporting {table}...", end=" ")
        
        # Get schema
        schema = get_table_schema(table)
        if schema:
            backup_data["schemas"][table] = schema
        
        # Get data
        data = get_table_data(table)
        if data is not None:
            backup_data["tables"][table] = data
            print(f"({len(data)} rows)")
        else:
            backup_data["tables"][table] = []
            print("(0 rows or error)")
    
    # Step 3: Export auth users
    print("\n[3/10] Exporting auth.users...")
    auth_users = get_auth_users()
    if auth_users:
        backup_data["auth"]["users"] = auth_users
        print(f"       Found {len(auth_users)} users")
    else:
        backup_data["auth"]["users"] = []
        print("       No users found or access denied")
    
    # Step 4: Export storage buckets
    print("\n[4/10] Exporting storage buckets...")
    buckets = get_storage_buckets()
    if buckets:
        backup_data["storage"]["buckets"] = buckets
        print(f"       Found {len(buckets)} buckets")
    else:
        backup_data["storage"]["buckets"] = []
        print("       No buckets found")
    
    # Step 5: Export storage objects metadata
    print("\n[5/10] Exporting storage objects metadata...")
    objects = get_storage_objects()
    if objects:
        backup_data["storage"]["objects"] = objects
        print(f"       Found {len(objects)} objects")
    else:
        backup_data["storage"]["objects"] = []
        print("       No objects found")
    
    # Step 6: Export functions
    print("\n[6/10] Exporting database functions...")
    functions = get_database_functions()
    if functions:
        backup_data["functions"] = functions
        print(f"       Found {len(functions)} functions")
    else:
        print("       No custom functions found")
    
    # Step 7: Export triggers
    print("\n[7/10] Exporting triggers...")
    triggers = get_database_triggers()
    if triggers:
        backup_data["triggers"] = triggers
        print(f"       Found {len(triggers)} triggers")
    else:
        print("       No triggers found")
    
    # Step 8: Export RLS policies
    print("\n[8/10] Exporting RLS policies...")
    policies = get_rls_policies()
    if policies:
        backup_data["policies"] = policies
        print(f"       Found {len(policies)} policies")
    else:
        print("       No RLS policies found")
    
    # Step 9: Export indexes
    print("\n[9/10] Exporting indexes...")
    indexes = get_indexes()
    if indexes:
        backup_data["indexes"] = indexes
        print(f"       Found {len(indexes)} indexes")
    else:
        print("       No indexes found")
    
    # Step 10: Export foreign keys
    print("\n[10/10] Exporting foreign keys...")
    fks = get_foreign_keys()
    if fks:
        backup_data["foreign_keys"] = fks
        print(f"       Found {len(fks)} foreign keys")
    else:
        print("       No foreign keys found")
    
    # Save backup to JSON file
    json_file = backup_dir / f"supabase_complete_backup_{PROJECT_ID}_{timestamp}.json"
    print(f"\nSaving backup to {json_file}...")
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, default=str, ensure_ascii=False)
    
    file_size = os.path.getsize(json_file) / (1024 * 1024)
    
    # Generate SQL dump file
    sql_file = backup_dir / f"supabase_schema_dump_{PROJECT_ID}_{timestamp}.sql"
    print(f"Generating SQL schema dump to {sql_file}...")
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(f"-- Supabase Schema Dump\n")
        f.write(f"-- Project: {PROJECT_ID}\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
        
        # Write CREATE TABLE statements
        for table, schema in backup_data["schemas"].items():
            f.write(f"\n-- Table: {table}\n")
            f.write(f"CREATE TABLE IF NOT EXISTS public.{table} (\n")
            columns = []
            for col in schema:
                col_def = f"    {col['column_name']} {col['data_type']}"
                if col['is_nullable'] == 'NO':
                    col_def += " NOT NULL"
                if col['column_default']:
                    col_def += f" DEFAULT {col['column_default']}"
                columns.append(col_def)
            f.write(",\n".join(columns))
            f.write("\n);\n")
        
        # Write INSERT statements for data
        f.write("\n\n-- Data\n")
        for table, rows in backup_data["tables"].items():
            if rows:
                f.write(f"\n-- Data for table: {table}\n")
                for row in rows:
                    columns = ", ".join(row.keys())
                    values = []
                    for v in row.values():
                        if v is None:
                            values.append("NULL")
                        elif isinstance(v, (int, float)):
                            values.append(str(v))
                        elif isinstance(v, bool):
                            values.append("TRUE" if v else "FALSE")
                        else:
                            escaped = str(v).replace("'", "''")
                            values.append(f"'{escaped}'")
                    values_str = ", ".join(values)
                    f.write(f"INSERT INTO public.{table} ({columns}) VALUES ({values_str});\n")
        
        # Write RLS policies
        if backup_data["policies"]:
            f.write("\n\n-- RLS Policies\n")
            for policy in backup_data["policies"]:
                f.write(f"-- Policy: {policy.get('policyname')} on {policy.get('tablename')}\n")
    
    sql_size = os.path.getsize(sql_file) / (1024 * 1024)
    
    # Summary
    print("\n" + "=" * 70)
    print("BACKUP COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  1. JSON backup: {json_file}")
    print(f"     Size: {file_size:.2f} MB")
    print(f"  2. SQL dump: {sql_file}")
    print(f"     Size: {sql_size:.2f} MB")
    
    print(f"\nData summary:")
    print(f"  Tables: {len(backup_data['tables'])}")
    total_rows = sum(len(rows) for rows in backup_data['tables'].values())
    print(f"  Total rows: {total_rows}")
    print(f"  Auth users: {len(backup_data['auth'].get('users', []))}")
    print(f"  Storage buckets: {len(backup_data['storage'].get('buckets', []))}")
    print(f"  Storage objects: {len(backup_data['storage'].get('objects', []))}")
    print(f"  Functions: {len(backup_data['functions'])}")
    print(f"  Triggers: {len(backup_data['triggers'])}")
    print(f"  RLS Policies: {len(backup_data['policies'])}")
    print(f"  Indexes: {len(backup_data['indexes'])}")
    print(f"  Foreign Keys: {len(backup_data['foreign_keys'])}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
