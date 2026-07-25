"""guidance_service 单元测试。

测试范围（不依赖 DB / Dify 网络）：
- 纯函数：``_to_int`` / ``_build_context`` / ``_build_dify_inputs`` / ``_build_query``
- ``handle_signal``：用 ``unittest.mock.patch`` 替换 ``ai_repository.ensure_guidance_conversation``
  与 ``error_repository.save_error_event``，验证预处理逻辑（分类、调用契约）。
- ``dispatch_signal_task``：mock ``handle_signal`` / ``asyncio.create_task`` /
  ``guidance_stream_registry.subscriber_count``，验证返回结构和"启动后台任务"的契约。

运行方式（Windows）::

    py -m unittest test_guidance_service -v
"""
import asyncio
import unittest
from unittest import mock

import guidance_service


class GuidancePureFunctionsTest(unittest.TestCase):
    """纯函数测试：无 IO 依赖。"""

    def test_to_int_handles_none_empty_and_invalid(self):
        self.assertIsNone(guidance_service._to_int(None))
        self.assertIsNone(guidance_service._to_int(""))
        self.assertIsNone(guidance_service._to_int("abc"))
        self.assertIsNone(guidance_service._to_int({"x": 1}))
        self.assertEqual(guidance_service._to_int(5), 5)
        self.assertEqual(guidance_service._to_int("7"), 7)
        self.assertEqual(guidance_service._to_int(0), 0)

    def test_build_context_extracts_all_fields(self):
        signal = {
            "user_id": "10",
            "class_id": 2,
            "course_id": "3",
            "module_id": 4,
            "task_id": "5",
            "lab_session_id": "lab-xyz",
        }
        ctx = guidance_service._build_context(signal)
        self.assertEqual(ctx, {
            "user_id": 10,
            "class_id": 2,
            "course_id": 3,
            "module_id": 4,
            "task_id": 5,
            "question_id": None,
        })

    def test_build_context_handles_missing_fields(self):
        ctx = guidance_service._build_context({})
        self.assertEqual(ctx, {
            "user_id": None,
            "class_id": None,
            "course_id": None,
            "module_id": None,
            "task_id": None,
            "question_id": None,
        })

    def test_build_dify_inputs_truncates_long_fields(self):
        long_error = "E" * 2000
        long_commands = ["cmd-" + str(i) for i in range(200)]
        long_task = "T" * 2000
        signal = {
            "trigger_reason": "repeated_error",
            "container_name": "sqli-lab-web-1",
            "lab_key": "sqli-lab",
            "error_slice": long_error,
            "recent_commands": long_commands,
            "lab_task_summary": long_task,
            "frustration_score": 7,
            "locale": "zh-CN",
        }
        inputs = guidance_service._build_dify_inputs(signal)
        self.assertEqual(inputs["trigger_reason"], "repeated_error")
        self.assertEqual(inputs["container_name"], "sqli-lab-web-1")
        self.assertEqual(inputs["lab_key"], "sqli-lab")
        self.assertEqual(inputs["frustration_score"], 7)
        self.assertEqual(inputs["locale"], "zh-CN")
        # 截断到 800 字符以内
        self.assertLessEqual(len(inputs["error_slice"]), 800)
        self.assertLessEqual(len(inputs["lab_task_summary"]), 800)
        self.assertLessEqual(len(inputs["recent_commands"]), 800)
        # recent_commands 仍是合法 JSON
        import json as _json
        self.assertIsInstance(_json.loads(inputs["recent_commands"]), list)

    def test_build_dify_inputs_handles_empty_signal(self):
        inputs = guidance_service._build_dify_inputs({})
        self.assertEqual(inputs["trigger_reason"], "")
        self.assertEqual(inputs["container_name"], "")
        self.assertEqual(inputs["frustration_score"], 0)
        self.assertEqual(inputs["locale"], "zh-CN")

    def test_build_query_includes_all_sections(self):
        signal = {
            "container_name": "sqli-lab-web-1",
            "lab_key": "sqli-lab",
            "trigger_reason": "repeated_error",
            "error_slice": "permission denied: /etc/shadow",
            "recent_commands": ["cat /etc/shadow", "ls /var/lib/mysql"],
            "lab_task_summary": "完成 SQL 注入实验",
        }
        error_classified = {
            "error_signature": "permission_denied",
            "error_category": "permission",
            "severity": "high",
        }
        query = guidance_service._build_query(signal, error_classified)
        # 各关键段落都应出现
        self.assertIn("sqli-lab-web-1", query)
        self.assertIn("repeated_error", query)
        self.assertIn("permission_denied", query)
        self.assertIn("permission", query)
        self.assertIn("permission denied: /etc/shadow", query)
        self.assertIn("cat /etc/shadow", query)
        self.assertIn("完成 SQL 注入实验", query)
        # 启发式诊断风格提示应出现
        self.assertIn("启发式", query)

    def test_build_query_handles_missing_error_classified(self):
        signal = {
            "container_name": "xss-lab-web-1",
            "lab_key": "xss-lab",
            "trigger_reason": "stuck_loop",
        }
        query = guidance_service._build_query(signal, None)
        self.assertIn("xss-lab-web-1", query)
        self.assertIn("stuck_loop", query)
        # 无 error_classified 时不应崩溃
        self.assertIsInstance(query, str)
        self.assertGreater(len(query), 0)


