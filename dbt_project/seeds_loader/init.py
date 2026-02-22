#!/usr/bin/env python3
"""ローダー初期化ツール

seeds_loader/design.md の仕様に基づき、データウェアハウスの public_raw スキーマを初期化します。

実行前提:
  - docker-compose.yml の dwh-db コンテナが起動していること
  - プロジェクトルートに .env.local ファイルが存在すること

処理内容:
  1. public_raw スキーマが存在する場合、中のテーブルごと削除する
  2. public_raw スキーマを新規作成する

使い方:
  uv run python dbt_project/seeds_loader/init.py
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# プロジェクトルートの .env.local を読み込む
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.local")

CONN_PARAMS = {
    "host": os.getenv("DWH_PGHOST", "localhost"),
    "port": int(os.getenv("DWH_PGPORT", "5434")),
    "user": os.getenv("DWH_PGUSER"),
    "password": os.getenv("DWH_PGPASSWORD"),
    "dbname": os.getenv("DWH_PGDATABASE"),
}


def init_raw_schema(conn: psycopg2.extensions.connection) -> None:
    """public_raw スキーマを初期化する。既存の場合はテーブルごと削除して再作成する。"""
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS public_raw CASCADE")
    print("  public_raw スキーマを削除しました（存在した場合）")
    cur.execute("CREATE SCHEMA public_raw")
    print("  public_raw スキーマを作成しました")
    conn.commit()


def main() -> None:
    print("=== ローダー初期化 ===")
    print(f"接続先 : {CONN_PARAMS['host']}:{CONN_PARAMS['port']}")
    print(f"DB 名  : {CONN_PARAMS['dbname']}")
    print()

    conn = None
    try:
        conn = psycopg2.connect(**CONN_PARAMS)

        print("[1/1] public_raw スキーマを初期化...")
        init_raw_schema(conn)

    except psycopg2.OperationalError as e:
        print(f"\n[エラー] データベースに接続できません: {e}", file=sys.stderr)
        print(
            "dwh-db コンテナが起動しているか確認してください: docker compose up -d dwh-db",
            file=sys.stderr,
        )
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n[エラー] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()

    print()
    print("=== 初期化完了 ===")


if __name__ == "__main__":
    main()
