#!/usr/bin/env python3
"""
Run database migration for audio artifacts.
"""

import asyncio
import asyncpg
import os


async def run_migration():
    """Run the audio artifacts migration."""
    
    # Read migration file
    migration_path = "db/migrations/003_add_audio_artifacts.sql"
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    print(f"📄 Reading migration: {migration_path}")
    print(f"📊 SQL length: {len(migration_sql)} chars\n")
    
    # Connect to database
    dsn = os.getenv("SUPABASE_URL", "")
    if not dsn:
        print("❌ SUPABASE_URL environment variable not set")
        return False
    
    print(f"🔌 Connecting to database...")
    
    try:
        conn = await asyncpg.connect(dsn)
        print("✅ Connected to database\n")
        
        # Run migration
        print("🚀 Running migration...")
        await conn.execute(migration_sql)
        print("✅ Migration executed successfully\n")
        
        # Verify tables were created
        print("🔍 Verifying tables...")
        
        # Check audio_artifacts table
        result = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'audio_artifacts'
            )
            """
        )
        
        if result:
            print("  ✅ audio_artifacts table created")
            
            # Check columns
            columns = await conn.fetch(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'audio_artifacts'
                ORDER BY ordinal_position
                """
            )
            
            print("  Columns:")
            for col in columns:
                print(f"    - {col['column_name']}: {col['data_type']}")
        else:
            print("  ❌ audio_artifacts table not found")
        
        # Check if audio_url column was added to artifacts
        audio_url_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'artifacts' 
                AND column_name = 'audio_url'
            )
            """
        )
        
        if audio_url_exists:
            print("  ✅ audio_url column added to artifacts table")
        else:
            print("  ❌ audio_url column not found in artifacts table")
        
        await conn.close()
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)
