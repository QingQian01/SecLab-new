from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AI_TEMPLATE = REPOSITORY_ROOT / "seclab-backend" / "ai-agent-service" / ".env.example"
FRONTEND_TEMPLATE = REPOSITORY_ROOT / "SecLab-FrontEnd-2" / ".env.example"
DEPLOYMENT_DOCUMENT = REPOSITORY_ROOT / "SecLab网络安全漏洞综合实验平台部署说明文档.md"

REQUIRED_AI_KEYS = {
    "DIFY_API_URL",
    "DIFY_API_KEY",
    "DIFY_WORKFLOW_ID",
    "DIFY_APP_ID",
    "DIFY_RAG_MODE",
    "ENABLE_DIFY_KNOWLEDGE_RAG",
    "ENABLE_FAKE_LLM_FOR_TEST",
    "STRICT_SOURCE_EXAMPLE_VALIDATION",
    "FLAG_ANSWERS_JSON",
    "SERVICE_HOST",
    "SERVICE_PORT",
    "CORS_ORIGINS",
    "ALLOWED_CONTAINER_PREFIXES",
    "MAX_LOG_LINES",
    "TOOL_API_KEY",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
    "MYSQL_CHARSET",
}

REQUIRED_FRONTEND_KEYS = {
    "VITE_API_BASE_URL",
    "VITE_EXPERIMENT_MODULE_BASE_URL",
    "VITE_IMAGE_SERVICE_BASE_URL",
    "VITE_DOCKER_API_URL",
    "VITE_AGENT_BASE_URL",
}


def parse_env_keys(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8")
    return set(re.findall(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", content))


class RuntimeConfigTemplateTest(unittest.TestCase):
    def test_ai_template_contains_all_runtime_keys(self):
        self.assertEqual(REQUIRED_AI_KEYS - parse_env_keys(AI_TEMPLATE), set())

    def test_frontend_template_contains_all_service_urls(self):
        self.assertEqual(REQUIRED_FRONTEND_KEYS - parse_env_keys(FRONTEND_TEMPLATE), set())

    def test_deployment_document_runs_validator_before_start(self):
        content = DEPLOYMENT_DOCUMENT.read_text(encoding="utf-8")

        self.assertIn("python runtime_config_validator.py .env", content)
        self.assertIn("VITE_EXPERIMENT_MODULE_BASE_URL", content)


if __name__ == "__main__":
    unittest.main()
