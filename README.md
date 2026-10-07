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

The skill is one folder containing `SKILL.md` (agent instructions) and `digitarq-download.py` (the downloader). Copy the whole folder into the skills directory of your agent runtime. Keep the folder name `digitarq-get`: the `name` in the `SKILL.md` YAML front matter must match the folder name.

| Runtime | Install command |
|---|---|
| Shared agent-skills convention (DeepSeek Harness, Kun, other tools) | `cp -R digitarq-get ~/.agents/skills/digitarq-get` |
| Matrix Agent | `cp -R digitarq-get ~/.minimaxagent/skills/digitarq-get` |
| Claude Code | `cp -R digitarq-get ~/.claude/skills/digitarq-get` |
| QoderWork | `mkdir -p ~/.qoderwork/skills && cp -R digitarq-get ~/.qoderwork/skills/digitarq-get` |
| Any other runtime | copy `digitarq-get/` anywhere and point the agent at `digitarq-get/SKILL.md` |

From the published repository you can also use the skills CLI:

```bash
npx skills add github.com/joaquimrcarvalho/digitarq-get
```

No installation is needed to run the downloader by hand: `python3 digitarq-download.py …` works from a clone in any directory.

### Installing for pha users

[pha](https://github.com/joaquimrcarvalho/personal-historical-archive) archives carry their own agent skills in `<archive>/skills/<name>/SKILL.md`, and pha ships an `inbox`/`dropbox` pipeline for ingesting documents. There are two ways to make this skill available to a pha agent.

**A. Into the pha archive** (recommended; any agent pointed at the archive finds it):

```bash
export PHA_ARCHIVE_DIR="${PHA_ARCHIVE_DIR:-$HOME/jesuit-archive}"   # adapt to your archive
cp -R digitarq-get "$PHA_ARCHIVE_DIR/skills/digitarq-get"
```

**B. Into the agent runtime** (shared agent-skills convention used by pha agents and other tools):

```bash
cp -R digitarq-get ~/.agents/skills/digitarq-get
```

Both can be used at once, but keep the folder name `digitarq-get`.

**Using the downloader inside a pha workflow.** pha treats one folder under `<archive>/dropbox/documents/` as one document, so downloaded page images can be ingested directly. `page_001.jpg`, `page_002.jpg`, … sort in page order.

```bash
export PHA_HOME="$HOME/develop/personal-historical-archive"   # adapt
export PHA_ARCHIVE_DIR="$HOME/jesuit-archive"                 # adapt
PHA="$PHA_HOME/.venv/bin/pha"

# 1. One folder = one document, downloaded straight into the dropbox
python3 "$PHA_ARCHIVE_DIR/skills/digitarq-get/digitarq-download.py" \
  --document-id <document_id> \
  --output-dir "$PHA_ARCHIVE_DIR/dropbox/documents/digitarq-<slug>"

# 2. Transcribe and index the new document
"$PHA" scan --path documents/digitarq-<slug>
```

To hold the download for human review before it is scanned, put it in the inbox instead, then move and scan:

```bash
mkdir -p "$PHA_ARCHIVE_DIR/inbox/collections/<collection>/digitarq-<slug>"
python3 "$PHA_ARCHIVE_DIR/skills/digitarq-get/digitarq-download.py" \
  --document-id <document_id> \
  --output-dir "$PHA_ARCHIVE_DIR/inbox/collections/<collection>/digitarq-<slug>"
"$PHA" inbox --move --path collections/<collection>/digitarq-<slug>
"$PHA" scan --path collections/<collection>/digitarq-<slug>
```

Notes:

- If you installed only into the agent runtime (option B), run the script from ~/.agents/skills/digitarq-get/digitarq-download.py instead.
- For collection-specific palaeographer/encoder rules, add or point to a `pha.yaml` in the collection folder.
- `pha scan` skips unchanged documents on re-runs; add `--reprocess` to force a full re-extraction.
- The real `PHA_HOME` and archive paths are recorded in `pha-location.md` inside the archive (also printed by `pha info`).

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
