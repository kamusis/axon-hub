#!/usr/bin/env python3
"""
One-click remote WeChat Official Account draft publisher (gzh-publish-remote).

Architecture (Two-Part Split Custody):
- The remote whitelisted host holds ONLY the AES-encrypted SQLite database (enc:...).
- The local machine holds ONLY the decryption key in ~/.config/gzh-publish-remote/secret.key (0600).
- During publishing, this script stages images and HTML to a temporary remote directory,
  injects WECHAT_MCP_SECRET_KEY in-memory over SSH to execute WechatMcpTool
  (wechat_upload_img -> wechat_permanent_media -> wechat_draft), syncs the mmbiz-replaced
  HTML back locally, and cleans up the remote temporary directory.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import uuid
from pathlib import Path


DEFAULT_KEY_FILE = os.path.expanduser("~/.config/gzh-publish-remote/secret.key")
DEFAULT_SSH_HOST = "dev.mopheus.ai"
DEFAULT_SSH_IP = "163.44.99.140"
DEFAULT_REMOTE_MCP_ROOT = (
    "/home/moclaw-dev/.npm/_npx/5b2c752cad86da39/node_modules/wechat-official-account-mcp/dist/src"
)


def load_secret_key(key_file: str) -> str:
    """Read WECHAT_MCP_SECRET_KEY from environment or local 0600 key file."""
    env_key = os.environ.get("WECHAT_MCP_SECRET_KEY", "").strip()
    if env_key:
        return env_key
    path = Path(key_file).expanduser()
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing decryption key file: {path}. "
            "Create it with chmod 600 containing your WECHAT_MCP_SECRET_KEY."
        )
    key = path.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError(f"Decryption key file {path} is empty.")
    return key


def validate_pure_html(html_path: Path) -> str:
    """Ensure the input HTML is a pure WeChat fragment, not a full preview document."""
    if html_path.name.endswith("_预览.html"):
        raise ValueError(f"Refusing to publish preview HTML file: {html_path}. Use the pure HTML file.")
    content = html_path.read_text(encoding="utf-8")
    lower = content.lower()
    for forbidden in ("<!doctype", "<html", "<head", "<body", "<script"):
        if forbidden in lower:
            raise ValueError(
                f"HTML file {html_path} contains forbidden tag '{forbidden}'. "
                "Only pure <section> fragment HTML is allowed."
            )
    return content


def download_or_copy_image(src: str, base_dir: Path, dest_dir: Path, idx: int) -> Path:
    """Download a remote image URL or copy a local image path into dest_dir."""
    if src.startswith("http://") or src.startswith("https://"):
        clean_path = src.split("?", 1)[0]
        ext = os.path.splitext(clean_path)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
            ext = ".jpg"
        out_path = dest_dir / f"img_{idx}{ext}"
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            out_path.write_bytes(resp.read())
        return out_path

    candidate = Path(src).expanduser()
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    if not candidate.is_file():
        raise FileNotFoundError(f"Image not found locally: {src} (resolved: {candidate})")
    ext = candidate.suffix.lower() or ".jpg"
    out_path = dest_dir / f"img_{idx}{ext}"
    shutil.copy2(candidate, out_path)
    return out_path


def ensure_cover_under_limit(image_path: Path, max_bytes: int = 900_000) -> Path:
    """Compress cover image as JPEG if larger than max_bytes or in PNG/WebP format."""
    if image_path.stat().st_size <= max_bytes and image_path.suffix.lower() in (".jpg", ".jpeg"):
        return image_path
    compressed = image_path.parent / "cover_compressed.jpg"
    if shutil.which("sips"):
        subprocess.run(
            [
                "sips",
                "-s",
                "format",
                "jpeg",
                "-s",
                "formatOptions",
                "75",
                "-Z",
                "1280",
                str(image_path),
                "--out",
                str(compressed),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if compressed.is_file() and compressed.stat().st_size <= max_bytes:
            return compressed
    return image_path


def build_remote_mjs(mcp_root: str) -> str:
    """Generate the remote Node ESM script that invokes WechatMcpTool."""
    return f"""import fs from 'fs';
