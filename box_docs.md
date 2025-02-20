# Get a Token
1. https://uchicago.app.box.com/developers/console/newapp
2. Custom app. Purpose: automation, user: customer, oauth
3. Back to 'My Platforms Apps'
4. Hover on app, click '...'
5. Generate Developer Token

# Create a folder
https://developer.box.com/reference/post-folders/
```bash
curl -i -X POST "https://api.box.com/2.0/folders" \
     -H "authorization: Bearer <ACCESS_TOKEN>" \
     -H "content-type: application/json" \
     -d '{
       "name": "New Folder",
       "parent": {
         "id": "0"
       }
     }'
```
returns
```json
{
  "type": "folder",
  "id": "308400057161", !!!!HERE!!!!
  "sequence_id": "0",
  "etag": "0",
  "name": "test New Folder",
  "created_at": "2025-02-20T07:30:51-08:00",
  "modified_at": "2025-02-20T07:30:51-08:00",
  "description": "",
  "size": 0,
  "path_collection": {
    "total_count": 1,
    "entries": [
      {
        "type": "folder",
        "id": "0",
        "sequence_id": null,
        "etag": null,
        "name": "All Files"
      }
    ]
  },
  "created_by": {
    "type": "user",
    "id": "14297527528",
    "name": "Dylan Halpern",
    "login": "dhalpern@uchicago.edu"
  },
  "modified_by": {
    "type": "user",
    "id": "14297527528",
    "name": "Dylan Halpern",
    "login": "dhalpern@uchicago.edu"
  },
  "trashed_at": null,
  "purged_at": null,
  "content_created_at": "2025-02-20T07:30:51-08:00",
  "content_modified_at": "2025-02-20T07:30:51-08:00",
  "owned_by": {
    "type": "user",
    "id": "14297527528",
    "name": "Dylan Halpern",
    "login": "dhalpern@uchicago.edu"
  },
  "shared_link": null,
  "folder_upload_email": null,
  "parent": {
    "type": "folder",
    "id": "0",
    "sequence_id": null,
    "etag": null,
    "name": "All Files"
  },
  "item_status": "active",
  "item_collection": {
    "total_count": 0,
    "entries": [],
    "offset": 0,
    "limit": 100,
    "order": [
      {
        "by": "type",
        "direction": "ASC"
      },
      {
        "by": "name",
        "direction": "ASC"
      }
    ]
  }
}
```
# Upload a file
https://developer.box.com/reference/post-files-content/
```bash
curl -i -X POST "https://upload.box.com/api/2.0/files/content" \
     -H "authorization: Bearer <token>" \
     -H "content-type: multipart/form-data" \
     -F attributes='{"name":"filename.extension", "parent":{"id":"0"}}' \
     -F file=@path/to/file.txt
```
returns 
```json
{
  "total_count": 1,
  "entries": [
    {
      "type": "file",
      "id": "1783205659173", !!!!!HERE!!!!!!!
      "file_version": {
        "type": "file_version",
        "id": "1964938667973", 
        "sha1": "1b3774096610f1e829974f2b247b121e40ad77f0"
      },
      "sequence_id": "0",
      "etag": "0",
      "sha1": "1b3774096610f1e829974f2b247b121e40ad77f0",
      "name": "csds_tstesttsst.jpeg",
      "description": "",
      "size": 34475,
      "path_collection": {
        "total_count": 1,
        "entries": [
          {
            "type": "folder",
            "id": "0",
            "sequence_id": null,
            "etag": null,
            "name": "All Files"
          }
        ]
      },
      "created_at": "2025-02-20T07:16:26-08:00",
      "modified_at": "2025-02-20T07:16:26-08:00",
      "trashed_at": null,
      "purged_at": null,
      "content_created_at": "2025-02-20T07:16:26-08:00",
      "content_modified_at": "2025-02-20T07:16:26-08:00",
      "created_by": {
        "type": "user",
        "id": "14297527528",
        "name": "Dylan Halpern",
        "login": "dhalpern@uchicago.edu"
      },
      "modified_by": {
        "type": "user",
        "id": "14297527528",
        "name": "Dylan Halpern",
        "login": "dhalpern@uchicago.edu"
      },
      "owned_by": {
        "type": "user",
        "id": "14297527528",
        "name": "Dylan Halpern",
        "login": "dhalpern@uchicago.edu"
      },
      "shared_link": null,
      "parent": {
        "type": "folder",
        "id": "0",
        "sequence_id": null,
        "etag": null,
        "name": "All Files"
      },
      "item_status": "active"
    }
  ]
}
```

# Generate a Shared URL
https://developer.box.com/reference/put-files-id--add-shared-link/#param-shared_link-vanity_name
```bash
curl -i -X PUT "https://api.box.com/2.0/files/{id}?fields=shared_link" \
     -H "authorization: Bearer <token>" \
     -d '{
       "shared_link": {
         "access": "open",
         "permissions": {
           "can_download": true
         },
         "vanity_name": "file-name-picky-nosymbol-no-underscore-32char"
       }
     }'
```
returns
```json
{
  "type": "file",
  "id": "1783205659173",
  "etag": "1",
  "shared_link": {
    "url": "https://uchicago.box.com/v/csds-test-test-test",
    "download_url": "https://uchicago.box.com/shared/static/s91y4c2g073hpj5t9ztvomm99w5a95b5.jpeg",
    "vanity_url": "https://uchicago.box.com/v/csds-test-test-test",
    "vanity_name": "csds-test-test-test",
    "effective_access": "open",
    "effective_permission": "can_download",
    "is_password_enabled": false,
    "unshared_at": null,
    "download_count": 0,
    "preview_count": 0,
    "access": "open",
    "permissions": {
      "can_preview": true,
      "can_download": true,
      "can_edit": false
    }
  }
}
```