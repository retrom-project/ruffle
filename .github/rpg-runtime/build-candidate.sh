#!/usr/bin/env bash
set -euo pipefail
test "$(id -u)" != 0
exec python3 "$(dirname "$0")/build_candidate.py" "$@"
