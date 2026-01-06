"""
Database schema fix script - Auto-run version
Increases VARCHAR column sizes to accommodate longer source strings
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_varchar_columns():
    """Fix VARCHAR column sizes in risk_results table"""

    engine = create_engine(DATABASE_URL)

    # SQL commands to alter column types
    alter_commands = [
        # Fix source columns (10 -> 200 for long source descriptions)
        "ALTER TABLE risk_results ALTER COLUMN wetlands_source TYPE VARCHAR(200);",
        "ALTER TABLE risk_results ALTER COLUMN flood_source TYPE VARCHAR(200);",
        "ALTER TABLE risk_results ALTER COLUMN slope_source TYPE VARCHAR(200);",
        "ALTER TABLE risk_results ALTER COLUMN road_source TYPE VARCHAR(200);",
        "ALTER TABLE risk_results ALTER COLUMN protected_land_source TYPE VARCHAR(200);",
        "ALTER TABLE risk_results ALTER COLUMN utility_source TYPE VARCHAR(200);",

        # Fix other short VARCHAR columns for safety
        "ALTER TABLE risk_results ALTER COLUMN flood_zone TYPE VARCHAR(50);",
        "ALTER TABLE risk_results ALTER COLUMN flood_severity TYPE VARCHAR(20);",
        "ALTER TABLE risk_results ALTER COLUMN slope_severity TYPE VARCHAR(20);",
        "ALTER TABLE risk_results ALTER COLUMN overall_risk TYPE VARCHAR(20);",
    ]

    try:
        with engine.connect() as conn:
            logger.info("Starting schema migration...")

            for i, command in enumerate(alter_commands, 1):
                logger.info(f"Executing command {i}/{len(alter_commands)}")
                try:
                    conn.execute(text(command))
                    conn.commit()
                    logger.info(f"  ✅ Success")
                except Exception as e:
                    if "does not exist" in str(e):
                        logger.warning(f"  ⚠ Column already migrated or doesn't exist")
                    else:
                        raise

            logger.info("=" * 60)
            logger.info("✅ Schema migration completed successfully!")
            logger.info("All VARCHAR columns have been resized.")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE SCHEMA FIX - AUTO RUN")
    print("=" * 60)
    print()
    fix_varchar_columns()
    print()
    print("✅ Migration complete! You can now process properties successfully.")
    print("=" * 60)
