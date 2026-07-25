import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

import main
from teacher_ai_analysis_service import provider_failure_message


class TeacherApiErrorTest(unittest.TestCase):
    def test_teacher_auth_loads_owned_teaching_classes(self):
        connection = _FakeConnection(
            user={
                "user_id": 7,
                "user_student_number": "teacher01",
                "user_name": "王老师",
                "is_deleted": 0,
                "user_role": "TEACHER",
            },
            classes=[{"teaching_class_id": 101}, {"teaching_class_id": 103}],
        )
        with patch.object(main, "get_connection", return_value=connection):
            context = main._load_teacher_auth_context(7)

        self.assertEqual(context["role"], "teacher")
        self.assertEqual(context["owned_teaching_class_ids"], [101, 103])
        self.assertEqual(context["scope_class_ids"], [])
        self.assertEqual(connection.cursor_instance.execute_count, 2)

    def test_internal_exception_does_not_leak_details(self):
        error = main._teacher_repo_error(RuntimeError("database password leaked"))

        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.detail, "数据加载失败，请重新加载。")
        self.assertNotIn("password", str(error.detail))

    def test_permission_and_missing_data_are_controlled(self):
        forbidden = main._teacher_repo_error(PermissionError("student outside teacher scope"))
        missing = main._teacher_repo_error(KeyError("classId does not exist: 999"))

        self.assertEqual((forbidden.status_code, forbidden.detail), (403, "当前账号无权查看该数据。"))
        self.assertEqual((missing.status_code, missing.detail), (404, "请求的数据已不存在或无权访问。"))

    def test_student_assignment_scope_accepts_self_and_rejects_another_student(self):
        context = {"user_id": 261, "role": "student"}

        main._require_student_self(context, 261)
        with self.assertRaises(main.HTTPException) as raised:
            main._require_student_self(context, 262)

        self.assertEqual(raised.exception.status_code, 403)

    def test_teacher_assignment_training_request_tracks_intervention_and_knowledge(self):
        payload = main._build_teacher_assignment_training_request(
            261,
            {
                "interventionId": 17,
                "knowledgePointName": "SQL盲注",
            },
        )

        self.assertEqual(payload["user_id"], 261)
        self.assertEqual(payload["recommendation_id"], "intervention-17")
        self.assertEqual(payload["knowledge_tags"], ["SQL盲注"])
        self.assertEqual(payload["source"], "teacher_assignment")
        self.assertEqual(payload["count"], 5)


class AiAnalysisHealthTest(unittest.IsolatedAsyncioTestCase):
    async def test_missing_dify_configuration_is_reported_without_secret_values(self):
        with (
            patch.object(main, "DIFY_API_URL", ""),
            patch.object(main, "DIFY_API_KEY", ""),
        ):
            result = await main._probe_dify_configuration()

        self.assertEqual(
            result,
            {
                "configured": False,
                "providerReachable": False,
                "message": "Dify 尚未配置。",
            },
        )

    async def test_configured_dify_is_probed_through_parameters_endpoint(self):
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status.return_value = None
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = False
        client.get.return_value = response

        with (
            patch.object(main, "DIFY_API_URL", "https://api.dify.example/v1/"),
            patch.object(main, "DIFY_API_KEY", "secret-key"),
            patch.object(main.httpx, "AsyncClient", return_value=client),
        ):
            result = await main._probe_dify_configuration()

        self.assertTrue(result["configured"])
        self.assertTrue(result["providerReachable"])
        self.assertEqual(result["message"], "Dify 连接正常。")
        client.get.assert_awaited_once_with(
            "https://api.dify.example/v1/parameters",
            headers={"Authorization": "Bearer secret-key"},
        )

    async def test_dify_probe_failure_returns_safe_message(self):
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = False
        client.get.side_effect = httpx.ConnectError("connection failed")

        with (
            patch.object(main, "DIFY_API_URL", "https://api.dify.example/v1"),
            patch.object(main, "DIFY_API_KEY", "secret-key"),
            patch.object(main.httpx, "AsyncClient", return_value=client),
        ):
            result = await main._probe_dify_configuration()

        self.assertEqual(result["configured"], True)
        self.assertEqual(result["providerReachable"], False)
        self.assertEqual(result["message"], "Dify 已配置，但当前无法连接。")


class AiAnalysisProviderFailureTest(unittest.TestCase):
    def test_timeout_is_reported_as_generation_timeout_not_missing_configuration(self):
        message = provider_failure_message(TimeoutError("stream stalled"))

        self.assertIn("已连接", message)
        self.assertIn("生成超时", message)
        self.assertIn("额度", message)

    def test_rate_limit_is_reported_as_quota_or_rate_limit(self):
        request = httpx.Request("POST", "https://api.dify.example/v1/chat-messages")
        response = httpx.Response(429, request=request)
        message = provider_failure_message(httpx.HTTPStatusError("rate limited", request=request, response=response))

        self.assertIn("额度或调用频率", message)


class _FakeCursor:
    def __init__(self, user, classes):
        self.user = user
        self.classes = classes
        self.execute_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, *_args, **_kwargs):
        self.execute_count += 1

    def fetchone(self):
        return self.user

    def fetchall(self):
        return self.classes


class _FakeConnection:
    def __init__(self, user, classes):
        self.cursor_instance = _FakeCursor(user, classes)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self.cursor_instance


if __name__ == "__main__":
    unittest.main()
