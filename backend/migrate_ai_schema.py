"""
Database migration script to add new AI analysis columns
Run this script to update the database schema for AI imagery analysis
"""

from sqlalchemy import text
from database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add new columns to ai_analysis_results table"""

    migrations = [
        # Add imagery source columns
        """
        ALTER TABLE ai_analysis_results
        ADD COLUMN IF NOT EXISTS satellite_image_source VARCHAR(100);
        """,
        """
        ALTER TABLE ai_analysis_results
        ADD COLUMN IF NOT EXISTS street_image_source VARCHAR(100);
        """,
        # Add power line geometry column
        """
        ALTER TABLE ai_analysis_results
        ADD COLUMN IF NOT EXISTS power_line_geometry TEXT;
        """,
    ]

    db = SessionLocal()

    try:
        logger.info("Starting database migration...")

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
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'ai_analysis_results'
            ORDER BY column_name;
        """))

        columns = [row[0] for row in result]
        logger.info(f"Current ai_analysis_results columns: {', '.join(columns)}")

        # Check for required columns
        required_columns = [
            'satellite_image_source',
            'street_image_source',
            'power_line_geometry'
        ]

        missing = [col for col in required_columns if col not in columns]
        if missing:
            logger.error(f"Missing columns: {', '.join(missing)}")
            return False

        logger.info("✅ All required columns are present!")
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
        print("You can now run the application with: python main.py")
    else:
        print("\n❌ Migration failed. Please check the logs above.")
        exit(1)
