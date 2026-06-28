#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES=("welfare-agent" "invitation-agent")

echo "Pull latest service repositories..."

for service in "${SERVICES[@]}"; do
  repo_dir="${ROOT_DIR}/../${service}"

  if [ ! -d "${repo_dir}" ]; then
    echo "Missing ../${service}. Clone it next to playmcp-infra before deploying." >&2
    exit 1
  fi

  if [ ! -f "${repo_dir}/Dockerfile" ]; then
    echo "Missing ../${service}/Dockerfile. See docs/service-contract.md." >&2
    exit 1
  fi

  if [ -d "${repo_dir}/.git" ]; then
    branch="$(git -C "${repo_dir}" branch --show-current)"
    if [ -n "${branch}" ]; then
      git -C "${repo_dir}" pull --ff-only origin "${branch}"
    fi
  fi
done

if [ ! -f "${ROOT_DIR}/.env" ]; then
  cp "${ROOT_DIR}/env/.env.example" "${ROOT_DIR}/.env"
  echo "Created .env from env/.env.example"
fi

echo "Deploy services with Docker Compose..."

cd "${ROOT_DIR}"
"${ROOT_DIR}/scripts/compose.sh" up -d --build

echo "Deployment completed."
"${ROOT_DIR}/scripts/compose.sh" ps
