# Digitarq Download

Downloads high resolution images from the Portuguese Archives digital library (Digitarq).

## Overview

This skill enables AI agents to download digital documents and images from the Portuguese National Archives (Arquivo Nacional da Torre do Tombo) via the Digitarq platform.

## ⚠️ Important: Sidebar Order Matters

**The page numbers in Digitarq correspond to the sidebar order (top to bottom), NOT numerical file ID order.**

The sidebar shows pages labeled 1, 2, 3... in sequence. Each page has a `fileId` value that may NOT be sequential. Always extract file IDs from the sidebar in the order they appear.

## Features

- Download full-resolution images from any Digitarq document
- Support for both direct URLs and archive reference codes
- Parallel downloading for speed
- Automatic page-list retrieval via the public JSON API (in correct sidebar order)

## Installation

For Matrix Agent, copy this folder to your skills directory:
```bash
cp -r digitarq-get ~/.minimaxagent/skills/
```

## Usage

### Request a Download

```
Download images from digitarq reference PT/TT/CF/054 to ./my-folder
```

### Command Line

```bash
python3 digitarq-download.py --document-id <id> --output-dir <folder>
```

## How It Works

1. **Find document**: Navigate to Digitarq and locate the document
2. **Get page list**: Query the public JSON API (`/rdigital/{document_id}`) for the ordered fileId list
3. **Download**: Fetch images using the download API

### Sidebar Order Mapping

The file viewer shows thumbnails in the sidebar. The order (top to bottom) IS the correct page order.

| Sidebar Position | fileId | Save As |
|-----------------|--------|---------|
| 1 | 12175626 | page_001.jpg |
| 2 | 12175625 | page_002.jpg |
| ... | ... | ... |
| N | XXXXXX | page_NNN.jpg |

## Requirements

- Python 3.6+
- Internet connection to digitarq.arquivos.pt

## License

MIT License - See [LICENSE](LICENSE) for details.
