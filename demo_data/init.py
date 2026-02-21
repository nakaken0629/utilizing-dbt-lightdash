#!/usr/bin/env python3
"""デモデータ初期化ツール

design.md の仕様に基づき、デモ用データベースを初期化します。

実行前提:
  - docker-compose.yml の db コンテナが起動していること
  - プロジェクトルートに .env ファイルが存在すること

処理内容:
  1. DEMO-EC データベースが存在する場合は削除する
  2. DEMO-EC データベースを新規作成する
  3. DEMO-EC-DEVELOPER ユーザーが存在しない場合は作成する
  4. DEMO-EC-DEVELOPER ユーザーに PUBLIC スキーマへの全権限を付与する
  5. models.md の定義に従いテーブルを作成する
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込む
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DEMO_DB = "DEMO-EC"
DEMO_USER = "DEMO-EC-DEVELOPER"
DEMO_PASSWORD = os.getenv("DEMO_PGPASSWORD", "demo_password")

# db コンテナへの接続設定（ホストからアクセスするためポート 5433 を使用）
CONN_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "user": os.getenv("PGUSER", "lightdash"),
    "password": os.getenv("PGPASSWORD", "lightdash_password"),
    "dbname": os.getenv("PGDATABASE", "lightdash"),
}


def drop_database_if_exists(conn: psycopg2.extensions.connection, db_name: str) -> None:
    """データベースが存在する場合、既存接続を切断してから削除する"""
    cur = conn.cursor()
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid()",
        [db_name],
    )
    cur.execute(
        sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name))
    )
    print(f"  データベース '{db_name}' を削除しました（存在した場合）")


def create_database(conn: psycopg2.extensions.connection, db_name: str) -> None:
    """データベースを作成する"""
    cur = conn.cursor()
    cur.execute(
        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
    )
    print(f"  データベース '{db_name}' を作成しました")


def create_user_if_not_exists(
    conn: psycopg2.extensions.connection, user: str, password: str
) -> None:
    """ユーザーが存在しない場合に作成する"""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [user])
    if cur.fetchone():
        print(f"  ユーザー '{user}' はすでに存在します（スキップ）")
    else:
        cur.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(user)),
            [password],
        )
        print(f"  ユーザー '{user}' を作成しました")


def grant_connect_privilege(
    conn: psycopg2.extensions.connection, db_name: str, user: str
) -> None:
    """ユーザーにデータベースへの接続権限を付与する"""
    cur = conn.cursor()
    cur.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            sql.Identifier(db_name), sql.Identifier(user)
        )
    )
    print(f"  ユーザー '{user}' にデータベース '{db_name}' への接続権限を付与しました")


def create_tables(db_name: str) -> None:
    """models.md の定義に従いテーブルを作成する"""
    demo_conn_params = {**CONN_PARAMS, "dbname": db_name}
    conn = psycopg2.connect(**demo_conn_params)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS member (
                id           SERIAL       PRIMARY KEY,
                last_name    VARCHAR(50)  NOT NULL,
                first_name   VARCHAR(50)  NOT NULL,
                birth_date   DATE         NOT NULL,
                gender       SMALLINT     NOT NULL,
                address      VARCHAR(255) NOT NULL,
                status       SMALLINT     NOT NULL,
                last_login_at TIMESTAMP,
                created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
                updated_at   TIMESTAMP    NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'member' を作成しました")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS member_property (
                id            INTEGER PRIMARY KEY REFERENCES member(id),
                to_paid_days  INTEGER,
                to_sleep_days INTEGER,
                to_quit_days  INTEGER
            )
        """)
        print("  テーブル 'member_property' を作成しました")

        conn.commit()
    finally:
        conn.close()


def grant_schema_privileges(db_name: str, user: str) -> None:
    """DEMO-EC データベースに接続し、PUBLIC スキーマへの全権限を付与する"""
    demo_conn_params = {**CONN_PARAMS, "dbname": db_name}
    conn = psycopg2.connect(**demo_conn_params)
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(user))
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}"
            ).format(sql.Identifier(user))
        )
        cur.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}"
            ).format(sql.Identifier(user))
        )
    finally:
        conn.close()
    print(f"  ユーザー '{user}' に PUBLIC スキーマへの全権限を付与しました")


def main() -> None:
    print("=== デモデータベース初期化 ===")
    print(f"接続先 : {CONN_PARAMS['host']}:{CONN_PARAMS['port']}")
    print(f"DB 名  : {DEMO_DB}")
    print(f"ユーザー: {DEMO_USER}")
    print()

    conn = None
    try:
        conn = psycopg2.connect(**CONN_PARAMS)
        conn.autocommit = True

        print("[1/5] データベースを削除（存在する場合）...")
        drop_database_if_exists(conn, DEMO_DB)

        print("[2/5] データベースを作成...")
        create_database(conn, DEMO_DB)

        print("[3/5] ユーザーを作成（存在しない場合）...")
        create_user_if_not_exists(conn, DEMO_USER, DEMO_PASSWORD)

        print("[4/5] 権限を付与...")
        grant_connect_privilege(conn, DEMO_DB, DEMO_USER)
        conn.close()
        conn = None

        grant_schema_privileges(DEMO_DB, DEMO_USER)

        print("[5/5] テーブルを作成...")
        create_tables(DEMO_DB)

    except psycopg2.OperationalError as e:
        print(f"\n[エラー] データベースに接続できません: {e}", file=sys.stderr)
        print("db コンテナが起動しているか確認してください: docker compose up -d db", file=sys.stderr)
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
