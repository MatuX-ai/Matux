# XEdu 工具链 Jupyter Notebook 镜像
# 用于 OpenHydra 集成测试

FROM jupyter/base-notebook:python-3.9.18

# 维护者信息
LABEL maintainer="iMato Team <support@imato.edu>"
LABEL description="XEdu Toolchain for AI Education"
LABEL version="2.0.1"

# 设置工作目录
WORKDIR /home/jovyan

# 切换为 root 用户以安装系统依赖
USER root

# 安装系统级依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    vim \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 切换回 jovyan 用户
USER jovyan

# 安装 XEdu 核心组件
# 基于官方 XEdu (https://github.com/PaddlePaddle/XEdu)
RUN pip install --no-cache-dir \
    xedu-basett==2.0.1 \
    xedu-basenn==2.0.1 \
    xedu-baseml==2.0.1 \
    xedu-mmedu==2.0.1 \
    xedu-xeduhub==2.0.1 \
    xedu-xedullm==2.0.1 \
    xedu-easytrain==2.0.1 \
    xedu-basedeploy==2.0.1

# 安装额外的机器学习库
RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    paddlepaddle \
    matplotlib \
    scikit-learn \
    opencv-python-headless \
    pillow \
    tqdm \
    numpy \
    pandas

# 创建示例和数据目录
RUN mkdir -p /home/jovyan/notebooks/examples \
    /home/jovyan/data \
    /home/jovyan/models \
    /home/jovyan/logs

# 复制示例 Notebooks
COPY backend/notebooks/*.ipynb /home/jovyan/notebooks/examples/

# 设置文件权限
RUN chmod -R 755 /home/jovyan/notebooks

# 配置 Jupyter
ENV JUPYTER_ENABLE_LAB=yes
ENV GRANT_SUDO=yes

# 暴露端口
EXPOSE 8888

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/api || exit 1

# 启动命令
CMD ["start-notebook.sh", "--NotebookApp.token=''"]
