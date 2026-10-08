#!/usr/bin/env python3
"""
Digitarq Download Script

Downloads all images from a Digitarq document in the CORRECT page order.
Page numbers follow the sidebar order returned by the public JSON API,
NOT numerical fileId order (fileIds are usually not sequential).

Usage:
    python3 digitarq-download.py --document-id <id> --output-dir <folder>
    python3 digitarq-download.py --reference PT/AHU/CU/064/0024/00064 --output-dir <folder>

Example:
    python3 digitarq-download.py --document-id e6981fa6d437493da5b5163d586bff7e --output-dir ./download
    python3 digitarq-download.py --reference PT/AHU/CU/064/0024/00064 --output-dir ./PT-AHU-CU-064-0024-00064
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
SEARCH_URL = BASE_URL + "/api/docs/search"
RDIGITAL_URL = BASE_URL + "/rdigital"
DOWNLOAD_URL = BASE_URL + "/api/rdigital/dissemination"
USER_AGENT = "Mozilla/5.0 (compatible; digitarq-get/1.0; +https://github.com/joaquimrcarvalho/digitarq-get)"
JPEG_MAGIC = bytes([0xFF, 0xD8, 0xFF])
MIN_VALID_SIZE = 1024  # a real page is always larger than this

DEFAULT_WORKERS = 10
MAX_WORKERS = 20


def _http_get(url, timeout=60, headers=None):
    """GET a URL and return the raw body bytes."""
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def resolve_reference(reference, max_results=10):
    """
    Resolve an archive reference to a Digitarq document ID via the public
    document search API.

    Endpoint:
        GET /api/docs/search?query={reference}&max={max_results}

    Each result carries:
        id                     -> document ID for /documentDetails/{id} and /rdigital/{id}
        referenceCode.value    -> exact archive reference
        descriptionLevel.value -> e.g. DC (documento composto)
        titles[].value         -> document title
        presentQuota.value     -> e.g. "AHU_CU_MOCAMBIQUE, Cx. 24, D. 64"
        filesCount             -> number of images

    Returns (document_id, record). Raises ValueError when the reference is not
    found or does not match any result exactly.
    """
    query = urllib.parse.urlencode({"query": reference, "max": max_results})
    body = _http_get(SEARCH_URL + "?" + query, headers={"Accept": "application/json"})
    data = json.loads(body.decode("utf-8", errors="replace"))
    results = data.get("results") or []
    if not results:
        raise ValueError("no document found for reference %r" % reference)

    wanted = reference.strip().upper()
    for item in results:
        code = ((item.get("referenceCode") or {}).get("value") or "").strip().upper()
        if code == wanted:
            return item["id"], item
    if len(results) == 1:
        return results[0]["id"], results[0]

    codes = [((r.get("referenceCode") or {}).get("value") or "?") for r in results[:5]]
    raise ValueError(
        "reference %r not matched exactly; top results: %s" % (reference, ", ".join(codes))
    )


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


def describe_reference(record, fallback):
    """One-line summary of a search record, used in the console output."""
    code = ((record.get("referenceCode") or {}).get("value")) or fallback
    quota = (record.get("presentQuota") or {}).get("value") or ""
    parts = [code]
    if quota:
        parts.append(quota)
    return " | ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Download images from Digitarq")
    parser.add_argument("--document-id", help="Digitarq document ID (hash in a /documentDetails/ or /fileViewer/ URL)")
    parser.add_argument("--reference", help="Archive reference to resolve first, e.g. PT/AHU/CU/064/0024/00064")
    parser.add_argument("--output-dir", default="./digitarq-download", help="Output directory")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_WORKERS, help="Concurrent downloads, 1-%d (default %d). Keep it low to avoid overloading the server" % (MAX_WORKERS, DEFAULT_WORKERS))
    parser.add_argument(
        "--sidebar-mapping",
        help="Optional JSON file with a page to fileId mapping, bypassing the automatic lookup",
    )

    args = parser.parse_args()

    if args.document_id and args.reference:
        parser.error("use either --document-id or --reference, not both")
    if not args.sidebar_mapping and not (args.document_id or args.reference):
        parser.error("provide --document-id, --reference or --sidebar-mapping")

    if args.max_workers < 1:
        parser.error("--max-workers must be at least 1")
    if args.max_workers > MAX_WORKERS:
        print("Capping --max-workers at %d to avoid overloading Digitarq (requested %d)." % (MAX_WORKERS, args.max_workers))
        args.max_workers = MAX_WORKERS

    if args.sidebar_mapping and not os.path.exists(args.sidebar_mapping):
        print("Sidebar mapping file not found: %s" % args.sidebar_mapping)
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    if args.sidebar_mapping and os.path.exists(args.sidebar_mapping):
        with open(args.sidebar_mapping) as handle:
            sidebar_mapping = json.load(handle)
        file_ids = [(int(page), int(file_id)) for page, file_id in sidebar_mapping.items()]
        file_ids.sort(key=lambda item: item[0])
        print("Loaded %d file IDs from mapping file" % len(file_ids))
    else:
        document_id = args.document_id
        expected_files = None

        if args.reference:
            print("Resolving reference %s..." % args.reference)
            try:
                document_id, record = resolve_reference(args.reference)
            except urllib.error.HTTPError as exc:
                print("Failed to resolve reference: HTTP %s %s" % (exc.code, exc.reason))
                return 1
            except Exception as exc:
                print("Failed to resolve reference: %s" % exc)
                return 1

            expected_files = record.get("filesCount")
            print("Resolved to document %s (%s)" % (document_id, describe_reference(record, args.reference)))
            if expected_files is not None:
                print("  search reports %s image(s)" % expected_files)

        print("Fetching file list for document %s..." % document_id)
        try:
            file_ids = extract_sidebar_fileids(document_id)
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
        if expected_files is not None and int(expected_files) != len(file_ids):
            print("Warning: search reports %s image(s) but the page list has %d; check the reference." % (expected_files, len(file_ids)))

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