class HandleSignalTest(unittest.TestCase):
    """handle_signal 测试：mock ai_repository 与 error_repository。"""

    def test_handle_signal_classifies_error_and_ensures_conversation(self):
        signal = {
            "signal_id": "sig-001",
            "lab_session_id": "lab-001",
            "user_id": "10",
            "class_id": 2,
            "course_id": 3,
            "module_id": 4,
            "task_id": 5,
            "container_name": "sqli-lab-web-1",
            "error_slice": "permission denied: /etc/shadow",
            "trigger_reason": "repeated_error",
            "triggered_at": "2026-07-20T10:00:00",
        }

        with mock.patch.object(
            guidance_service.error_repository, "classify_error_excerpt"
        ) as mock_classify, mock.patch.object(
            guidance_service.error_repository, "save_error_event"
        ) as mock_save_err, mock.patch.object(
            guidance_service.ai_repository, "ensure_guidance_conversation"
        ) as mock_ensure:
            mock_classify.return_value = {
                "error_signature": "permission_denied",
                "error_category": "permission",
                "severity": "high",
            }
            mock_ensure.return_value = {
                "conversation_id": "guidance-lab-001",
                "dify_conversation_id": None,
            }

            prepared = guidance_service.handle_signal(signal)

        # 分类函数被调用
        mock_classify.assert_called_once()
        args, kwargs = mock_classify.call_args
        self.assertEqual(args[0], "permission denied: /etc/shadow")
        self.assertEqual(kwargs.get("exit_code"), None)

        # 错误事件被持久化（参数校验关键字段）
        mock_save_err.assert_called_once()
        saved = mock_save_err.call_args[0][0]
        self.assertEqual(saved["lab_session_id"], "lab-001")
        self.assertEqual(saved["error_signature"], "permission_denied")
        self.assertEqual(saved["source"], "guidance-proactive")
        self.assertEqual(saved["raw_excerpt"], "permission denied: /etc/shadow")

        # 会话被查找/创建（传入 safe_lab_session_id 与 context）
        mock_ensure.assert_called_once()
        ensure_kwargs = mock_ensure.call_args[1]
        self.assertEqual(ensure_kwargs["lab_session_id"], "lab-001")
        self.assertEqual(ensure_kwargs["context"]["user_id"], 10)
        self.assertEqual(ensure_kwargs["context"]["task_id"], 5)

        # 返回结构完整
        self.assertEqual(prepared["conversation_id"], "guidance-lab-001")
        self.assertIsNone(prepared["dify_conversation_id"])
        self.assertEqual(prepared["lab_session_id"], "lab-001")
        self.assertEqual(prepared["user_id"], 10)
        self.assertEqual(prepared["error_classified"]["error_signature"], "permission_denied")
        self.assertIsInstance(prepared["query"], str)
        self.assertIsInstance(prepared["inputs"], dict)

    def test_handle_signal_skips_classification_when_no_error_slice(self):
        """无 error_slice 时不分类、不持久化错误事件，但仍 ensure 会话。"""
        signal = {
            "signal_id": "sig-002",
            "lab_session_id": "lab-002",
            "trigger_reason": "stuck_loop",
            "container_name": "xss-lab-web-1",
            "lab_key": "xss-lab",
            "recent_commands": ["ls", "ls", "ls"],
        }

        with mock.patch.object(
            guidance_service.error_repository, "classify_error_excerpt"
        ) as mock_classify, mock.patch.object(
            guidance_service.error_repository, "save_error_event"
        ) as mock_save_err, mock.patch.object(
            guidance_service.ai_repository, "ensure_guidance_conversation"
        ) as mock_ensure:
            mock_ensure.return_value = {
                "conversation_id": "guidance-lab-002",
                "dify_conversation_id": None,
            }

            prepared = guidance_service.handle_signal(signal)

        mock_classify.assert_not_called()
        mock_save_err.assert_not_called()
        mock_ensure.assert_called_once()
        self.assertEqual(prepared["conversation_id"], "guidance-lab-002")
        self.assertIsNone(prepared["error_classified"])
        # query 仍可构造
        self.assertIn("xss-lab-web-1", prepared["query"])

    def test_handle_signal_anon_lab_session_when_missing(self):
        """无 lab_session_id 时用 anon-{signal_id} 兜底，避免会话表空值。"""
        signal = {
            "signal_id": "sig-003",
            "trigger_reason": "stuck_loop",
        }

        with mock.patch.object(
            guidance_service.error_repository, "classify_error_excerpt"
        ), mock.patch.object(
            guidance_service.error_repository, "save_error_event"
        ), mock.patch.object(
            guidance_service.ai_repository, "ensure_guidance_conversation"
        ) as mock_ensure:
            mock_ensure.return_value = {
                "conversation_id": "guidance-anon-sig-003",
                "dify_conversation_id": None,
            }
            prepared = guidance_service.handle_signal(signal)

        ensure_kwargs = mock_ensure.call_args[1]
        self.assertEqual(ensure_kwargs["lab_session_id"], "anon-sig-003")
        self.assertEqual(prepared["lab_session_id"], "anon-sig-003")

    def test_handle_signal_continues_when_save_error_event_fails(self):
        """save_error_event 抛异常时不应阻塞 ensure_guidance_conversation。"""
        signal = {
            "signal_id": "sig-004",
            "lab_session_id": "lab-004",
            "error_slice": "permission denied",
            "trigger_reason": "repeated_error",
        }

        with mock.patch.object(
            guidance_service.error_repository, "classify_error_excerpt"
        ) as mock_classify, mock.patch.object(
            guidance_service.error_repository, "save_error_event",
            side_effect=RuntimeError("db down"),
        ), mock.patch.object(
            guidance_service.ai_repository, "ensure_guidance_conversation"
        ) as mock_ensure:
            mock_classify.return_value = {
                "error_signature": "permission_denied",
                "error_category": "permission",
                "severity": "high",
            }
            mock_ensure.return_value = {
                "conversation_id": "guidance-lab-004",
                "dify_conversation_id": None,
            }
            # 不应抛
            prepared = guidance_service.handle_signal(signal)

        # ensure 仍被调用
        mock_ensure.assert_called_once()
        self.assertEqual(prepared["conversation_id"], "guidance-lab-004")


