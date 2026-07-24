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

LEGACY_MOJIBAKE_MARKERS = re.compile(r"[ÃÂæåçèéÖÑÄÊ£¡µÎÏ½]|�")


def normalize_display_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    visible = re.sub(r"[\s\W_]", "", text, flags=re.UNICODE)
    if not visible or set(visible) == {"?"}:
        return fallback
    if LEGACY_MOJIBAKE_MARKERS.search(text) and not re.search(r"[\u4e00-\u9fff]", text):
        return fallback
    return text


def classify_risk(attempted_student_count: int, incorrect_student_count: int, incorrect_rate: float) -> str:
    del attempted_student_count, incorrect_student_count
    if incorrect_rate >= 0.60:
        return "high"
    if incorrect_rate >= 0.40:
        return "medium"
    if incorrect_rate >= 0.20:
        return "attention"
    return "good"


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
        "title": normalize_display_text(title, "学习事件"),
        "detail": normalize_display_text(detail, "")[:500],
        "status": status,
        "labSessionId": lab_session_id,
        "moduleId": module_id,
        "taskId": task_id,
        **extra,
    }


def _short_text(value: Any, limit: int = 120) -> str:
    text = normalize_display_text(value, "")
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _event_experiment_name(row: dict[str, Any], payload: dict[str, Any]) -> str:
    context = _json_object(payload.get("context"))
    return (
        normalize_display_text(context.get("experimentTitle"), "")
        or normalize_display_text(context.get("moduleName"), "")
        or normalize_display_text(row.get("module_name"), "")
        or normalize_display_text(row.get("course_name"), "")
    )


def _experiment_title(name: str) -> str:
    value = _short_text(name, 80)
    if not value:
        return "实验"
    return value if value.endswith("实验") else f"{value}实验"


def _submitted_answer_text(payload: dict[str, Any], snapshot: dict[str, Any]) -> str:
    answer = payload.get("answer")
    options = snapshot.get("options")
    if isinstance(options, list):
        indices = answer if isinstance(answer, list) else [answer]
        selected = []
        for value in indices:
            try:
                index = int(value)
            except (TypeError, ValueError):
                continue
            if 0 <= index < len(options):
                selected.append(normalize_display_text(options[index], ""))
        if selected:
            return "、".join(item for item in selected if item)
    if isinstance(answer, (dict, list)):
        return json.dumps(answer, ensure_ascii=False, default=str)
    return normalize_display_text(answer, "未记录作答内容")


def _is_formula_copy(value: Any) -> bool:
    text = normalize_display_text(value, "")
    return any(
        marker in text
        for marker in (
            "占综合分",
            "内部采用",
            "作为可落地代理指标",
            "不是对立维度",
        )
    )


