from __future__ import annotations

from typing import Any

from database import get_connection
from profile_repository import rebuild_student_profile
from teacher_repository import USER_SERVICE_SCHEMA, require_owned_teaching_class


def rebuild_teaching_class_profiles(class_id: int, teacher_id: int) -> dict[str, Any]:
    require_owned_teaching_class(teacher_id, class_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT student_id
                FROM `{USER_SERVICE_SCHEMA}`.`teaching_class_student`
                WHERE teaching_class_id = %(class_id)s
                ORDER BY student_id
                """,
                {"class_id": class_id},
            )
            student_ids = [int(row["student_id"]) for row in cursor.fetchall() or []]

            if not student_ids:
                # 教学班未在 teaching_class_student 登记学生时（例如直接使用行政班 class_id），
                # 回退到 class 表按 user.class_id_class_id 查询该班级学生，与教师分析一致。
                cursor.execute(
                    f"""
                    SELECT user_id
                    FROM `{USER_SERVICE_SCHEMA}`.`user`
                    WHERE class_id_class_id = %(class_id)s
                      AND (is_admin IS NULL OR is_admin = b'0' OR is_admin = 0)
                      AND COALESCE(is_deleted, 0) = 0
                    ORDER BY user_id
                    """,
                    {"class_id": class_id},
                )
                student_ids = [int(row["user_id"]) for row in cursor.fetchall() or []]

    failures: list[dict[str, Any]] = []
    rebuilt_count = 0
    for student_id in student_ids:
        try:
            rebuild_student_profile(student_id)
            rebuilt_count += 1
        except Exception:
            failures.append({"studentId": student_id, "message": "画像生成失败"})

    return {
        "teachingClassId": class_id,
        "studentCount": len(student_ids),
        "rebuiltCount": rebuilt_count,
        "failedCount": len(failures),
        "failures": failures,
    }
