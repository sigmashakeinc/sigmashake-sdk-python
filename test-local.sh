#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_ENV="$SCRIPT_DIR/../../dev.env"

if [[ -f "$DEV_ENV" ]]; then
    # shellcheck source=/dev/null
    source "$DEV_ENV"
fi

if [[ -z "${SIGMASHAKE_BASE_URL:-}" ]]; then
    echo "ERROR: SIGMASHAKE_BASE_URL not set."
    echo "  Run: source ../../dev.env  (or: ../../dev-full-stack.sh init)"
    exit 1
fi

echo "Testing Python SDK against $SIGMASHAKE_BASE_URL"
cd "$SCRIPT_DIR"
python3 -m pytest tests/ -v "$@"
