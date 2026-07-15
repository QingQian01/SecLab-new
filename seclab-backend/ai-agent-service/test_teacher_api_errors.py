import unittest

import main


class TeacherApiErrorTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
