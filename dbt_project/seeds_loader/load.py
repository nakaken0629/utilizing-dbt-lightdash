#!/usr/bin/env python3
"""ローダー データ投入ツール

seeds_loader/design.md の仕様に基づき、db から dwh-db の public_raw スキーマに
データを投入します。

実行前提:
  - init.py を実行済みであること（public_raw スキーマが作成済みであること）
  - db の DEMO-EC データベースにデータが投入済みであること

処理内容:
  db の各テーブルの内容を public_raw スキーマにそのままコピーする。
  テーブルが存在しない場合はソースのカラム定義をもとに作成する。
  既存データは実行のたびに洗い替えする。

使い方:
  uv run python dbt_project/seeds_loader/load.py
"""

import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込む
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

# ソース DB (db / DEMO-EC)
SRC_CONN_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "dbname": "DEMO-EC",
}

# デスティネーション DB (dwh-db)
DST_CONN_PARAMS = {
    "host": os.getenv("DWH_DB_HOST", "localhost"),
    "port": int(os.getenv("DWH_DB_PORT", "5434")),
    "user": os.getenv("DWH_PGUSER"),
    "password": os.getenv("DWH_PGPASSWORD"),
    "dbname": os.getenv("DWH_PGDATABASE"),
}

DEST_SCHEMA = "public_raw"

# コピー対象テーブル（外部キー依存の順序で定義）
TABLES = [
    "member",
    "member_status_log",
    "category",
    "food",
    "purchase",
    "purchase_detail",
]


# ---------------------------------------------------------------------------
# テーブル定義取得・生成
# ---------------------------------------------------------------------------

def get_column_info(cur: psycopg2.extensions.cursor, table_name: str) -> list[tuple]:
    """ソーステーブルのカラム情報を information_schema から取得する。"""
    cur.execute(
        """
        SELECT column_name, data_type, character_maximum_length,
               numeric_precision, numeric_scale
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
        """,
        (table_name,),
    )
    return cur.fetchall()


def _map_pg_type(
    data_type: str,
    char_max_len: int | None,
    num_precision: int | None,
    num_scale: int | None,
) -> str:
    """information_schema の data_type をカラム定義用の型文字列に変換する。"""
    if data_type == "integer":
        return "INTEGER"
    if data_type == "smallint":
        return "SMALLINT"
    if data_type == "bigint":
        return "BIGINT"
    if data_type == "character varying":
        return f"VARCHAR({char_max_len})"
    if data_type == "character":
        return f"CHAR({char_max_len})"
    if data_type == "text":
        return "TEXT"
    if data_type in ("timestamp without time zone", "timestamp with time zone"):
        return "TIMESTAMP"
    if data_type == "date":
        return "DATE"
    if data_type == "boolean":
        return "BOOLEAN"
    if data_type == "numeric":
        if num_precision is not None and num_scale is not None:
            return f"NUMERIC({num_precision},{num_scale})"
        return "NUMERIC"
    return data_type.upper()


def create_table_if_not_exists(
    dst_cur: psycopg2.extensions.cursor,
    table_name: str,
    col_info: list[tuple],
) -> None:
    """デスティネーションの public_raw スキーマにテーブルを作成する。

    外部キー・NOT NULL などの制約は付与しない。
    """
    col_defs = [
        f"    {col_name} {_map_pg_type(data_type, char_max_len, num_precision, num_scale)}"
        for col_name, data_type, char_max_len, num_precision, num_scale in col_info
    ]
    dst_cur.execute(
        f"CREATE TABLE IF NOT EXISTS {DEST_SCHEMA}.{table_name} (\n"
        + ",\n".join(col_defs)
        + "\n)"
    )


# ---------------------------------------------------------------------------
# データコピー
# ---------------------------------------------------------------------------

def copy_table(
    src_cur: psycopg2.extensions.cursor,
    dst_cur: psycopg2.extensions.cursor,
    table_name: str,
    col_info: list[tuple],
) -> None:
    """ソーステーブルの全データをデスティネーションにコピーする。"""
    columns = [row[0] for row in col_info]
    cols_str = ", ".join(columns)

    src_cur.execute(f"SELECT {cols_str} FROM {table_name}")
    rows = src_cur.fetchall()

    dst_cur.execute(f"TRUNCATE TABLE {DEST_SCHEMA}.{table_name}")
    if rows:
        psycopg2.extras.execute_values(
            dst_cur,
            f"INSERT INTO {DEST_SCHEMA}.{table_name} ({cols_str}) VALUES %s",
            rows,
        )

    print(f"  {table_name}: {len(rows)} 件コピーしました")


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== データ投入 ===")
    print(
        f"ソース          : {SRC_CONN_PARAMS['host']}:{SRC_CONN_PARAMS['port']}"
        f" / {SRC_CONN_PARAMS['dbname']}"
    )
    print(
        f"デスティネーション: {DST_CONN_PARAMS['host']}:{DST_CONN_PARAMS['port']}"
        f" / {DST_CONN_PARAMS['dbname']}.{DEST_SCHEMA}"
    )
    print()

    src_conn = dst_conn = None
    try:
        src_conn = psycopg2.connect(**SRC_CONN_PARAMS)
        dst_conn = psycopg2.connect(**DST_CONN_PARAMS)
        src_cur = src_conn.cursor()
        dst_cur = dst_conn.cursor()

        for table_name in TABLES:
            print(f"'{table_name}' を処理中...")
            col_info = get_column_info(src_cur, table_name)
            create_table_if_not_exists(dst_cur, table_name, col_info)
            copy_table(src_cur, dst_cur, table_name, col_info)
            dst_conn.commit()

    except psycopg2.OperationalError as e:
        print(f"\n[エラー] データベースに接続できません: {e}", file=sys.stderr)
        print(
            "db および dwh-db コンテナが起動しているか確認してください:"
            " docker compose up -d",
            file=sys.stderr,
        )
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n[エラー] {e}", file=sys.stderr)
        if dst_conn:
            dst_conn.rollback()
        sys.exit(1)
    finally:
        if src_conn:
            src_conn.close()
        if dst_conn:
            dst_conn.close()

    print()
    print("=== データ投入完了 ===")


if __name__ == "__main__":
    main()
