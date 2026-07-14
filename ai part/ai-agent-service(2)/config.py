import os
from dotenv import load_dotenv

load_dotenv()

# Dify Agent 配置
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-dOnVHdf7HKM5BuLy4942IKVd")

# 本服务配置
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8010"))

# 允许的跨域来源（前端地址）
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:80,http://localhost,http://192.168.1.106:5173"
).split(",")

# Docker 白名单容器名前缀（安全过滤）
ALLOWED_CONTAINER_PREFIXES = os.getenv(
    "ALLOWED_CONTAINER_PREFIXES",
    "sqli,xss,csrf,upload,dir,cmd,sec-code"
).split(",")

# 每次最多返回的日志行数
MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "200"))

