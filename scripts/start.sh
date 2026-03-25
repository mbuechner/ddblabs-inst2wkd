#!/usr/bin/env sh
set -eu

APP_HOME="${APP_HOME:-/opt/app}"
PORT="${PORT:-8080}"

cd "${APP_HOME}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
