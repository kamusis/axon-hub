"""
Helper script to replace original image src with WeChat mmbiz CDN URLs in clean HTML.
"""

import os
import json
import argparse

def replace_images(html_path, upload_results_path, output_html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    with open(upload_results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # results: [{"original_src": "...", "wechat_url": "..."}, ...]
    count = 0
    for item in results:
        orig = item.get("original_src")
        wechat_url = item.get("wechat_url")
        if orig and wechat_url and orig in html:
            html = html.replace(orig, wechat_url)
            count += 1
            print(f"Replaced: {orig} -> {wechat_url}")

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Replaced {count} image URLs. Output written to {output_html_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replace image URLs in HTML with WeChat CDN URLs.")
    parser.add_argument("html_path", help="Path to clean HTML file")
    parser.add_argument("upload_results_path", help="Path to JSON file containing original_src and wechat_url mapping")
    parser.add_argument("output_html_path", help="Path to write the updated HTML file")
    args = parser.parse_args()
    replace_images(args.html_path, args.upload_results_path, args.output_html_path)
