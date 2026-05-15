# Digitarq Download Skill

Downloads high resolution images from the Portuguese Archives digital library (Digitarq).

## When to Use

When the user wants to download images from a digital document hosted on:
- https://digitarq.arquivos.pt/documentDetails/{id}
- https://digitarq.arquivos.pt/fileViewer/{id}

## How It Works

1. **Fetch document metadata**: Access the document details page to get the document ID
2. **Get file list**: Access the file viewer to extract all file IDs from the sidebar
3. **Download images**: Use the API endpoint to download full-resolution images in parallel

## Usage

### Download all images from a document URL

```
Download images from https://digitarq.arquivos.pt/documentDetails/49c3d3deb2ae4d9197820417c75c6647
```

### Download images by archive reference

```
Download images from digitarq reference PT/TT/AJCJ/AJ028
```

### Download to a specific folder

```
Download images from digitarq to ./my-manuscript-folder
```

## Technical Details

### URL Patterns

**Document Details Page:**
```
https://digitarq.arquivos.pt/documentDetails/{document_id}
```

**File Viewer Page:**
```
https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false
```

**Thumbnail URL:**
```
https://digitarq.arquivos.pt/rdigital/thumb?fileId={file_id}
```

**Full Resolution Download URL:**
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

### Workflow

1. Extract `document_id` from URL (the hash in the URL, e.g., `49c3d3deb2ae4d9197820417c75c6647`)
2. Fetch the file viewer page to get sidebar thumbnails
3. Extract file IDs from the sidebar (each thumbnail has a `fileId` in the URL)
4. Download all images using the full-res API endpoint

### File ID Extraction

The file viewer shows thumbnails in the sidebar (10 at a time). Each thumbnail URL contains:
```
/rdigital/thumb?fileId={file_id}
```

The sidebar uses infinite scroll - scroll down to load all thumbnails and extract all file IDs.

### Image Format

- Format: JPEG
- Resolution: ~2000x2200 pixels (varies by document)
- License: CC BY-SA 4.0 (check specific document)
- Naming: Save as `page_{page_num:03d}.jpg`

## Installation

For Matrix Agent, copy this folder to your skills directory:
```bash
cp -r digitarq-get ~/.minimaxagent/skills/
```

## Sub-Agent Instructions

### For Browser Expert (Main Agent must delegate)

1. **Find document**: Search Digitarq for the reference or navigate to the document URL
2. **Extract document ID**: Get the hash from `/documentDetails/{document_id}`
3. **Get file IDs**: Navigate to `/fileViewer/{document_id}?isRepresentation=false`
4. **Extract all file IDs**: The sidebar shows 10 thumbnails at a time with infinite scroll
5. **Report back**: Return the complete list of file IDs

### For Bash/Download Script

Use the Python download script included in this package:
```bash
python3 digitarq-download.py --document-id <id> --output-dir <folder>
```

Or implement using:
```python
import urllib.request

base_url = "https://digitarq.arquivos.pt/api/rdigital/dissemination"
file_ids = list(range(start_id, end_id + 1))

for file_id in file_ids:
    url = f"{base_url}?fileId={file_id}&download=true"
    # Download with parallel execution
```

## License

CC BY-SA 4.0 - See LICENSE file for details.