import path from 'path';
import {{ AuthManager }} from '{mcp_root}/auth/auth-manager.js';
import {{ WechatMcpTool }} from '{mcp_root}/mcp-tool/index.js';

async function main() {{
  const workDir = process.argv[2];
  const meta = JSON.parse(fs.readFileSync(path.join(workDir, 'meta.json'), 'utf-8'));
  let html = fs.readFileSync(path.join(workDir, 'article.html'), 'utf-8');

  const authManager = new AuthManager();
  await authManager.initialize();
  const wechatTool = new WechatMcpTool(authManager);
  wechatTool.initialize();

  const replacedImages = [];
  for (const item of meta.images) {{
    const remoteFilePath = path.join(workDir, item.filename);
    const resImg = await wechatTool.callTool('wechat_upload_img', {{ filePath: remoteFilePath }});
    const textImg = resImg.content?.[0]?.text || '';
    const matchImg = textImg.match(/图片URL:\\s*(\\S+)/);
    if (!matchImg) {{
      throw new Error(`Failed to upload content image ${{item.filename}}: ${{textImg}}`);
    }}
    const mmbizUrl = matchImg[1];
    html = html.split(item.original_src).join(mmbizUrl);
    replacedImages.push({{ originalSrc: item.original_src, mmbizUrl }});
  }}

  fs.writeFileSync(path.join(workDir, 'article_mmbiz.html'), html, 'utf-8');

  const coverFilePath = path.join(workDir, meta.coverFilename);
  const resPerm = await wechatTool.callTool('wechat_permanent_media', {{
    action: 'add',
    type: 'image',
    filePath: coverFilePath,
  }});
  const textPerm = resPerm.content?.[0]?.text || '';
  const matchPerm = textPerm.match(/素材ID:\\s*(\\S+)/);
  if (!matchPerm) {{
    throw new Error(`Failed to upload permanent cover image: ${{textPerm}}`);
  }}
  const thumbMediaId = matchPerm[1];

  const resDraft = await wechatTool.callTool('wechat_draft', {{
    action: 'add',
    articles: [
      {{
        title: meta.title,
        author: meta.author,
        digest: meta.digest,
        content: html,
        thumbMediaId,
        showCoverPic: 1,
        needOpenComment: 1,
        onlyFansCanComment: 0,
      }},
    ],
  }});
  const textDraft = resDraft.content?.[0]?.text || '';
  if (resDraft.isError) {{
    throw new Error(`Failed to create WeChat draft: ${{textDraft}}`);
  }}
  const matchDraft = textDraft.match(/草稿ID:\\s*(\\S+)/);
  const draftMediaId = matchDraft ? matchDraft[1] : textDraft.trim();

  console.log('===GZH_RESULT_JSON===');
  console.log(JSON.stringify({{
    title: meta.title,
    author: meta.author,
    digest: meta.digest,
    draftMediaId,
    thumbMediaId,
    replacedImages,
  }}));
  process.exit(0);
}}

