# Digitarq Download

Downloads high-resolution images from the Portuguese Archives digital library (Digitarq / Arquivo Nacional da Torre do Tombo).

## Overview

This skill enables AI agents (and humans) to download scanned documents from [digitarq.arquivos.pt](https://digitarq.arquivos.pt). Given a document ID, it retrieves the ordered page list and downloads every page as a full-resolution JPEG.

## ⚠️ Important: sidebar order, not fileId order

**Page numbers correspond to the sidebar order (top to bottom), NOT numerical `fileId` order.**

Each page has a `fileId` that may be non-sequential (and often decreases). The public JSON API returns the page list already in sidebar order, so the page number is the position in that list — never sort by `fileId`.

Worked example for document `e6981fa6d437493da5b5163d586bff7e`:

| Sidebar page | fileId | Saved as |
|---|---|---|
| 1 | 12175626 | page_001.jpg |
| 2 | 12175625 | page_002.jpg |
| 3 | 12175624 | page_003.jpg |
| ... | ... | ... |
| 138 | 12175752 | page_138.jpg |

## Features

- Automatic page-list retrieval via the public JSON API (`/rdigital/{document_id}`), already in sidebar order
- Full-resolution JPEG downloads (typically ~1400–2000+ px per side)
- Parallel downloads (default 10 workers)
- Resumable: valid pages already on disk are skipped on re-runs
- Robust: JPEG magic-byte validation, atomic writes and retries (3 attempts with backoff)
- Pagination-aware: handles documents with more than 1000 pages
- Optional `--sidebar-mapping` escape hatch for manually supplied page→fileId JSON

## Requirements

- Python 3.6+
- Internet access to `digitarq.arquivos.pt`

## Installation

Copy this folder into your agent skills directory:

```bash
cp -r digitarq-get ~/.minimaxagent/skills/
```

## Usage

### Command line

```bash
python3 digitarq-download.py --document-id <document_id> --output-dir <folder>
```

Example:

```bash
python3 digitarq-download.py \
  --document-id e6981fa6d437493da5b5163d586bff7e \
  --output-dir ./PT-TT-CF-054
```

Output files are named `page_001.jpg`, `page_002.jpg`, ... in sidebar/page order.

Options:

| Option | Default | Description |
|---|---|---|
| `--document-id` | required | Document ID (hash in `/documentDetails/{id}` or `/fileViewer/{id}`) |
| `--output-dir` | `./digitarq-download` | Destination folder |
| `--max-workers` | `10` | Concurrent downloads |
| `--sidebar-mapping` | – | JSON file `{"1": 12175626, "2": 12175625}`, bypasses the automatic lookup |

### Agent workflow

```
Download images from digitarq reference PT/TT/CF/054 to ./my-folder
```

If the user supplies an archive reference code (e.g. `PT/TT/CF/054`) instead of a document ID, the agent must first resolve it to a `documentDetails` URL (see `SUB_AGENTS.md`), then run the download. Direct `documentDetails`/`fileViewer` URLs can be used as-is: the hash in the URL is the document ID.

## How it works

1. **Resolve the document ID** — the hash in `https://digitarq.arquivos.pt/documentDetails/{document_id}`.
2. **Get the ordered page list** — `GET https://digitarq.arquivos.pt/rdigital/{document_id}?fromIndex=0&max=1000`. The JSON `results` array is in sidebar order; `total` is the page count, used to paginate when needed.
3. **Download each page** — `GET https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true`, in parallel.
4. **Verify while writing** — the response must start with the JPEG magic bytes; files are written to `.part` and atomically renamed.
5. **Resume-friendly** — pages already present and valid are skipped on re-runs.

### API endpoints used

| Purpose | URL |
|---|---|
| Document details (HTML) | `https://digitarq.arquivos.pt/documentDetails/{document_id}` |
| File viewer (HTML, SPA) | `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false` |
| Ordered page list (JSON) | `https://digitarq.arquivos.pt/rdigital/{document_id}?fromIndex=0&max=1000` |
| Full-resolution image | `https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true` |

Note: `/api/rdigital/files/{document_id}` is an internal route that returns `401 Unauthorized`; use `/rdigital/{document_id}` instead.

## Verification

```bash
ls ./my-folder | wc -l        # file count should match the page total
file ./my-folder/page_001.jpg    # should be "JPEG image data"
```

## Troubleshooting

- **Wrong page order** — you sorted or numbered by `fileId`. Always use the order returned by the API (sidebar order).
- **`No file IDs found`** — the document ID may be wrong, or the API changed; use `--sidebar-mapping` as a temporary workaround.
- **Missing pages** — the API `total` is authoritative; a gap in `fileId` numbers does not mean a missing page (IDs are not sequential).
- **HTTP 401** — you are calling an internal endpoint (`/api/rdigital/files/...`). Use the public `/rdigital/{document_id}`.
- **Misleading `Content-Type`** — the dissemination endpoint sometimes reports `image/tiff` while returning JPEG bytes; trust the magic bytes.

## License

- **Code**: MIT — see [LICENSE](LICENSE).
- **Archival images**: © Arquivo Nacional da Torre do Tombo / Digitarq, distributed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); verify the license of each document before reuse.
