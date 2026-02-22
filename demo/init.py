#!/usr/bin/env python3
"""デモデータ初期化ツール

design.md の仕様に基づき、デモ用データベースを初期化します。

実行前提:
  - docker-compose.yml の demo-db コンテナが起動していること
  - プロジェクトルートに .env.local ファイルが存在すること

処理内容:
  1. demo-db データベースが存在する場合は削除する
  2. demo-db データベースを新規作成する
  3. demo-user ユーザーが存在しない場合は作成する
  4. demo-user ユーザーに PUBLIC スキーマへの全権限を付与する
  5. models.md の定義に従いテーブルを作成する
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# プロジェクトルートの .env.local を読み込む
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

DEMO_DB = "demo-db"
DEMO_USER = "demo-user"
DEMO_PASSWORD = os.getenv("DEMO_PGPASSWORD", "demo_password")

# demo-db コンテナへの接続設定（ホストからアクセスするためポート 5435 を使用）
CONN_PARAMS = {
    "host": os.getenv("DEMO_PGHOST", "localhost"),
    "port": int(os.getenv("DEMO_PGPORT", "5435")),
    "user": os.getenv("DEMO_PGUSER", "demo_user"),
    "password": os.getenv("DEMO_PGPASSWORD", "demo_password"),
    "dbname": os.getenv("DEMO_PGDATABASE", "demo_db"),
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
                paid_at      TIMESTAMP,
                quit_at      TIMESTAMP,
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id         SERIAL       PRIMARY KEY,
                name       VARCHAR(100) NOT NULL,
                created_at TIMESTAMP    NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP    NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'category' を作成しました")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS food (
                id          SERIAL        PRIMARY KEY,
                name        VARCHAR(100)  NOT NULL,
                category_id INTEGER       NOT NULL REFERENCES category(id),
                price       INTEGER       NOT NULL,
                created_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
                updated_at  TIMESTAMP     NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'food' を作成しました")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase (
                id               SERIAL       PRIMARY KEY,
                member_id        INTEGER      NOT NULL REFERENCES member(id),
                member_name      VARCHAR(100) NOT NULL,
                shipping_address VARCHAR(255) NOT NULL,
                purchased_at     TIMESTAMP    NOT NULL,
                total_amount     INTEGER      NOT NULL,
                created_at       TIMESTAMP    NOT NULL DEFAULT NOW(),
                updated_at       TIMESTAMP    NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'purchase' を作成しました")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_detail (
                id          SERIAL       PRIMARY KEY,
                purchase_id INTEGER      NOT NULL REFERENCES purchase(id),
                food_id     INTEGER      NOT NULL REFERENCES food(id),
                food_name   VARCHAR(100) NOT NULL,
                unit_price  INTEGER      NOT NULL,
                quantity    INTEGER      NOT NULL,
                subtotal    INTEGER      NOT NULL,
                created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
                updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'purchase_detail' を作成しました")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS member_status_log (
                id            SERIAL    PRIMARY KEY,
                member_id     INTEGER   NOT NULL REFERENCES member(id),
                status_before SMALLINT  NOT NULL,
                status_after  SMALLINT  NOT NULL,
                changed_at    TIMESTAMP NOT NULL,
                created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        print("  テーブル 'member_status_log' を作成しました")

        conn.commit()
    finally:
        conn.close()


def grant_schema_privileges(db_name: str, user: str) -> None:
    """demo-db データベースに接続し、PUBLIC スキーマへの全権限を付与する"""
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
        print("demo-db コンテナが起動しているか確認してください: docker compose up -d demo-db", file=sys.stderr)
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
