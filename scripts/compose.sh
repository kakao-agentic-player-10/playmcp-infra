#!/usr/bin/env bash

set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose "$@"
fi

cat >&2 <<'EOF'
Docker Compose is not available.

Install Docker Desktop, or install the standalone Compose binary:
  brew install docker-compose
EOF

exit 1
