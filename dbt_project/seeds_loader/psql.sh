#!/bin/bash
# データウェアハウス（dwh-db）に psql で接続するスクリプト

set -euo pipefail

# プロジェクトルートの .env.local を読み込む
ENV_FILE="$(cd "$(dirname "$0")/../../.." && pwd)/.env.local"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

# ホスト・ポートはホストからコンテナへの接続設定を優先
HOST="${DWH_PGHOST:-localhost}"
PORT="${DWH_PGPORT:-5434}"
USER="${DWH_PGUSER:-dbt_user}"
export PGPASSWORD="${DWH_PGPASSWORD:-dbt_password}"

exec psql -h "$HOST" -p "$PORT" -U "$USER" -d "${DWH_PGDATABASE:-lightdash}" "$@"
