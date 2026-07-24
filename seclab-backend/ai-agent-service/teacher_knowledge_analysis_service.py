from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from database import get_connection
from teacher_ai_analysis_service import _call_dify_for_student_analysis
from teacher_learning_insight_repository import get_knowledge_risk_detail


EXERCISE_ROLES = {"FOUNDATION", "CONSOLIDATION", "TRANSFER"}
REVIEW_STATUSES = {"PENDING_REVIEW", "APPROVED", "NEEDS_REVISION", "REJECTED"}
EDITABLE_FIELDS = {
    "questionType": "question_type",
    "stem": "stem",
    "options": "options_json",
    "standardAnswer": "standard_answer",
    "explanation": "explanation",
    "difficulty": "difficulty",
    "generationRationale": "generation_rationale",
}


class AnalysisAlreadyRunningError(RuntimeError):
    pass


class ProviderUnavailableError(RuntimeError):
    pass


class InvalidAnalysisResultError(ValueError):
    pass


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS teacher_knowledge_analysis (
      analysis_id BIGINT NOT NULL AUTO_INCREMENT,
      teacher_id BIGINT NOT NULL,
      teaching_class_id BIGINT NOT NULL,
      course_id INT NOT NULL,
      knowledge_point_id BIGINT NOT NULL,
      analysis_status VARCHAR(16) NOT NULL DEFAULT 'IDLE',
      analysis_json LONGTEXT NULL,
      evidence_json LONGTEXT NULL,
      last_attempt_at DATETIME(6) NULL,
      last_error_message VARCHAR(500) NULL,
      generated_at DATETIME(6) NULL,
      updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
      PRIMARY KEY (analysis_id),
      UNIQUE KEY uk_teacher_knowledge_scope (teacher_id, teaching_class_id, course_id, knowledge_point_id),
      KEY idx_teacher_knowledge_lookup (teaching_class_id, course_id, knowledge_point_id, analysis_status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS teacher_knowledge_exercise (
      exercise_id BIGINT NOT NULL AUTO_INCREMENT,
      analysis_id BIGINT NOT NULL,
      exercise_role VARCHAR(24) NOT NULL,
      question_type VARCHAR(32) NOT NULL,
      stem TEXT NOT NULL,
      options_json LONGTEXT NULL,
      standard_answer LONGTEXT NOT NULL,
      explanation LONGTEXT NULL,
      difficulty INT NOT NULL DEFAULT 1,
      generation_rationale TEXT NULL,
      review_status VARCHAR(24) NOT NULL DEFAULT 'PENDING_REVIEW',
      review_comment TEXT NULL,
      source_version INT NOT NULL DEFAULT 1,
      reviewed_by BIGINT NULL,
      reviewed_at DATETIME(6) NULL,
      created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
      updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
      PRIMARY KEY (exercise_id),
      UNIQUE KEY uk_teacher_knowledge_exercise_role (analysis_id, exercise_role),
      KEY idx_teacher_knowledge_exercise_review (review_status, updated_at),
      CONSTRAINT fk_teacher_knowledge_exercise_analysis FOREIGN KEY (analysis_id)
        REFERENCES teacher_knowledge_analysis (analysis_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize_exercise(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exerciseId": int(row["exercise_id"]),
        "analysisId": int(row["analysis_id"]),
        "role": row.get("exercise_role"),
        "questionType": row.get("question_type"),
        "stem": row.get("stem"),
        "options": _loads(row.get("options_json"), []),
        "standardAnswer": row.get("standard_answer"),
        "explanation": row.get("explanation") or "",
        "difficulty": int(row.get("difficulty") or 1),
        "generationRationale": row.get("generation_rationale") or "",
        "reviewStatus": row.get("review_status") or "PENDING_REVIEW",
        "reviewComment": row.get("review_comment") or "",
        "sourceVersion": int(row.get("source_version") or 1),
        "reviewedBy": row.get("reviewed_by"),
        "reviewedAt": _iso(row.get("reviewed_at")),
        "updatedAt": _iso(row.get("updated_at")),
    }


class KnowledgeAnalysisRepository:
    def __init__(
        self,
        connection_factory: Callable[..., Any] = get_connection,
        memory_store: Optional[dict[Any, Any]] = None,
    ):
        self.connection_factory = connection_factory
        self.memory_store = memory_store

    @staticmethod
    def _key(teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int):
        return teacher_id, class_id, course_id, knowledge_point_id

    def ensure_schema(self) -> None:
        if self.memory_store is not None:
            return
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                for statement in SCHEMA_STATEMENTS:
                    cursor.execute(statement)
            conn.commit()

    def begin(self, teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int) -> None:
        key = self._key(teacher_id, class_id, course_id, knowledge_point_id)
        if self.memory_store is not None:
            row = self.memory_store.setdefault(key, {
                "analysis_id": len([item for item in self.memory_store if isinstance(item, tuple) and len(item) == 4]) + 1,
                "teacher_id": teacher_id,
                "teaching_class_id": class_id,
                "course_id": course_id,
                "knowledge_point_id": knowledge_point_id,
                "analysis_status": "IDLE",
                "analysis_json": None,
                "evidence_json": None,
                "last_error_message": None,
                "generated_at": None,
                "exercises": [],
            })
            if row["analysis_status"] == "RUNNING":
                raise AnalysisAlreadyRunningError("knowledge analysis is already running")
            row.update(analysis_status="RUNNING", last_attempt_at=_utcnow(), last_error_message=None)
            return
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT analysis_status FROM teacher_knowledge_analysis
                    WHERE teacher_id=%s AND teaching_class_id=%s AND course_id=%s AND knowledge_point_id=%s
                    FOR UPDATE
                    """,
                    key,
                )
                current = cursor.fetchone()
                if current and current.get("analysis_status") == "RUNNING":
                    raise AnalysisAlreadyRunningError("knowledge analysis is already running")
                cursor.execute(
                    """
                    INSERT INTO teacher_knowledge_analysis (
                      teacher_id, teaching_class_id, course_id, knowledge_point_id,
                      analysis_status, last_attempt_at, last_error_message
                    ) VALUES (%s,%s,%s,%s,'RUNNING',NOW(6),NULL)
                    ON DUPLICATE KEY UPDATE analysis_status='RUNNING', last_attempt_at=NOW(6), last_error_message=NULL
                    """,
                    key,
                )
            conn.commit()

    def save_success(
        self,
        teacher_id: int,
        class_id: int,
        course_id: int,
        knowledge_point_id: int,
        analysis: dict[str, Any],
        evidence: dict[str, Any],
        exercises: list[dict[str, Any]],
    ) -> None:
        key = self._key(teacher_id, class_id, course_id, knowledge_point_id)
        if self.memory_store is not None:
            row = self.memory_store[key]
            row.update(
                analysis_status="READY",
                analysis_json=analysis,
                evidence_json=evidence,
                last_error_message=None,
                generated_at=_utcnow(),
            )
            stored = []
            for item in exercises:
                exercise_id = max(
                    [value.get("exercise_id", 0) for value in self.memory_store.values() if isinstance(value, dict)] + [0]
                ) + len(stored) + 1
                stored.append({
                    "exercise_id": exercise_id,
                    "analysis_id": row["analysis_id"],
                    "exercise_role": item["role"],
                    "question_type": item["questionType"],
                    "stem": item["stem"],
                    "options_json": item.get("options") or [],
                    "standard_answer": item["standardAnswer"],
                    "explanation": item.get("explanation") or "",
                    "difficulty": item.get("difficulty") or 1,
                    "generation_rationale": item.get("generationRationale") or "",
                    "review_status": "PENDING_REVIEW",
                    "review_comment": "",
                    "source_version": 1,
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "updated_at": _utcnow(),
                })
            row["exercises"] = stored
            return
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE teacher_knowledge_analysis
                    SET analysis_status='READY', analysis_json=%s, evidence_json=%s,
                        generated_at=NOW(6), last_error_message=NULL
                    WHERE teacher_id=%s AND teaching_class_id=%s AND course_id=%s AND knowledge_point_id=%s
                    """,
                    (_dumps(analysis), _dumps(evidence), *key),
                )
                cursor.execute(
                    """SELECT analysis_id FROM teacher_knowledge_analysis
                    WHERE teacher_id=%s AND teaching_class_id=%s AND course_id=%s AND knowledge_point_id=%s""",
                    key,
                )
                analysis_id = int(cursor.fetchone()["analysis_id"])
                for item in exercises:
                    cursor.execute(
                        """
                        INSERT INTO teacher_knowledge_exercise (
                          analysis_id, exercise_role, question_type, stem, options_json,
                          standard_answer, explanation, difficulty, generation_rationale,
                          review_status, review_comment, source_version, reviewed_by, reviewed_at
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'PENDING_REVIEW',NULL,1,NULL,NULL)
                        ON DUPLICATE KEY UPDATE question_type=VALUES(question_type), stem=VALUES(stem),
                          options_json=VALUES(options_json), standard_answer=VALUES(standard_answer),
                          explanation=VALUES(explanation), difficulty=VALUES(difficulty),
                          generation_rationale=VALUES(generation_rationale), review_status='PENDING_REVIEW',
                          review_comment=NULL, source_version=source_version+1, reviewed_by=NULL, reviewed_at=NULL
                        """,
                        (
                            analysis_id, item["role"], item["questionType"], item["stem"],
                            _dumps(item.get("options") or []), item["standardAnswer"],
                            item.get("explanation") or "", item.get("difficulty") or 1,
                            item.get("generationRationale") or "",
                        ),
                    )
            conn.commit()

    def save_failure(self, teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int, message: str) -> None:
        key = self._key(teacher_id, class_id, course_id, knowledge_point_id)
        if self.memory_store is not None:
            row = self.memory_store[key]
            row["analysis_status"] = "READY" if row.get("analysis_json") else "FAILED"
            row["last_error_message"] = str(message)[:500]
            return
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE teacher_knowledge_analysis
                    SET analysis_status=IF(analysis_json IS NULL,'FAILED','READY'), last_error_message=%s
                    WHERE teacher_id=%s AND teaching_class_id=%s AND course_id=%s AND knowledge_point_id=%s
                    """,
                    (str(message)[:500], *key),
                )
            conn.commit()

    def _get_memory_exercise(self, teacher_id: int, class_id: int, exercise_id: int):
        for key, row in self.memory_store.items():
            if not isinstance(key, tuple) or len(key) != 4:
                continue
            if key[0] != teacher_id or key[1] != class_id:
                continue
            for exercise in row.get("exercises") or []:
                if int(exercise["exercise_id"]) == int(exercise_id):
                    return exercise
        raise KeyError("knowledge exercise does not exist")

    def update_exercise(self, teacher_id: int, class_id: int, exercise_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {key: value for key, value in changes.items() if key in EDITABLE_FIELDS}
        if not allowed:
            raise ValueError("no editable exercise fields supplied")
        if self.memory_store is not None:
            row = self._get_memory_exercise(teacher_id, class_id, exercise_id)
            for key, value in allowed.items():
                row[EDITABLE_FIELDS[key]] = value
            row.update(
                review_status="PENDING_REVIEW",
                review_comment="",
                reviewed_by=None,
                reviewed_at=None,
                source_version=int(row.get("source_version") or 1) + 1,
                updated_at=_utcnow(),
            )
            return _serialize_exercise(row)
        assignments = []
        values = []
        for key, value in allowed.items():
            column = EDITABLE_FIELDS[key]
            assignments.append(f"{column}=%s")
            values.append(_dumps(value) if key == "options" else value)
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE teacher_knowledge_exercise e
                    INNER JOIN teacher_knowledge_analysis a ON a.analysis_id=e.analysis_id
                    SET {', '.join(assignments)}, e.review_status='PENDING_REVIEW',
                        e.review_comment=NULL, e.reviewed_by=NULL, e.reviewed_at=NULL,
                        e.source_version=e.source_version+1
                    WHERE e.exercise_id=%s AND a.teacher_id=%s AND a.teaching_class_id=%s
                    """,
                    (*values, exercise_id, teacher_id, class_id),
                )
                if cursor.rowcount != 1:
                    raise KeyError("knowledge exercise does not exist")
            conn.commit()
        return self.get_exercise(teacher_id, class_id, exercise_id)

    def review_exercise(self, teacher_id: int, class_id: int, exercise_id: int, status: str, comment: str) -> dict[str, Any]:
        status = str(status or "").upper()
        if status not in REVIEW_STATUSES - {"PENDING_REVIEW"}:
            raise ValueError("unsupported exercise review status")
        if self.memory_store is not None:
            row = self._get_memory_exercise(teacher_id, class_id, exercise_id)
            row.update(
                review_status=status,
                review_comment=str(comment or "").strip(),
                reviewed_by=teacher_id,
                reviewed_at=_utcnow(),
                updated_at=_utcnow(),
            )
            return _serialize_exercise(row)
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE teacher_knowledge_exercise e
                    INNER JOIN teacher_knowledge_analysis a ON a.analysis_id=e.analysis_id
                    SET e.review_status=%s, e.review_comment=%s, e.reviewed_by=%s, e.reviewed_at=NOW(6)
                    WHERE e.exercise_id=%s AND a.teacher_id=%s AND a.teaching_class_id=%s
                    """,
                    (status, str(comment or "").strip(), teacher_id, exercise_id, teacher_id, class_id),
                )
                if cursor.rowcount != 1:
                    raise KeyError("knowledge exercise does not exist")
            conn.commit()
        return self.get_exercise(teacher_id, class_id, exercise_id)

    def get_exercise(self, teacher_id: int, class_id: int, exercise_id: int) -> dict[str, Any]:
        if self.memory_store is not None:
            return _serialize_exercise(self._get_memory_exercise(teacher_id, class_id, exercise_id))
        self.ensure_schema()
        with self.connection_factory() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT e.* FROM teacher_knowledge_exercise e
                    INNER JOIN teacher_knowledge_analysis a ON a.analysis_id=e.analysis_id
                    WHERE e.exercise_id=%s AND a.teacher_id=%s AND a.teaching_class_id=%s
                    """,
                    (exercise_id, teacher_id, class_id),
                )
                row = cursor.fetchone()
        if not row:
            raise KeyError("knowledge exercise does not exist")
        return _serialize_exercise(row)

    def get(self, teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int) -> dict[str, Any]:
        key = self._key(teacher_id, class_id, course_id, knowledge_point_id)
        if self.memory_store is not None:
            row = self.memory_store.get(key)
            if not row:
                return {
                    "teacherId": teacher_id, "teachingClassId": class_id, "courseId": course_id,
                    "knowledgePointId": knowledge_point_id, "analysisStatus": "IDLE", "analysis": None,
                    "evidence": None, "lastErrorMessage": None, "generatedAt": None, "exercises": [],
                }
            exercises = [_serialize_exercise(item) for item in row.get("exercises") or []]
        else:
            self.ensure_schema()
            with self.connection_factory() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """SELECT * FROM teacher_knowledge_analysis
                        WHERE teacher_id=%s AND teaching_class_id=%s AND course_id=%s AND knowledge_point_id=%s""",
                        key,
                    )
                    row = cursor.fetchone()
                    if row:
                        cursor.execute(
                            "SELECT * FROM teacher_knowledge_exercise WHERE analysis_id=%s ORDER BY exercise_id",
                            (row["analysis_id"],),
                        )
                        exercises = [_serialize_exercise(item) for item in cursor.fetchall() or []]
                    else:
                        exercises = []
            if not row:
                return {
                    "teacherId": teacher_id, "teachingClassId": class_id, "courseId": course_id,
                    "knowledgePointId": knowledge_point_id, "analysisStatus": "IDLE", "analysis": None,
                    "evidence": None, "lastErrorMessage": None, "generatedAt": None, "exercises": [],
                }
        return {
            "teacherId": teacher_id,
            "teachingClassId": class_id,
            "courseId": course_id,
            "knowledgePointId": knowledge_point_id,
            "analysisStatus": row.get("analysis_status") or "IDLE",
            "analysis": _loads(row.get("analysis_json"), None),
            "evidence": _loads(row.get("evidence_json"), None),
            "lastErrorMessage": row.get("last_error_message"),
            "generatedAt": _iso(row.get("generated_at")),
            "exercises": exercises,
        }


