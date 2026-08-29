"""
Helper script for gzh-publish skill.
Scans HTML content for image URLs, downloads remote images into a local temporary folder,
and prepares local files for wechat_upload_img and wechat_permanent_media tool calls.
"""

import os
import re
import urllib.request
import argparse
import json

def extract_and_download_images(html_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find all img src attributes
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    matches = img_pattern.findall(html)
    
    downloaded_images = []
    for idx, src in enumerate(matches):
        if src.startswith("http://") or src.startswith("https://"):
            ext = os.path.splitext(src.split("?")[0])[1] or ".jpg"
            local_filename = f"image_{idx}{ext}"
            local_path = os.path.abspath(os.path.join(output_dir, local_filename))
            print(f"Downloading {src} -> {local_path}...")
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                req = urllib.request.Request(src, headers=headers)
                with urllib.request.urlopen(req) as resp, open(local_path, 'wb') as out_f:
                    out_f.write(resp.read())
                downloaded_images.append({
                    "original_src": src,
                    "local_path": local_path
                })
            except Exception as e:
                print(f"Error downloading {src}: {e}")
        elif os.path.exists(src):
            downloaded_images.append({
                "original_src": src,
                "local_path": os.path.abspath(src)
            })

    manifest_path = os.path.join(output_dir, "images_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(downloaded_images, f, ensure_ascii=False, indent=2)

    print(f"Downloaded/located {len(downloaded_images)} images. Manifest saved to {manifest_path}")
    return downloaded_images

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and download images from HTML for WeChat publishing.")
    parser.add_argument("html_path", help="Path to clean HTML file")
    parser.add_argument("--output-dir", default="scratch/wechat_images", help="Directory to save downloaded images")
    args = parser.parse_args()
    extract_and_download_images(args.html_path, args.output_dir)
