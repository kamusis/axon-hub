---
name: qrcode
description: Generate, display, and decode QR codes from URLs/text or screenshots/images. Use when the user asks to make a QR code, read what a QR code contains, extract a URL from a QR screenshot, compare QR payloads, or verify QR generation/decoding round trips.
---

# QR Code

## Overview

Use local command-line tools for QR work:

- `qrencode` to generate QR images.
- `zbarimg` to decode QR images.
- `identify` / `convert` from ImageMagick when an image needs inspection, format conversion, or cropping.

Prefer these deterministic tools over ad hoc JavaScript/Python packages.

## Generate

Create a PNG QR code:

```bash
qrencode -o /tmp/qrcode.png 'https://example.com/path?x=1'
```

For easier phone scanning, use a larger module size and margin:

```bash
qrencode -s 8 -m 2 -o /tmp/qrcode.png 'https://example.com/path?x=1'
```

After generating, verify the payload before showing or sharing:

```bash
zbarimg --quiet --raw /tmp/qrcode.png
```

When replying in Codex desktop, embed the generated image with an absolute path:

```markdown
![QR code](/tmp/qrcode.png)
```

## Decode

Decode an image or screenshot:

```bash
zbarimg --quiet --raw /absolute/path/to/image.png
```

If the QR is embedded in a larger screenshot and decoding fails, inspect dimensions:

```bash
identify /absolute/path/to/screenshot.png
```

Crop roughly around the QR code, then retry:

```bash
convert /absolute/path/to/screenshot.png -crop WIDTHxHEIGHT+X+Y /tmp/qr-crop.png
zbarimg --quiet --raw /tmp/qr-crop.png
```

If the QR is small or blurry, enlarge before decoding:

```bash
convert /tmp/qr-crop.png -resize 400% /tmp/qr-crop-big.png
zbarimg --quiet --raw /tmp/qr-crop-big.png
```

## Workflow

1. For generation requests, write the exact requested payload into `qrencode`.
2. Decode the generated PNG with `zbarimg` and confirm it matches exactly.
3. For decode requests, run `zbarimg` directly first.
4. If direct decode fails, crop/enlarge with ImageMagick and retry.
5. Report the decoded payload as plain text. If it is a URL, do not silently rewrite or normalize it.

## Notes

- JSON responses may escape `&` as `\u0026`; convert it back to `&` before manual URL testing or QR generation.
- QR payload comparison must be exact, including query parameter spelling and hostnames.
- For temporary diagnostic images, prefer `/tmp/<descriptive-name>.png`.