class DispatchSignalTaskTest(unittest.TestCase):
    """dispatch_signal_task 测试：mock handle_signal / asyncio.create_task。"""

    def test_dispatch_returns_summary_and_schedules_task(self):
        signal = {
            "signal_id": "sig-dispatch-1",
            "lab_session_id": "lab-dispatch",
            "trigger_reason": "repeated_error",
        }
        prepared = {
            "conversation_id": "guidance-lab-dispatch",
            "dify_conversation_id": None,
            "query": "test query",
            "inputs": {"trigger_reason": "repeated_error"},
            "user_id": 10,
            "lab_session_id": "lab-dispatch",
            "error_classified": None,
        }

        scheduled_coros = []

        def fake_create_task(coro):
            # 捕获 coro 不真正调度；调用方负责 close 避免 warning
            scheduled_coros.append(coro)
            return mock.MagicMock(name="Task")

        with mock.patch.object(
            guidance_service, "handle_signal", return_value=prepared
        ) as mock_handle, mock.patch.object(
            guidance_service.asyncio, "create_task", side_effect=fake_create_task
        ) as mock_create, mock.patch.object(
            guidance_service.guidance_stream_registry, "subscriber_count", return_value=2
        ) as mock_count:
            result = guidance_service.dispatch_signal_task(signal)

        mock_handle.assert_called_once_with(signal)
        mock_create.assert_called_once()
        mock_count.assert_called_once_with("lab-dispatch")
        self.assertEqual(result, {
            "signal_id": "sig-dispatch-1",
            "conversation_id": "guidance-lab-dispatch",
            "subscriber_count": 2,
            "accepted": True,
        })
        # 后台 coro 已被捕获（不实际执行，避免触发 Dify 调用）
        self.assertEqual(len(scheduled_coros), 1)
        # 关闭 coro 避免 'coroutine was never awaited' 警告
        scheduled_coros[0].close()

    def test_dispatch_generates_signal_id_when_missing(self):
        signal = {
            "lab_session_id": "lab-no-sigid",
            "trigger_reason": "stuck_loop",
        }
        prepared = {
            "conversation_id": "guidance-lab-no-sigid",
            "dify_conversation_id": None,
            "query": "q",
            "inputs": {},
            "user_id": None,
            "lab_session_id": "lab-no-sigid",
            "error_classified": None,
        }
        scheduled_coros = []

        def fake_create_task(coro):
            scheduled_coros.append(coro)
            return mock.MagicMock(name="Task")

        with mock.patch.object(
            guidance_service, "handle_signal", return_value=prepared
        ), mock.patch.object(
            guidance_service.asyncio, "create_task", side_effect=fake_create_task
        ), mock.patch.object(
            guidance_service.guidance_stream_registry, "subscriber_count", return_value=0
        ):
            result = guidance_service.dispatch_signal_task(signal)

        self.assertTrue(result["signal_id"].startswith("sig-"))
        self.assertEqual(result["subscriber_count"], 0)
        self.assertTrue(result["accepted"])
        scheduled_coros[0].close()


if __name__ == "__main__":
    unittest.main()