#!/usr/bin/env python3
import json
import multiprocessing
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

# Get the Box Developer Token from environment variables
BOX_TOKEN = os.environ["BOX_DEVELOPER_TOKEN"]
if not BOX_TOKEN:
    print("Error: BOX_DEVELOPER_TOKEN not found in environment variables")
    print("Please create a .env file with your Box developer token")
    sys.exit(1)


class BoxUploader:  # noqa D101
    def __init__(self, db_file_path: Path):
        """Initialize the Box uploader with database connection."""
        self.db_path = db_file_path
        self.folders_cache = {"0": "All Files"}  # Root folder
        self.lock = multiprocessing.Lock()

        # Get the root folder ID from the database
        self.root_folder_id = self.get_root_folder_id()

    def get_root_folder_id(self):
        """Get the root folder ID from the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        # The root folder has an empty folder_path
        cursor.execute("SELECT box_folder_id FROM folders WHERE folder_path = ''")
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return result[0]
        else:
            # Default to 0 if not found
            return "0"

    def get_db_connection(self):
        """Get a connection to the SQLite database."""
        return sqlite3.connect(self.db_path, timeout=30)

    def get_folder_id_from_path(self, folder_path):
        """Get the internal database ID for a folder path."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM folders WHERE folder_path = ?
            """,
            (folder_path,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
        return None

    def update_folder_box_id(self, folder_path, box_folder_id):
        """Update the Box folder ID for a specific folder path in the database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE folders
                SET box_folder_id = ?, status = 'complete', created_at = datetime('now')
                WHERE folder_path = ?
                """,
                (box_folder_id, folder_path),
            )
            conn.commit()
        except Exception as e:
            print(f"Error updating folder ID for {folder_path}: {e}")
        finally:
            conn.close()

    def create_folder(self, folder_name, parent_id, parent_path):
        """Create a folder in Box and return the folder ID."""
        if not folder_name:
            return parent_id

        # Check cache first - make sure parent_id is a Box folder ID
        cache_key = f"{parent_id}:{folder_name}"
        with self.lock:
            if cache_key in self.folders_cache:
                return self.folders_cache[cache_key]

        url = "https://api.box.com/2.0/folders"
        headers = {"authorization": f"Bearer {BOX_TOKEN}", "Content-Type": "application/json"}
        data = {"name": folder_name, "parent": {"id": parent_id}}

        import pdb

        pdb.set_trace()
        try:
            response = requests.post(url, headers=headers, json=data)
            valid_responses = [200, 201]

            if response.status_code in valid_responses:
                folder_data = response.json()
                folder_id = folder_data.get("id")
                with self.lock:
                    self.folders_cache[cache_key] = folder_id

                # Build the full path for this new folder
                current_path = str(Path(parent_path) / folder_name) if parent_path else folder_name

                # Update the box_folder_id in the database
                self.update_folder_box_id(current_path, folder_id)

                print(f"Created folder '{folder_name}' (ID: {folder_id})")
                return folder_id
            else:
                # Check if the folder already exists
                if response.status_code == 409:  # noqa PLR2004
                    # Conflict - folder already exists
                    # Extract the existing folder ID from the error response
                    error_data = response.json()
                    if "context_info" in error_data and "conflicts" in error_data["context_info"]:
                        for conflict in error_data["context_info"]["conflicts"]:
                            if conflict["type"] == "folder" and conflict["name"] == folder_name:
                                folder_id = conflict["id"]
                                with self.lock:
                                    self.folders_cache[cache_key] = folder_id

                                # Build the full path for this folder
                                current_path = str(Path(parent_path) / folder_name) if parent_path else folder_name

                                # Update the box_folder_id in the database
                                self.update_folder_box_id(current_path, folder_id)

                                print(f"Found existing folder '{folder_name}' (ID: {folder_id})")
                                return folder_id

                # If we can't extract the ID or it's a different error, raise an exception
                response.raise_for_status()
                return parent_id
        except Exception as e:
            print(f"Error creating folder '{folder_name}': {str(e)}")
            return parent_id

    def ensure_folder_path(self, folder_path):
        """Create all folders in the path if they don't exist and update folder IDs in the database."""
        if not folder_path or folder_path == "." or folder_path == "/":
            return self.root_folder_id

        # Split the path and create each folder, storing the IDs
        parts = Path(folder_path).parts
        current_box_id = self.root_folder_id  # This is the Box folder ID
        current_path = ""

        for part in parts:
            if part and part != ".":  # Skip empty parts
                # Build the path incrementally
                current_path = str(Path(current_path) / part) if current_path else part

                # Create folder using the Box parent folder ID
                current_box_id = self.create_folder(part, current_box_id, current_path.replace(part, "").rstrip("/"))

        return current_box_id

    def upload_file(self, file_info):
        """Upload a file to Box and update the database with the status."""
        file_id = file_info["id"]
        file_path = file_info["file_path"]
        file_name = file_info["file_name"]
        folder_path = file_info["folder_path"]
        size = file_info["size"]

        # Connect to the database
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            # Update status to in_process and record start time
            cursor.execute(
                """
                UPDATE files
                SET status = 'in_process', start_time = datetime('now'), attempt_count = attempt_count + 1
                WHERE id = ? AND (status = 'not_started' OR status = 'error')
                """,
                (file_id,),
            )

            # Check if a row was actually updated (locking mechanism)
            if cursor.rowcount == 0:
                print(f"File '{file_name}' is already being processed or completed by another worker")
                conn.commit()
                conn.close()
                return

            conn.commit()

            print(f"Uploading '{file_name}' ({self.format_size(size)}) - {file_path}")

            # Create the folder structure in Box - no root_id parameter needed anymore
            box_folder_id = self.ensure_folder_path(folder_path)

            # Upload the file
            url = "https://upload.box.com/api/2.0/files/content"
            headers = {"Authorization": f"Bearer {BOX_TOKEN}"}

            # Prepare the multipart/form-data payload
            attributes = {"name": file_name, "parent": {"id": box_folder_id}}

            files = {
                "attributes": (None, json.dumps(attributes), "application/json"),
                "file": (file_name, Path.open(file_path, "rb")),
            }

            response = requests.post(url, headers=headers, files=files)
            valid_responses = [200, 201]
            if response.status_code in valid_responses:
                data = response.json()
                box_file_id = data["entries"][0]["id"] if "entries" in data else None

                # Get the folder_id from the database
                db_folder_id = self.get_folder_id_from_path(folder_path)

                # Update database with success status and both IDs
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'complete', end_time = datetime('now'),
                        box_file_id = ?, box_folder_id = ?
                    WHERE id = ?
                    """,
                    (box_file_id, box_folder_id, file_id),
                )

                # Also ensure the folder record is updated with the Box folder ID
                if db_folder_id:
                    cursor.execute(
                        """
                        UPDATE folders
                        SET box_folder_id = ?, status = 'complete', created_at = datetime('now')
                        WHERE id = ? AND (box_folder_id IS NULL OR box_folder_id = '')
                        """,
                        (box_folder_id, db_folder_id),
                    )

                print(f"✅ Successfully uploaded '{file_name}' to Box (ID: {box_file_id})")
            else:
                # Update database with error status
                error_message = f"HTTP Error {response.status_code}: {response.text}"
                cursor.execute(
                    """
                    UPDATE files
                    SET status = 'error', end_time = datetime('now'), error_message = ?
                    WHERE id = ?
                    """,
                    (error_message, file_id),
                )

                print(f"❌ Error uploading '{file_name}': {error_message}")

        except Exception as e:
            # Update database with error status
            error_message = str(e)
            cursor.execute(
                """
                UPDATE files
                SET status = 'error', end_time = datetime('now'), error_message = ?
                WHERE id = ?
                """,
                (error_message, file_id),
            )

            print(f"❌ Exception uploading '{file_name}': {error_message}")

        finally:
            conn.commit()
            conn.close()

    def get_files_to_upload(self, limit=10):
        """Get files that need to be uploaded (not started or error status)."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, file_path, file_name, folder_path, size, status, attempt_count
            FROM files
            WHERE status IN ('not_started', 'error') AND attempt_count < 3
            ORDER BY status DESC, attempt_count ASC, size ASC
            LIMIT ?
            """,
            (limit,),
        )

        columns = ["id", "file_path", "file_name", "folder_path", "size", "status", "attempt_count"]
        files = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return files

    def format_size(self, size_bytes):
        """Format size in bytes to human-readable format."""
        if size_bytes is None:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:  # noqa PLR2004
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.2f} PB"

    def upload_worker(self, queue):
        """Worker process for uploading files."""
        while True:
            file_info = queue.get()
            if file_info is None:  # Poison pill
                break
            self.upload_file(file_info)

    def upload_files_single_worker(self):
        """Upload files using a single worker for debugging purposes."""
        print("Starting upload with single worker (debug mode)")

        try:
            while True:
                # Get a batch of files to upload
                files_to_upload = self.get_files_to_upload(limit=5)

                if not files_to_upload:
                    print("No more files to upload.")
                    break

                # Process each file directly in the main thread
                for file_info in files_to_upload:
                    self.upload_file(file_info)

                    # Small delay to avoid hammering the database
                    time.sleep(0.5)

            print("All uploads complete.")

        except KeyboardInterrupt:
            print("Upload interrupted.")
            print("Upload stopped.")

    def upload_files_concurrently(self, max_workers=4):
        """Upload files concurrently or directly based on worker count."""
        # Use direct mode for single worker (easier debugging)
        if max_workers == 1:
            self.upload_files_single_worker()
            return

        # Otherwise use multiprocessing
        print(f"Starting upload with {max_workers} concurrent workers")

        # Create a queue and workers
        queue = multiprocessing.Queue(maxsize=max_workers * 2)
        workers = []

        try:
            # Start worker processes
            for _ in range(max_workers):
                p = multiprocessing.Process(target=self.upload_worker, args=(queue,))
                p.start()
                workers.append(p)

            # Keep submitting files until there are no more to process
            while True:
                files_to_upload = self.get_files_to_upload(limit=max_workers * 2)

                if not files_to_upload:
                    print("No more files to upload.")
                    break

                for file_info in files_to_upload:
                    queue.put(file_info)

                # Add a small delay to prevent database contention
                time.sleep(2)

            # Send poison pills to stop workers
            for _ in range(max_workers):
                queue.put(None)

            # Wait for all workers to finish
            for p in workers:
                p.join()

            print("All uploads complete.")

        except KeyboardInterrupt:
            print("Upload interrupted. Waiting for workers to finish current tasks...")

            # Send poison pills to stop workers
            for _ in range(max_workers):
                queue.put(None)

            # Wait for all workers to finish
            for p in workers:
                p.join(timeout=10)
                if p.is_alive():
                    p.terminate()

            print("Upload stopped.")


def main():
    """Core Loop."""
    db_file = Path(os.environ["DB_FILE"])

    # Get number of workers from environment, directly
    num_workers = int(os.environ["UPLOAD_WORKERS"])

    # Debug mode flag (can be activated with UPLOAD_WORKERS=1)
    debug_mode = num_workers == 1
    if debug_mode:
        print("*** DEBUG MODE ENABLED: Running with single worker for easier debugging ***")

    uploader = BoxUploader(db_file)
    uploader.upload_files_concurrently(max_workers=num_workers)


if __name__ == "__main__":
    main()
