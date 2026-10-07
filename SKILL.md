# Digitarq Download Skill

Downloads high resolution images from the Portuguese Archives digital library (Digitarq).

## When to Use

When the user wants to download images from a digital document hosted on:
- https://digitarq.arquivos.pt/documentDetails/{id}
- https://digitarq.arquivos.pt/fileViewer/{id}

## How It Works

1. **Fetch document metadata**: Access the document details page to get the document ID
2. **Get file list**: Query the public JSON API (`/rdigital/{document_id}`) or parse the file viewer sidebar
3. **Download images**: Use the API endpoint to download full-resolution images in parallel

## IMPORTANT: Sidebar Order vs File ID Order

**CRITICAL**: Page numbers in Digitarq correspond to the sidebar order (top to bottom), NOT numerical file ID order.

The sidebar shows pages labeled 1, 2, 3... in order from top to bottom. Each page has a `fileId` that may NOT be sequential or in numerical order.

Example (document e6981fa6d437493da5b5163d586bff7e):
| Sidebar Page | fileId |
|-------------|--------|
| 1 | 12175626 |
| 2 | 12175625 |
| 3 | 12175624 |
| ... | ... |
| 138 | 12175752 |

## Usage

### Download all images from a document

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

**Public page list API (JSON):** https://digitarq.arquivos.pt/rdigital/{document_id}?fromIndex=0&max=1000

**Full Resolution Download URL:**
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

### Workflow

1. Extract `document_id` from URL (the hash in the URL)
2. Navigate to the file viewer: `/fileViewer/{document_id}?isRepresentation=false`
3. **Extract file IDs from sidebar in order** - each thumbnail shows a page number and has `fileId=` in its image URL
4. Download images mapping sidebar page number -> file ID

### File ID Extraction

The sidebar shows thumbnails with page numbers (1, 2, 3...) and each has a fileId:
```
/rdigital/thumb?fileId={file_id}
```

**CRITICAL**: The sidebar order is the CORRECT page order. File IDs may jump around.

Navigate to different pages in the file viewer to extract all file IDs. The sidebar updates to show surrounding pages.

### Image Format

- Format: JPEG
- Resolution: ~2000x2200 pixels (varies by document)
- License: CC BY-SA 4.0 (check specific document)
- Naming: Save as `page_{page_num:03d}.jpg`

## Common Issues

### Wrong Page Order
If downloaded images don't match the document's page order:
- The sidebar order IS the correct order
- File IDs are NOT sequential and do NOT correspond to page numbers
- Always extract file IDs from the sidebar in the order they appear

### Missing Pages
Some file IDs may be missing (document has scanned pages, not all numbers exist).
Always verify by checking the sidebar shows "Navegar: /138" (138 pages total).

## Implementation Notes

- Download images in parallel batches (10-20 concurrent) for speed
- File IDs are NOT sequential - always use sidebar order
- Verify downloads by checking file size (> 100KB typically)
- Create output directory before downloading
- Use proper page numbering based on sidebar position, not file ID
