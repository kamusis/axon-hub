# 扫描版 PDF 转图片方法

扫描版 PDF 需先转为图片，才能用多模态大模型视觉能力识别。

## 依赖

无需额外安装，项目 `requirements.txt` 中的 `pymupdf` 和 `Pillow` 即可完成。

## 转换方法

```python
import fitz  # pymupdf

pdf_path = "scan.pdf"
doc = fitz.open(pdf_path)

for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=300)
    output_path = f"{pdf_path.replace('.pdf', '')}_page_{page_num+1}.png"
    pix.save(output_path)
    print(f"已转换: {output_path}")

doc.close()
```

输出：`scan_page_1.png`, `scan_page_2.png`, ...

然后用 Read 工具逐页识别即可。
