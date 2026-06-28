#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES=("welfare-agent" "invitation-agent")
FAILED=0

ok() {
  printf '[OK] %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  FAILED=1
}

if "${ROOT_DIR}/scripts/compose.sh" version >/dev/null 2>&1; then
  ok "Docker Compose command is available"
else
  fail "Docker Compose command is not available"
fi

if docker info >/dev/null 2>&1; then
  ok "Docker daemon is reachable"
else
  warn "Docker daemon is not reachable. Start Docker Desktop before running up/build."
fi

if [ -f "${ROOT_DIR}/.env" ]; then
  ok ".env exists"
else
  warn ".env is missing. Run: cp env/.env.example .env"
fi

for service in "${SERVICES[@]}"; do
  repo_dir="${ROOT_DIR}/../${service}"
  if [ -d "${repo_dir}" ]; then
    ok "../${service} exists"
  else
    warn "../${service} is missing"
    continue
  fi

  if [ -f "${repo_dir}/Dockerfile" ]; then
    ok "../${service}/Dockerfile exists"
  else
    fail "../${service}/Dockerfile is missing"
  fi
done

cd "${ROOT_DIR}"
if "${ROOT_DIR}/scripts/compose.sh" config >/dev/null; then
  ok "docker-compose config is valid"
else
  fail "docker-compose config failed"
fi

exit "${FAILED}"
