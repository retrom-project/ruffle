"""Promote a verified, clean fork build to immutable release assets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from build_candidate import git

REPOSITORY = "https://github.com/retrom-project/ruffle"
UPSTREAM = "e46d1642fb67a53b56ffa4b1871cb7c57589e36d"
ABI = "ruffle-host-v1"
FILES = {"LICENSE.md", "LICENSE_APACHE", "LICENSE_MIT", "core.ruffle.js", "ruffle.js", "ruffle.wasm"}


def validate_candidate(candidate, commit):
    descriptor = json.loads((candidate / "retrom-core-candidate.json").read_text())
    expected = {"schemaVersion": 1, "kind": "RETROM_CORE_CANDIDATE_V1", "coreId": "ruffle",
                "repository": REPOSITORY, "commit": commit, "dirty": False, "adapterAbi": ABI}
    if any(descriptor.get(key) != value for key, value in expected.items()):
        raise ValueError("RUFFLE_RELEASE_CANDIDATE_IDENTITY_INVALID")
    if not re.fullmatch(r"[0-9a-f]{64}", descriptor.get("sourceTreeSha256", "")):
        raise ValueError("RUFFLE_RELEASE_SOURCE_DIGEST_INVALID")
    records = descriptor.get("files", [])
    if len(records) != len(FILES) or {row.get("filename") for row in records} != FILES:
        raise ValueError("RUFFLE_RELEASE_INVENTORY_INVALID")
    if {entry.name for entry in candidate.iterdir()} != FILES | {"retrom-core-candidate.json"}:
        raise ValueError("RUFFLE_RELEASE_EXTRA_FILES")
    for row in records:
        path = candidate / row["filename"]
        limit = (64 if path.name == "ruffle.wasm" else 4) * 1024 * 1024
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= limit:
            raise ValueError("RUFFLE_RELEASE_FILE_INVALID")
        data = path.read_bytes()
        if row.get("sizeBytes") != len(data) or row.get("sha256") != hashlib.sha256(data).hexdigest():
            raise ValueError("RUFFLE_RELEASE_FILE_MISMATCH")
    return descriptor


def release(candidate, output, tag, tag_ref=None):
    if not re.fullmatch(r"retrom-core-ge46d1642fb67-r[1-9][0-9]*(-rc\.[1-9][0-9]*)?", tag):
        raise ValueError("RUFFLE_RELEASE_TAG_INVALID")
    tag_ref = tag_ref or f"refs/tags/{tag}"
    if tag_ref not in {f"refs/tags/{tag}", f"refs/retrom-release/{tag}"}:
        raise ValueError("RUFFLE_RELEASE_TAG_REF_INVALID")
    commit = git("rev-parse", "HEAD")
    if git("cat-file", "-t", tag_ref) != "tag" or git("rev-list", "-n", "1", tag_ref) != commit:
        raise ValueError("RUFFLE_RELEASE_TAG_COMMIT_INVALID")
    git("merge-base", "--is-ancestor", commit, "origin/retrom/ge46d1642fb67")
    git("merge-base", "--is-ancestor", UPSTREAM, commit)
    if git("status", "--porcelain"):
        raise ValueError("RUFFLE_RELEASE_DIRTY")
    descriptor = validate_candidate(candidate, commit)
    output.mkdir(parents=True, exist_ok=False)
    for name in sorted(FILES):
        shutil.copyfile(candidate / name, output / name)
    metadata = {"schemaVersion": 1, "repository": REPOSITORY, "tag": tag, "commit": commit,
                "adapterAbi": ABI, "upstreamRepository": "https://github.com/ruffle-rs/ruffle",
                "upstreamCommit": UPSTREAM, "sourceTreeSha256": descriptor["sourceTreeSha256"],
                "files": descriptor["files"]}
    (output / "rpg-runtime-release.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--tag-ref")
    args = parser.parse_args()
    release(args.candidate, args.output, args.tag, args.tag_ref)
