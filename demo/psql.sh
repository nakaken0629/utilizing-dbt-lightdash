#!/bin/bash
# demo-db データベースに psql で接続するスクリプト

set -euo pipefail

# プロジェクトルートの .env.local を読み込む
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env.local"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

# ホスト・ポートはホストからコンテナへの接続設定を優先
HOST="${DEMO_PGHOST:-localhost}"
PORT="${DEMO_PGPORT:-5435}"
USER="${DEMO_PGUSER:-demo_user}"
export PGPASSWORD="${DEMO_PGPASSWORD:-demo_password}"

exec psql -h "$HOST" -p "$PORT" -U "$USER" -d "demo-db" "$@"
