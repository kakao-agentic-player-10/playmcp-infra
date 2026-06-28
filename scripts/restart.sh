#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="${1:-}"

case "${SERVICE}" in
  "")
    cd "${ROOT_DIR}"
    "${ROOT_DIR}/scripts/compose.sh" restart
    ;;
  welfare-agent|invitation-agent)
    cd "${ROOT_DIR}"
    "${ROOT_DIR}/scripts/compose.sh" restart "${SERVICE}"
    ;;
  *)
    echo "Usage: ./scripts/restart.sh [welfare-agent|invitation-agent]" >&2
    exit 1
    ;;
esac

echo "Services restarted."
"${ROOT_DIR}/scripts/compose.sh" ps
