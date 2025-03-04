#!/usr/bin/env python3
import os
import sqlite3
import sys
import time
from pathlib import Path


def ensure_parent_folders(conn, base_dir, current_dir, path_to_id):
    """
    Ensure all parent folders exist in the database.

    Returns the folder_id of the current directory.
    """
    # Convert paths to Path objects if they aren't already
    base_dir = Path(base_dir)
    current_dir = Path(current_dir)

    # Get relative path from base directory
    if current_dir.absolute() == base_dir.absolute():
        rel_path = ""
    else:
        try:
            rel_path = str(current_dir.relative_to(base_dir))
        except ValueError:
            # This can happen if current_dir is not relative to base_dir
            print(f"Warning: {current_dir} is not relative to {base_dir}")
            rel_path = str(current_dir)

    # Skip if this is a dot directory
    if rel_path == "." or rel_path == "..":
        # Return the base directory ID
        return path_to_id[""]

    # Check if we already know this path's ID
    if rel_path in path_to_id:
        return path_to_id[rel_path]

    # We need to ensure this path exists in the DB
    cursor = conn.cursor()

    # First check if it's already in the database
    cursor.execute("SELECT id FROM folders WHERE folder_path = ?", (rel_path,))
    result = cursor.fetchone()

    if result:
        # It exists, cache and return the ID
        folder_id = result[0]
        path_to_id[rel_path] = folder_id
        return folder_id

    # It doesn't exist, so we need to ensure the parent exists first
    parent_path = current_dir.parent

    if parent_path == base_dir.parent:
        # We've gone too far up
        parent_id = None
    else:
        # Recursively ensure parent exists
        parent_id = ensure_parent_folders(conn, base_dir, parent_path, path_to_id)

    # Now we can create this folder
    # Skip explicitly adding "." or ".." entries
    if rel_path and rel_path != "." and rel_path != "..":
        cursor.execute(
            """
        INSERT INTO folders (folder_path, status, parent)
        VALUES (?, 'not_created', ?)
        """,
            (rel_path, parent_id),
        )

        folder_id = cursor.lastrowid
        path_to_id[rel_path] = folder_id
        return folder_id
    else:
        # Return the root folder ID for "." or ".." or empty paths
        return path_to_id[""]


def scan_files_single_pass(base_dir: Path, db_file: Path, commit_every=1000):
    """Scan directory tree in a single pass, processing both folders and files."""
    start_time = time.time()

    print(f"Scanning directory: {base_dir}")
    print(f"Using database: {db_file}")

    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys = ON")

    # Get root folder ID or create it if doesn't exist
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM folders WHERE folder_path = ''")
    result = cursor.fetchone()

    if result:
        root_id = result[0]
    else:
        cursor.execute("""
        INSERT INTO folders (folder_path, box_folder_id, status, parent)
        VALUES ('', '0', 'complete', NULL)
        """)
        root_id = cursor.lastrowid

    # Initialize counters and cache
    path_to_id = {"": root_id}
    folder_count = 1  # Count the root folder
    file_count = 0
    skipped_files = []
    batch_size = 0
    total_size = 0

    # Process the directory tree - os.walk is more efficient for large file systems
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        root_path = Path(root)

        try:
            # Ensure this directory exists in the database
            folder_id = ensure_parent_folders(conn, base_dir, root_path, path_to_id)

            # Process files in this directory
            file_batch = []
            for file_name in files:
                # Skip hidden and system files
                if file_name.startswith(".") or "DS_Store" in file_name:
                    skipped_files.append((str(root_path), file_name))
                    continue

                file_path = Path(root) / file_name
                abs_path = str(file_path.resolve())

                # Get relative folder path
                if root == str(base_dir):
                    rel_folder_path = ""
                else:
                    rel_folder_path = str(Path(root).relative_to(base_dir))

                try:
                    size = file_path.stat().st_size
                    total_size += size
                except (PermissionError, OSError):
                    skipped_files.append((str(root_path), file_name))
                    continue

                # Add to batch
                file_batch.append((abs_path, file_name, rel_folder_path, folder_id, size))
                batch_size += 1

            # Insert file batch
            if file_batch:
                cursor.executemany(
                    """
                INSERT OR IGNORE INTO files (file_path, file_name, folder_path, folder_id, size, status)
                VALUES (?, ?, ?, ?, ?, 'not_started')
                """,
                    file_batch,
                )

                file_count += len(file_batch)

            # Commit periodically
            if batch_size >= commit_every:
                conn.commit()
                elapsed = time.time() - start_time
                rate = file_count / elapsed if elapsed > 0 else 0
                print(
                    f"Processed {folder_count} folders, {file_count} files ({rate:.1f} files/sec), {len(skipped_files)} skipped"
                )
                print(f"Total size: {format_size(total_size)}")
                batch_size = 0

        except Exception as e:
            print(f"Error processing directory {root}: {e}")

    # Final commit
    conn.commit()
    conn.close()

    duration = time.time() - start_time
    print(f"\nScan complete in {duration:.1f} seconds")
    print(f"Added {folder_count} folders and {file_count} files to database")
    print(f"Skipped {len(skipped_files)} files")
    print(f"Total data size: {format_size(total_size)}")

    if skipped_files:
        print("\nSkipped Files:")
        # Create a set to eliminate duplicates while preserving folder path information
        unique_skipped = set(skipped_files)

        # Filter out DS_Store files
        filtered_skipped = [
            (folder_path, file_name) for folder_path, file_name in unique_skipped if "DS_Store" not in file_name
        ]

        if filtered_skipped:
            for folder_path, file_name in sorted(filtered_skipped):
                print(f"{folder_path}/{file_name}")
        else:
            print("Only DS_Store files were skipped.")


def format_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:  # noqa PLR2004
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


if __name__ == "__main__":
    base_dir = Path("/data")
    db_file = Path(os.environ["DB_FILE"])

    if not base_dir.exists():
        print(f"Error: Directory '{base_dir}' does not exist")
        sys.exit(1)

    scan_files_single_pass(base_dir, db_file)
