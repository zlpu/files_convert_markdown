from docx import Document
def convert_word_to_md(filepath):
    doc = Document(filepath)
    md_text = ""
    for para in doc.paragraphs:
        md_text += para.text + '  \n'
    return md_text