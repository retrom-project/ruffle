import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.candidate = Path(self.directory.name) / "candidate"
        self.candidate.mkdir()
        self.commit = "a" * 40
        self.descriptor = {"schemaVersion": 1, "kind": "RETROM_CORE_CANDIDATE_V1", "coreId": "ruffle",
                           "repository": release.REPOSITORY, "commit": self.commit, "dirty": False,
                           "adapterAbi": release.ABI, "sourceTreeSha256": "b" * 64, "files": []}
        for name in sorted(release.FILES):
            data = name.encode()
            (self.candidate / name).write_bytes(data)
            self.descriptor["files"].append({"filename": name, "sizeBytes": len(data),
                                             "sha256": hashlib.sha256(data).hexdigest()})
        self.write_descriptor()

    def write_descriptor(self):
        (self.candidate / "retrom-core-candidate.json").write_text(json.dumps(self.descriptor))

    def test_clean_inventory(self):
        self.assertEqual(release.validate_candidate(self.candidate, self.commit), self.descriptor)

    def test_bad_identity(self):
        for key, value in [("dirty", True), ("commit", "c" * 40), ("adapterAbi", "wrong"),
                           ("repository", "https://example.com"), ("sourceTreeSha256", "bad")]:
            original = self.descriptor[key]
            self.descriptor[key] = value
            self.write_descriptor()
            with self.subTest(key=key), self.assertRaises(ValueError):
                release.validate_candidate(self.candidate, self.commit)
            self.descriptor[key] = original

    def test_tampered_file(self):
        (self.candidate / "ruffle.js").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            release.validate_candidate(self.candidate, self.commit)

    def test_extra_file(self):
        (self.candidate / "extra").touch()
        with self.assertRaises(ValueError):
            release.validate_candidate(self.candidate, self.commit)

    def test_symlink(self):
        (self.candidate / "ruffle.js").unlink()
        (self.candidate / "ruffle.js").symlink_to("core.ruffle.js")
        with self.assertRaises(ValueError):
            release.validate_candidate(self.candidate, self.commit)

    def test_duplicate_inventory(self):
        self.descriptor["files"][0] = self.descriptor["files"][1]
        self.write_descriptor()
        with self.assertRaises(ValueError):
            release.validate_candidate(self.candidate, self.commit)

    def test_reject_wrong_tag_before_build_access(self):
        with self.assertRaisesRegex(ValueError, "TAG_INVALID"):
            release.release(self.candidate, Path(self.directory.name) / "release", "latest")

    def test_reject_lightweight_tag(self):
        with patch.object(release, "git", side_effect=[self.commit, "commit"]):
            with self.assertRaisesRegex(ValueError, "TAG_COMMIT_INVALID"):
                release.release(self.candidate, Path(self.directory.name) / "release", "retrom-core-ge46d1642fb67-r1")

    def test_promote_exact_files(self):
        output = Path(self.directory.name) / "release"
        with patch.object(release, "git", side_effect=[self.commit, "tag", self.commit, "", "", ""]):
            release.release(self.candidate, output, "retrom-core-ge46d1642fb67-r1")
        self.assertEqual({p.name for p in output.iterdir()}, release.FILES | {"rpg-runtime-release.json"})
        metadata = json.loads((output / "rpg-runtime-release.json").read_text())
        self.assertEqual(metadata["commit"], self.commit)
        self.assertEqual(metadata["files"], self.descriptor["files"])


if __name__ == "__main__":
    unittest.main()
