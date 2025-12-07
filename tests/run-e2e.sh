#!/bin/sh
set -eu

cd "$(dirname "$0")"

echo "Building and running ATR e2e tests..."
docker compose up atr e2e --build --abort-on-container-exit --exit-code-from e2e

docker compose down -v
