from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Iterable, Optional

from database import get_connection
from profile_repository import get_latest_student_profile
from teacher_repository import USER_SERVICE_SCHEMA, require_student_in_owned_teaching_class


DIMENSIONS = (
    ("knowledge_mastery", "知识掌握", "knowledge_mastery_score", {"ATTEMPT", "SUCCESS"}),
    ("troubleshooting", "排障能力", "troubleshooting_score", {"ERROR", "COMMAND", "HINT", "SUCCESS"}),
    ("autonomy", "自主探索", "autonomy_score", {"LAB_START", "COMMAND", "SUCCESS"}),
    ("ai_collaboration", "AI 协同", "ai_collaboration_score", {"AI", "HINT", "COMMAND", "SUCCESS"}),
    ("engagement", "学习投入", "engagement_score", {"LAB_START", "ATTEMPT", "SUCCESS", "COMMAND"}),
)


def classify_risk(attempted_student_count: int, incorrect_student_count: int, incorrect_rate: float) -> str:
    if incorrect_student_count >= 8 or (attempted_student_count >= 5 and incorrect_rate >= 0.55):
        return "high"
    if incorrect_student_count >= 4 or (attempted_student_count >= 5 and incorrect_rate >= 0.30):
        return "medium"
    return "low"


def match_knowledge_course(category: Any, courses: list[dict[str, Any]]) -> dict[str, Any]:
    category_text = str(category or "").strip().lower()
    aliases = {
        "sql注入": ("sql注入", "sql injection"),
        "xss": ("xss",),
        "csrf": ("csrf",),
        "命令执行": ("命令执行", "操作系统安全"),
        "文件上传": ("文件上传",),
        "目录遍历": ("目录遍历",),
    }
    category_aliases = next(
        (values for key, values in aliases.items() if key in category_text),
        (category_text,),
    )
    for course in courses:
        course_name = str(course.get("courseName") or "").lower()
        if any(alias and alias in course_name for alias in category_aliases):
            return course
    return {"courseId": None, "courseName": "扩展知识点（未排期）", "teachingOrder": None}


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def redact_command(command: Any) -> str:
    value = str(command or "")[:2048]
    patterns = (
        (r"(?i)(authorization\s*:\s*bearer\s+)[^\s'\"]+", r"\1***"),
        (r"(?i)(--password(?:=|\s+))[^\s'\"]+", r"\1***"),
        (r"(?i)(--cookie(?:=|\s+))[^\r\n]+?(?=\s+--|\s+https?://|$)", r"\1***"),
        (r"(?i)(cookie\s*:\s*)[^\r\n]+", r"\1***"),
        (r"(?i)(token|api[_-]?key|secret)=([^&\s]+)", r"\1=***"),
    )
    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)
    return value


def _timeline_item(
    *,
    kind: str,
    occurred_at: Any,
    source_id: Any,
    title: str,
    detail: str = "",
    status: str = "info",
    lab_session_id: Any = None,
    module_id: Any = None,
    task_id: Any = None,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "occurredAt": _iso(occurred_at),
        "sourceId": str(source_id or ""),
        "title": title,
        "detail": str(detail or "")[:500],
        "status": status,
        "labSessionId": lab_session_id,
        "moduleId": module_id,
        "taskId": task_id,
        **extra,
    }


