#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if docker compose version >/dev/null 2>&1; then
    compose=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    compose=(docker-compose)
else
    echo "Install Docker Compose first." >&2
    exit 1
fi
wait_url() {
    local url="$1" deadline=$((SECONDS + ${STARTUP_TIMEOUT:-180}))
    until curl --fail --silent --max-time 5 "$url" >/dev/null; do
        if (( SECONDS >= deadline )); then
            echo "Timed out waiting for $url. Check docker compose logs." >&2
            return 1
        fi
        sleep 3
    done
}
if [[ "${1:-}" == --demo ]]; then
    python3 make_demo_data.py
fi
"${compose[@]}" up --build -d
wait_url http://localhost:9200/_cluster/health
wait_url http://localhost:5002/health
# The one-shot indexer must finish successfully before we announce readiness.
indexer_id=$("${compose[@]}" ps -a -q data_indexer)
if [[ -z "$indexer_id" ]]; then
    echo "Data indexer container was not created." >&2
    exit 1
fi
deadline=$((SECONDS + ${INDEX_TIMEOUT:-300}))
while [[ "$(docker inspect --format '{{.State.Running}}' "$indexer_id")" == true ]]; do
    if (( SECONDS >= deadline )); then
        echo "Indexing timed out. Check docker compose logs data_indexer." >&2
        exit 1
    fi
    sleep 3
done
if [[ "$(docker inspect --format '{{.State.ExitCode}}' "$indexer_id")" != 0 ]]; then
    echo "Indexing failed. Check docker compose logs data_indexer." >&2
    exit 1
fi
echo "Map ready at http://localhost:5002"
echo "Address search requires a populated GNAF_SCHEMA (default gnaf_202502)."
echo "Check the worker with: docker compose logs gnaf_worker"
if [[ "${1:-}" == --open ]]; then
    if command -v open >/dev/null 2>&1; then open http://localhost:5002
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:5002
    fi
fi
