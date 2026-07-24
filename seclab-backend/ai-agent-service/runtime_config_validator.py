from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


REQUIRED_KEYS = (
    "DIFY_API_URL",
    "DIFY_API_KEY",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
)

BOOLEAN_KEYS = (
    "ENABLE_FAKE_LLM_FOR_TEST",
    "ENABLE_DIFY_KNOWLEDGE_RAG",
    "STRICT_SOURCE_EXAMPLE_VALIDATION",
)

PORT_KEYS = ("SERVICE_PORT", "MYSQL_PORT")
PLACEHOLDER_MARKERS = ("your_", "_here", "change_me", "changeme", "replace_me")
ALLOWED_RAG_MODES = {"local", "hybrid", "dify"}
ALLOWED_BOOLEAN_VALUES = {"true", "false", "1", "0", "yes", "no", "on", "off"}


def _text(values: Mapping[str, Any], key: str) -> str:
    value = values.get(key)
    return "" if value is None else str(value).strip()


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def validate_runtime_config(values: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []

    for key in REQUIRED_KEYS:
        value = _text(values, key)
        if not value:
            issues.append(f"{key}: 缺少必填配置")
        elif _is_placeholder(value):
            issues.append(f"{key}: 仍是示例占位符")

    api_url = _text(values, "DIFY_API_URL")
    if api_url and not api_url.lower().startswith(("http://", "https://")):
        issues.append("DIFY_API_URL: 必须是 http:// 或 https:// 地址")

    for key in PORT_KEYS:
        value = _text(values, key)
        if not value:
            if key not in REQUIRED_KEYS:
                issues.append(f"{key}: 缺少端口配置")
            continue
        try:
            port = int(value)
        except ValueError:
            issues.append(f"{key}: 必须是 1-65535 的整数")
            continue
        if not 1 <= port <= 65535:
            issues.append(f"{key}: 必须是 1-65535 的整数")

    max_log_lines = _text(values, "MAX_LOG_LINES")
    if max_log_lines:
        try:
            if int(max_log_lines) <= 0:
                raise ValueError
        except ValueError:
            issues.append("MAX_LOG_LINES: 必须是正整数")

    for key in BOOLEAN_KEYS:
        value = _text(values, key).lower()
        if value and value not in ALLOWED_BOOLEAN_VALUES:
            issues.append(f"{key}: 必须是 true/false、1/0、yes/no 或 on/off")

    rag_mode = _text(values, "DIFY_RAG_MODE").lower()
    if rag_mode and rag_mode not in ALLOWED_RAG_MODES:
        issues.append("DIFY_RAG_MODE: 必须是 local、hybrid 或 dify")

    flag_answers = _text(values, "FLAG_ANSWERS_JSON")
    if flag_answers:
        try:
            parsed = json.loads(flag_answers)
        except json.JSONDecodeError:
            issues.append("FLAG_ANSWERS_JSON: 必须是有效的 JSON 对象")
        else:
            if not isinstance(parsed, dict):
                issues.append("FLAG_ANSWERS_JSON: 必须是 JSON 对象")

    return issues


def load_and_validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: 配置文件不存在，请先复制 .env.example"]
    return validate_runtime_config(dotenv_values(path))


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    path = Path(arguments[0]) if arguments else Path(__file__).with_name(".env")
    issues = load_and_validate(path)
    if issues:
        for issue in issues:
            print(f"[ERROR] {issue}")
        return 2
    print("[OK] 运行配置检查通过，未输出任何密钥内容。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