main().catch((err) => {{
  console.error('Fatal error:', err);
  process.exit(1);
}});
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish WeChat draft via remote whitelisted host.")
    parser.add_argument("--html", required=True, help="Path to pure WeChat HTML file")
    parser.add_argument("--title", required=True, help="Article title (<= 64 chars)")
    parser.add_argument("--author", default="Kamus", help="Article author (<= 8 CJK chars)")
    parser.add_argument("--digest", required=True, help="Article digest (<= 120 chars)")
    parser.add_argument("--cover", default="", help="Optional cover image path or URL (defaults to first <img>)")
    parser.add_argument("--ssh-host", default=DEFAULT_SSH_HOST, help="SSH host alias")
    parser.add_argument("--ssh-ip", default=DEFAULT_SSH_IP, help="Explicit SSH HostName IP to bypass FakeIP")
    parser.add_argument("--key-file", default=DEFAULT_KEY_FILE, help="Local 0600 file containing WECHAT_MCP_SECRET_KEY")
    parser.add_argument("--mcp-root", default=DEFAULT_REMOTE_MCP_ROOT, help="Remote wechat-official-account-mcp dist/src path")
    args = parser.parse_args()

    if len(args.title) > 64:
        raise ValueError(f"Title length ({len(args.title)}) exceeds WeChat 64-char limit.")
    if len(args.digest) > 120:
        raise ValueError(f"Digest length ({len(args.digest)}) exceeds WeChat 120-char limit.")

    secret_key = load_secret_key(args.key_file)
    html_path = Path(args.html).expanduser().resolve()
    html = validate_pure_html(html_path)

    img_srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    unique_srcs = []
    for s in img_srcs:
        if s not in unique_srcs:
            unique_srcs.append(s)

    run_id = uuid.uuid4().hex[:10]
    remote_dir = f"/tmp/gzh_pub_{run_id}"
    ssh_opts = ["-o", f"HostName={args.ssh_ip}"] if args.ssh_ip else []

    with tempfile.TemporaryDirectory(prefix="gzh_stage_") as tmp_dir_str:
        stage_dir = Path(tmp_dir_str)
        (stage_dir / "article.html").write_text(html, encoding="utf-8")

        images_meta = []
        first_local_image = None
        for idx, src in enumerate(unique_srcs):
            if "mmbiz.qpic.cn" in src:
                continue
            local_img = download_or_copy_image(src, html_path.parent, stage_dir, idx)
            if first_local_image is None:
                first_local_image = local_img
            images_meta.append({"original_src": src, "filename": local_img.name})

        if args.cover:
            cover_local = download_or_copy_image(args.cover, html_path.parent, stage_dir, 999)
        elif first_local_image is not None:
            cover_local = first_local_image
        else:
            raise ValueError("No cover image provided via --cover and no downloadable <img> found in HTML.")

        cover_ready = ensure_cover_under_limit(cover_local)
        meta = {
            "title": args.title,
            "author": args.author,
            "digest": args.digest,
            "images": images_meta,
            "coverFilename": cover_ready.name,
        }
        (stage_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        (stage_dir / "run_publish.mjs").write_text(build_remote_mjs(args.mcp_root), encoding="utf-8")

        # 1. Upload staged directory to remote /tmp
        subprocess.run(
            ["scp", *ssh_opts, "-r", str(stage_dir), f"{args.ssh_host}:{remote_dir}"],
            check=True,
        )

        try:
            # 2. Run remote publisher with in-memory WECHAT_MCP_SECRET_KEY and fetch updated HTML
            remote_cmd = (
                f"WECHAT_MCP_SECRET_KEY='{secret_key}' "
                f"node {remote_dir}/run_publish.mjs {remote_dir}"
            )
            proc = subprocess.run(
                ["ssh", *ssh_opts, args.ssh_host, remote_cmd],
                check=True,
                capture_output=True,
                text=True,
            )
            stdout = proc.stdout
            if "===GZH_RESULT_JSON===" not in stdout:
                print(stdout)
                raise RuntimeError("Remote publisher did not emit result JSON.")

            result_json_str = stdout.split("===GZH_RESULT_JSON===", 1)[1].strip().splitlines()[0]
            result = json.loads(result_json_str)

            # 3. Sync mmbiz-replaced HTML back to local HTML path
            subprocess.run(
                ["scp", *ssh_opts, f"{args.ssh_host}:{remote_dir}/article_mmbiz.html", str(html_path)],
                check=True,
            )
        finally:
            subprocess.run(
                ["ssh", *ssh_opts, args.ssh_host, f"rm -rf {remote_dir}"],
                check=False,
            )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
