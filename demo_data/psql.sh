#!/bin/bash
# DEMO-EC データベースに psql で接続するスクリプト

set -euo pipefail

# プロジェクトルートの .env を読み込む
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

# ホスト・ポートはホストからコンテナへの接続設定を優先
HOST="${DB_HOST:-localhost}"
PORT="${DB_PORT:-5433}"
USER="${PGUSER:-lightdash}"
export PGPASSWORD="${PGPASSWORD:-lightdash_password}"

exec psql -h "$HOST" -p "$PORT" -U "$USER" -d "DEMO-EC" "$@"
