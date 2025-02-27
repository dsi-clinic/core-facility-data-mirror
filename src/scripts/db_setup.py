#!/usr/bin/env python3
import os
import sqlite3
import sys
from pathlib import Path


def setup_database(db_file: Path, box_root_folder_id: int = 0, force: bool = False):
    """Initialize the SQLite database with the required schema."""
    # Check if database file already exists
    if db_file.exists():
        if not force:
            print(f"Warning: Database file {db_file} already exists.")
            response = input("Do you want to delete it and create a new one? (y/n): ")
            if response.lower() not in ["y", "yes"]:
                print("Operation cancelled. Database was not modified.")
                sys.exit(0)

        # Delete the existing database file
        print(f"Removing existing database file: {db_file}")
        try:
            db_file.unlink()
        except Exception as e:
            print(f"Error removing database file: {e}")
            sys.exit(1)

    # Ensure the data directory exists
    db_dir = db_file.parent
    if db_dir:  # Only create directory if there's a path component
        db_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating new database at: {db_file}")

    # Connect to the SQLite database
    conn = sqlite3.connect(str(db_file))

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    # Create the folders table first with parent column
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_path TEXT UNIQUE,
        box_folder_id TEXT,
        parent_folder_id TEXT,
        parent INTEGER,
        status TEXT DEFAULT 'not_created',
        created_at TIMESTAMP,
        error_message TEXT,
        FOREIGN KEY (parent) REFERENCES folders(id)
    )
    """)

    # Add the default root folder (Box always has "0" as the root folder ID)
    cursor.execute(f"""
    INSERT OR IGNORE INTO folders (folder_path, box_folder_id, status, parent)
    VALUES ('', '{box_root_folder_id}', 'complete', NULL)
    """)

    # Create the files table with a foreign key to folders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        file_name TEXT,
        folder_path TEXT,
        folder_id INTEGER,
        size INTEGER,
        status TEXT DEFAULT 'not_started',
        attempt_count INTEGER DEFAULT 0,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        box_file_id TEXT,
        error_message TEXT,
        FOREIGN KEY (folder_id) REFERENCES folders(id)
    )
    """)

    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON files (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON files (file_path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_folder_path ON folders (folder_path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_box_folder_id ON folders (box_folder_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_status ON folders (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_folders_parent ON folders (parent)")

    conn.commit()
    conn.close()

    print("Database setup complete. Ready to scan files.")


if __name__ == "__main__":
    # Get DB file location from environment
    db_file_location = Path(os.environ["DB_FILE"])
    box_root_folder_id = os.environ["BOX_ROOT_FOLDER_ID"]
    print(f"Using database location: {db_file_location}")

    # Check for --force flag
    force = False
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        force = True
        print("Force mode enabled: will overwrite existing database without confirmation")

    setup_database(db_file_location, box_root_folder_id, force)
