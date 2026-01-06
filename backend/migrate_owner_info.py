"""
Database migration script to add new skip tracing owner information fields
Run this script to update the property_owner_info table schema
"""

from sqlalchemy import text
from database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add new columns to property_owner_info table for comprehensive owner data"""

    migrations = [
        # Owner Name Fields
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS owner_first_name VARCHAR(255);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS owner_last_name VARCHAR(255);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS owner_full_name VARCHAR(500);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS owner_middle_name VARCHAR(255);
        """,

        # Contact Information - Phone
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS phone_primary VARCHAR(50);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS phone_secondary VARCHAR(50);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS phone_mobile VARCHAR(50);
        """,

        # Contact Information - Email
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS email_primary VARCHAR(255);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS email_secondary VARCHAR(255);
        """,

        # Mailing Address Fields
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS mailing_street TEXT;
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS mailing_city VARCHAR(255);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS mailing_state VARCHAR(2);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS mailing_zip VARCHAR(20);
        """,
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS mailing_full_address TEXT;
        """,

        # Owner Details
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS owner_occupied BOOLEAN;
        """,

        # Processing Metadata
        """
        ALTER TABLE property_owner_info
        ADD COLUMN IF NOT EXISTS processing_time_seconds FLOAT;
        """,

        # Update default status
        """
        ALTER TABLE property_owner_info
        ALTER COLUMN owner_info_status SET DEFAULT 'pending';
        """,
    ]

    db = SessionLocal()

    try:
        logger.info("Starting owner info migration...")

        for i, migration in enumerate(migrations, 1):
            try:
                logger.info(f"Running migration {i}/{len(migrations)}...")
                db.execute(text(migration))
                db.commit()
                logger.info(f"Migration {i} completed successfully")
            except Exception as e:
                logger.warning(f"Migration {i} skipped (may already exist): {str(e)}")
                db.rollback()

        logger.info("All migrations completed!")

        # Verify the columns exist
        result = db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'property_owner_info'
            ORDER BY column_name;
        """))

        columns = {row[0]: row[1] for row in result}
        logger.info(f"Current property_owner_info columns: {len(columns)} total")

        # Check for required new columns
        required_columns = [
            'owner_first_name', 'owner_last_name', 'owner_full_name',
            'phone_primary', 'phone_mobile', 'email_primary',
            'mailing_street', 'mailing_city', 'mailing_state', 'mailing_zip',
            'owner_occupied', 'processing_time_seconds'
        ]

        missing = [col for col in required_columns if col not in columns]
        if missing:
            logger.error(f"Missing columns: {', '.join(missing)}")
            return False

        logger.info("✅ All required columns are present!")
        logger.info("\nKey owner info fields:")
        for col in required_columns:
            logger.info(f"  - {col}: {columns[col]}")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✅ Migration completed successfully!")
        print("The property_owner_info table now has all skip tracing fields")
        print("\nYou can now run skip tracing on properties!")
    else:
        print("\n❌ Migration failed. Please check the logs above.")
        exit(1)
