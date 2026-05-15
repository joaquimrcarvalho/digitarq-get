# Sub-Agent Instructions

## Browser Expert

### Find Document by Reference

When given a reference code like `PT/TT/CF/054`:

1. Navigate to `https://digitarq.arquivos.pt`
2. Use the search function to find the reference
3. Get document ID from URL: `/documentDetails/{document_id}`
4. Return the full document URL

### Extract File IDs

1. Navigate to: `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false`
2. Look at the sidebar showing thumbnails (10 per view)
3. Extract all `fileId` values from thumbnail URLs
4. The sidebar has infinite scroll - scroll down to load more thumbnails
5. Collect ALL file IDs until all pages are loaded
6. Return the complete list sorted

### Important

- The sidebar loads thumbnails on demand
- Scroll down continuously to trigger loading of remaining thumbnails
- Each thumbnail contains `fileId={number}` in its image src URL
- Don't stop until you've found all file IDs

## Bash/Python Download Agent

### Download Images

After receiving file IDs from Browser Expert:

1. Create output directory
2. Download images in parallel using the API:
   ```
   https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
   ```
3. Save as `page_{page_num:03d}.jpg`

### Verify Downloads

- Check file count matches expected
- Verify file sizes > 50KB
- Report any errors

## File ID Pattern

File IDs are typically sequential numbers. Example from PT/TT/CF/054:
- Total pages: 138
- File ID range: 12175615 to 12175752

The exact pattern depends on the document. Always extract from the actual page.