# 1. 使用 Python 3.11 瘦镜像
FROM python:3.11-slim

# 2. 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    HOME=/home/user

# 3. 创建一个非 root 用户 (Hugging Face 的要求)
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# 4. 安装系统依赖 (需要 root 权限)
# 这些是 Playwright 运行 Chromium 所必须的系统库
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 5. 复制依赖文件并安装
COPY --chown=user:user requirements.txt .

# 切换到非 root 用户执行后续操作
USER user
RUN pip install --no-cache-dir -r requirements.txt

# 6. 安装 Crawl4AI 专有组件和 Playwright 浏览器
# 注意：在 HF 上，浏览器默认安装在 /home/user/.cache/ms-playwright
RUN crawl4ai-setup
RUN python3 -m playwright install --with-deps chromium

# 7. 复制项目代码
COPY --chown=user:user . .

# 8. 暴露端口
EXPOSE 7860

# 9. 启动命令
# 使用 host 0.0.0.0 和端口 7860 才能在 HF 上访问
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
