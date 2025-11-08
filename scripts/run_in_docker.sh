#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-agencyos/openenv-runner:local}
DOCKERFILE=${DOCKERFILE:-docker/openenv-runner.Dockerfile}
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# Ensure daemon is reachable
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker daemon is not reachable. Start Docker Desktop and retry." >&2
  exit 1
fi

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "🏗️  Building $IMAGE_NAME from $DOCKERFILE"
  docker build -t "$IMAGE_NAME" -f "$PROJECT_ROOT/$DOCKERFILE" "$PROJECT_ROOT"
fi

docker run --rm \
  -v "$PROJECT_ROOT":/workspace \
  -e AGENCY_ENV_SPEC=/workspace/envs/agency_env_spec.json \
  -e RUN_TESTS_USE_UV=${RUN_TESTS_USE_UV:-0} \
  "$IMAGE_NAME" "$@"
