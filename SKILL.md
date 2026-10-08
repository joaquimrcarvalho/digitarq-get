---
name: digitarq-get
description: Download full-resolution page images from Digitarq (Arquivo Nacional da Torre do Tombo / Portuguese National Archives) for a document ID or archive reference, preserving sidebar/page order. Use when the user wants to download, fetch, or ingest a Digitarq document, manuscript, or reference code (for example PT/TT/AJCJ/AJ028) as JPEG page images.
license: MIT
---

# Digitarq Download Skill

Downloads high-resolution images from the Portuguese Archives digital library (Digitarq).

## When to Use

When the user wants to download images from a digital document hosted on:
- https://digitarq.arquivos.pt/documentDetails/{id}
- https://digitarq.arquivos.pt/fileViewer/{id}
- or identified by an archive reference such as PT/TT/AJCJ/AJ028

## How It Works

1. **Resolve the document ID**: the hash in `/documentDetails/{document_id}`. When the user gives an archive reference code, use the public search API: `GET /api/docs/search?query={reference}&max=5`. Each result has `id` (the document ID), `referenceCode.value`, `presentQuota.value` and `filesCount`; the script does this automatically with `--reference`. A browser search is only the fallback.
2. **Get the ordered page list**: query the public JSON API `GET /rdigital/{document_id}?fromIndex=0&max=1000`. The `results` array is already in sidebar/page order; `total` is the page count (paginate when there are more pages than `max`).
3. **Download images**: fetch every page from the dissemination endpoint in parallel — default 10 workers, never more than 20 — validating JPEG magic bytes and writing atomically.
4. **Page numbering**: use the position of a page in the API `results` list — never the numeric `fileId`.

The bundled script `digitarq-download.py` performs all four steps.

## IMPORTANT: Sidebar Order vs File ID Order

**CRITICAL**: Page numbers in Digitarq correspond to the sidebar order (top to bottom), NOT numerical file ID order.

Each page has a `fileId` that may NOT be sequential or in numerical order.

Example (document e6981fa6d437493da5b5163d586bff7e):
| Sidebar Page | fileId |
|-------------|--------|
| 1 | 12175626 |
| 2 | 12175625 |
| 3 | 12175624 |
| ... | ... |
| 138 | 12175752 |

## Usage

Run the bundled script from the skill folder:

```bash
python3 digitarq-download.py --document-id <document_id> --output-dir ./my-manuscript-folder
python3 digitarq-download.py --reference PT/AHU/CU/064/0024/00064 --output-dir ./PT-AHU-CU-064-0024-00064
```

Agent requests that resolve to this skill:

```
Download images from https://digitarq.arquivos.pt/documentDetails/<id>
Download images from digitarq reference PT/TT/AJCJ/AJ028
Download images from digitarq to ./my-manuscript-folder
```

Useful options:
- `--max-workers 10` — concurrent downloads (default 10, hard cap 20; higher values are capped with a warning)
- `--reference PT/AHU/CU/064/0024/00064` - resolve an archive reference to a document ID first (public search API)
- `--sidebar-mapping mapping.json` — escape hatch with page→fileId pairs (`{"1": 12175626, "2": 12175625}`)
- Re-running is safe: valid pages already in the output folder are skipped.

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

**Document search API (JSON, resolves a reference):**
```
https://digitarq.arquivos.pt/api/docs/search?query={reference}&max=5
```

**Public page list API (JSON):**
```
https://digitarq.arquivos.pt/rdigital/{document_id}?fromIndex=0&max=1000
```

**Full-resolution download URL:**
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

### Workflow

1. Extract `document_id` from the URL (the hash in the URL)
2. Fetch the ordered list: `GET /rdigital/{document_id}?fromIndex=0&max=1000`
3. Download each page: `GET /api/rdigital/dissemination?fileId={file_id}&download=true`
4. Save as `page_{page_num:03d}.jpg`, numbering by position in the API list

### File ID Extraction

The public JSON API returns, for example:

```json
{
  "results": [
    {"id": "12175626", "name": "PT-TT-CF-054_m0001.jpg"},
    {"id": "12175625", "name": "PT-TT-CF-054_m0002.jpg"}
  ],
  "total": 138
}
```

`id` is the `fileId`; the array order is the page order. The internal route `/api/rdigital/files/{document_id}` returns `401 Unauthorized` and must not be used.

Browser fallback (only when the API is unavailable): open `/fileViewer/{document_id}?isRepresentation=false` and read the sidebar thumbnails in order; each thumbnail URL contains `/rdigital/thumb?fileId={file_id}`.

### Image Format

- Format: JPEG (the `Content-Type` header can be misleading; trust the magic bytes)
- Resolution: ~1400–2000+ px per side (varies by document)
- License: CC BY-SA 4.0 (check the specific document)
- Naming: `page_{page_num:03d}.jpg`

## Common Issues

### Wrong Page Order

If downloaded images do not match the document's page order:
- You sorted or numbered by `fileId`; use the API/sidebar order instead
- File IDs are NOT sequential and do NOT correspond to page numbers

### Missing Pages

Use `total` from the JSON API — it is authoritative. A gap in `fileId` numbers does not mean a missing page (IDs are not sequential; some pages may be blank scans).

## Implementation Notes

- Download with the default 10 concurrent workers; never exceed the hard cap of 20
- One document at a time; do not start several downloads in parallel against Digitarq
- Never sort by `fileId`; always preserve the API/sidebar order
- Validate JPEG magic bytes and skip already-valid pages on re-runs
- Verify the downloaded count against the API `total`

## Server etiquette (be a good netizen)

Digitarq is a public service. Keep it healthy for other users:

- Use the defaults (10 workers); the script caps `--max-workers` at 20 and warns above that.
- Run one download job at a time, especially for large documents (hundreds of pages).
- On timeouts, `429` or `5xx`, stop and re-run later with fewer workers; every page already retries 3 times with exponential backoff.
- Fetch only the document the user asked for; never crawl or bulk-harvest the catalogue.
- Keep the honest `digitarq-get/1.0` User-Agent sent by the script.
- For a big job, tell the user roughly how long it will take instead of starting parallel downloads.

## Using with pha

Inside a pha archive, one folder under `<archive>/dropbox/documents/` is one document, so the download can be ingested directly:

```bash
python3 digitarq-download.py \
  --document-id <document_id> \
  --output-dir "$PHA_ARCHIVE_DIR/dropbox/documents/digitarq-<slug>"

"$PHA_HOME/.venv/bin/pha" scan --path documents/digitarq-<slug>
```

`page_001.jpg`, `page_002.jpg`, … sort in page order. To hold the download for human review first, download into `$PHA_ARCHIVE_DIR/inbox/collections/<collection>/digitarq-<slug>/`, then run `pha inbox --move` and `pha scan`. See the README for installation into a pha archive and full details.
