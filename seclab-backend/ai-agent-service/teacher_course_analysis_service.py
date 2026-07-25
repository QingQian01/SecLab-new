from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from database import get_connection
from teacher_ai_analysis_service import _call_dify_for_student_analysis, provider_failure_message
from teacher_analysis_repository import AnalysisAlreadyRunningError
from teacher_repository import (
    list_generated_questions_for_teacher,
    require_owned_teaching_class,
    require_student_in_owned_teaching_class,
)
from training_repository import list_generated_question_attempts


USER_SERVICE_SCHEMA = "userservice"


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _json_loads(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _latest(attempts: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    return attempts[-1] if attempts else None


def build_course_question_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    student_groups: dict[int, dict[str, Any]] = {}
    knowledge_groups: dict[str, dict[str, Any]] = {}
    latest_attempts = [attempt for item in records if (attempt := _latest(item.get("attemptHistory") or []))]

    for item in records:
        student = item.get("student") or {}
        student_id = int(student.get("studentId") or 0)
        student_group = student_groups.setdefault(
            student_id,
            {
                "studentId": student_id,
                "studentName": student.get("studentName") or "未知学生",
                "studentNumber": student.get("studentNumber"),
                "questionCount": 0,
                "attemptCount": 0,
                "correctQuestionCount": 0,
                "incorrectQuestionCount": 0,
            },
        )
        attempts = item.get("attemptHistory") or []
        latest = _latest(attempts)
        student_group["questionCount"] += 1
        student_group["attemptCount"] += len(attempts)
        if latest and latest.get("isCorrect") is True:
            student_group["correctQuestionCount"] += 1
        elif latest and latest.get("isCorrect") is False:
            student_group["incorrectQuestionCount"] += 1

        knowledge_name = str(item.get("knowledgePointName") or "未标注知识点")
        knowledge_group = knowledge_groups.setdefault(
            knowledge_name,
            {
                "knowledgePointName": knowledge_name,
                "questionCount": 0,
                "attemptCount": 0,
                "correctQuestionCount": 0,
                "incorrectQuestionCount": 0,
                "affectedStudentIds": set(),
            },
        )
        knowledge_group["questionCount"] += 1
        knowledge_group["attemptCount"] += len(attempts)
        if latest and latest.get("isCorrect") is True:
            knowledge_group["correctQuestionCount"] += 1
        elif latest and latest.get("isCorrect") is False:
            knowledge_group["incorrectQuestionCount"] += 1
            knowledge_group["affectedStudentIds"].add(student_id)

    attempted_questions = len(latest_attempts)
    correct_questions = sum(1 for item in latest_attempts if item.get("isCorrect") is True)
    incorrect_questions = sum(1 for item in latest_attempts if item.get("isCorrect") is False)
    scores = [float(item.get("score") or 0) for item in latest_attempts]

    students = []
    for item in student_groups.values():
        attempted = item["correctQuestionCount"] + item["incorrectQuestionCount"]
        item["accuracyRate"] = round(item["correctQuestionCount"] / attempted, 4) if attempted else 0.0
        students.append(item)
    students.sort(key=lambda item: (-item["incorrectQuestionCount"], item["studentNumber"] or ""))

    knowledge_points = []
    for item in knowledge_groups.values():
        affected = item.pop("affectedStudentIds")
        attempted = item["correctQuestionCount"] + item["incorrectQuestionCount"]
        item["affectedStudentCount"] = len(affected)
        item["accuracyRate"] = round(item["correctQuestionCount"] / attempted, 4) if attempted else 0.0
        knowledge_points.append(item)
    knowledge_points.sort(key=lambda item: (-item["incorrectQuestionCount"], item["knowledgePointName"]))

    return {
        "studentCount": len(student_groups),
        "questionCount": len(records),
        "attemptedQuestionCount": attempted_questions,
        "attemptCount": sum(len(item.get("attemptHistory") or []) for item in records),
        "correctQuestionCount": correct_questions,
        "incorrectQuestionCount": incorrect_questions,
        "accuracyRate": round(correct_questions / attempted_questions, 4) if attempted_questions else 0.0,
        "averageScore": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "students": students,
        "knowledgePoints": knowledge_points,
    }


def build_course_analysis_fallback(
    records: list[dict[str, Any]],
    *,
    scope: str,
    course: dict[str, Any],
    provider_message: Optional[str] = None,
) -> dict[str, Any]:
    summary = build_course_question_summary(records)
    course_name = str(course.get("courseName") or "当前课程")
    weak = [item for item in summary["knowledgePoints"] if item["incorrectQuestionCount"] > 0][:3]
    representative = []
    for item in records:
        latest = _latest(item.get("attemptHistory") or [])
        if latest and latest.get("isCorrect") is False:
            representative.append(
                {
                    "generatedQuestionId": item.get("generatedQuestionId"),
                    "title": item.get("title") or "未命名题目",
                    "studentName": (item.get("student") or {}).get("studentName"),
                    "knowledgePointName": item.get("knowledgePointName") or "未标注知识点",
                    "latestAnswer": latest.get("answer"),
                    "standardAnswer": item.get("standardAnswer") or item.get("referenceAnswer"),
                    "score": latest.get("score"),
                }
            )
        if len(representative) >= 5:
            break
    focus_text = "、".join(item["knowledgePointName"] for item in weak) or "暂无集中错误知识点"
    return {
        "scope": "student_course" if scope.upper() == "STUDENT" or scope.lower() == "student" else "class_course",
        "courseId": int(course.get("courseId") or 0),
        "courseName": course_name,
        "generatedBy": "course_evidence_fallback",
        "fallbackUsed": True,
        "providerMessage": provider_message,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "overallComment": (
            f"{course_name}共记录 {summary['questionCount']} 道题、{summary['attemptCount']} 次作答，"
            f"按每道题最后一次作答统计正确率为 {summary['accuracyRate'] * 100:.1f}%。重点关注：{focus_text}。"
        ),
        "summary": summary,
        "knowledgeFindings": [
            {
                **item,
                "evidence": f"该知识点有 {item['incorrectQuestionCount']} 道题最后一次仍答错，涉及 {item['affectedStudentCount']} 名学生。",
                "teacherAction": "打开下方错题查看学生答案与标准答案，讲评后下发同知识点变式题。",
            }
            for item in weak
        ],
        "representativeMistakes": representative,
        "teachingSuggestions": [
            "优先讲解最后一次仍答错的题目，并要求学生说明错误原因。",
            "对同一题重试后答对的学生，抽查其修正过程而不只看最终答案。",
            "五维画像仅作为跨课程统计参考，课程结论以本课程真实作答证据为准。",
        ],
    }


class TeacherCourseAnalysisRepository:
    def __init__(
        self,
        connection_factory: Callable[..., Any] = get_connection,
        memory_store: Optional[dict[tuple[int, int, int, str, int], dict[str, Any]]] = None,
    ):
        self.connection_factory = connection_factory
        self.memory_store = memory_store

    @staticmethod
    def _key(teacher_id: int, class_id: int, course_id: int, scope: str, student_id: int) -> tuple[int, int, int, str, int]:
        return teacher_id, class_id, course_id, scope.upper(), student_id

    def _empty(self, key: tuple[int, int, int, str, int]) -> dict[str, Any]:
        teacher_id, class_id, course_id, scope, student_id = key
        return {"teacher_id": teacher_id, "teaching_class_id": class_id, "course_id": course_id, "scope": scope, "student_id": student_id, "analysis_status": "IDLE", "analysis_json": None, "source_stats_json": None, "last_error_message": None, "generated_at": None}

    def ensure_schema(self) -> None:
        if self.memory_store is not None:
            return
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS teacher_course_analysis (
                        teacher_id BIGINT NOT NULL,
                        teaching_class_id BIGINT NOT NULL,
                        course_id INT NOT NULL,
                        analysis_scope VARCHAR(16) NOT NULL,
                        student_id BIGINT NOT NULL DEFAULT 0,
                        analysis_status VARCHAR(16) NOT NULL DEFAULT 'IDLE',
                        analysis_json LONGTEXT NULL,
                        source_stats_json LONGTEXT NULL,
                        data_cutoff_at DATETIME(6) NULL,
                        last_attempt_at DATETIME(6) NULL,
                        last_error_message VARCHAR(500) NULL,
                        generated_at DATETIME(6) NULL,
                        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                        PRIMARY KEY (teacher_id, teaching_class_id, course_id, analysis_scope, student_id),
                        KEY idx_teacher_course_analysis_lookup (teaching_class_id, course_id, analysis_scope, student_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                )
            conn.commit()

    def begin(self, teacher_id: int, class_id: int, course_id: int, scope: str, student_id: int, cutoff: datetime) -> None:
        key = self._key(teacher_id, class_id, course_id, scope, student_id)
        if self.memory_store is not None:
            row = self.memory_store.setdefault(key, self._empty(key))
            if row["analysis_status"] == "RUNNING":
                raise AnalysisAlreadyRunningError("course analysis is already running")
            row.update(analysis_status="RUNNING", data_cutoff_at=cutoff, last_attempt_at=datetime.now(), last_error_message=None)
            return
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO teacher_course_analysis (teacher_id, teaching_class_id, course_id, analysis_scope, student_id, analysis_status, data_cutoff_at, last_attempt_at)
                    VALUES (%(teacher_id)s, %(class_id)s, %(course_id)s, %(scope)s, %(student_id)s, 'RUNNING', %(cutoff)s, NOW(6))
                    ON DUPLICATE KEY UPDATE analysis_status='RUNNING', data_cutoff_at=VALUES(data_cutoff_at), last_attempt_at=NOW(6), last_error_message=NULL
                    """,
                    {"teacher_id": teacher_id, "class_id": class_id, "course_id": course_id, "scope": scope.upper(), "student_id": student_id, "cutoff": cutoff},
                )
            conn.commit()

    def save_success(self, teacher_id: int, class_id: int, course_id: int, scope: str, student_id: int, cutoff: datetime, analysis: dict[str, Any], stats: dict[str, Any]) -> None:
        key = self._key(teacher_id, class_id, course_id, scope, student_id)
        if self.memory_store is not None:
            row = self.memory_store.setdefault(key, self._empty(key))
            row.update(analysis_status="READY", analysis_json=analysis, source_stats_json=stats, data_cutoff_at=cutoff, generated_at=datetime.now(), last_error_message=None)
            return
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO teacher_course_analysis (teacher_id, teaching_class_id, course_id, analysis_scope, student_id, analysis_status, analysis_json, source_stats_json, data_cutoff_at, generated_at)
                    VALUES (%(teacher_id)s, %(class_id)s, %(course_id)s, %(scope)s, %(student_id)s, 'READY', %(analysis)s, %(stats)s, %(cutoff)s, NOW(6))
                    ON DUPLICATE KEY UPDATE analysis_status='READY', analysis_json=VALUES(analysis_json), source_stats_json=VALUES(source_stats_json), data_cutoff_at=VALUES(data_cutoff_at), generated_at=NOW(6), last_error_message=NULL
                    """,
                    {"teacher_id": teacher_id, "class_id": class_id, "course_id": course_id, "scope": scope.upper(), "student_id": student_id, "analysis": json.dumps(analysis, ensure_ascii=False), "stats": json.dumps(stats, ensure_ascii=False), "cutoff": cutoff},
                )
            conn.commit()

    def save_failure(self, teacher_id: int, class_id: int, course_id: int, scope: str, student_id: int, message: str) -> None:
        key = self._key(teacher_id, class_id, course_id, scope, student_id)
        if self.memory_store is not None:
            row = self.memory_store.setdefault(key, self._empty(key))
            row["analysis_status"] = "READY" if row.get("analysis_json") else "FAILED"
            row["last_error_message"] = message
            return
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE teacher_course_analysis SET analysis_status=IF(analysis_json IS NULL,'FAILED','READY'), last_error_message=%(message)s WHERE teacher_id=%(teacher_id)s AND teaching_class_id=%(class_id)s AND course_id=%(course_id)s AND analysis_scope=%(scope)s AND student_id=%(student_id)s", {"teacher_id": teacher_id, "class_id": class_id, "course_id": course_id, "scope": scope.upper(), "student_id": student_id, "message": str(message)[:500]})
            conn.commit()

    def get_latest(self, teacher_id: int, class_id: int, course_id: int, scope: str, student_id: int) -> dict[str, Any]:
        key = self._key(teacher_id, class_id, course_id, scope, student_id)
        if self.memory_store is not None:
            row = self.memory_store.get(key, self._empty(key))
        else:
            self.ensure_schema()
            with self.connection_factory() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM teacher_course_analysis WHERE teacher_id=%(teacher_id)s AND teaching_class_id=%(class_id)s AND course_id=%(course_id)s AND analysis_scope=%(scope)s AND student_id=%(student_id)s", {"teacher_id": teacher_id, "class_id": class_id, "course_id": course_id, "scope": scope.upper(), "student_id": student_id})
                    row = cursor.fetchone() or self._empty(key)
        return {"teacherId": teacher_id, "teachingClassId": class_id, "courseId": course_id, "scope": scope.upper(), "studentId": student_id or None, "analysisStatus": row.get("analysis_status") or "IDLE", "analysis": _json_loads(row.get("analysis_json")), "sourceStats": _json_loads(row.get("source_stats_json")), "lastErrorMessage": row.get("last_error_message"), "generatedAt": _iso(row.get("generated_at"))}


COURSE_ANALYSIS_REPOSITORY = TeacherCourseAnalysisRepository()


def require_course_in_owned_class(teacher_id: int, class_id: int, course_id: int) -> dict[str, Any]:
    require_owned_teaching_class(teacher_id, class_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT c.id AS course_id, c.course_name FROM `{USER_SERVICE_SCHEMA}`.`teaching_class_course` tcc INNER JOIN `{USER_SERVICE_SCHEMA}`.`course` c ON c.id=tcc.course_id WHERE tcc.teaching_class_id=%(class_id)s AND tcc.course_id=%(course_id)s LIMIT 1", {"class_id": class_id, "course_id": course_id})
            row = cursor.fetchone()
    if not row:
        raise PermissionError("course is outside the selected teaching class")
    return {"courseId": int(row["course_id"]), "courseName": row.get("course_name") or f"课程 {course_id}"}


def collect_course_question_records(class_id: int, course_id: int, current_user: dict[str, Any], student_id: Optional[int] = None) -> dict[str, Any]:
    teacher_id = int(current_user.get("user_id") or 0)
    course = require_course_in_owned_class(teacher_id, class_id, course_id)
    if student_id is not None:
        require_student_in_owned_teaching_class(teacher_id, class_id, student_id)
    first = list_generated_questions_for_teacher(current_user=current_user, teaching_class_id=class_id, course_id=course_id, student_id=student_id, page=1, size=100)
    records = list(first.get("items") or [])
    page = 2
    while len(records) < int(first.get("total") or 0):
        batch = list_generated_questions_for_teacher(current_user=current_user, teaching_class_id=class_id, course_id=course_id, student_id=student_id, page=page, size=100)
        records.extend(batch.get("items") or [])
        page += 1
    attempts_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for session_id in {item.get("trainingSessionId") for item in records if item.get("trainingSessionId")}:
        for attempt in list_generated_question_attempts(str(session_id), user_id=student_id):
            attempts_by_question[str(attempt.get("generated_question_id"))].append({"attemptId": attempt.get("attempt_id"), "answer": attempt.get("answer"), "isCorrect": attempt.get("is_correct"), "score": attempt.get("score"), "costTime": attempt.get("cost_time"), "submittedAt": attempt.get("submitted_at")})
    for item in records:
        item["attemptHistory"] = attempts_by_question.get(str(item.get("generatedQuestionId")), [])
    return {"success": True, "teachingClassId": class_id, "course": course, "studentId": student_id, "items": records, "summary": build_course_question_summary(records)}


def get_course_analysis(class_id: int, course_id: int, current_user: dict[str, Any], student_id: Optional[int] = None) -> dict[str, Any]:
    teacher_id = int(current_user.get("user_id") or 0)
    require_course_in_owned_class(teacher_id, class_id, course_id)
    if student_id is not None:
        require_student_in_owned_teaching_class(teacher_id, class_id, student_id)
    return COURSE_ANALYSIS_REPOSITORY.get_latest(teacher_id, class_id, course_id, "STUDENT" if student_id else "CLASS", student_id or 0)


async def run_course_analysis(class_id: int, course_id: int, current_user: dict[str, Any], student_id: Optional[int] = None) -> dict[str, Any]:
    teacher_id = int(current_user.get("user_id") or 0)
    scope = "STUDENT" if student_id else "CLASS"
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None)
    evidence = collect_course_question_records(class_id, course_id, current_user, student_id)
    if not evidence["items"]:
        raise ValueError("当前课程暂无可分析的做题记录")
    COURSE_ANALYSIS_REPOSITORY.begin(teacher_id, class_id, course_id, scope, student_id or 0, cutoff)
    provider_message = None
    result = None
    prompt = "你是网络安全课程教师助理。请只根据给定课程作答证据返回JSON，字段包括overallComment、knowledgeFindings、representativeMistakes、teachingSuggestions；不得按五维画像组织结论。证据：" + json.dumps(evidence, ensure_ascii=False)
    try:
        payload = await asyncio.wait_for(_call_dify_for_student_analysis(prompt, f"course-{course_id}-{scope.lower()}-{student_id or class_id}"), timeout=12)
        if isinstance(payload, dict) and payload.get("overallComment"):
            result = {**payload, "scope": "student_course" if student_id else "class_course", "courseId": course_id, "courseName": evidence["course"]["courseName"], "generatedBy": "dify", "fallbackUsed": False, "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    except Exception as exc:
        provider_message = provider_failure_message(exc)
    if result is None:
        result = build_course_analysis_fallback(evidence["items"], scope=scope, course=evidence["course"], provider_message=provider_message)
    COURSE_ANALYSIS_REPOSITORY.save_success(teacher_id, class_id, course_id, scope, student_id or 0, cutoff, result, evidence["summary"])
    return COURSE_ANALYSIS_REPOSITORY.get_latest(teacher_id, class_id, course_id, scope, student_id or 0)
