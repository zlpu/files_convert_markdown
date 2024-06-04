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