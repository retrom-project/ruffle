"""Explicit fork-owned Web build and bounded candidate inventory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def build(output):
    if not output.is_absolute() or not output.is_dir() or any(output.iterdir()):
        raise ValueError("RUFFLE_CANDIDATE_OUTPUT_INVALID")
    recipe = ROOT / ".github/rpg-runtime/Dockerfile"
    image = "retrom-ruffle-toolchain:" + hashlib.sha256(recipe.read_bytes()).hexdigest()[:16]
    run("docker", "build", "-t", image, "-f", str(recipe), str(recipe.parent))
    common = Path(git("rev-parse", "--git-common-dir")).resolve()
    cache = ROOT / ".retrom-build"
    cache.mkdir(exist_ok=True)
    run("docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
        "--mount", f"type=bind,src={ROOT},dst={ROOT}",
        "--mount", f"type=bind,src={common},dst={common},readonly",
        "--env", f"CARGO_HOME={cache}/cargo", "--env", f"NPM_CONFIG_CACHE={cache}/npm",
        "--env", "RETROM_BUILD=1", "--env", f"SOURCE_DATE_EPOCH={git('show', '-s', '--format=%ct', 'HEAD')}",
        "--workdir", str(ROOT / "web"), image,
        "bash", "-ec", "npm ci --ignore-scripts && npm run build --workspace=ruffle-core && "
        "npm run build --workspace=ruffle-selfhosted")
    dist = ROOT / "web/packages/selfhosted/dist"
    sources = {name: dist / name for name in ["ruffle.js", "core.ruffle.js", "ruffle.wasm"]}
    for name in ["LICENSE.md", "LICENSE_MIT", "LICENSE_APACHE"]:
        sources[name] = ROOT / name if (ROOT / name).is_file() else dist / name
    records = []
    for name, source in sorted(sources.items()):
        data = source.read_bytes()
        if not data or len(data) > 64 * 1024 * 1024:
            raise ValueError("RUFFLE_CANDIDATE_FILE_INVALID")
        (output / name).write_bytes(data)
        records.append({"filename": name, "sizeBytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    digest = hashlib.sha256()
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    for name in sorted(set(names.split(b"\0")) - {b""}):
        path = ROOT / os.fsdecode(name)
        if path.is_file():
            digest.update(name + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    descriptor = {"schemaVersion": 1, "kind": "RETROM_CORE_CANDIDATE_V1", "coreId": "ruffle",
                  "repository": "https://github.com/retrom-project/ruffle", "branch": git("branch", "--show-current"),
                  "commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain")),
                  "sourceTreeSha256": digest.hexdigest(), "adapterAbi": "ruffle-host-v1", "files": records}
    (output / "retrom-core-candidate.json").write_text(json.dumps(descriptor, sort_keys=True) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2 or os.getuid() == 0:
        raise SystemExit("Usage: build-candidate.sh ABSOLUTE_EMPTY_DIRECTORY (non-root)")
    build(Path(sys.argv[1]))
