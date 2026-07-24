import unittest

from teacher_knowledge_analysis_service import (
    AnalysisAlreadyRunningError,
    KnowledgeAnalysisRepository,
    KnowledgeAnalysisService,
    ProviderUnavailableError,
)


def evidence_loader(_teacher_id, _class_id, _course_id, _knowledge_point_id):
    return {
        "knowledgePointId": 71,
        "knowledgePointName": "联合查询列数判断",
        "attemptedCount": 10,
        "incorrectCount": 4,
        "commonMistakes": [{"answer": "直接猜三列", "studentCount": 3}],
        "representativeAttempts": [{"answer": "直接猜三列", "standardAnswer": "先用 ORDER BY 验证"}],
    }


def provider_result():
    return {
        "overallConclusion": "多数错误来自跳过列数验证。",
        "commonMistakes": [{"title": "直接猜列数", "reason": "未形成验证顺序"}],
        "teachingAdvice": [{"title": "先证据后结论", "action": "课堂演示 ORDER BY 递增验证"}],
        "exercises": [
            {"role": "FOUNDATION", "questionType": "short_answer", "stem": "如何判断列数？", "options": [], "standardAnswer": "使用 ORDER BY 递增", "explanation": "观察报错边界", "difficulty": 1, "generationRationale": "检查基础步骤"},
            {"role": "CONSOLIDATION", "questionType": "short_answer", "stem": "如何确认回显位？", "options": [], "standardAnswer": "使用 UNION SELECT 标记值", "explanation": "定位页面回显", "difficulty": 2, "generationRationale": "巩固同类技能"},
            {"role": "TRANSFER", "questionType": "short_answer", "stem": "无报错时怎样验证？", "options": [], "standardAnswer": "使用布尔或时间差异", "explanation": "迁移到盲注", "difficulty": 3, "generationRationale": "检查迁移能力"},
        ],
    }


class KnowledgeAnalysisServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = {}
        self.repository = KnowledgeAnalysisRepository(memory_store=self.store)

    async def test_transient_timeout_is_retried_once(self):
        calls = 0

        async def provider(_prompt, _user):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise TimeoutError()
            return provider_result()

        service = KnowledgeAnalysisService(
            self.repository,
            evidence_loader,
            provider,
            timeout_seconds=0.1,
            max_attempts=2,
        )

        result = await service.run_analysis(7, 101, 7, 71)

        self.assertEqual(calls, 2)
        self.assertEqual(result["analysisStatus"], "READY")

    async def test_bare_timeout_uses_current_evidence_instead_of_blocking_teacher(self):
        async def provider(_prompt, _user):
            raise TimeoutError()

        service = KnowledgeAnalysisService(
            self.repository,
            evidence_loader,
            provider,
            timeout_seconds=0.1,
            max_attempts=2,
        )

        result = await service.run_analysis(7, 101, 7, 71)

        self.assertEqual(result["analysisStatus"], "READY")
        self.assertIsNone(result["lastErrorMessage"])
        self.assertIn("联合查询列数判断", result["analysis"]["overallConclusion"])
        self.assertEqual(len(result["exercises"]), 3)
        self.assertTrue(all(item["standardAnswer"] for item in result["exercises"]))

    async def test_invalid_provider_shape_uses_real_mistakes_and_answers(self):
        async def provider(_prompt, _user):
            return {"answer": "不是约定的结构"}

        service = KnowledgeAnalysisService(self.repository, evidence_loader, provider)
        result = await service.run_analysis(7, 101, 7, 71)

        self.assertEqual(result["analysisStatus"], "READY")
        self.assertEqual(
            result["analysis"]["commonMistakes"][0]["answer"],
            "直接猜三列",
        )
        self.assertEqual(
            result["exercises"][0]["standardAnswer"],
            "先用 ORDER BY 验证",
        )

    async def test_malformed_provider_response_is_not_retried_before_evidence_result(self):
        calls = 0

        async def provider(_prompt, _user):
            nonlocal calls
            calls += 1
            raise ValueError("AI 返回内容不是有效结构化结果")

        service = KnowledgeAnalysisService(
            self.repository,
            evidence_loader,
            provider,
            max_attempts=2,
        )

        result = await service.run_analysis(7, 101, 7, 71)

        self.assertEqual(calls, 1)
        self.assertEqual(result["analysisStatus"], "READY")

    async def test_evidence_result_prefers_explanatory_standard_answer_over_choice_value(self):
        def mixed_evidence(*_args):
            return {
                **evidence_loader(*_args),
                "representativeAttempts": [
                    {"title": "选择题", "standardAnswer": "[2]"},
                    {
                        "title": "列数判断",
                        "standardAnswer": "从 ORDER BY 1 开始递增，首次报错的序号减一即为列数。",
                    },
                ],
            }

        async def provider(_prompt, _user):
            return {"answer": "不是约定的结构"}

        service = KnowledgeAnalysisService(self.repository, mixed_evidence, provider)
        result = await service.run_analysis(7, 101, 7, 71)

        self.assertIn("ORDER BY 1", result["exercises"][0]["standardAnswer"])
        self.assertIn("列数判断", result["exercises"][0]["stem"])

    async def test_success_persists_three_independent_pending_exercises(self):
        async def provider(_prompt, _user):
            return provider_result()

        service = KnowledgeAnalysisService(self.repository, evidence_loader, provider)
        result = await service.run_analysis(7, 101, 7, 71)

        self.assertEqual(result["analysisStatus"], "READY")
        self.assertEqual(len(result["exercises"]), 3)
        self.assertEqual({item["role"] for item in result["exercises"]}, {"FOUNDATION", "CONSOLIDATION", "TRANSFER"})
        self.assertTrue(all(item["reviewStatus"] == "PENDING_REVIEW" for item in result["exercises"]))

    async def test_failed_refresh_preserves_latest_success_and_review_status(self):
        calls = 0

        async def provider(_prompt, _user):
            nonlocal calls
            calls += 1
            if calls == 1:
                return provider_result()
            raise TimeoutError("provider timeout")

        service = KnowledgeAnalysisService(self.repository, evidence_loader, provider)
        first = await service.run_analysis(7, 101, 7, 71)
        approved = service.review_exercise(
            7,
            101,
            first["exercises"][0]["exerciseId"],
            "APPROVED",
            "可用于课堂",
        )
        refreshed = await service.run_analysis(7, 101, 7, 71)
        latest = service.get_analysis(7, 101, 7, 71)

        self.assertEqual(refreshed["analysis"], first["analysis"])
        self.assertEqual(latest["analysis"], first["analysis"])
        self.assertEqual(latest["analysisStatus"], "READY")
        self.assertTrue(latest["lastErrorMessage"])
        latest_first = next(
            item for item in latest["exercises"]
            if item["exerciseId"] == approved["exerciseId"]
        )
        self.assertEqual(latest_first["reviewStatus"], "APPROVED")
        self.assertEqual(latest_first["reviewComment"], "可用于课堂")
        self.assertEqual(latest_first["sourceVersion"], approved["sourceVersion"])

    async def test_running_analysis_is_rejected(self):
        self.repository.begin(7, 101, 7, 71)
        service = KnowledgeAnalysisService(self.repository, evidence_loader, lambda *_args: None)

        with self.assertRaises(AnalysisAlreadyRunningError):
            await service.run_analysis(7, 101, 7, 71)

    async def test_edit_resets_approval_and_review_is_independent(self):
        async def provider(_prompt, _user):
            return provider_result()

        service = KnowledgeAnalysisService(self.repository, evidence_loader, provider)
        result = await service.run_analysis(7, 101, 7, 71)
        first, second = result["exercises"][:2]
        approved = service.review_exercise(7, 101, first["exerciseId"], "APPROVED", "可下发")
        service.review_exercise(7, 101, second["exerciseId"], "REJECTED", "超出范围")
        edited = service.update_exercise(7, 101, first["exerciseId"], {"stem": "修改后的题干"})

        self.assertEqual(approved["reviewStatus"], "APPROVED")
        self.assertEqual(edited["reviewStatus"], "PENDING_REVIEW")
        self.assertEqual(edited["sourceVersion"], 2)
        latest = service.get_analysis(7, 101, 7, 71)
        statuses = {item["exerciseId"]: item["reviewStatus"] for item in latest["exercises"]}
        self.assertEqual(statuses[second["exerciseId"]], "REJECTED")

    async def test_regenerates_only_the_selected_exercise(self):
        calls = 0

        async def provider(_prompt, _user):
            nonlocal calls
            calls += 1
            if calls == 1:
                return provider_result()
            return {
                "role": "FOUNDATION",
                "questionType": "short_answer",
                "stem": "重新生成的基础题",
                "options": [],
                "standardAnswer": "先验证再判断",
                "explanation": "强调证据链",
                "difficulty": 1,
                "generationRationale": "替换不合适的基础题",
            }

        service = KnowledgeAnalysisService(self.repository, evidence_loader, provider)
        initial = await service.run_analysis(7, 101, 7, 71)
        first, second = initial["exercises"][:2]
        regenerated = await service.regenerate_exercise(7, 101, first["exerciseId"])
        latest = service.get_analysis(7, 101, 7, 71)

        self.assertEqual(regenerated["stem"], "重新生成的基础题")
        self.assertEqual(regenerated["sourceVersion"], 2)
        unchanged = next(item for item in latest["exercises"] if item["exerciseId"] == second["exerciseId"])
        self.assertEqual(unchanged["stem"], second["stem"])


if __name__ == "__main__":
    unittest.main()
