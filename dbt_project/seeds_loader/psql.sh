#!/bin/bash
# データウェアハウス（dwh-db）に psql で接続するスクリプト

set -euo pipefail

# プロジェクトルートの .env を読み込む
ENV_FILE="$(cd "$(dirname "$0")/../.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

# ホスト・ポートはホストからコンテナへの接続設定を優先
HOST="${DWH_DB_HOST:-localhost}"
PORT="${DWH_DB_PORT:-5434}"
USER="${DWH_PGUSER:-lightdash}"
export PGPASSWORD="${DWH_PGPASSWORD:-lightdash_password}"

exec psql -h "$HOST" -p "$PORT" -U "$USER" -d "${DWH_PGDATABASE:-lightdash}" "$@"
