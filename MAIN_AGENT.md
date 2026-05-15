# MAIN AGENT INSTRUCTIONS

## How to Use This Skill

When the user requests to download images from Digitarq, follow this workflow:

### Step 1: Understand the Request

The user may provide:
- A direct Digitarq URL: `https://digitarq.arquivos.pt/documentDetails/{document_id}`
- An archive reference: `PT/TT/CF/054`
- Just a reference without "PT/TT/": `CF/054`

### Step 2: Extract Document ID

If the user provides a direct URL, extract the document ID from the hash.

If the user provides a reference code:
1. Delegate to **Browser Expert** to search Digitarq and find the document
2. Get the document ID from the resulting URL

### Step 3: Extract File IDs

1. Navigate to `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false`
2. Delegate to **Browser Expert** to extract all file IDs from the sidebar thumbnails
3. The sidebar uses infinite scroll - scroll down to load all thumbnails
4. Each thumbnail has a `fileId` in its URL: `/rdigital/thumb?fileId={file_id}`

### Step 4: Download Images

Use the download API endpoint:
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

Options for downloading:
1. **Python script**: Use `digitarq-download.py` with `--document-id` and `--output-dir`
2. **Inline Python**: Write a Python script using `urllib.request` with `ThreadPoolExecutor`
3. **Bash curl**: Use curl with `-L` flag for redirects

### Step 5: Verify

Check that all files were downloaded:
- Count files matches expected number
- File sizes are > 50KB (valid images)

## Example Delegation

```
Main Agent: "Download images from digitarq reference PT/TT/CF/054 to ~/downloads/manuscript"

Delegation 1 (Browser Expert):
- Find document at digitarq.pt
- Search for "PT/TT/CF/054"
- Return document ID and full URL

Delegation 2 (Browser Expert):
- Navigate to file viewer
- Extract ALL file IDs from sidebar (138 total)

Delegation 3 (Bash/Python):
- Download all 138 images using parallel requests
- Save to ~/downloads/manuscript
```

## URL Patterns Reference

| Purpose | URL Pattern |
|---------|-------------|
| Document Details | `https://digitarq.arquivos.pt/documentDetails/{document_id}` |
| File Viewer | `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false` |
| Thumbnail | `https://digitarq.arquivos.pt/rdigital/thumb?fileId={file_id}` |
| Download (full-res) | `https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true` |

## Important Notes

- File IDs are sequential but may not be contiguous
- The sidebar shows 10 thumbnails at a time with infinite scroll
- Images are JPEG format, typically ~2000x2200 pixels
- License is CC BY-SA 4.0 (verify per document)
- Download in parallel (10-20 concurrent) for best performance