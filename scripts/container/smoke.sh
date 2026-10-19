#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# Unique resources keep this test separate from development containers.
smoke_id="solar-sites-smoke-$(date +%s)-$$"
smoke_image="solar-sites-assessment:${smoke_id}"
smoke_volume="${smoke_id}-data"
smoke_container="${smoke_id}-app"

cleanup() {
  local result=$?
  if (( result != 0 )); then docker logs --tail 60 "$smoke_container" >&2 || true; fi
  docker rm -f "$smoke_container" >/dev/null 2>&1 || true
  docker volume rm "$smoke_volume" >/dev/null 2>&1 || true
  docker image rm "$smoke_image" >/dev/null 2>&1 || true
  exit "$result"
}

wait_for_readiness() {
  local port=$1
  local attempt
  for (( attempt=0; attempt<60; attempt++ )); do
    if curl --fail --silent --max-time 2 "http://127.0.0.1:${port}/readyz" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo 'Container readiness timed out' >&2
  return 1
}

run_checks() {
  local phase=$1
  local port
  # Only the data volume and temporary files are writable.
  timeout 30 docker run -d --name "$smoke_container" --read-only --tmpfs /tmp \
    --cap-drop ALL --security-opt no-new-privileges --memory 512m --cpus 2 --pids-limit 128 \
    --mount "type=volume,src=$smoke_volume,dst=/data" -p 127.0.0.1::8000 "$smoke_image" >/dev/null
  port=$(docker inspect --format '{{(index (index .NetworkSettings.Ports "8000/tcp") 0).HostPort}}' "$smoke_container")
  wait_for_readiness "$port"
  timeout 90 docker exec -i "$smoke_container" python - "$phase" < scripts/container/check.py
  timeout 80 docker stop --time 75 "$smoke_container" >/dev/null
  docker rm "$smoke_container" >/dev/null
}

main() {
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  timeout 600 docker build -t "$smoke_image" .
  docker volume create "$smoke_volume" >/dev/null

  # Recreate the container with the same volume to check persistence.
  local phase
  for phase in seed restore; do
    run_checks "$phase"
  done
  printf '%s\n' 'Container smoke passed: startup, static assets, authenticated site creation and persistence'
}

main "$@"
