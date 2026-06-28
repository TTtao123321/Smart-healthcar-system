#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_ARGS=(-f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.patient-agent-e2e.yml")
DOCKER_BIN="${DOCKER_BIN:-$(command -v docker || true)}"

if [ -z "$DOCKER_BIN" ] && [ -x "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
  DOCKER_BIN="/Applications/Docker.app/Contents/Resources/bin/docker"
fi

if [ -z "$DOCKER_BIN" ]; then
  echo "docker executable not found" >&2
  exit 127
fi

cleanup() {
  "$DOCKER_BIN" compose "${COMPOSE_ARGS[@]}" logs patient_agent_backend patient_agent_frontend > "$ROOT/patient-agent-e2e.log" || true
  "$DOCKER_BIN" compose "${COMPOSE_ARGS[@]}" down || true
}

trap cleanup EXIT

"$DOCKER_BIN" compose "${COMPOSE_ARGS[@]}" up -d --build patient_agent_backend patient_agent_frontend
until curl -fsS http://127.0.0.1:8001/health >/dev/null; do sleep 2; done
until curl -fsS http://127.0.0.1:5174 >/dev/null; do sleep 2; done

cd "$ROOT/patient_agent_frontend"
npx playwright test "$@"
