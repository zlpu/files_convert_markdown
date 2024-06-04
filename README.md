## 主要功能
- 支持转化文档类型： PDF、word转为markdown
- 支持上传文件的方式： 单文件上传（单文件转化）、多文件上传（批量转化）、上传文件夹（批量转化）
- 下载转化后markdown文件：支持单文件下载、批量下载


![上传界面](https://files.mdnice.com/user/42695/630d5ecb-0581-4bc1-bfca-01fd6acc99e6.png)

![转化后](https://files.mdnice.com/user/42695/a45b9005-7ede-4251-a676-51435ea9a567.png)

|        |  |        
| :--------- | :--: | 
| 下载完整代码     |  私信“转markdown项目代码”  |  
|  github项目地址  |    |  
| 在线体验 |  https://3mw.cn/31kcd  | 


## 项目结构
 - 本项目使用Flask框架进行开发
 - python版本：3.9
```
file_convert_markdown/
│
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html
├── static/
│   └── uploads/
├── utils/
    ├── __init__.py
    ├── convert_pdf_to_md.py
    └── convert_word_to_md.py
```



## 部署运行
### 方式1.本地python运行
下载代码后，直接运行python app.py即可
### 方式2.docker运行
- 项目代码中我已提供Dcokerfile文件，可以直接构建镜像
- 该项目我已打包docker镜像，镜像可以从公有仓库拉取，使用方式如下：
```bash
docker run -itd --name=file_convert_md01 -p 5000:5000 --restart=always registry.cn-hangzhou.aliyuncs.com/pzl_images/files_convert_markdown:v20240604
```


# 代码内容
## 1. `requirements.txt`

创建一个`requirements.txt`文件来列出所需的Python库：

```
flask
python-docx
pdfminer.six
```


## 2. `app.py`

主应用文件`app.py`：

```python
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
```

## 3. `templates/index.html`

创建一个美观的HTML文件`templates/index.html`来展示简历信息：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档转Markdown</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <!-- 使用相对路径添加Favicon -->
    <link rel="icon" href="https://www.runoob.com/wp-content/uploads/2019/03/iconfinder_markdown_298823.png" type="image/x-icon">
    <link rel="shortcut icon" href=" https://www.runoob.com/wp-content/uploads/2019/03/iconfinder_markdown_298823.png" type="image/x-icon">
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center">文档转Markdown</h1>

        <!-- 添加图片 -->
        <div class="text-center">
            <img src="https://picture.gptkong.com/20240604/22485b1e3ed546421e904c0634bac1f331.png" style="width: 30%;" alt="Logo">
        </div>

        <!-- 添加说明文字 -->
        <p class="text-center">支持将PDF和Word文档转换为Markdown格式。</p>
        <form action="{{ url_for('index') }}" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="file">选择文件</label>
                <input type="file" class="form-control-file" id="file" name="files[]" multiple>
            </div>
            <div class="form-group">
                <label for="folder">选择文件夹</label>
                <input type="file" class="form-control-file" id="folder" name="folder[]" multiple webkitdirectory directory>
            </div>
            <button type="submit" class="btn btn-primary">上传并转换</button>
        </form>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="alert alert-info mt-3">
                    {% for message in messages %}
                        <p>{{ message }}</p>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        {% if markdown_files %}
            <h3 class="mt-5">转换后的文件</h3>
            <form action="{{ url_for('download_all') }}" method="post">
                <ul class="list-group">
                    {% for filename in markdown_files %}
                        <li class="list-group-item">
                            <input type="checkbox" name="filenames" value="{{ filename }}">
                            {{ filename }}
                            <a href="{{ url_for('download_file', filename=filename) }}" class="btn btn-success btn-sm float-right">下载</a>
                        </li>
                    {% endfor %}
                </ul>
                <button type="submit" class="btn btn-primary mt-3">批量下载</button>
            </form>
        {% endif %}
    </div>
</body>
</html>


```


## 4. `utils/convert_pdf_to_md.py`

编写PDF转Markdown的工具函数：

```python
from pdfminer.high_level import extract_text
def convert_pdf_to_md(filepath):
    text = extract_text(filepath)
    # 简单的文本转 Markdown，可以根据需要进行更复杂的转换
    md_text = text.replace('\n', '  \n')
    return md_text
```

## 5. `utils/convert_word_to_md.py`

编写Word转Markdown的工具函数：

```python
from docx import Document
def convert_word_to_md(filepath):
    doc = Document(filepath)
    md_text = ""
    for para in doc.paragraphs:
        md_text += para.text + '  \n'
    return md_text
```


## 6. 运行项目

安装所需的Python库：

```bash
pip install -r requirements.txt
```

运行Flask应用：

```bash
python app.py
```

访问`http://127.0.0.1:5000/`，就可以在浏览器上使用这个文件转markdown格式的工具

---

如果不想使用传统的运行方式，可以使用docker来创建服务，提供docker镜像封装办法，封装成镜像后，方便使用

## docker镜像封装

```Dockerfile
# 使用官方Python基础镜像
FROM python:3.9
# 设置工作目录
WORKDIR /app
# 将requirements.txt复制到工作目录
COPY requirements.txt .
# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 复制当前目录下所有文件到工作目录
COPY . .
# 暴露应用端口（假设你的应用在5000端口运行）
EXPOSE 5000
# 设置环境变量（如果有需要）
#ENV APP_ENV=production
# 运行应用程序
CMD ["python", "app.py"]
```

## 镜像构建
```
docker build -t 镜像名称:v1 .
```


## 创建容器（跑服务）
```
docker run -it --name=file_to_md -p 5000:5000 镜像名称:v1
```

访问`http://127.0.0.1:5000/`，就可以在浏览器上使用这个文件转markdown格式的工具
