"""
Migration script to add new skip trace fields to property_owner_info table.
Run this script to add the new BatchData API fields.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def migrate():
    """Add new skip trace fields to property_owner_info table."""
    engine = create_engine(DATABASE_URL)

    # New columns to add
    new_columns = [
        # Phone fields
        ("phone_count", "INTEGER"),
        ("phone_list", "JSONB"),

        # Email fields
        ("email_count", "INTEGER"),
        ("email_list", "JSONB"),

        # Mailing address additional fields
        ("mailing_zip_plus4", "VARCHAR(10)"),
        ("mailing_county", "VARCHAR(255)"),
        ("mailing_validity", "VARCHAR(50)"),

        # All persons from skip trace
        ("all_persons", "JSONB"),

        # Compliance flags
        ("is_deceased", "BOOLEAN DEFAULT FALSE"),
        ("is_litigator", "BOOLEAN DEFAULT FALSE"),
        ("has_dnc", "BOOLEAN DEFAULT FALSE"),
        ("has_tcpa", "BOOLEAN DEFAULT FALSE"),
        ("tcpa_blacklisted", "BOOLEAN DEFAULT FALSE"),

        # Bankruptcy and lien info
        ("has_bankruptcy", "BOOLEAN DEFAULT FALSE"),
        ("bankruptcy_info", "JSONB"),
        ("has_involuntary_lien", "BOOLEAN DEFAULT FALSE"),
        ("lien_info", "JSONB"),

        # Property ID from skip trace
        ("skip_trace_property_id", "VARCHAR(255)"),

        # Raw response
        ("raw_response", "JSONB"),
    ]

    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'property_owner_info'
            )
        """))
        table_exists = result.scalar()

        if not table_exists:
            print("Table property_owner_info does not exist. Creating via SQLAlchemy models...")
            from models import Base
            Base.metadata.create_all(engine)
            print("Table created successfully!")
            return

        print("Adding new columns to property_owner_info table...")

        for column_name, column_type in new_columns:
            try:
                # Check if column already exists
                check_sql = text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = 'property_owner_info'
                        AND column_name = '{column_name}'
                    )
                """)
                exists = conn.execute(check_sql).scalar()

                if exists:
                    print(f"  Column '{column_name}' already exists, skipping...")
                    continue

                # Add the column
                alter_sql = text(f"""
                    ALTER TABLE property_owner_info
                    ADD COLUMN {column_name} {column_type}
                """)
                conn.execute(alter_sql)
                conn.commit()
                print(f"  Added column: {column_name} ({column_type})")

            except Exception as e:
                print(f"  Error adding column {column_name}: {str(e)}")
                conn.rollback()

        # Also update mailing_state to allow longer values
        try:
            alter_sql = text("""
                ALTER TABLE property_owner_info
                ALTER COLUMN mailing_state TYPE VARCHAR(10)
            """)
            conn.execute(alter_sql)
            conn.commit()
            print("  Updated mailing_state column to VARCHAR(10)")
        except Exception as e:
            print(f"  Note: mailing_state update: {str(e)}")
            conn.rollback()

        print("\nMigration completed successfully!")
        print("\nNew fields available:")
        print("  - phone_list: Full list of phones with carrier, DNC, TCPA, score, etc.")
        print("  - email_list: Full list of emails with tested status")
        print("  - all_persons: Up to 3 persons associated with property")
        print("  - Compliance flags: is_deceased, is_litigator, has_dnc, has_tcpa")
        print("  - Bankruptcy/lien info: has_bankruptcy, has_involuntary_lien")


if __name__ == "__main__":
    migrate()
