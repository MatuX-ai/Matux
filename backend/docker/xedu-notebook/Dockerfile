FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libhdf5-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    jupyterlab==4.0.0 \
    notebook==7.0.0 \
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    matplotlib>=3.7.0 \
    scikit-learn>=1.3.0 \
    opencv-python>=4.8.0 \
    pillow>=10.0.0 \
    requests>=2.31.0 \
    tqdm>=4.65.0

# 安装 XEdu 工具链
RUN pip install --no-cache-dir \
    xedu-base-dt>=1.0.0 \
    xedu-base-ml>=1.0.0 \
    xedu-base-nn>=1.0.0 \
    xedu-mmedu>=1.0.0 \
    xedu-hub>=1.0.0 \
    xedu-base-deploy>=1.0.0 \
    xedu-easytrain>=1.0.0 \
    xedu-llm>=1.0.0

# 安装额外的 AI 框架（可选）
RUN pip install --no-cache-dir \
    torch>=2.0.0 \
    torchvision>=0.15.0 \
    tensorflow>=2.13.0 \
    keras>=2.13.0

# 复制示例 notebooks
COPY notebooks/ /home/xeduuser/notebooks/examples/

# 设置启动命令
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
