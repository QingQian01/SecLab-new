import unittest
from unittest.mock import patch

import main


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