def _dimension_fact_summary(key: str, evidence: list[dict[str, Any]]) -> str:
    counts = {
        kind: sum(1 for item in evidence if item.get("kind") == kind)
        for kind in ("ATTEMPT", "SUCCESS", "ERROR", "COMMAND", "HINT", "LAB_START", "AI")
    }
    if key == "knowledge_mastery":
        attempts = counts["ATTEMPT"]
        correct = sum(
            1
            for item in evidence
            if item.get("kind") == "ATTEMPT"
            and (item.get("isCorrect") is True or item.get("status") == "success")
        )
        if attempts:
            return f"记录 {attempts} 次作答，其中 {correct} 次正确。"
        if counts["SUCCESS"]:
            return f"记录 {counts['SUCCESS']} 次实验验证成功。"
        return "暂无题目作答或实验验证记录。"
    if key == "troubleshooting":
        parts = []
        if counts["ERROR"]:
            parts.append(f"{counts['ERROR']} 次报错")
        if counts["COMMAND"]:
            parts.append(f"{counts['COMMAND']} 次操作")
        if counts["HINT"]:
            parts.append(f"{counts['HINT']} 次求助")
        return f"记录 {'、'.join(parts)}。" if parts else "暂无排障过程记录。"
    if key == "autonomy":
        if counts["COMMAND"]:
            return f"记录 {counts['LAB_START']} 次实验启动、{counts['COMMAND']} 次实验操作。"
        if counts["LAB_START"]:
            return f"记录 {counts['LAB_START']} 次实验启动，尚未采集到实验内操作。"
        return "暂无自主实验操作记录。"
    if key == "ai_collaboration":
        if counts["AI"]:
            return f"记录 {counts['AI']} 次 AI 对话，可查看具体提问与回复。"
        return "暂无可展示的 AI 对话记录。"
    if key == "engagement":
        parts = []
        if counts["LAB_START"]:
            parts.append(f"{counts['LAB_START']} 次实验启动")
        if counts["ATTEMPT"]:
            parts.append(f"{counts['ATTEMPT']} 次作答")
        if counts["SUCCESS"]:
            parts.append(f"{counts['SUCCESS']} 次验证成功")
        return f"记录 {'、'.join(parts)}。" if parts else "暂无实验参与记录。"
    return "暂无学习记录。"


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
        payload = _json_object(row.get("payload_json"))
        experiment_name = _event_experiment_name(row, payload)

        if event_type == "AI_INTERACTION":
            prompt = _short_text(payload.get("prompt"), 100)
            if not prompt:
                continue
            reply = _short_text(payload.get("assistant_reply"), 280)
            context_name = _event_experiment_name(row, payload)
            detail_parts = []
            if context_name:
                detail_parts.append(f"实验：{context_name}")
            if reply:
                detail_parts.append(f"AI 回复：{reply}")
            items.append(
                _timeline_item(
                    kind="AI",
                    occurred_at=row.get("event_time"),
                    source_id=row.get("event_id"),
                    title=f"咨询 AI：{prompt}",
                    detail=" · ".join(detail_parts),
                    status="info",
                    lab_session_id=row.get("lab_session_id"),
                    module_id=row.get("module_id"),
                    task_id=row.get("task_id"),
                )
            )
            continue

        if event_type in {"LAB_START", "START_LAB"}:
            runtime_name = _experiment_title(experiment_name)
            container_name = normalize_display_text(payload.get("container_name"), "")
            target_url = normalize_display_text(payload.get("target_url"), "")
            detail_parts = []
            if container_name:
                detail_parts.append(f"靶机：{container_name}")
            if target_url:
                detail_parts.append(f"地址：{target_url}")
            items.append(
                _timeline_item(
                    kind="LAB_START",
                    occurred_at=row.get("event_time"),
                    source_id=row.get("event_id"),
                    title=f"启动 {runtime_name}",
                    detail=" · ".join(detail_parts),
                    status="info",
                    lab_session_id=row.get("lab_session_id"),
                    module_id=row.get("module_id"),
                    task_id=row.get("task_id"),
                )
            )
            continue

        if event_type == "LAB_STOP":
            runtime_name = _experiment_title(experiment_name)
            container_name = normalize_display_text(payload.get("container_name"), "")
            target_url = normalize_display_text(payload.get("target_url"), "")
            detail_parts = []
            if container_name:
                detail_parts.append(f"靶机：{container_name}")
            if target_url:
                detail_parts.append(f"地址：{target_url}")
            items.append(
                _timeline_item(
                    kind="LAB_STOP",
                    occurred_at=row.get("event_time"),
                    source_id=row.get("event_id"),
                    title=f"结束 {runtime_name}",
                    detail=" · ".join(detail_parts),
                    status="info",
                    lab_session_id=row.get("lab_session_id"),
                    module_id=row.get("module_id"),
                    task_id=row.get("task_id"),
                )
            )
            continue

        if event_type == "QUESTION_SUBMIT":
            snapshot = _json_object(row.get("question_snapshot_json"))
            question = _short_text(snapshot.get("content"), 120) or f"实验题 {row.get('question_id') or ''}".strip()
            answer = _short_text(_submitted_answer_text(payload, snapshot), 160)
            correct = payload.get("is_correct") in (1, True)
            score = float(payload.get("score") or 0)
            items.append(
                _timeline_item(
                    kind="ATTEMPT",
                    occurred_at=row.get("event_time"),
                    source_id=row.get("event_id"),
                    title=f"作答：{question}",
                    detail=f"作答：{answer} · {'回答正确' if correct else '回答错误'} · {score:g} 分",
                    status="success" if correct else "failed",
                    lab_session_id=row.get("lab_session_id"),
                    module_id=row.get("module_id"),
                    task_id=row.get("task_id"),
                    score=score,
                    isCorrect=correct,
                )
            )
            continue

        if event_type not in learning_kind:
            continue
        kind, title, status = learning_kind[event_type]
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
    dimensions = []
    for key, label, score_field, event_kinds in DIMENSIONS:
        evidence = [item for item in reversed(timeline) if item.get("kind") in event_kinds][:6]
        explanation = explanations.get(score_field)
        if isinstance(explanation, dict):
            explanation = explanation.get("explanation") or explanation.get("summary")
        if not explanation or _is_formula_copy(explanation):
            explanation = _dimension_fact_summary(key, evidence)
        dimensions.append(
            {
                "key": key,
                "label": label,
                "score": float(profile[score_field]) if profile.get(score_field) is not None else None,
                "summary": normalize_display_text(
                    explanation,
                    _dimension_fact_summary(key, evidence),
                ),
                "evidence": evidence,
            }
        )
    return dimensions