def _validate_result(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InvalidAnalysisResultError("AI analysis must be a JSON object")
    for field in ("overallConclusion", "commonMistakes", "teachingAdvice", "exercises"):
        if not payload.get(field):
            raise InvalidAnalysisResultError(f"AI analysis is missing {field}")
    exercises = payload.get("exercises")
    if not isinstance(exercises, list) or len(exercises) != 3:
        raise InvalidAnalysisResultError("AI analysis must contain exactly three exercises")
    roles = {str(item.get("role") or "").upper() for item in exercises if isinstance(item, dict)}
    if roles != EXERCISE_ROLES:
        raise InvalidAnalysisResultError("AI exercises must cover foundation, consolidation and transfer")
    normalized = []
    for item in exercises:
        if not item.get("stem") or not item.get("standardAnswer"):
            raise InvalidAnalysisResultError("AI exercise is missing stem or standard answer")
        normalized.append({
            **item,
            "role": str(item["role"]).upper(),
            "questionType": item.get("questionType") or "short_answer",
            "options": item.get("options") if isinstance(item.get("options"), list) else [],
            "difficulty": max(1, min(int(item.get("difficulty") or 1), 5)),
        })
    return {**payload, "exercises": normalized}


def _text(value: Any, default: str = "") -> str:
    normalized = str(value or "").strip()
    return normalized or default


def _is_explanatory_answer(value: Any) -> bool:
    answer = _text(value)
    if len(answer) < 10:
        return False
    try:
        parsed = json.loads(answer)
    except (TypeError, ValueError):
        return True
    return isinstance(parsed, str) and len(parsed.strip()) >= 10


def _build_evidence_result(evidence: dict[str, Any]) -> dict[str, Any]:
    knowledge_name = _text(evidence.get("knowledgePointName"), "当前知识点")
    attempted_count = int(evidence.get("attemptedCount") or 0)
    incorrect_count = int(evidence.get("incorrectCount") or 0)
    incorrect_rate = evidence.get("incorrectRate")
    if incorrect_rate is None:
        incorrect_rate = incorrect_count / attempted_count if attempted_count else 0
    percent = round(float(incorrect_rate) * 100, 1)

    raw_mistakes = [
        item for item in (evidence.get("commonMistakes") or [])
        if isinstance(item, dict) and _text(item.get("answer"))
    ]
    common_mistakes = [
        {
            "title": f"高频错误作答 {index + 1}",
            "reason": (
                f"作答“{_text(item.get('answer'))}”出现 {int(item.get('count') or 0)} 次，"
                f"涉及 {int(item.get('studentCount') or 0)} 名学生。"
            ),
            "answer": _text(item.get("answer")),
            "count": int(item.get("count") or 0),
            "studentCount": int(item.get("studentCount") or 0),
        }
        for index, item in enumerate(raw_mistakes[:3])
    ]
    if not common_mistakes:
        common_mistakes = [{
            "title": "未形成集中错误",
            "reason": f"当前记录的 {attempted_count} 次作答中有 {incorrect_count} 次错误。",
            "answer": "",
            "count": incorrect_count,
            "studentCount": int(evidence.get("incorrectStudentCount") or 0),
        }]

    attempts = [
        item for item in (evidence.get("representativeAttempts") or [])
        if isinstance(item, dict)
    ]
    reference = next(
        (item for item in attempts if _is_explanatory_answer(item.get("standardAnswer"))),
        None,
    ) or next(
        (item for item in attempts if _text(item.get("standardAnswer"))),
        {},
    )
    reference_title = _text(reference.get("title"), knowledge_name)
    standard_answer = _text(
        reference.get("standardAnswer"),
        f"答案需准确说明“{knowledge_name}”的关键判断步骤，并给出与实验要求一致的依据。",
    )
    common_answer = _text(raw_mistakes[0].get("answer")) if raw_mistakes else ""
    mistake_action = (
        f"先展示高频错误作答“{common_answer}”，再与标准答案逐项对照。"
        if common_answer else
        "选取本次作答记录与标准答案逐项对照。"
    )

    exercises = [
        {
            "role": "FOUNDATION",
            "questionType": "short_answer",
            "stem": f"请完成“{reference_title}”，写出关键判断步骤。",
            "options": [],
            "standardAnswer": standard_answer,
            "explanation": f"依据本次“{knowledge_name}”作答记录中的标准答案进行核对。",
            "difficulty": 1,
            "generationRationale": "复查本次错误记录对应的基础步骤。",
        },
        {
            "role": "CONSOLIDATION",
            "questionType": "short_answer",
            "stem": (
                f"有同学在“{knowledge_name}”中作答“{common_answer}”。"
                "请指出问题并写出正确答案。"
                if common_answer else
                f"请复核“{knowledge_name}”的作答过程，写出正确答案及判断依据。"
            ),
            "options": [],
            "standardAnswer": standard_answer,
            "explanation": mistake_action,
            "difficulty": 2,
            "generationRationale": "针对本次高频错误进行辨析。",
        },
        {
            "role": "TRANSFER",
            "questionType": "short_answer",
            "stem": f"实验条件变化后，如何继续验证“{knowledge_name}”？请写出步骤与判断依据。",
            "options": [],
            "standardAnswer": standard_answer,
            "explanation": "按标准答案检查步骤、顺序和判断依据是否完整。",
            "difficulty": 3,
            "generationRationale": "检验能否在变化条件下复用本知识点的判断方法。",
        },
    ]
    return {
        "overallConclusion": (
            f"“{knowledge_name}”共有 {attempted_count} 次作答，其中 {incorrect_count} 次错误，"
            f"错误率 {percent:g}%。"
        ),
        "commonMistakes": common_mistakes,
        "teachingAdvice": [
            {
                "title": "对照讲评",
                "action": mistake_action,
            },
            {
                "title": "当堂复练",
                "action": "讲评后完成基础题与巩固题，重点检查步骤和判断依据。",
            },
        ],
        "exercises": exercises,
    }


class KnowledgeAnalysisService:
    def __init__(
        self,
        repository: KnowledgeAnalysisRepository,
        evidence_loader: Callable[[int, int, int, int], dict[str, Any]],
        provider: Callable[[str, str], Awaitable[dict[str, Any]]],
        timeout_seconds: float = 45,
        max_attempts: int = 2,
    ):
        self.repository = repository
        self.evidence_loader = evidence_loader
        self.provider = provider
        self.timeout_seconds = max(0.1, float(timeout_seconds))
        self.max_attempts = max(1, int(max_attempts))

    async def _request_provider(self, prompt: str, user_key: str) -> dict[str, Any]:
        last_error: Optional[ProviderUnavailableError] = None
        for attempt in range(self.max_attempts):
            try:
                return await asyncio.wait_for(
                    self.provider(prompt, user_key),
                    timeout=self.timeout_seconds,
                )
            except TimeoutError as exc:
                detail = str(exc).strip()
                message = f"AI 分析请求超时：{detail}" if detail else "AI 分析请求超时，请稍后重试"
                last_error = ProviderUnavailableError(message)
                last_error.__cause__ = exc
            except ValueError as exc:
                message = str(exc).strip() or "AI 返回内容不是有效结构化结果"
                raise ProviderUnavailableError(message) from exc
            except Exception as exc:
                message = str(exc).strip() or "AI 分析服务暂不可用，请稍后重试"
                last_error = ProviderUnavailableError(message)
                last_error.__cause__ = exc
            if attempt + 1 < self.max_attempts:
                await asyncio.sleep(0)
        raise last_error or ProviderUnavailableError("AI 分析服务暂不可用，请稍后重试")

    def get_analysis(self, teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int):
        return self.repository.get(teacher_id, class_id, course_id, knowledge_point_id)

    async def run_analysis(self, teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int):
        evidence = self.evidence_loader(teacher_id, class_id, course_id, knowledge_point_id)
        if int(evidence.get("attemptedCount") or 0) <= 0:
            raise ValueError("当前知识点暂无可分析的有效作答")
        previous = self.repository.get(teacher_id, class_id, course_id, knowledge_point_id)
        self.repository.begin(teacher_id, class_id, course_id, knowledge_point_id)
        prompt = (
            "你是网络安全实验课教师助理。只能根据给定知识点证据返回JSON。"
            "字段必须是overallConclusion、commonMistakes、teachingAdvice、exercises。"
            "exercises必须正好三道，role分别为FOUNDATION、CONSOLIDATION、TRANSFER，"
            "每道包含questionType、stem、options、standardAnswer、explanation、difficulty、generationRationale。"
            "不得编造学生姓名、人数或证据。证据：" + _dumps(evidence)
        )
        try:
            raw = await self._request_provider(
                prompt,
                f"knowledge-{class_id}-{course_id}-{knowledge_point_id}",
            )
            result = _validate_result(raw)
        except AnalysisAlreadyRunningError:
            raise
        except Exception as exc:
            if previous.get("analysis"):
                message = str(exc).strip() or "AI 分析服务暂不可用，请稍后重试"
                self.repository.save_failure(
                    teacher_id,
                    class_id,
                    course_id,
                    knowledge_point_id,
                    message,
                )
                return self.get_analysis(teacher_id, class_id, course_id, knowledge_point_id)
            result = _validate_result(_build_evidence_result(evidence))
        analysis = {key: result[key] for key in ("overallConclusion", "commonMistakes", "teachingAdvice")}
        self.repository.save_success(
            teacher_id, class_id, course_id, knowledge_point_id,
            analysis, evidence, result["exercises"],
        )
        return self.get_analysis(teacher_id, class_id, course_id, knowledge_point_id)

    def update_exercise(self, teacher_id: int, class_id: int, exercise_id: int, changes: dict[str, Any]):
        return self.repository.update_exercise(teacher_id, class_id, exercise_id, changes)

    def review_exercise(self, teacher_id: int, class_id: int, exercise_id: int, status: str, comment: str = ""):
        return self.repository.review_exercise(teacher_id, class_id, exercise_id, status, comment)

    async def regenerate_exercise(self, teacher_id: int, class_id: int, exercise_id: int):
        current = self.repository.get_exercise(teacher_id, class_id, exercise_id)
        prompt = (
            "你是网络安全实验课教师助理。请重新生成一道与原题相同角色的例题，只返回JSON对象，"
            "字段为role、questionType、stem、options、standardAnswer、explanation、difficulty、generationRationale。"
            "不得改变role。原题：" + _dumps(current)
        )
        try:
            raw = await self._request_provider(prompt, f"knowledge-exercise-{exercise_id}")
        except Exception as exc:
            message = str(exc).strip() or "AI 分析服务暂不可用，请稍后重试"
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(message) from exc
        item = raw.get("exercise") if isinstance(raw, dict) and isinstance(raw.get("exercise"), dict) else raw
        if not isinstance(item, dict) or not item.get("stem") or not item.get("standardAnswer"):
            raise ProviderUnavailableError("AI 未返回完整例题")
        if str(item.get("role") or "").upper() != str(current.get("role") or "").upper():
            raise ProviderUnavailableError("AI 返回的例题角色与原题不一致")
        return self.repository.update_exercise(
            teacher_id,
            class_id,
            exercise_id,
            {
                "questionType": item.get("questionType") or "short_answer",
                "stem": item["stem"],
                "options": item.get("options") if isinstance(item.get("options"), list) else [],
                "standardAnswer": item["standardAnswer"],
                "explanation": item.get("explanation") or "",
                "difficulty": max(1, min(int(item.get("difficulty") or 1), 5)),
                "generationRationale": item.get("generationRationale") or "",
            },
        )


def _load_evidence(teacher_id: int, class_id: int, course_id: int, knowledge_point_id: int):
    return get_knowledge_risk_detail(teacher_id, class_id, course_id, knowledge_point_id, 1, 100)


async def _provider(prompt: str, user_key: str):
    return await _call_dify_for_student_analysis(prompt, user_key)


KNOWLEDGE_ANALYSIS_REPOSITORY = KnowledgeAnalysisRepository()
KNOWLEDGE_ANALYSIS_SERVICE = KnowledgeAnalysisService(
    KNOWLEDGE_ANALYSIS_REPOSITORY,
    _load_evidence,
    _provider,
)
