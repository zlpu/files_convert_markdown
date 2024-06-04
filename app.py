"""
作者：微信公众号-IT软件推荐员
邮箱：pzl960504@outlook.com
项目名：文档转markdown
"""
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
import os
import re
import zipfile
from werkzeug.utils import secure_filename
from utils.convert_pdf_to_md import convert_pdf_to_md
from utils.convert_word_to_md import convert_word_to_md
from io import BytesIO
from docx.opc.exceptions import PackageNotFoundError  # 导入 PackageNotFoundError

app = Flask(__name__)
# 设置文件上传和Markdown文件的保存目录
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MARKDOWN_FOLDER'] = 'static/markdowns/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
app.secret_key = 'supersecretkey'
# 如果上传文件的目录不存在，则创建它
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# 如果Markdown文件的目录不存在，则创建它
if not os.path.exists(app.config['MARKDOWN_FOLDER']):
    os.makedirs(app.config['MARKDOWN_FOLDER'])


# 检查文件扩展名是否被允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# 清理文件名，去除无效字符并规范化文件名
def sanitize_filename(filename):
    # 删除无效字符并规范化文件名
    filename = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5.]+', '_', filename)
    return filename


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files[]')  # 获取上传的文件列表
        folder_files = request.files.getlist('folder[]')  # 获取上传的文件夹内文件列表
        all_files = files + folder_files  # 合并所有文件
        markdown_files = []  # 用于存储生成的Markdown文件列表

        for file in all_files:
            if file and allowed_file(file.filename):  # 如果文件存在且是允许的类型
                filename = file.filename
                sanitized_filename = sanitize_filename(filename)  # 清理文件名
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)  # 生成文件保存的路径
                # 创建必要的目录结构
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)  # 保存文件
                try:
                    # 根据文件类型转换为Markdown格式
                    if filename.rsplit('.', 1)[1].lower() == 'pdf':
                        md_content = convert_pdf_to_md(filepath)
                    elif filename.rsplit('.', 1)[1].lower() == 'docx':
                        md_content = convert_word_to_md(filepath)
                    md_filename = sanitized_filename.rsplit('.', 1)[0] + '.md'  # 生成Markdown文件名
                    md_filepath = os.path.join(app.config['MARKDOWN_FOLDER'], md_filename)  # 生成Markdown文件保存路径
                    with open(md_filepath, 'w', encoding='utf-8') as md_file:
                        md_file.write(md_content)  # 写入Markdown内容
                    markdown_files.append(md_filename)  # 添加到Markdown文件列表
                except PackageNotFoundError:
                    flash(f'文件 {file.filename} 不是有效的DOCX文件')
                except Exception as e:
                    flash(f'处理文件 {file.filename} 时发生错误: {str(e)}')
        return render_template('index.html', markdown_files=markdown_files)  # 渲染模板并传递Markdown文件列表
    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    # 从目录中发送文件，作为附件下载
    return send_from_directory(app.config['MARKDOWN_FOLDER'], filename, as_attachment=True)


@app.route('/download_all', methods=['POST'])
def download_all():
    filenames = request.form.getlist('filenames')  # 获取表单中选定的文件名列表
    if not filenames:
        flash('没有选择文件进行下载')
        return redirect(url_for('index'))
    # 创建一个字节流对象，用于保存 ZIP 文件
    zip_stream = BytesIO()
    with zipfile.ZipFile(zip_stream, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in filenames:
            filepath = os.path.join(app.config['MARKDOWN_FOLDER'], filename)
            zipf.write(filepath, arcname=filename)  # 将文件写入 ZIP 文件
    zip_stream.seek(0)
    # 返回 ZIP 文件作为响应
    return send_file(zip_stream, mimetype='application/zip', as_attachment=True, download_name='markdown_files.zip')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')