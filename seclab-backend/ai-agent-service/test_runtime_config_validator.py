from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from runtime_config_validator import main, validate_runtime_config


def complete_values() -> dict[str, str]:
    return {
        "DIFY_API_URL": "https://api.dify.ai/v1",
        "DIFY_API_KEY": "app-valid-runtime-key",
        "DIFY_RAG_MODE": "local",
        "ENABLE_DIFY_KNOWLEDGE_RAG": "false",
        "ENABLE_FAKE_LLM_FOR_TEST": "false",
        "STRICT_SOURCE_EXAMPLE_VALIDATION": "false",
        "SERVICE_HOST": "0.0.0.0",
        "SERVICE_PORT": "8010",
        "CORS_ORIGINS": "http://localhost:5173",
        "ALLOWED_CONTAINER_PREFIXES": "sqli,xss,csrf",
        "MAX_LOG_LINES": "200",
        "TOOL_API_KEY": "",
        "FLAG_ANSWERS_JSON": "{}",
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "seclab_app",
        "MYSQL_PASSWORD": "local-password",
        "MYSQL_DATABASE": "seclab_profile",
        "MYSQL_CHARSET": "utf8mb4",
    }


class RuntimeConfigValidatorTest(unittest.TestCase):
    def test_complete_configuration_has_no_issues(self):
        self.assertEqual(validate_runtime_config(complete_values()), [])

    def test_missing_or_placeholder_secrets_are_reported_by_name_only(self):
        values = complete_values()
        values["DIFY_API_KEY"] = "your_dify_api_key_here"
        values.pop("MYSQL_PASSWORD")

        issues = validate_runtime_config(values)

        self.assertTrue(any("DIFY_API_KEY" in issue for issue in issues))
        self.assertTrue(any("MYSQL_PASSWORD" in issue for issue in issues))
        self.assertTrue(all("your_dify_api_key_here" not in issue for issue in issues))

    def test_invalid_port_boolean_and_flag_json_are_reported(self):
        values = complete_values()
        values.update(
            {
                "SERVICE_PORT": "99999",
                "ENABLE_DIFY_KNOWLEDGE_RAG": "sometimes",
                "FLAG_ANSWERS_JSON": "[]",
            }
        )

        issues = validate_runtime_config(values)

        self.assertTrue(any("SERVICE_PORT" in issue for issue in issues))
        self.assertTrue(any("ENABLE_DIFY_KNOWLEDGE_RAG" in issue for issue in issues))
        self.assertTrue(any("FLAG_ANSWERS_JSON" in issue for issue in issues))

    def test_cli_does_not_print_secret_values(self):
        values = complete_values()
        values["DIFY_API_KEY"] = "your_dify_api_key_here"
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text(
                "\n".join(f"{key}={value}" for key, value in values.items()),
                encoding="utf-8",
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = main([str(env_path)])

        self.assertEqual(exit_code, 2)
        self.assertIn("DIFY_API_KEY", output.getvalue())
        self.assertNotIn("your_dify_api_key_here", output.getvalue())

    def test_cli_reports_missing_env_file(self):
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["definitely-missing.env"])

        self.assertEqual(exit_code, 2)
        self.assertIn("definitely-missing.env", output.getvalue())


if __name__ == "__main__":
    unittest.main()
