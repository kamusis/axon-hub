#!/usr/bin/env python3
"""
一键微信公众号草稿直发脚本 (gzh-publish: publish_wechat.py)
直接读取环境变量 WECHAT_PUB_APPID 与 WECHAT_PUB_APPSECRET，
自动完成正文配图转存微信 CDN、封面素材注册与公众号草稿箱推送。
"""

import os
import sys
import json
import argparse
import mimetypes
import tempfile
import urllib.request
import urllib.parse
import re
from pathlib import Path

def get_env_credentials():
    appid = os.environ.get("WECHAT_PUB_APPID", "").strip()
    secret = os.environ.get("WECHAT_PUB_APPSECRET", "").strip()
    if not appid or not secret:
        # Fallback to reading ~/.bashrc if invoked in non-interactive shell
        bashrc_path = Path.home() / ".bashrc"
        if bashrc_path.is_file():
            content = bashrc_path.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("export WECHAT_PUB_APPID="):
                    appid = line.split("=", 1)[1].strip("'\" ")
                elif line.startswith("export WECHAT_PUB_APPSECRET="):
                    secret = line.split("=", 1)[1].strip("'\" ")
    if not appid or not secret:
        raise ValueError("缺少环境变量 WECHAT_PUB_APPID 或 WECHAT_PUB_APPSECRET，请在 ~/.bashrc 中配置。")
    return appid, secret

def get_access_token(appid: str, secret: str) -> str:
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        if "access_token" not in data:
            raise RuntimeError(f"获取微信 Access Token 失败: {data}")
        return data["access_token"]

def upload_img(access_token: str, file_path: str) -> str:
    """上传正文图片到微信 CDN，不占用素材库配额，返回 mmbiz 官方 URL。"""
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "url" not in res:
            raise RuntimeError(f"正文配图转存微信 CDN 失败: {res}")
        return res["url"]

def upload_permanent_material(access_token: str, file_path: str) -> str:
    """上传图片至永久素材库以获得 thumb_media_id。"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "media_id" not in res:
            raise RuntimeError(f"注册封面永久素材失败: {res}")
        return res["media_id"]

def add_draft(access_token: str, title: str, author: str, digest: str, content: str, thumb_media_id: str) -> str:
    """在微信公众号草稿箱创建草稿。"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = {
        "articles": [
            {
                "title": title[:64],
                "author": author[:8],
                "digest": digest[:120],
                "content": content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }
        ]
    }
    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "media_id" not in res:
            raise RuntimeError(f"创建微信草稿失败: {res}")
        return res["media_id"]

def publish_html(html_path: str, title: str, author: str = "Mopheus", digest: str = "", cover_path: str = None) -> dict:
    html_file = Path(html_path).resolve()
    if not html_file.is_file():
        raise FileNotFoundError(f"找不到 HTML 文件: {html_path}")
    if html_file.name.endswith("_预览.html"):
        raise ValueError("请使用纯净正文 HTML（不带 _预览.html 后缀）进行发布！")

    appid, secret = get_env_credentials()
    print(f"1. 正在获取微信 Access Token (AppID: {appid})...")
    token = get_access_token(appid, secret)
    print("   ✓ Access Token 获取成功")

    html_content = html_file.read_text(encoding="utf-8")

    # 提取所有图片 src
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    all_imgs = img_pattern.findall(html_content)

    with tempfile.TemporaryDirectory() as temp_dir:
        # 转存正文图片到微信 CDN
        replaced_count = 0
        cover_local = None

        if cover_path and os.path.exists(cover_path):
            cover_local = cover_path

        for idx, src in enumerate(all_imgs):
            if "mmbiz.qpic.cn" in src:
                continue
            local_img = os.path.join(temp_dir, f"img_{idx}.jpg")
            if src.startswith("http://") or src.startswith("https://"):
                print(f"2. 下载外链配图: {src[:60]}...")
                headers = {"User-Agent": "Mozilla/5.0"}
                req = urllib.request.Request(src, headers=headers)
                with urllib.request.urlopen(req) as r, open(local_img, "wb") as f:
                    f.write(r.read())
            elif os.path.isfile(src):
                local_img = src
            else:
                continue

            if not cover_local and idx == 0:
                cover_local = local_img

            print(f"   ➔ 上传至微信 CDN...")
            mmbiz_url = upload_img(token, local_img)
            html_content = html_content.replace(src, mmbiz_url)
            replaced_count += 1

        if not cover_local and all_imgs:
            # 下载第一张图作为封面
            first_src = all_imgs[0]
            cover_local = os.path.join(temp_dir, "cover.jpg")
            if first_src.startswith("http"):
                req = urllib.request.Request(first_src, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as r, open(cover_local, "wb") as f:
                    f.write(r.read())
            elif os.path.isfile(first_src):
                cover_local = first_src

        if not cover_local:
            raise ValueError("未找到可用封面图，请提供 --cover 参数或在文章中插入配图。")

        print("3. 上传永久封面素材...")
        thumb_media_id = upload_permanent_material(token, cover_local)
        print(f"   ✓ 封面素材 thumb_media_id: {thumb_media_id}")

        print("4. 正在推送到微信公众号草稿箱...")
        draft_media_id = add_draft(
            access_token=token,
            title=title,
            author=author,
            digest=digest,
            content=html_content,
            thumb_media_id=thumb_media_id
        )
        print(f"   ✓ 草稿创建成功! Draft Media ID: {draft_media_id}")

        return {
            "draft_media_id": draft_media_id,
            "thumb_media_id": thumb_media_id,
            "replaced_images": replaced_count,
            "title": title,
            "author": author,
            "digest": digest
        }

def main():
    parser = argparse.ArgumentParser(description="微信公众号一键草稿推送工具")
    parser.add_argument("--html", required=True, help="纯净正文 HTML 文件路径")
    parser.add_argument("--title", required=True, help="文章标题（≤64字符）")
    parser.add_argument("--author", default="Mopheus", help="作者署名（≤8字符）")
    parser.add_argument("--digest", default="", help="文章摘要（≤120字符）")
    parser.add_argument("--cover", default=None, help="封面图片本地路径（可选，默认提取第一张配图）")

    args = parser.parse_args()
    publish_html(args.html, args.title, args.author, args.digest, args.cover)

if __name__ == "__main__":
    main()
