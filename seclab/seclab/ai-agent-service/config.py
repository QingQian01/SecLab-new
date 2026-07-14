import os

from dotenv import load_dotenv

load_dotenv()

# Dify Agent configuration
DIFY_API_URL = os.getenv("DIFY_API_URL", "")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_WORKFLOW_ID = os.getenv("DIFY_WORKFLOW_ID", "")
DIFY_APP_ID = os.getenv("DIFY_APP_ID", "")
ENABLE_FAKE_LLM_FOR_TEST = os.getenv("ENABLE_FAKE_LLM_FOR_TEST", "false")

# AI agent service listener
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8010"))

# Frontend CORS allowlist
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.1.106:5173",
]

configured_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

CORS_ORIGINS = list(dict.fromkeys(configured_cors_origins + DEFAULT_CORS_ORIGINS))

# Docker tool container name allowlist
ALLOWED_CONTAINER_PREFIXES = os.getenv(
    "ALLOWED_CONTAINER_PREFIXES",
    "sqli,xss,csrf,upload,dir,cmd,sec-code",
).split(",")

# Maximum log lines returned by Docker tools
MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "200"))

# MySQL persistence for learning events and profile snapshots
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "seclab_app")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Seclab@123")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "seclab_profile")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")
