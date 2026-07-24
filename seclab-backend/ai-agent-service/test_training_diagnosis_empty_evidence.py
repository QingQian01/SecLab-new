import unittest
from unittest.mock import patch

from training_diagnosis_service import _score_candidates


class TrainingDiagnosisEmptyEvidenceTest(unittest.TestCase):
    def test_does_not_invent_knowledge_points_without_learning_evidence(self):
        catalog = {
            1: {"knowledge_point_id": 1, "name": "SQL注入联合查询列数判断"},
            2: {"knowledge_point_id": 2, "name": "SQL盲注与时间延迟判断"},
            3: {"knowledge_point_id": 3, "name": "XSS输入输出上下文判断"},
        }
        evidence = {
            "recent_submissions": [],
            "recent_events": [],
            "recent_ai_topics": [],
        }

        with patch("training_diagnosis_service._kp_catalog", return_value=catalog):
            result = _score_candidates(
                evidence=evidence,
                scores={},
                recent_focus="",
                tags=[],
            )

        self.assertEqual([], result)


if __name__ == "__main__":
    unittest.main()
