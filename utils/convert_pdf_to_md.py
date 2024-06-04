from pdfminer.high_level import extract_text
def convert_pdf_to_md(filepath):
    text = extract_text(filepath)
    # 简单的文本转 Markdown，可以根据需要进行更复杂的转换
    md_text = text.replace('\n', '  \n')
    return md_text