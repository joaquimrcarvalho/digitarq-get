#!/usr/bin/env python3
"""
Digitarq Download Script

Downloads all images from a Digitarq document by extracting file IDs from the file viewer.

Usage:
    python3 digitarq-download.py --document-id <id> --output-dir <folder>
    
    python3 digitarq-download.py --document-id e6981fa6d437493da5b5163d586bff7e --output-dir ./download
"""

import argparse
import urllib.request
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import URLError, HTTPError

BASE_URL = "https://digitarq.arquivos.pt"
THUMB_URL = f"{BASE_URL}/rdigital/thumb?fileId="
DOWNLOAD_URL = f"{BASE_URL}/api/rdigital/dissemination"
FILEVIEWER_URL = f"{BASE_URL}/fileViewer"

def extract_file_ids_from_html(html_content):
    """Extract file IDs from HTML content by finding thumb URLs."""
    import re
    pattern = r'fileId=(\d+)'
    matches = re.findall(pattern, html_content)
    return list(set(int(m) for m in matches))

def get_file_ids_via_api(document_id):
    """Get all file IDs for a document via the file viewer page."""
    import urllib.request
    
    url = f"{FILEVIEWER_URL}/{document_id}?isRepresentation=false"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Extract file IDs from HTML
        import re
        pattern = r'fileId=(\d+)'
        matches = re.findall(pattern, html)
        
        # Try to find total pages from the sidebar
        page_match = re.search(r'Navegar:\s*</span>\s*<span[^>]*>(\d+)', html)
        total_pages = int(page_match.group(1)) if page_match else len(set(matches))
        
        file_ids = sorted(set(int(m) for m in matches))
        
        return file_ids, total_pages
        
    except Exception as e:
        print(f"Error fetching file viewer: {e}")
        return [], 0

def download_image(file_id, output_dir, page_num):
    """Download a single image and save it."""
    filename = f"page_{page_num:03d}.jpg"
    filepath = os.path.join(output_dir, filename)
    
    # Skip if already exists and valid size
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        if size > 50000:
            return (file_id, "skipped", 0)
    
    url = f"{DOWNLOAD_URL}?fileId={file_id}&download=true"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
            with open(filepath, 'wb') as f:
                f.write(data)
        return (file_id, "success", len(data))
    except Exception as e:
        return (file_id, f"error: {e}", 0)

def main():
    parser = argparse.ArgumentParser(description='Download images from Digitarq')
    parser.add_argument('--document-id', required=True, help='Digitarq document ID (from URL hash)')
    parser.add_argument('--output-dir', default='./digitarq-download', help='Output directory')
    parser.add_argument('--max-workers', type=int, default=10, help='Concurrent downloads')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Fetching file IDs for document {args.document_id}...")
    file_ids, total_pages = get_file_ids_via_api(args.document_id)
    
    if not file_ids:
        print("No file IDs found. Please check the document ID.")
        return 1
    
    print(f"Found {len(file_ids)} images (reported {total_pages} pages)")
    
    # Download in parallel
    print(f"Downloading to {args.output_dir}...")
    completed = 0
    success = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {}
        
        # Map file IDs to page numbers (sorted by ID for consistency)
        sorted_ids = sorted(file_ids)
        for i, file_id in enumerate(sorted_ids):
            page_num = i + 1
            future = executor.submit(download_image, file_id, args.output_dir, page_num)
            futures[future] = (file_id, page_num)
        
        for future in as_completed(futures):
            file_id, status, size = future.result()
            completed += 1
            
            if status == "success":
                success += 1
                print(f"[{completed}/{len(file_ids)}] page_{file_id}: {size} bytes")
            elif status == "skipped":
                print(f"[{completed}/{len(file_ids)}] Already exists, skipping")
            else:
                errors += 1
                print(f"[{completed}/{len(file_ids)}] Error: {status}")
    
    print(f"\nDownload complete!")
    print(f"Success: {success}, Errors: {errors}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    exit(main())