#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="${1:-}"

case "${SERVICE}" in
  welfare-agent|invitation-agent)
    ;;
  *)
  echo "Usage: ./scripts/logs.sh [welfare-agent|invitation-agent]"
  exit 1
    ;;
esac

cd "${ROOT_DIR}"
exec "${ROOT_DIR}/scripts/compose.sh" logs -f --tail="${TAIL_LINES:-200}" "${SERVICE}"
