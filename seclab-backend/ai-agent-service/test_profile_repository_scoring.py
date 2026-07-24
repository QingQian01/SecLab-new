import unittest
from collections import defaultdict

from profile_repository import _has_learning_evidence, _score_profile


class ProfileRepositoryScoringTest(unittest.TestCase):
    def test_no_learning_evidence_has_no_dimension_scores(self):
        scores, _ = _score_profile(defaultdict(int))

        self.assertEqual(0, scores["ai_collaboration_score"])
        self.assertEqual(0, scores["overall_score"])

    def test_learning_evidence_requires_a_recorded_action(self):
        self.assertFalse(_has_learning_evidence(defaultdict(int)))
        self.assertTrue(_has_learning_evidence(defaultdict(int, question_submit_count=1)))


if __name__ == "__main__":
    unittest.main()
