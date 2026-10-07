#!/usr/bin/env python3
"""
Digitarq Download Script

Downloads all images from a Digitarq document in the CORRECT page order.
Page numbers follow the sidebar order returned by the public JSON API,
NOT numerical fileId order (fileIds are usually not sequential).

Usage:
    python3 digitarq-download.py --document-id <id> --output-dir <folder>

Example:
    python3 digitarq-download.py --document-id e6981fa6d437493da5b5163d586bff7e --output-dir ./download
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://digitarq.arquivos.pt"
RDIGITAL_URL = BASE_URL + "/rdigital"
DOWNLOAD_URL = BASE_URL + "/api/rdigital/dissemination"
USER_AGENT = "Mozilla/5.0"
JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF])
MIN_VALID_SIZE = 1024  # a real page is always larger than this


def _http_get(url, timeout=60, headers=None):
    """GET a URL and return the raw body bytes."""
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def extract_sidebar_fileids(document_id, page_size=1000):
    """
    Fetch the page list in sidebar order from the public Digitarq JSON API.

    Endpoint:
        GET /rdigital/{document_id}?fromIndex={start}&max={page_size}

    The response is a JSON object with keys results, total, max and fromIndex.
    The order of the results list matches the sidebar (page) order, so the
    page number is its position in that list. Paginates with total when a
    document has more pages than page_size.

    Returns a list of (page_num, file_id) tuples in page order.
    """
    file_ids = []
    from_index = 0

    while True:
        query = urllib.parse.urlencode({"fromIndex": from_index, "max": page_size})
        url = RDIGITAL_URL + "/" + urllib.parse.quote(str(document_id)) + "?" + query
        body = _http_get(url, headers={"Accept": "application/json"})
        data = json.loads(body.decode("utf-8", errors="replace"))
        results = data.get("results") or []
        if not results:
            break

        for item in results:
            file_ids.append((len(file_ids) + 1, int(item["id"])))

        total = data.get("total")
        from_index = len(file_ids)
        if total is not None and from_index >= int(total):
            break
        if len(results) < page_size:
            break

    return file_ids


def is_valid_jpeg(filepath):
    """
    Check that a file is a plausible JPEG image.

    The dissemination endpoint sometimes returns a misleading Content-Type
    (for example image/tiff for actual JPEG bytes), so check magic bytes.
    """
    try:
        if os.path.getsize(filepath) < MIN_VALID_SIZE:
            return False
        with open(filepath, "rb") as handle:
            return handle.read(len(JPEG_MAGIC)) == JPEG_MAGIC
    except OSError:
        return False


def download_image(file_id, output_dir, page_num, attempts=3):
    """Download a single page and save it as page_NNN.jpg (atomic write)."""
    filename = "page_%03d.jpg" % page_num
    filepath = os.path.join(output_dir, filename)

    # Skip when a valid file is already present
    if os.path.exists(filepath) and is_valid_jpeg(filepath):
        return (file_id, page_num, "skipped", os.path.getsize(filepath))

    url = DOWNLOAD_URL + "?fileId=" + str(file_id) + "&download=true"
    tmp_path = filepath + ".part"
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            data = _http_get(url, timeout=120)
            if not data.startswith(JPEG_MAGIC):
                raise ValueError("response is not a JPEG (starts with %r)" % data[:8])
            with open(tmp_path, "wb") as handle:
                handle.write(data)
            os.replace(tmp_path, filepath)
            return (file_id, page_num, "success", len(data))
        except Exception as exc:
            last_error = exc
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if attempt < attempts:
                time.sleep(2 ** attempt)

    return (file_id, page_num, "error: %s" % last_error, 0)


def main():
    parser = argparse.ArgumentParser(description="Download images from Digitarq")
    parser.add_argument("--document-id", required=True, help="Digitarq document ID from the URL hash")
    parser.add_argument("--output-dir", default="./digitarq-download", help="Output directory")
    parser.add_argument("--max-workers", type=int, default=10, help="Concurrent downloads")
    parser.add_argument(
        "--sidebar-mapping",
        help="Optional JSON file with a page to fileId mapping, bypassing the automatic lookup",
    )

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if args.sidebar_mapping and os.path.exists(args.sidebar_mapping):
        with open(args.sidebar_mapping) as handle:
            sidebar_mapping = json.load(handle)
        file_ids = [(int(page), int(file_id)) for page, file_id in sidebar_mapping.items()]
        file_ids.sort(key=lambda item: item[0])
        print("Loaded %d file IDs from mapping file" % len(file_ids))
    else:
        print("Fetching file list for document %s..." % args.document_id)
        try:
            file_ids = extract_sidebar_fileids(args.document_id)
        except urllib.error.HTTPError as exc:
            print("Failed to fetch file list: HTTP %s %s" % (exc.code, exc.reason))
            return 1
        except Exception as exc:
            print("Failed to fetch file list: %s" % exc)
            return 1

        if not file_ids:
            print("No file IDs found. Please provide a sidebar mapping file.")
            return 1

        print("Found %d pages (sidebar order)" % len(file_ids))

    print("Downloading to %s..." % args.output_dir)
    completed = 0
    success = 0
    skipped = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(download_image, file_id, args.output_dir, page_num): page_num
            for page_num, file_id in file_ids
        }

        for future in as_completed(futures):
            file_id, page_num, status, size = future.result()
            completed += 1

            if status == "success":
                success += 1
                print("[%d/%d] page_%03d: %d bytes" % (completed, len(file_ids), page_num, size))
            elif status == "skipped":
                skipped += 1
                print("[%d/%d] page_%03d: already valid, skipping" % (completed, len(file_ids), page_num))
            else:
                errors += 1
                print("[%d/%d] page_%03d: %s" % (completed, len(file_ids), page_num, status))

    print("")
    print("Download complete.")
    print("Success: %d, Skipped: %d, Errors: %d" % (success, skipped, errors))

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    exit(main())
