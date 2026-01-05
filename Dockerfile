# 1. 使用 Python 3.11 瘦镜像
FROM python:3.11-slim

# 2. 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    HOME=/home/user

# 3. 创建一个非 root 用户
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# 4. 安装系统依赖 (以 root 身份执行)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libwayland-client0 libxcomposite1 \
    libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖并安装包
COPY --chown=user:user requirements.txt .

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
RUN pip install --no-cache-dir -r requirements.txt

# 6. 安装浏览器内核 (关键修改)
# 这一步我们只安装浏览器二进制文件，不带 --with-deps，避免触发 sudo
RUN playwright install chromium
# 如果你使用 undetected 模式，crawl4ai 会用到 patchright
RUN python3 -m patchright install chromium || echo "Patchright not installed"

# 7. 初始化 Crawl4AI 数据库 (跳过它内部的浏览器安装)
# 我们直接运行初始化命令，忽略它内部安装浏览器的报错
RUN crawl4ai-setup || echo "Setup finished with some warnings"

# 8. 复制项目代码
COPY --chown=user:user . .

# 9. 暴露端口并启动
EXPOSE 7860
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
