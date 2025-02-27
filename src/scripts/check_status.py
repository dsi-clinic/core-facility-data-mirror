#!/usr/bin/env python3
import os
import sqlite3
import sys
import time
from pathlib import Path


def format_size(size_bytes):
    """Format size in bytes to human-readable format."""
    if size_bytes is None:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:  # noqa PLR2004
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} PB"


def check_status(db_path, watch=False, interval=5):
    """
    Check the status of file uploads.

    If watch is True, keep updating the status every 'interval' seconds.
    """
    db_path_obj = Path(db_path)

    if not db_path_obj.exists():
        print(f"Error: Database file {db_path} not found.")
        print("Please run 'make init-db' first.")
        return

    try:
        while True:
            # Clear screen if in watch mode
            if watch:
                os.system("cls" if os.name == "nt" else "clear")
                print(f"Box Upload Status Monitor (updating every {interval} seconds)")
                print("Press Ctrl+C to exit")
                print("=" * 60)

            # Connect to the SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get counts by status
            cursor.execute("SELECT status, COUNT(*) FROM files GROUP BY status")
            status_counts = cursor.fetchall()

            # Get totals
            cursor.execute("SELECT COUNT(*), SUM(size) FROM files")
            total_count, total_size = cursor.fetchone()

            # Get uploaded size
            cursor.execute("SELECT SUM(size) FROM files WHERE status = 'complete'")
            uploaded_size = cursor.fetchone()[0] or 0

            # Prepare status display
            status_display = {}
            for status, count in status_counts:
                status_display[status] = count

            print("\nUpload Status:")
            print(f"  Not Started: {status_display.get('not_started', 0)}")
            print(f"  In Process:  {status_display.get('in_process', 0)}")
            print(f"  Complete:    {status_display.get('complete', 0)}")
            print(f"  Error:       {status_display.get('error', 0)}")

            # Display progress
            if total_size and total_size > 0:
                progress = (uploaded_size / total_size) * 100
                print(f"\nProgress: {progress:.1f}% ({format_size(uploaded_size)} of {format_size(total_size)})")

                # Progress bar
                bar_length = 40
                filled_length = int(bar_length * uploaded_size // total_size)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                print(f"[{bar}] {total_count} files")
            else:
                print("\nNo files found in database.")

            # Get recent uploads
            cursor.execute("""
            SELECT file_name, end_time, box_file_id
            FROM files
            WHERE status = 'complete'
            ORDER BY end_time DESC
            LIMIT 5
            """)
            recent_uploads = cursor.fetchall()

            if recent_uploads:
                print("\nRecent Uploads:")
                for file_name, end_time, box_file_id in recent_uploads:
                    print(f"  {file_name} (ID: {box_file_id}) - {end_time}")

            # Get recent errors
            cursor.execute("""
            SELECT file_name, error_message, attempt_count
            FROM files
            WHERE status = 'error'
            ORDER BY end_time DESC
            LIMIT 5
            """)
            recent_errors = cursor.fetchall()

            if recent_errors:
                print("\nRecent Errors:")
                for file_name, error_message, attempt_count in recent_errors:
                    error_preview = error_message[:60] + "..." if len(error_message) > 60 else error_message  # noqa PLR2004
                    print(f"  {file_name} (Attempts: {attempt_count}) - {error_preview}")

            conn.close()

            if not watch:
                break

            # Wait for next update
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nMonitor stopped.")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    db_path = os.environ["DB_FILE"]
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        interval = 5
        if len(sys.argv) > 2:  # noqa PLR2004
            try:
                interval = int(sys.argv[2])
            except ValueError:
                pass
        check_status(db_path, watch=True, interval=interval)
    else:
        check_status(db_path)
