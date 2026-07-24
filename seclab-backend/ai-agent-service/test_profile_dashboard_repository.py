import unittest

import profile_dashboard_repository as dashboard


class CompletedExperimentsTest(unittest.TestCase):
    def test_completion_count_uses_persisted_completion_events(self):
        class Cursor:
            sql = ""

            def execute(self, sql, params):
                self.sql = sql

            def fetchone(self):
                return {"total": 1}

        cursor = Cursor()

        self.assertEqual(dashboard._completed_courses(cursor, 291), 1)
        self.assertIn("challenge_completion_event", cursor.sql)
        self.assertIn("completion_status", cursor.sql)
        self.assertIn("COUNT(DISTINCT", cursor.sql)


class LearningProfileEvidenceTest(unittest.TestCase):
    def test_empty_snapshot_is_presented_as_an_empty_profile(self):
        profile = {
            "overall_score": 9,
            "ai_collaboration_score": 60,
            "profile_summary_json": {
                "evidence": {
                    "eventCount": 0,
                    "aiInteractionCount": 0,
                    "aiAskCount": 0,
                    "questionSubmitCount": 0,
                    "flagSubmitCount": 0,
                    "labStartCount": 0,
                    "activeDayCount": 0,
                }
            },
        }

        result = dashboard._learning_profile(profile)

        self.assertEqual(0, result["comprehensiveScore"])
        self.assertEqual([], result["tags"])
        self.assertTrue(all(item["score"] == 0 for item in result["skills"]))

    def test_snapshot_with_a_submission_keeps_its_scores(self):
        profile = {
            "overall_score": 45,
            "knowledge_mastery_score": 45,
            "profile_summary_json": {
                "evidence": {"questionSubmitCount": 1}
            },
        }

        result = dashboard._learning_profile(profile)

        self.assertEqual(45, result["comprehensiveScore"])


if __name__ == "__main__":
    unittest.main()