def compose_learning_timeline(
    *,
    learning_rows: Iterable[dict[str, Any]],
    command_rows: Iterable[dict[str, Any]],
    error_rows: Iterable[dict[str, Any]],
    attempt_rows: Iterable[dict[str, Any]],
    completion_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    learning_kind = {
        "LAB_START": ("LAB_START", "开始安全实验", "info"),
        "START_LAB": ("LAB_START", "开始安全实验", "info"),
        "HINT_REQUEST": ("HINT", "请求学习提示", "warning"),
        "AI_INTERACTION": ("AI", "使用 AI 辅助", "info"),
        "LAB_COMPLETE": ("SUCCESS", "完成安全实验", "success"),
        "CHALLENGE_COMPLETE": ("SUCCESS", "完成安全挑战", "success"),
        "FLAG_SUBMIT": ("ATTEMPT", "提交 Flag", "info"),
        "FLAG_SUBMIT_FAILED": ("ATTEMPT", "Flag 验证失败", "failed"),
    }
    for row in learning_rows:
        event_type = str(row.get("event_type") or "")
        if event_type not in learning_kind:
            continue
        kind, title, status = learning_kind[event_type]
        payload = _json_object(row.get("payload_json"))
        items.append(
            _timeline_item(
                kind=kind,
                occurred_at=row.get("event_time"),
                source_id=row.get("event_id"),
                title=title,
                detail=str(payload.get("summary") or payload.get("message") or ""),
                status=status,
                lab_session_id=row.get("lab_session_id"),
                module_id=row.get("module_id"),
                task_id=row.get("task_id"),
            )
        )

    commands = list(command_rows)
    for row in commands:
        exit_code = row.get("exit_code")
        succeeded = exit_code == 0
        retry_outcome = "success" if succeeded else "pending"
        if not succeeded:
            retry_outcome = "recovered" if any(
                later.get("lab_session_id") == row.get("lab_session_id")
                and later.get("cmd_category") == row.get("cmd_category")
                and later.get("exit_code") == 0
                and later.get("executed_at") is not None
                and row.get("executed_at") is not None
                and later.get("executed_at") > row.get("executed_at")
                for later in commands
            ) else "unresolved"
        items.append(
            _timeline_item(
                kind="COMMAND",
                occurred_at=row.get("executed_at"),
                source_id=row.get("command_id"),
                title="命令执行成功" if succeeded else "命令执行失败",
                detail=str(row.get("output_digest") or ""),
                status="success" if succeeded else "failed",
                lab_session_id=row.get("lab_session_id"),
                module_id=row.get("module_id"),
                task_id=row.get("task_id"),
                command=redact_command(row.get("command")),
                commandCategory=row.get("cmd_category"),
                exitCode=exit_code,
                retryOutcome=retry_outcome,
            )
        )

    for row in error_rows:
        items.append(
            _timeline_item(
                kind="ERROR",
                occurred_at=row.get("occurred_at"),
                source_id=row.get("error_id"),
                title=str(row.get("error_category") or "实验错误"),
                detail=str(row.get("raw_excerpt") or row.get("error_signature") or ""),
                status="failed",
                lab_session_id=row.get("lab_session_id"),
                module_id=row.get("module_id"),
                task_id=row.get("task_id"),
                errorCategory=row.get("error_category"),
                severity=row.get("severity"),
                commandId=row.get("command_id"),
            )
        )

    for row in attempt_rows:
        correct = row.get("is_correct") in (1, True)
        items.append(
            _timeline_item(
                kind="ATTEMPT",
                occurred_at=row.get("submitted_at"),
                source_id=row.get("attempt_id"),
                title=str(row.get("title") or "训练题作答"),
                detail=f"得分 {float(row.get('score') or 0):.1f}",
                status="success" if correct else "failed",
                module_id=row.get("module_id"),
                task_id=row.get("task_id"),
                score=float(row.get("score") or 0),
                isCorrect=correct,
                generatedQuestionId=row.get("generated_question_id"),
            )
        )

    for row in completion_rows:
        items.append(
            _timeline_item(
                kind="SUCCESS",
                occurred_at=row.get("created_at"),
                source_id=row.get("id"),
                title="安全实验验证成功",
                detail=f"用时 {int(row.get('total_time_seconds') or 0)} 秒",
                status="success",
                lab_session_id=row.get("lab_session_id"),
                module_id=row.get("module_id"),
                task_id=row.get("task_id"),
                aiAskCount=int(row.get("total_ai_ask_count") or 0),
            )
        )

    items.sort(key=lambda item: (item.get("occurredAt") or "", item.get("sourceId") or ""))
    return items


def build_capability_dimensions(
    profile: Optional[dict[str, Any]],
    timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    profile = profile or {}
    summary = _json_object(profile.get("profile_summary_json"))
    explanations = summary.get("dimension_explanations")
    explanations = explanations if isinstance(explanations, dict) else {}
    fallback_evidence = list(reversed(timeline[-3:]))
    dimensions = []
    for key, label, score_field, event_kinds in DIMENSIONS:
        evidence = [item for item in reversed(timeline) if item.get("kind") in event_kinds][:6]
        dimensions.append(
            {
                "key": key,
                "label": label,
                "score": float(profile[score_field]) if profile.get(score_field) is not None else None,
                "summary": str(explanations.get(score_field) or "该维度根据当前可追溯学习证据计算。"),
                "evidence": evidence or fallback_evidence,
            }
        )
    return dimensions


def _load_learning_rows(student_id: int, limit: int) -> dict[str, list[dict[str, Any]]]:
    limit = max(10, min(int(limit), 200))
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT event_id, lab_session_id, module_id, task_id, event_type,
                       event_time, payload_json
                FROM learning_event
                WHERE user_id = %(student_id)s
                ORDER BY event_time DESC, id DESC
                LIMIT %(limit)s
                """,
                {"student_id": student_id, "limit": limit},
            )
            learning_rows = list(cursor.fetchall() or [])
            cursor.execute(
                """
                SELECT command_id, lab_session_id, module_id, task_id, command,
                       cmd_category, exit_code, output_digest, executed_at
                FROM container_command_event
                WHERE user_id = %(student_id)s
                ORDER BY executed_at DESC
                LIMIT %(limit)s
                """,
                {"student_id": student_id, "limit": limit},
            )
            command_rows = list(cursor.fetchall() or [])
            cursor.execute(
                """
                SELECT error_id, lab_session_id, module_id, task_id, command_id,
                       error_signature, error_category, raw_excerpt, severity, occurred_at
                FROM error_event
                WHERE user_id = %(student_id)s
                ORDER BY occurred_at DESC
                LIMIT %(limit)s
                """,
                {"student_id": student_id, "limit": limit},
            )
            error_rows = list(cursor.fetchall() or [])
            cursor.execute(
                """
                SELECT gqa.attempt_id, gqa.generated_question_id, gqa.score,
                       gqa.is_correct, gqa.submitted_at, gq.title, gq.module_id, gq.task_id
                FROM generated_question_attempt gqa
                LEFT JOIN generated_question gq
                  ON gq.generated_question_id = gqa.generated_question_id
                WHERE gqa.user_id = %(student_id)s
                ORDER BY gqa.submitted_at DESC
                LIMIT %(limit)s
                """,
                {"student_id": student_id, "limit": limit},
            )
            attempt_rows = list(cursor.fetchall() or [])
            cursor.execute(
                """
                SELECT id, lab_session_id, module_id, task_id, completion_status,
                       total_time_seconds, total_ai_ask_count, created_at
                FROM challenge_completion_event
                WHERE user_id = %(student_id)s
                ORDER BY created_at DESC
                LIMIT %(limit)s
                """,
                {"student_id": student_id, "limit": limit},
            )
            completion_rows = list(cursor.fetchall() or [])
    return {
        "learning_rows": learning_rows,
        "command_rows": command_rows,
        "error_rows": error_rows,
        "attempt_rows": attempt_rows,
        "completion_rows": completion_rows,
    }


def get_learning_replay(
    teacher_id: int,
    class_id: int,
    student_id: int,
    limit: int = 100,
) -> dict[str, Any]:
    require_student_in_owned_teaching_class(teacher_id, class_id, student_id)
    rows = _load_learning_rows(student_id, limit)
    return {
        "teachingClassId": class_id,
        "studentId": student_id,
        "items": compose_learning_timeline(**rows)[-max(10, min(int(limit), 200)):],
    }


def get_capability_evidence(
    teacher_id: int,
    class_id: int,
    student_id: int,
) -> dict[str, Any]:
    replay = get_learning_replay(teacher_id, class_id, student_id, limit=120)
    profile = get_latest_student_profile(student_id)
    return {
        "teachingClassId": class_id,
        "studentId": student_id,
        "profileSnapshotId": profile.get("snapshot_id") if profile else None,
        "computedAt": _iso(profile.get("computed_at")) if profile else None,
        "overallScore": float(profile["overall_score"]) if profile and profile.get("overall_score") is not None else None,
        "dimensions": build_capability_dimensions(profile, replay["items"]),
    }


def _split_pairs(value: Any, key_name: str, value_name: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw_item in str(value or "").split("|||"):
        if not raw_item or "::" not in raw_item:
            continue
        raw_key, raw_value = raw_item.split("::", 1)
        key: Any = raw_key
        if raw_key.isdigit():
            key = int(raw_key)
        items.append({key_name: key, value_name: raw_value})
    return items


def get_class_risk_map(teacher_id: int, class_id: int) -> dict[str, Any]:
    from teacher_repository import require_owned_teaching_class

    require_owned_teaching_class(teacher_id, class_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT c.id AS course_id, c.course_name, tcc.teaching_order
                FROM `{USER_SERVICE_SCHEMA}`.`teaching_class_course` tcc
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`course` c ON c.id = tcc.course_id
                WHERE tcc.teaching_class_id = %(class_id)s
                ORDER BY tcc.teaching_order
                """,
                {"class_id": class_id},
            )
            courses = [
                {
                    "courseId": row.get("course_id"),
                    "courseName": row.get("course_name"),
                    "teachingOrder": row.get("teaching_order"),
                }
                for row in cursor.fetchall() or []
            ]
            cursor.execute(
                f"""
                SELECT
                    gq.knowledge_point_id,
                    COALESCE(kp.name, '未标注知识点') AS knowledge_point_name,
                    COALESCE(kp.category, '未分类') AS knowledge_category,
                    COUNT(DISTINCT ts.user_id) AS student_count,
                    COUNT(DISTINCT CASE WHEN gqa.attempt_id IS NOT NULL THEN gqa.user_id END) AS attempted_student_count,
                    COUNT(DISTINCT CASE WHEN gqa.is_correct = 0 THEN gqa.user_id END) AS incorrect_student_count,
                    COUNT(gqa.attempt_id) AS attempted_count,
                    SUM(CASE WHEN gqa.is_correct = 0 THEN 1 ELSE 0 END) AS incorrect_count,
                    GROUP_CONCAT(
                        DISTINCT CASE WHEN gqa.is_correct = 0
                            THEN CONCAT(gqa.user_id, '::', COALESCE(u.user_name, u.user_student_number, '未命名学生'))
                        END SEPARATOR '|||'
                    ) AS affected_students,
                    GROUP_CONCAT(
                        DISTINCT CONCAT(gq.generated_question_id, '::', REPLACE(gq.title, '|||', ''))
                        ORDER BY gq.created_at DESC SEPARATOR '|||'
                    ) AS representative_questions
                FROM generated_question gq
                INNER JOIN training_session ts
                  ON ts.training_session_id = gq.training_session_id
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_student` tcs
                  ON tcs.student_id = ts.user_id
                 AND tcs.teaching_class_id = %(class_id)s
                LEFT JOIN generated_question_attempt gqa
                  ON gqa.generated_question_id = gq.generated_question_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`user` u
                  ON u.user_id = gqa.user_id
                LEFT JOIN knowledge_point kp
                  ON kp.knowledge_point_id = gq.knowledge_point_id
                GROUP BY gq.knowledge_point_id, kp.name, kp.category
                ORDER BY incorrect_student_count DESC, knowledge_point_name
                """,
                {"class_id": class_id},
            )
            rows = list(cursor.fetchall() or [])

    result_items = []
    for row in rows:
        attempted_count = int(row.get("attempted_count") or 0)
        incorrect_count = int(row.get("incorrect_count") or 0)
        attempted_students = int(row.get("attempted_student_count") or 0)
        incorrect_students = int(row.get("incorrect_student_count") or 0)
        incorrect_rate = round(incorrect_count / attempted_count, 4) if attempted_count else 0.0
        matched_course = match_knowledge_course(row.get("knowledge_category"), courses)
        result_items.append(
            {
                **matched_course,
                "knowledgePointId": row.get("knowledge_point_id"),
                "knowledgePointName": row.get("knowledge_point_name"),
                "knowledgeCategory": row.get("knowledge_category"),
                "studentCount": int(row.get("student_count") or 0),
                "attemptedStudentCount": attempted_students,
                "incorrectStudentCount": incorrect_students,
                "attemptedCount": attempted_count,
                "incorrectCount": incorrect_count,
                "incorrectRate": incorrect_rate,
                "riskLevel": classify_risk(attempted_students, incorrect_students, incorrect_rate),
                "affectedStudents": _split_pairs(row.get("affected_students"), "studentId", "studentName"),
                "representativeQuestions": _split_pairs(
                    row.get("representative_questions"),
                    "generatedQuestionId",
                    "title",
                )[:3],
            }
        )
    result_items.sort(key=lambda item: (
        item.get("teachingOrder") if item.get("teachingOrder") is not None else 999,
        {"high": 0, "medium": 1, "low": 2}.get(str(item.get("riskLevel")), 3),
        str(item.get("knowledgePointName") or ""),
    ))
    return {"teachingClassId": class_id, "items": result_items}
