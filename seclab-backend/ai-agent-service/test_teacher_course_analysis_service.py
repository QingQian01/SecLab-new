import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from teacher_course_analysis_service import (
    TeacherCourseAnalysisRepository,
    build_course_question_summary,
    collect_course_question_records,
    run_course_analysis,
)
from training_repository import DEFAULT_TASK_KP


class TeacherCourseQuestionSummaryTest(unittest.TestCase):
    def setUp(self):
        self.records = [
            {
                "generatedQuestionId": "q-1",
                "student": {"studentId": 21, "studentName": "张晨", "studentNumber": "20260001"},
                "courseId": 2,
                "courseName": "XSS与CSRF攻击",
                "knowledgePointName": "XSS输出上下文",
                "title": "识别属性上下文",
                "attemptHistory": [
                    {"attemptId": "a-1", "isCorrect": False, "score": 40, "submittedAt": "2026-07-14T09:00:00"},
                    {"attemptId": "a-2", "isCorrect": True, "score": 90, "submittedAt": "2026-07-14T09:08:00"},
                ],
            },
            {
                "generatedQuestionId": "q-2",
                "student": {"studentId": 22, "studentName": "李晴", "studentNumber": "20260002"},
                "courseId": 2,
                "courseName": "XSS与CSRF攻击",
                "knowledgePointName": "XSS输出上下文",
                "title": "选择编码方式",
                "attemptHistory": [
                    {"attemptId": "a-3", "isCorrect": False, "score": 20, "submittedAt": "2026-07-14T10:00:00"},
                ],
            },
        ]

    def test_summary_counts_all_attempts_but_accuracy_uses_latest_result(self):
        summary = build_course_question_summary(self.records)

        self.assertEqual(summary["questionCount"], 2)
        self.assertEqual(summary["attemptCount"], 3)
        self.assertEqual(summary["correctQuestionCount"], 1)
        self.assertEqual(summary["incorrectQuestionCount"], 1)
        self.assertEqual(summary["accuracyRate"], 0.5)
        self.assertEqual(summary["studentCount"], 2)

    def test_summary_keeps_student_and_knowledge_point_drill_down(self):
        summary = build_course_question_summary(self.records)

        zhang = next(item for item in summary["students"] if item["studentId"] == 21)
        self.assertEqual(zhang["attemptCount"], 2)
        self.assertEqual(summary["knowledgePoints"][0]["incorrectQuestionCount"], 1)
        self.assertEqual(summary["knowledgePoints"][0]["affectedStudentCount"], 1)

class TeacherCourseAnalysisRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.store = {}
        self.repository = TeacherCourseAnalysisRepository(memory_store=self.store)
        self.cutoff = datetime(2026, 7, 17, 9, 0, 0)

    def test_course_and_scope_have_independent_results(self):
        self.repository.save_success(7, 101, 1, "CLASS", 0, self.cutoff, {"overallComment": "SQL班级"}, {})
        self.repository.save_success(7, 101, 2, "STUDENT", 21, self.cutoff, {"overallComment": "张晨XSS"}, {})

        class_result = self.repository.get_latest(7, 101, 1, "CLASS", 0)
        student_result = self.repository.get_latest(7, 101, 2, "STUDENT", 21)

        self.assertEqual(class_result["analysis"]["overallComment"], "SQL班级")
        self.assertEqual(student_result["analysis"]["overallComment"], "张晨XSS")
        self.assertEqual(student_result["courseId"], 2)

    def test_failed_refresh_preserves_previous_course_result(self):
        self.repository.save_success(7, 101, 2, "STUDENT", 21, self.cutoff, {"overallComment": "旧结果"}, {})
        self.repository.begin(7, 101, 2, "STUDENT", 21, self.cutoff + timedelta(hours=1))
        self.repository.save_failure(7, 101, 2, "STUDENT", 21, "Dify超时")

        result = self.repository.get_latest(7, 101, 2, "STUDENT", 21)

        self.assertEqual(result["analysisStatus"], "FAILED")
        self.assertIsNone(result["analysis"])
        self.assertEqual(result["lastErrorMessage"], "Dify超时")

    def test_legacy_fallback_result_is_not_returned(self):
        self.repository.save_success(
            7,
            101,
            2,
            "CLASS",
            0,
            self.cutoff,
            {"generatedBy": "course_evidence_fallback", "fallbackUsed": True},
            {},
        )

        result = self.repository.get_latest(7, 101, 2, "CLASS", 0)

        self.assertEqual(result["analysisStatus"], "IDLE")
        self.assertIsNone(result["analysis"])


class _FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.sql = ""
        self.params = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params or {}

    def fetchall(self):
        return self.rows


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor


class TeacherCourseRealSubmissionTest(unittest.TestCase):
    def test_sql_injection_detection_task_has_a_knowledge_point_mapping(self):
        self.assertIn((1, 3, 102), DEFAULT_TASK_KP)

    def test_collects_persisted_course_question_submissions_for_teaching_class(self):
        cursor = _FakeCursor([
            {
                "attempt_key": "submission:sub-1",
                "student_id": 295,
                "course_id": 1,
                "knowledge_point_id": 102,
                "knowledge_point_name": "SQL盲注与时间延迟判断",
                "is_correct": 1,
                "answer_json": "[1]",
                "score": 4,
                "cost_time": 35,
                "submitted_at": datetime(2026, 7, 24, 12, 18),
                "generated_question_id": "1",
                "title": "实验题 3-1",
                "standard_answer": "[1]",
                "student_name": "姜理想",
                "student_number": "2023210405029",
                "teaching_class_name": "网络安全232班",
            },
        ])
        current_user = {"user_id": 1, "role": "teacher"}

        with (
            patch("teacher_course_analysis_service.require_course_in_owned_class", return_value={"courseId": 1, "courseName": "SQL注入基础实验"}),
            patch("teacher_course_analysis_service.require_student_in_owned_teaching_class"),
            patch("teacher_course_analysis_service.get_connection", return_value=_FakeConnection(cursor)),
        ):
            result = collect_course_question_records(1, 1, current_user, student_id=295)

        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["student"]["studentId"], 295)
        self.assertEqual(result["items"][0]["attemptHistory"][0]["isCorrect"], True)
        self.assertIn("teaching_class_student", cursor.sql)
        self.assertEqual(cursor.params["class_id"], 1)
        self.assertEqual(cursor.params["course_id"], 1)

    def test_analysis_provider_failure_is_not_replaced_with_fallback(self):
        current_user = {"user_id": 1, "role": "teacher"}
        evidence = {
            "items": [{"generatedQuestionId": "course-295-1-3-1", "attemptHistory": [{"isCorrect": True}]}],
            "summary": {"questionCount": 1},
            "course": {"courseId": 1, "courseName": "SQL注入基础实验"},
        }
        repository = Mock()

        with (
            patch("teacher_course_analysis_service.collect_course_question_records", return_value=evidence),
            patch("teacher_course_analysis_service._call_dify_for_student_analysis", new=AsyncMock(side_effect=RuntimeError("provider down"))),
            patch("teacher_course_analysis_service.COURSE_ANALYSIS_REPOSITORY", repository),
        ):
            with self.assertRaises(RuntimeError):
                asyncio.run(run_course_analysis(1, 1, current_user))

        repository.save_failure.assert_called_once()
        repository.save_success.assert_not_called()


if __name__ == "__main__":
    unittest.main()
