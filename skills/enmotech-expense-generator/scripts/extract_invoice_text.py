"""
extract_invoice_text.py — 从指定目录的 PDF 和图片文件中提取发票文本信息。

用法:
  python extract_invoice_text.py <目录路径> [--output-dir <图片输出目录>]

策略（按优先级）:
  PDF 文件:
    1. pdfplumber 提取文本层（电子发票 PDF）
    2. PyMuPDF (fitz) 转图片（扫描件/图片 PDF），供后续 multimodal 读取
  图片文件 (.jpg, .jpeg, .bmp):
    1. Pillow 转 PNG（Read 工具对 JPG/BMP 可能报 binary file 错误，PNG 通常可正常读取）
  PNG 文件:
    1. 直接可用 Read 工具读取，无需转换

依赖:
  pip install pdfplumber PyMuPDF Pillow

输出:
  - stdout: 每个文件的处理结果
  - --output-dir: 转换后的 PNG 图片存放目录
"""
import os
import sys
import argparse
import re


def natural_sort_key(s):
    """自然排序 key 函数：file2.png 排在 file10.png 前面。"""
    parts = re.split(r'(\d+)', s)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def extract_text_with_pdfplumber(pdf_path):
    """用 pdfplumber 提取 PDF 文本层。

    Returns:
        (text: str|None, error: str|None)
    """
    import pdfplumber
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return None, str(e)
    return text.strip() if text.strip() else None, None


def pdf_to_images(pdf_path, output_dir, pdf_name):
    """用 PyMuPDF 将 PDF 每页转为 PNG 图片。

    Returns:
        (images: list[str], error: str|None)
    """
    import fitz  # PyMuPDF
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 200 DPI：PDF 转图平衡清晰度和文件大小；
            # JPG/BMP 转 PNG 用 300 DPI（见 convert_image_to_png），
            # 两者场景不同，无需统一。
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat)
            base_name = os.path.splitext(pdf_name)[0]
            img_filename = f"{base_name}_p{page_num + 1}.png"
            img_path = os.path.join(output_dir, img_filename)
            pix.save(img_path)
            images.append(img_path)
        doc.close()
    except Exception as e:
        return [], str(e)
    return images, None


def convert_image_to_png(img_path, output_dir):
    """用 Pillow 将非 PNG 图片转为 PNG（300 DPI），供 Read 工具 multimodal 读取。

    Read 工具对 JPG/BMP 可能报 'Cannot display content of binary file' 错误，
    PNG 格式通常可正常读取。

    Returns:
        (png_path: str|None, error: str|None)
    """
    from PIL import Image
    try:
        img = Image.open(img_path)
        img = img.convert('RGB')
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        png_path = os.path.join(output_dir, f"{base_name}.png")
        img.save(png_path, 'PNG', dpi=(300, 300))
        return png_path, None
    except Exception as e:
        return None, str(e)


def process_directory(target_dir, image_output_dir=None):
    """处理目录下所有 PDF 和图片文件。

    Args:
        target_dir: 包含发票文件的目录路径
        image_output_dir: 转换后图片输出目录（为 None 时使用 target_dir/_images/）

    Returns:
        dict: {
            "text_files": {filename: extracted_text, ...},
            "image_files": {filename: [image_path, ...], ...},
            "png_converted": {filename: png_path, ...},
            "skipped": {filename: reason, ...},
            "errors": {filename: error_message, ...}
        }
    """
    if image_output_dir is None:
        image_output_dir = os.path.join(target_dir, "_images")
    # 清理 _images/ 目录中的旧文件，保证幂等性
    if os.path.isdir(image_output_dir):
        for old_file in os.listdir(image_output_dir):
            old_path = os.path.join(image_output_dir, old_file)
            try:
                if os.path.isfile(old_path):
                    os.remove(old_path)
            except Exception:
                pass
    os.makedirs(image_output_dir, exist_ok=True)

    # 支持的文件扩展名
    supported_exts = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp'}
    # 需要 Pillow 转换的格式（Read 工具可能不支持的格式）
    convert_exts = {'.jpg', '.jpeg', '.bmp'}

    all_files = sorted([
        f for f in os.listdir(target_dir)
        if os.path.splitext(f)[1].lower() in supported_exts
    ], key=natural_sort_key)

    results = {
        "text_files": {},
        "image_files": {},
        "png_converted": {},
        "skipped": {},
        "errors": {},
    }

    for filename in all_files:
        filepath = os.path.join(target_dir, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext == '.pdf':
            # PDF: 先尝试文本提取，失败则转图片
            text, err = extract_text_with_pdfplumber(filepath)
            if text:
                results["text_files"][filename] = text
                print(f"[TEXT] {filename} ({len(text)} chars)")
            else:
                images, img_err = pdf_to_images(filepath, image_output_dir, filename)
                if images:
                    results["image_files"][filename] = images
                    print(f"[IMAGE] {filename} -> {len(images)} page(s)")
                else:
                    reason = img_err or err or "Unknown error"
                    results["errors"][filename] = reason
                    print(f"[ERROR] {filename}: {reason}")

        elif ext in convert_exts:
            # JPG/BMP 等: 用 Pillow 转 PNG
            png_path, err = convert_image_to_png(filepath, image_output_dir)
            if png_path:
                results["png_converted"][filename] = png_path
                size_kb = os.path.getsize(png_path) / 1024
                print(f"[CONVERT] {filename} -> {os.path.basename(png_path)} ({size_kb:.0f} KB)")
            else:
                results["errors"][filename] = err
                print(f"[ERROR] {filename}: {err}")

        elif ext == '.png':
            # PNG: 直接可用 Read 工具读取，无需转换
            results["skipped"][filename] = "PNG file, use Read tool directly"
            print(f"[SKIP] {filename} (already PNG, use Read tool directly)")

    # Summary
    print(f"\n--- Summary ---")
    print(f"Text extracted: {len(results['text_files'])} files")
    print(f"PDF -> images: {len(results['image_files'])} files")
    print(f"Image -> PNG: {len(results['png_converted'])} files")
    print(f"Skipped (already PNG): {len(results['skipped'])} files")
    print(f"Errors: {len(results['errors'])} files")

    return results


def main():
    parser = argparse.ArgumentParser(description="Extract text from invoice PDFs and convert images")
    parser.add_argument("directory", help="Directory containing invoice files (PDF, JPG, PNG, BMP)")
    parser.add_argument("--output-dir", help="Output directory for converted images")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    results = process_directory(args.directory, args.output_dir)

    # Print full text for each extracted file
    if results["text_files"]:
        print("\n--- Extracted Text ---")
        for filename, text in results["text_files"].items():
            print(f"\n{'='*60}")
            print(f"FILE: {filename}")
            print(f"{'='*60}")
            print(text)


if __name__ == "__main__":
    main()
