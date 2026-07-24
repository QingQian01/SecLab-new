import unittest
from unittest.mock import patch

from main import (
    ChatRequest,
    UnifiedStudentEventRequest,
    _model_data,
    build_chat_payload,
)


class ChatLabHintPayloadTest(unittest.TestCase):
    def test_ai_interaction_event_keeps_teacher_visible_conversation_details(self):
        event = UnifiedStudentEventRequest(
            event_type="AI_INTERACTION",
            prompt="如何判断当前 SQL 注入点？",
            assistant_reply="先比较正常参数与单引号输入后的响应差异。",
            message_role="user",
            used_context_injection=True,
            context={"experimentTitle": "SQL注入基础实验"},
            tool_calls=[{"tool": "get_container_logs", "status": "done"}],
        )

        data = _model_data(event, exclude_none=True)

        self.assertEqual(data["prompt"], "如何判断当前 SQL 注入点？")
        self.assertIn("响应差异", data["assistant_reply"])
        self.assertEqual(data["context"]["experimentTitle"], "SQL注入基础实验")
        self.assertEqual(data["tool_calls"][0]["tool"], "get_container_logs")

    @patch("main.docker_tools.get_container_logs")
    @patch("main.docker_tools.get_container_status")
    def test_hint_request_uses_local_runtime_evidence(
        self,
        get_container_status,
        get_container_logs,
    ):
        get_container_status.return_value = {
            "success": True,
            "data": {"name": "sqli-lab-web-1", "status": "running"},
        }
        get_container_logs.return_value = {
            "success": True,
            "container": "sqli-lab-web-1",
            "logs": '172.19.0.1 "GET /index.php?level=1&id=2 HTTP/1.1" 200',
        }

        payload = build_chat_payload(
            ChatRequest(
                query="请分析我当前的实验进展，并给出下一步提示。",
                conversation_id="old-conversation-with-failed-tools",
                user="295",
                inputs={
                    "hint_request": True,
                    "lab_context": {
                        "moduleName": "SQL 注入",
                        "experimentTitle": "SQL注入基础实验",
                        "containerName": "sqli-lab-web-1",
                        "targetUrl": "http://localhost:8091/index.php",
                    },
                },
            )
        )

        get_container_logs.assert_called_once_with("sqli-lab-web-1", tail=50)
        self.assertIn("running", payload["query"])
        self.assertIn("level=1&id=2", payload["query"])
        self.assertIn("SQL注入基础实验", payload["query"])
        self.assertIn("日志已经由平台读取", payload["query"])
        self.assertEqual({}, payload["inputs"])
        self.assertEqual("", payload["conversation_id"])

    @patch("main.docker_tools.get_container_logs")
    @patch("main.docker_tools.get_container_status")
    def test_regular_chat_is_not_enriched(
        self,
        get_container_status,
        get_container_logs,
    ):
        payload = build_chat_payload(ChatRequest(query="你好", inputs={}))

        self.assertEqual("你好", payload["query"])
        get_container_status.assert_not_called()
        get_container_logs.assert_not_called()

    @patch("main.docker_tools.get_container_logs")
    @patch("main.docker_tools.get_container_status")
    def test_regular_lab_chat_uses_local_runtime_context(
        self,
        get_container_status,
        get_container_logs,
    ):
        get_container_status.return_value = {
            "success": True,
            "data": {"name": "sqli-lab-web-1", "status": "running"},
        }
        get_container_logs.return_value = {
            "success": True,
            "container": "sqli-lab-web-1",
            "logs": 'GET /index.php?level=1&id=3 HTTP/1.1" 200',
        }

        payload = build_chat_payload(
            ChatRequest(
                query="我现在做到哪一步了？",
                conversation_id="old-tool-conversation",
                inputs={
                    "lab_runtime_context": True,
                    "lab_context": {"containerName": "sqli-lab-web-1"},
                },
            )
        )

        get_container_logs.assert_called_once_with("sqli-lab-web-1", tail=50)
        self.assertIn("level=1&id=3", payload["query"])
        self.assertEqual("", payload["conversation_id"])
        self.assertEqual({}, payload["inputs"])

    @patch("main.docker_tools.get_container_logs")
    @patch("main.docker_tools.get_container_status")
    def test_named_container_log_request_is_read_locally(
        self,
        get_container_status,
        get_container_logs,
    ):
        get_container_status.return_value = {
            "success": True,
            "data": {"name": "sqli-lab-web-1", "status": "running"},
        }
        get_container_logs.return_value = {
            "success": True,
            "container": "sqli-lab-web-1",
            "logs": "apache access log",
        }

        payload = build_chat_payload(
            ChatRequest(query="请读取 sqli-lab-web-1 的最新日志")
        )

        get_container_logs.assert_called_once_with("sqli-lab-web-1", tail=50)
        self.assertIn("apache access log", payload["query"])
        self.assertEqual({}, payload["inputs"])


if __name__ == "__main__":
    unittest.main()
