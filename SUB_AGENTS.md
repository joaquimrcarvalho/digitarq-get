# Sub-Agent Instructions

## Browser Expert

### Find Document by Reference

When given a reference code like `PT/TT/CF/054`:

1. Navigate to `https://digitarq.arquivos.pt`
2. Use the search function to find the reference
3. Get document ID from URL: `/documentDetails/{document_id}`
4. Return the full document URL

### Extract File IDs from Sidebar (CRITICAL)

Note: the included download script fetches this ordered list automatically from the public JSON API; use this browser workflow when running without the script.

1. Navigate to: `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false`
2. Look at the sidebar - it shows thumbnails labeled 1, 2, 3... up to total pages
3. **The sidebar order is the CORRECT page order**
4. Extract the `fileId` from each thumbnail's image URL: `/rdigital/thumb?fileId={file_id}`
5. **Navigate to different positions** (by clicking thumbnails or using selectedFile parameter) to see more thumbnails
6. Collect ALL file IDs in sidebar order (page 1 to page N)

The sidebar typically shows ~10 thumbnails at a time. Navigate to get them all.

### Important Notes

- **Sidebar order = Page number order**
- File IDs may jump around (not sequential)
- Check "Navegar: /138" to confirm total pages
- Always extract file IDs in the order they appear in sidebar

## Bash/Python Download Agent

### Download Images

After receiving file IDs from Browser Expert in sidebar order:

1. Create output directory
2. Download using CORRECT mapping:
   ```python
   # sidebar_order_fileids = [fid1, fid2, fid3, ...]  # from sidebar, page 1 to N
   
   for page_num, file_id in enumerate(sidebar_order_fileids, start=1):
       filename = f"page_{page_num:03d}.jpg"
       # Download fileId to filename
   ```

3. Download URL:
   ```
   https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
   ```

### Verify Downloads

- Count files matches sidebar page count
- Verify file sizes > 50KB
- Report any errors

## Example Mapping

For document with 138 pages, sidebar shows:
```
Page 1: fileId=12175626  -> page_001.jpg
Page 2: fileId=12175625  -> page_002.jpg
Page 3: fileId=12175624  -> page_003.jpg
...
Page 138: fileId=12175752 -> page_138.jpg
```

Note: fileIds decrease initially (12175626, 12175625, ...) then may jump to different ranges.
