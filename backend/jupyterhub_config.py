"""
JupyterHub 配置文件
用于 OpenHydra 集成测试
"""

import os

import docker

c = get_config()  # noqa

# Docker 客户端
client = docker.from_env()

# JupyterHub 基础配置
c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8081

# 认证配置 - 使用 DummyAuthenticator (测试用)
c.JupyterHub.authenticator_class = "dummyauthenticator.DummyAuthenticator"
c.DummyAuthenticator.allowed_users = {"xedudemo", "student1", "student2"}
c.DummyAuthenticator.admin_users = {"admin"}

# Spawner 配置 - 使用 DockerSpawner
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

# 使用 XEdu Notebook 镜像
c.DockerSpawner.image = "xedu/notebook:latest"

# 容器命名
c.DockerSpawner.container_name_template = "jupyter-{username}"

# 网络配置
c.DockerSpawner.network_name = "openhydra-network"

# 资源限制
c.DockerSpawner.cpu_limit = 2.0
c.DockerSpawner.mem_limit = "4G"

# 挂载用户数据卷
c.DockerSpawner.volumes = {
    "jupyter-user-{username}": "/home/xeduuser/work",
    "jupyter-shared": "/home/xeduuser/shared",
}

# 环境变量
c.DockerSpawner.environment = {
    "XEDU_ENABLED": "true",
    "OPENHYDRA_INTEGRATION": "true",
    "JUPYTERHUB_API_URL": "http://jupyterhub:8000/hub/api",
    "GRANT_SUDO": "no",
}

# 超时设置
c.DockerSpawner.start_timeout = 300
c.DockerSpawner.remove = True

# 预生成 Token (用于 OpenHydra 集成)
c.JupyterHub.services = [
    {"name": "openhydra-service", "api_token": "openhydra-secret123", "admin": True}
]

# 日志配置
c.JupyterHub.log_level = "INFO"
c.DockerSpawner.debug = True
