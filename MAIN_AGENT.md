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

### Step 3: Extract File IDs from Sidebar (CRITICAL STEP)

Note: the included script fetches this ordered list automatically from `/rdigital/{document_id}`. The browser workflow below is the fallback.

1. Navigate to: `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false`
2. **CRITICAL**: The sidebar shows pages 1, 2, 3... in ORDER. This is the correct page order.
3. Each thumbnail has a `fileId` value. Extract all file IDs IN SIDEBAR ORDER.
4. Navigate to different positions (page 10, page 30, page 50, etc.) to get all file IDs
5. The sidebar only shows ~10 thumbnails at a time, so scroll/navigate to collect all

### Step 4: Download Images

**CRITICAL MAPPING**: 
- page_001.jpg = fileId from sidebar page 1
- page_002.jpg = fileId from sidebar page 2
- etc.

Download URL:
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

Use the default 10 concurrent downloads (hard cap 20). Run one download job at a time and back off on errors - Digitarq is a public service (see README, Server etiquette).

### Step 5: Verify

Check that:
- Page numbers match sidebar order, NOT file ID order
- File count matches expected (check "Navegar: /138" for total pages)
- File sizes are reasonable (> 50KB)

## Common Mistakes to Avoid

### WRONG: Using sorted file IDs as page numbers
```python
# WRONG - file IDs may be non-sequential
file_ids = sorted(all_file_ids)  
for i, fid in enumerate(file_ids):
    save as page_{i}.jpg  # WRONG page order!
```

### CORRECT: Using sidebar order as page numbers
```python
# CORRECT - sidebar order IS page order
for sidebar_position, file_id in enumerate(sidebar_file_ids):
    save as page_{sidebar_position + 1}.jpg  # CORRECT!
```

## Example

For document e6981fa6d437493da5b5163d586bff7e:

| Sidebar Position | fileId | Save As |
|-----------------|--------|---------|
| 1 | 12175626 | page_001.jpg |
| 2 | 12175625 | page_002.jpg |
| 3 | 12175624 | page_003.jpg |
| ... | ... | ... |
| 138 | 12175752 | page_138.jpg |

The fileIds are NOT sequential but the sidebar position IS the page number.
