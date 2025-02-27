import os

from box_sdk_gen import BoxClient, BoxOAuth, GetAuthorizeUrlOptions, OAuthConfig
from flask import Flask, redirect, request, url_for

app = Flask(__name__)

BOX_CLIENT_ID = os.environ["BOX_CLIENT_ID"]
BOX_SECRET_ID = os.environ["BOX_SECRET_ID"]

AUTH = BoxOAuth(OAuthConfig(client_id=f"{BOX_CLIENT_ID}", client_secret=f"{BOX_SECRET_ID}"))


def create_html_table(data, headers=None):
    """Create a simple HTML table from a list of tuples."""
    # Start the table
    html = '<table border="1">\n'

    # Add header row if headers are provided
    if headers:
        html += "  <tr>\n"
        for header in headers:
            html += f"    <th>{header}</th>\n"
        html += "  </tr>\n"

    # Add data rows
    for row in data:
        # Check if this is a folder row based on the Type column (index 1)
        is_folder = row[1] == "Folder"

        # Add a simple style for folders - bold text with light blue background
        if is_folder:
            html += '  <tr style="font-weight: bold; background-color: #e6f2ff;">\n'
        else:
            html += "  <tr>\n"

        for cell in row:
            html += f"    <td>{cell}</td>\n"
        html += "  </tr>\n"

    # Close table
    html += "</table>"

    return html


def format_size(size_bytes):
    """Format file size in bytes to human-readable format."""
    if not size_bytes:
        return "N/A"

    if size_bytes < 1024:  # noqa PLR2004
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


@app.route("/")
def get_auth():
    """Start the OAuth flow."""
    auth_url = AUTH.get_authorize_url(
        options=GetAuthorizeUrlOptions(redirect_uri="http://localhost:4999/oauth2callback")
    )
    return redirect(auth_url, code=302)


@app.route("/oauth2callback")
def callback():
    """Handle OAuth callback and redirect to root folder."""
    AUTH.get_tokens_authorization_code_grant(request.args.get("code"))
    return redirect(url_for("browse_folder", folder_id="0"))


@app.route("/folder/<folder_id>")
def browse_folder(folder_id):
    """Browse a Box folder and display its contents."""
    client = BoxClient(auth=AUTH)

    try:
        # Get folder items
        folder_items = client.folders.get_folder_items(folder_id=folder_id)

        # Get folder name for title
        folder_name = "All Files" if folder_id == "0" else client.folders.get_folder_by_id(folder_id=folder_id).name

        # Prepare data for display
        table_data = []
        headers = ["ID", "Type", "Name", "Size", "Modified"]

        for item in folder_items.entries:
            # Get item ID
            item_id = item.id

            # Icon based on type
            if item.type.value == "folder":
                item_type = "Folder"
                # Add folder icon
                item_name = f"📁 {item.name}"
            else:
                item_type = "File"
                # Add file icon
                item_name = f"📄 {item.name}"

            # Create link to item
            if item.type.value == "folder":
                item_link = f'<a href="/folder/{item.id}">{item_name}</a>'
            else:
                item_link = f'<a href="/file/{item.id}">{item_name}</a>'

            # Get size (files only)
            size = format_size(item.size) if hasattr(item, "size") else "N/A"

            # Get modified date
            modified = item.modified_at if hasattr(item, "modified_at") else "N/A"

            table_data.append((item_id, item_type, item_link, size, modified))

        # Create table HTML
        table_html = create_html_table(table_data, headers)

        # Add a link back to parent if not in root
        if folder_id != "0":
            folder = client.folders.get_folder_by_id(folder_id=folder_id)
            if folder.parent:
                parent_link = f'<p><a href="/folder/{folder.parent.id}">👆 Back to parent folder</a></p>'
            else:
                parent_link = '<p><a href="/folder/0">🏠 Back to root</a></p>'
        else:
            parent_link = ""

        # Render simple HTML
        html = f"""
        <html>
        <head>
            <title>Box Folder: {folder_name} (ID: {folder_id})</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #0066cc; }}
                a {{ text-decoration: none; color: #0066cc; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Box Folder: {folder_name} (ID: {folder_id})</h1>
            {parent_link}
            {table_html}
        </body>
        </html>
        """

        return html

    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"


@app.route("/file/<file_id>")
def view_file(file_id):
    """View details of a Box file."""
    client = BoxClient(auth=AUTH)

    try:
        # Get file details
        file = client.files.get_file_by_id(file_id=file_id)

        # Prepare file details
        details = [
            ("ID", file.id),
            ("Name", file.name),
            ("Type", file.type.value),
            ("Size", format_size(file.size)),
            ("Created", file.created_at),
            ("Modified", file.modified_at),
            ("Parent ID", file.parent.id if file.parent else "None"),
        ]

        # Create details table
        details_table = create_html_table(details)

        # Get parent folder link
        parent_folder_id = file.parent.id if file.parent else "0"
        parent_link = f'<p><a href="/folder/{parent_folder_id}">👆 Back to folder</a></p>'

        # Render simple HTML
        html = f"""
        <html>
        <head>
            <title>Box File: {file.name} (ID: {file_id})</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #0066cc; }}
                a {{ text-decoration: none; color: #0066cc; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>File Details: 📄 {file.name} (ID: {file_id})</h1>
            {parent_link}
            {details_table}
        </body>
        </html>
        """

        return html

    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4999, debug=True)
