import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

import so100_motion as library


class MotionTests(unittest.TestCase):
    def test_all_recordings_and_endpoints(self):
        self.assertEqual(len(library.names()), 27)
        count = 0
        for name in library.names():
            motion = library.load(name)
            count += len(motion.frames)
            self.assertEqual(motion.sample(-1), motion.frames[0].pose)
            self.assertEqual(motion.sample(motion.duration + 1), motion.frames[-1].pose)
            for i in range(101):
                self.assertTrue(all(math.isfinite(v) for v in motion.sample(motion.duration * i / 100)))
        self.assertEqual(count, 198)

    def test_linear_interpolation_and_case_insensitive_lookup(self):
        motion = library.load("admiration")
        before, after = motion.frames[:2]
        expected = tuple((a + b) / 2 for a, b in zip(before.pose, after.pose))
        self.assertEqual(motion.sample((before.time + after.time) / 2), expected)
        self.assertEqual(motion, library.load("Admiration"))

    def test_duplicate_times_preserve_jump(self):
        motion = library.load("Craving")
        duplicate = [f for f in motion.frames if f.time == 2]
        self.assertEqual(len(duplicate), 2)
        self.assertNotEqual(duplicate[0].pose, duplicate[1].pose)
        self.assertEqual(motion.sample(2), duplicate[-1].pose)
        for a, b in zip(motion.sample(2 - 1e-9), duplicate[0].pose):
            self.assertAlmostEqual(a, b, places=7)

    def test_invalid_samples_and_unknown_names(self):
        motion = library.load("Joy")
        for value in [True, None, "1", float("nan"), float("inf"), -float("inf"), 10**1000]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                motion.sample(value)
        for value in ["../Joy", "unknown", None, "Joy.json"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                library.load(value)

    def test_invalid_files_fail_before_sampling(self):
        base = {
            "name": "fixture", "coordinate_system": "new_radians_empirical",
            "conversion_info": {"joint_order": list(library.JOINTS)},
            "keyframes": [{"time": 0, "pose": [0] * 6}, {"time": 1, "pose": [1] * 6}],
        }
        cases = []
        for key, value in [("keyframes", []), ("name", ""), ("coordinate_system", "unknown"), ("conversion_info", {})]:
            candidate = copy.deepcopy(base); candidate[key] = value; cases.append(candidate)
        for field, value in [("time", -1), ("time", True), ("pose", [0] * 5), ("pose", [0] * 5 + [float("nan")])]:
            candidate = copy.deepcopy(base); candidate["keyframes"][1][field] = value; cases.append(candidate)
        candidate = copy.deepcopy(base); candidate["keyframes"].reverse(); cases.append(candidate)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "motion.json"
            path.write_text(json.dumps(base))
            self.assertEqual(library.load_file(path).sample(0.5), (0.5,) * 6)
            for candidate in cases:
                path.write_text(json.dumps(candidate))
                with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                    library.load_file(path)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "motion.json"
            for field in ["time", "pose"]:
                path.write_text('{"keyframes": [{"' + field + '": 0, "' + field + '": 1}]}')
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                    library.load_file(path)


if __name__ == "__main__":
    unittest.main()
