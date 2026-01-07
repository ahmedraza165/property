"""
Database migration: Add original_data column to properties table
This preserves all original CSV data to prevent data loss on export
"""

from database import engine
from sqlalchemy import text

def migrate():
    """Add original_data JSONB column to properties table"""

    with engine.connect() as conn:
        try:
            # Add original_data column
            conn.execute(text("""
                ALTER TABLE properties
                ADD COLUMN IF NOT EXISTS original_data JSONB;
            """))

            # Create index for faster queries (optional but recommended)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_properties_original_data
                ON properties USING GIN (original_data);
            """))

            conn.commit()
            print("✓ Migration completed successfully!")
            print("✓ Added original_data JSONB column to properties table")
            print("✓ Created GIN index on original_data column")

        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration...")
    migrate()
    print("Done!")
