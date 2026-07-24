import unittest

import teacher_intervention_repository as interventions


class TeacherInterventionHelpersTest(unittest.TestCase):
    def test_metric_snapshot_contains_all_profile_dimensions(self):
        snapshot = interventions.build_metric_snapshot(
            {
                "snapshot_id": "profile-1",
                "computed_at": "2026-07-17T10:00:00",
                "overall_score": 70,
                "knowledge_mastery_score": 71,
                "troubleshooting_score": 63,
                "autonomy_score": 68,
                "ai_collaboration_score": 74,
                "engagement_score": 80,
            }
        )

        self.assertEqual(snapshot["snapshotId"], "profile-1")
        self.assertEqual(snapshot["scores"]["aiCollaboration"], 74.0)
        self.assertEqual(set(snapshot["scores"]), {
            "overall", "knowledgeMastery", "troubleshooting", "autonomy", "aiCollaboration", "engagement"
        })

    def test_comparison_reports_delta_and_improvement(self):
        baseline = {"scores": {"overall": 60.0, "troubleshooting": 50.0}}
        latest = {"scores": {"overall": 68.0, "troubleshooting": 62.0}}

        result = interventions.compare_metric_snapshots(baseline, latest)

        self.assertEqual(result["delta"]["overall"], 8.0)
        self.assertEqual(result["delta"]["troubleshooting"], 12.0)
        self.assertEqual(result["improvedDimensions"], ["overall", "troubleshooting"])

    def test_comparison_handles_missing_latest_profile(self):
        result = interventions.compare_metric_snapshots({"scores": {"overall": 60.0}}, None)

        self.assertEqual(result, {"delta": {}, "improvedDimensions": [], "status": "NO_FOLLOW_UP"})


if __name__ == "__main__":
    unittest.main()
