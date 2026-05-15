# Digitarq Download

Downloads high resolution images from the Portuguese Archives digital library (Digitarq).

## Overview

This skill enables AI agents to download digital documents and images from the Portuguese National Archives (Arquivo Nacional da Torre do Tombo) via the Digitarq platform.

## Features

- Download full-resolution images from any Digitarq document
- Support for both direct URLs and archive reference codes
- Parallel downloading for speed
- Automatic file ID extraction from file viewer pages

## Usage

### For Matrix Agent Users

Install the skill:
```bash
cp -r digitarq-get ~/.minimaxagent/skills/
```

Then ask to download:
```
Download images from digitarq reference PT/TT/CF/054 to ./my-folder
```

### For Main Agents (Delegation)

When the user requests a Digitarq download:

1. **Browser Expert** - Find document and extract file IDs
2. **Bash** - Download images using the API

#### Step 1: Find Document

Navigate to `https://digitarq.arquivos.pt` and search for the reference code.

Get the document ID from the URL: `/documentDetails/{document_id}`

#### Step 2: Extract File IDs

Navigate to: `https://digitarq.arquivos.pt/fileViewer/{document_id}?isRepresentation=false`

Extract all `fileId` values from thumbnail URLs in the sidebar.

#### Step 3: Download

Download images using the API endpoint:
```
https://digitarq.arquivos.pt/api/rdigital/dissemination?fileId={file_id}&download=true
```

### Command Line Usage

```bash
python3 digitarq-download.py --document-id <id> --output-dir <folder>
```

## Requirements

- Python 3.6+
- Internet connection to digitarq.arquivos.pt

## License

CC BY-SA 4.0 - Portuguese Archives Digital Library

See [LICENSE](LICENSE) for details.