#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import json

def upload_image(file_path, api_token):
    # Added is_private=0 to ensure the link is publicly accessible
    url = "https://s.ee/api/v1/file/upload?is_private=0"
    
    try:
        with open(file_path, "rb") as file:
            files = {"file": file}
            headers = {
                "Authorization": api_token,
                "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
            }
            
            print(f"Uploading {file_path} to {url}...")
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code != 200:
                print(f"Upload failed with status {response.status_code}")
                try:
                    err_data = response.json()
                    print(f"Error details: {err_data.get('message', 'No message')}")
                except:
                    print(f"Response text: {response.text}")
                sys.exit(1)
            
            result = response.json()
            if result.get("code") not in [0, 200]:
                print(f"Error: {result.get('message', 'Unknown error')}")
                sys.exit(1)
                
            img_data = result.get("data", {})
            direct_url = img_data.get("url")
            delete_url = img_data.get("delete", "N/A")
            filename = img_data.get("filename", "image")
            
            # Print mandatory OpenClaw media tag
            print(f"MEDIA: {direct_url}")
            
            print(f"🖼️ **S.EE Upload Success**")
            print(f"🔗 **Direct**: {direct_url}")
            print(f"🗑️  **Delete**: {delete_url}")
            print(f"")
            print(f"**Markdown**:")
            print(f"```markdown")
            print(f"![{filename}]({direct_url})")
            print(f"```")
            print(f"**HTML**:")
            print(f"```html")
            print(f"<img src=\"{direct_url}\" alt=\"{filename}\">")
            print(f"```")

    except Exception as e:
        print(f"Upload failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload image to S.EE")
    parser.add_argument("--file", required=True, help="Path to image file")
    args = parser.parse_args()
    
    token = os.environ.get("SEE_API_TOKEN")
    if not token:
        print("Error: SEE_API_TOKEN environment variable not set.")
        sys.exit(1)
        
    upload_image(args.file, token)