def _load_learning_rows(student_id: int, limit: int) -> dict[str, list[dict[str, Any]]]:
    limit = max(10, min(int(limit), 200))
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT le.event_id, le.lab_session_id, le.module_id, le.task_id,
                       le.question_id, le.event_type, le.event_time, le.payload_json,
                       c.course_name, m.module_name, qs.question_snapshot_json
                FROM learning_event le
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`course` c
                  ON c.id = le.course_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`module` m
                  ON m.module_id = le.module_id
                LEFT JOIN question_submission qs
                  ON le.event_type = 'QUESTION_SUBMIT'
                 AND qs.request_id = le.request_id
                WHERE le.user_id = %(student_id)s
                ORDER BY le.event_time DESC, le.id DESC
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


def build_knowledge_risk_items(
    rows: Iterable[dict[str, Any]],
    course_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    scoped_rows = [
        row for row in rows
        if course_id is None or int(row.get("course_id") or 0) == int(course_id)
    ]
    total_incorrect = sum(max(0, int(row.get("incorrect_count") or 0)) for row in scoped_rows)
    items: list[dict[str, Any]] = []
    for row in scoped_rows:
        attempted_count = int(row.get("attempted_count") or 0)
        incorrect_count = int(row.get("incorrect_count") or 0)
        attempted_students = int(row.get("attempted_student_count") or 0)
        incorrect_students = int(row.get("incorrect_student_count") or 0)
        incorrect_rate = round(incorrect_count / attempted_count, 4) if attempted_count else 0.0
        items.append(
            {
                "courseId": row.get("course_id"),
                "courseName": row.get("course_name") or "未命名实验",
                "teachingOrder": row.get("teaching_order"),
                "knowledgePointId": row.get("knowledge_point_id"),
                "knowledgePointName": row.get("knowledge_point_name"),
                "knowledgeCategory": row.get("knowledge_category"),
                "studentCount": int(row.get("student_count") or 0),
                "attemptedStudentCount": attempted_students,
                "incorrectStudentCount": incorrect_students,
                "unansweredStudentCount": max(0, int(row.get("student_count") or 0) - attempted_students),
                "attemptedCount": attempted_count,
                "incorrectCount": incorrect_count,
                "incorrectRate": incorrect_rate,
                "errorShare": round(incorrect_count / total_incorrect, 4) if total_incorrect else 0.0,
                "riskLevel": classify_risk(attempted_students, incorrect_students, incorrect_rate),
                "affectedStudents": _split_pairs(row.get("affected_students"), "studentId", "studentName"),
                "representativeQuestions": _split_pairs(
                    row.get("representative_questions"),
                    "generatedQuestionId",
                    "title",
                )[:3],
            }
        )
    risk_order = {"high": 0, "medium": 1, "attention": 2, "good": 3}
    items.sort(key=lambda item: (
        risk_order.get(str(item.get("riskLevel")), 4),
        -int(item.get("incorrectCount") or 0),
        str(item.get("knowledgePointName") or ""),
    ))
    return items


def _answer_text(value: Any) -> str:
    if value is None:
        return "未提供答案"
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return value.strip() or "未提供答案"
        if isinstance(parsed, str):
            return parsed.strip() or "未提供答案"
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def build_knowledge_risk_detail(
    *,
    summary: dict[str, Any],
    attempt_rows: Iterable[dict[str, Any]],
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    rows = list(attempt_rows)
    groups: dict[str, dict[str, Any]] = {}
    students: dict[int, dict[str, Any]] = {}
    representative_attempts: list[dict[str, Any]] = []
    for row in rows:
        answer = _answer_text(row.get("answer_json"))
        student_id = int(row.get("student_id") or 0)
        student_name = row.get("student_name") or f"学生 {student_id}"
        students.setdefault(student_id, {"studentId": student_id, "studentName": student_name})
        group = groups.setdefault(answer, {"answer": answer, "count": 0, "studentIds": set()})
        group["count"] += 1
        group["studentIds"].add(student_id)
        representative_attempts.append(
            {
                "studentId": student_id,
                "studentName": student_name,
                "generatedQuestionId": row.get("generated_question_id"),
                "title": row.get("title") or "未命名题目",
                "answer": answer,
                "standardAnswer": _answer_text(row.get("standard_answer")),
                "score": row.get("score"),
                "submittedAt": _iso(row.get("submitted_at")),
            }
        )
    common_mistakes = [
        {"answer": value["answer"], "count": value["count"], "studentCount": len(value["studentIds"])}
        for value in groups.values()
    ]
    common_mistakes.sort(key=lambda item: (-item["studentCount"], -item["count"], item["answer"]))
    student_items = sorted(students.values(), key=lambda item: (item["studentName"], item["studentId"]))
    page = max(1, int(page))
    size = max(1, min(int(size), 100))
    offset = (page - 1) * size
    return {
        **summary,
        "commonMistakes": common_mistakes,
        "affectedStudents": student_items[offset:offset + size],
        "representativeAttempts": representative_attempts[:10],
        "pagination": {"page": page, "size": size, "total": len(student_items)},
    }


def build_normalized_knowledge_attempts_sql() -> str:
    """Return one normalized row per persisted attempt and mapped knowledge point."""
    return f"""
        SELECT DISTINCT
            (CONVERT(CONCAT('generated:', gqa.attempt_id) USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS attempt_key,
            gqa.user_id AS student_id,
            ts.course_id AS course_id,
            COALESCE(gq.knowledge_point_id, 0) AS knowledge_point_id,
            gqa.is_correct,
            (CONVERT(gqa.answer_json USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS answer_json,
            gqa.score,
            gqa.cost_time,
            gqa.submitted_at,
            (CONVERT(gq.generated_question_id USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS generated_question_id,
            (CONVERT(COALESCE(gq.title, '个性化练习题') USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS title,
            (CONVERT(COALESCE(gq.stem, gq.title, '个性化练习题') USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS stem,
            gq.question_type,
            gq.options_json,
            (CONVERT(COALESCE(gq.reference_answer, gq.explanation, '') USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS standard_answer
        FROM generated_question_attempt gqa
        INNER JOIN generated_question gq
          ON gq.generated_question_id = gqa.generated_question_id
        INNER JOIN training_session ts
          ON ts.training_session_id = gq.training_session_id

        UNION ALL

        SELECT DISTINCT
            (CONVERT(CONCAT('submission:', qs.submission_id) USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS attempt_key,
            qs.user_id AS student_id,
            COALESCE(qs.course_id, mc.course_id) AS course_id,
            COALESCE(explicit_kp.knowledge_point_id, qkp.knowledge_point_id,
                     tkp.knowledge_point_id, 0) AS knowledge_point_id,
            qs.is_correct,
            (CONVERT(qs.answer_json USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS answer_json,
            qs.score,
            qs.cost_time,
            qs.created_at AS submitted_at,
            (CONVERT(CONCAT(
                'course-', COALESCE(qs.module_id, 0), '-', COALESCE(qs.task_id, 0), '-',
                COALESCE(qs.question_uid, CAST(qs.question_id AS CHAR))
            ) USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS generated_question_id,
            (CONVERT(COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(qs.question_snapshot_json, '$.content')),
                CONCAT('实验题 ', COALESCE(qs.task_id, 0), '-', qs.question_id)
            ) USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS title,
            (CONVERT(COALESCE(
                JSON_UNQUOTE(JSON_EXTRACT(qs.question_snapshot_json, '$.content')),
                CONCAT('实验题 ', COALESCE(qs.task_id, 0), '-', qs.question_id)
            ) USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS stem,
            qs.question_type,
            JSON_EXTRACT(qs.question_snapshot_json, '$.options') AS options_json,
            (CONVERT(COALESCE(CAST(qs.standard_answer_json AS CHAR), '') USING utf8mb4)
                COLLATE utf8mb4_unicode_ci) AS standard_answer
        FROM question_submission qs
        LEFT JOIN `{USER_SERVICE_SCHEMA}`.`module_course` mc
          ON qs.course_id IS NULL
         AND mc.module_id = qs.module_id
        LEFT JOIN knowledge_point explicit_kp
          ON explicit_kp.knowledge_point_id = qs.knowledge_point_id
        LEFT JOIN question_knowledge_point qkp
          ON explicit_kp.knowledge_point_id IS NULL
         AND (
              qkp.question_uid = qs.question_uid
              OR (qkp.question_uid IS NULL AND qkp.question_id = qs.question_id)
         )
        LEFT JOIN task_knowledge_point tkp
          ON explicit_kp.knowledge_point_id IS NULL
         AND qkp.knowledge_point_id IS NULL
         AND tkp.module_id = qs.module_id
         AND tkp.task_id = qs.task_id
        WHERE qs.user_id IS NOT NULL
          AND COALESCE(qs.course_id, mc.course_id) IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM generated_question_attempt linked_attempt
              WHERE linked_attempt.submission_id = qs.submission_id
          )
    """


def _get_class_risk_map_generated_only(
    teacher_id: int,
    class_id: int,
    course_id: Optional[int] = None,
) -> dict[str, Any]:
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
            course_filter = "AND ts.course_id = %(course_id)s" if course_id is not None else ""
            cursor.execute(
                f"""
                SELECT
                    ts.course_id,
                    c.course_name,
                    tcc.teaching_order,
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
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_course` tcc
                  ON tcc.teaching_class_id = %(class_id)s
                 AND tcc.course_id = ts.course_id
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`course` c
                  ON c.id = ts.course_id
                LEFT JOIN generated_question_attempt gqa
                  ON gqa.generated_question_id = gq.generated_question_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`user` u
                  ON u.user_id = gqa.user_id
                LEFT JOIN knowledge_point kp
                  ON kp.knowledge_point_id = gq.knowledge_point_id
                WHERE 1 = 1
                  {course_filter}
                GROUP BY ts.course_id, c.course_name, tcc.teaching_order,
                         gq.knowledge_point_id, kp.name, kp.category
                ORDER BY incorrect_student_count DESC, knowledge_point_name
                """,
                {"class_id": class_id, "course_id": course_id},
            )
            rows = list(cursor.fetchall() or [])

    result_items = build_knowledge_risk_items(rows, course_id=course_id)
    return {"teachingClassId": class_id, "courseId": course_id, "items": result_items}


def _get_knowledge_risk_detail_generated_only(
    teacher_id: int,
    class_id: int,
    course_id: int,
    knowledge_point_id: int,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    risk_map = get_class_risk_map(teacher_id, class_id, course_id)
    summary = next(
        (item for item in risk_map["items"] if int(item.get("knowledgePointId") or 0) == int(knowledge_point_id)),
        None,
    )
    if not summary:
        raise KeyError("knowledge point risk does not exist in selected experiment")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT gqa.user_id AS student_id,
                       COALESCE(u.user_name, u.user_student_number, '未命名学生') AS student_name,
                       gqa.answer_json, gqa.score, gqa.submitted_at,
                       gq.generated_question_id, gq.title,
                       COALESCE(gq.reference_answer, gq.explanation, '') AS standard_answer
                FROM generated_question_attempt gqa
                INNER JOIN generated_question gq
                  ON gq.generated_question_id = gqa.generated_question_id
                INNER JOIN training_session ts
                  ON ts.training_session_id = gq.training_session_id
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_student` tcs
                  ON tcs.teaching_class_id = %(class_id)s
                 AND tcs.student_id = gqa.user_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`user` u
                  ON u.user_id = gqa.user_id
                WHERE ts.course_id = %(course_id)s
                  AND gq.knowledge_point_id = %(knowledge_point_id)s
                  AND gqa.is_correct = 0
                ORDER BY gqa.submitted_at DESC, gqa.attempt_id DESC
                """,
                {
                    "class_id": class_id,
                    "course_id": course_id,
                    "knowledge_point_id": knowledge_point_id,
                },
            )
            rows = list(cursor.fetchall() or [])
    return build_knowledge_risk_detail(summary=summary, attempt_rows=rows, page=page, size=size)


def get_class_risk_map(
    teacher_id: int,
    class_id: int,
    course_id: Optional[int] = None,
) -> dict[str, Any]:
    from teacher_repository import require_owned_teaching_class

    require_owned_teaching_class(teacher_id, class_id)
    course_filter = "AND attempts.course_id = %(course_id)s" if course_id is not None else ""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                WITH normalized_attempts AS (
                    {build_normalized_knowledge_attempts_sql()}
                )
                SELECT
                    attempts.course_id,
                    c.course_name,
                    tcc.teaching_order,
                    attempts.knowledge_point_id,
                    COALESCE(kp.name, '未标注知识点') AS knowledge_point_name,
                    COALESCE(kp.category, '待归类') AS knowledge_category,
                    (SELECT COUNT(*)
                       FROM `{USER_SERVICE_SCHEMA}`.`teaching_class_student` class_member
                      WHERE class_member.teaching_class_id = %(class_id)s) AS student_count,
                    COUNT(DISTINCT attempts.student_id) AS attempted_student_count,
                    COUNT(DISTINCT CASE WHEN attempts.is_correct = 0 THEN attempts.student_id END)
                        AS incorrect_student_count,
                    COUNT(attempts.attempt_key) AS attempted_count,
                    SUM(CASE WHEN attempts.is_correct = 0 THEN 1 ELSE 0 END) AS incorrect_count,
                    GROUP_CONCAT(
                        DISTINCT CASE WHEN attempts.is_correct = 0
                            THEN CONCAT(attempts.student_id, '::',
                                COALESCE(u.user_name, u.user_student_number, '未命名学生'))
                        END SEPARATOR '|||'
                    ) AS affected_students,
                    GROUP_CONCAT(
                        DISTINCT CONCAT(attempts.generated_question_id, '::',
                            REPLACE(attempts.title, '|||', ''))
                        ORDER BY attempts.submitted_at DESC SEPARATOR '|||'
                    ) AS representative_questions
                FROM normalized_attempts attempts
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_student` tcs
                  ON tcs.student_id = attempts.student_id
                 AND tcs.teaching_class_id = %(class_id)s
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_course` tcc
                  ON tcc.teaching_class_id = %(class_id)s
                 AND tcc.course_id = attempts.course_id
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`course` c
                  ON c.id = attempts.course_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`user` u
                  ON u.user_id = attempts.student_id
                LEFT JOIN knowledge_point kp
                  ON kp.knowledge_point_id = attempts.knowledge_point_id
                WHERE 1 = 1
                  {course_filter}
                GROUP BY attempts.course_id, c.course_name, tcc.teaching_order,
                         attempts.knowledge_point_id, kp.name, kp.category
                ORDER BY incorrect_student_count DESC, knowledge_point_name
                """,
                {"class_id": class_id, "course_id": course_id},
            )
            rows = list(cursor.fetchall() or [])

    return {
        "teachingClassId": class_id,
        "courseId": course_id,
        "items": build_knowledge_risk_items(rows, course_id=course_id),
    }


def get_knowledge_risk_detail(
    teacher_id: int,
    class_id: int,
    course_id: int,
    knowledge_point_id: int,
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    risk_map = get_class_risk_map(teacher_id, class_id, course_id)
    summary = next(
        (
            item for item in risk_map["items"]
            if int(item.get("knowledgePointId") or 0) == int(knowledge_point_id)
        ),
        None,
    )
    if not summary:
        raise KeyError("knowledge point risk does not exist in selected experiment")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                WITH normalized_attempts AS (
                    {build_normalized_knowledge_attempts_sql()}
                )
                SELECT attempts.student_id,
                       COALESCE(u.user_name, u.user_student_number, '未命名学生') AS student_name,
                       attempts.answer_json, attempts.score, attempts.submitted_at,
                       attempts.generated_question_id, attempts.title,
                       attempts.standard_answer
                FROM normalized_attempts attempts
                INNER JOIN `{USER_SERVICE_SCHEMA}`.`teaching_class_student` tcs
                  ON tcs.teaching_class_id = %(class_id)s
                 AND tcs.student_id = attempts.student_id
                LEFT JOIN `{USER_SERVICE_SCHEMA}`.`user` u
                  ON u.user_id = attempts.student_id
                WHERE attempts.course_id = %(course_id)s
                  AND attempts.knowledge_point_id = %(knowledge_point_id)s
                  AND attempts.is_correct = 0
                ORDER BY attempts.submitted_at DESC, attempts.attempt_key DESC
                """,
                {
                    "class_id": class_id,
                    "course_id": course_id,
                    "knowledge_point_id": knowledge_point_id,
                },
            )
            rows = list(cursor.fetchall() or [])
    return build_knowledge_risk_detail(summary=summary, attempt_rows=rows, page=page, size=size)
