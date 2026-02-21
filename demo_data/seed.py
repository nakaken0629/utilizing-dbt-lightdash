#!/usr/bin/env python3
"""テストデータ生成ツール

design.md・models.md の仕様に従い、デモ用データを日付ごとに生成して投入します。

実行前提:
  - init.py を実行済みであること（データベース・テーブルが作成済みであること）

使い方:
  uv run python demo_data/seed.py
"""

import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras
from mimesis import Address, Finance, Food, Person
from mimesis.locales import Locale
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込む
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DEMO_DB = "DEMO-EC"
CONN_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "user": os.getenv("PGUSER", "lightdash"),
    "password": os.getenv("PGPASSWORD", "lightdash_password"),
    "dbname": DEMO_DB,
}


# ---------------------------------------------------------------------------
# データ生成ヘルパー
# ---------------------------------------------------------------------------

def generate_birth_date() -> date:
    """生年月日を年齢分布に従って生成する。

    分布:
      18〜30歳: 50%
      31〜60歳: 40%
      61〜70歳: 10%
    """
    today = date.today()
    r = random.random()
    if r < 0.50:
        age = random.randint(18, 30)
    elif r < 0.90:
        age = random.randint(31, 60)
    else:
        age = random.randint(61, 70)

    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # 月末日の問題を避けるため 28 日以内
    return date(birth_year, birth_month, birth_day)


def generate_gender() -> int:
    """性別を分布に従って生成する。

    分布:
      0（男）      :  7%
      1（女）      : 92%
      2（それ以外）:  1%
    """
    r = random.random()
    if r < 0.07:
        return 0
    elif r < 0.08:
        return 2
    else:
        return 1


def generate_member_property(member_id: int) -> tuple:
    """models.md のルールに従い member_property のデータを生成する。

    to_paid_days:
      10% の確率で 30〜180 のランダム値、90% で NULL

    to_sleep_days:
      to_paid_days が NULL でなければ NULL
      そうでなければ 20% の確率で 30〜180 のランダム値、80% で NULL

    to_quit_days:
      to_sleep_days が NULL でなければ NULL
      そうでなければ 5% の確率で max(30〜180 のランダム値, to_paid_days + 30)、95% で NULL
      ※ to_paid_days が NULL の場合は 30〜180 のランダム値をそのまま使用
    """
    to_paid_days = random.randint(30, 180) if random.random() < 0.10 else None

    if to_paid_days is not None:
        to_sleep_days = None
    else:
        to_sleep_days = random.randint(30, 180) if random.random() < 0.20 else None

    if to_sleep_days is not None:
        to_quit_days = None
    else:
        if random.random() < 0.05:
            random_days = random.randint(30, 180)
            if to_paid_days is not None:
                to_quit_days = max(random_days, to_paid_days + 30)
            else:
                to_quit_days = random_days
        else:
            to_quit_days = None

    return (member_id, to_paid_days, to_sleep_days, to_quit_days)


def _round_price(price: int) -> int:
    """価格を単位に従って切り捨てる。

    1000円未満: 10円単位で切り捨て
    1000円以上: 100円単位で切り捨て
    """
    if price < 1000:
        return (price // 10) * 10
    return (price // 100) * 100


# ---------------------------------------------------------------------------
# DB 操作
# ---------------------------------------------------------------------------

def insert_categories(
    cur: psycopg2.extensions.cursor,
    target_date: date,
) -> None:
    """Food プロバイダーのメソッド名を日本語訳して category テーブルに投入する。

    dish / drink / fruit / vegetable / spices の5件を固定で挿入する。
    name にはメソッド名の日本語訳を保存する。
    created_at / updated_at は開始日を設定する。
    """
    rows = [
        ("料理",     target_date, target_date),
        ("飲み物",   target_date, target_date),
        ("果物",     target_date, target_date),
        ("野菜",     target_date, target_date),
        ("スパイス", target_date, target_date),
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO category (name, created_at, updated_at)
        VALUES %s
        """,
        rows,
    )
    print(f"  category: {len(rows)} 件挿入しました")


def get_category_id_map(cur: psycopg2.extensions.cursor) -> dict[str, int]:
    """category テーブルから name → id のマッピングを取得する"""
    cur.execute("SELECT id, name FROM category")
    return {name: id_ for id_, name in cur.fetchall()}


def insert_foods(
    cur: psycopg2.extensions.cursor,
    count: int,
    start_date: date,
    category_id_map: dict[str, int],
) -> None:
    """food テーブルにテストデータを投入する。

    Food メソッドでカテゴリに対応する食品名を生成し、
    category_id は category テーブルから逆引きして設定する。
    price は Finance プロバイダーで生成する。
    created_at / updated_at は開始日を設定する。
    """
    food = Food(locale=Locale.JA)
    finance = Finance(locale=Locale.JA)

    # Foodメソッドと対応する日本語カテゴリ名のマッピング
    category_methods = [
        (food.dish,      "料理"),
        (food.drink,     "飲み物"),
        (food.fruit,     "果物"),
        (food.vegetable, "野菜"),
        (food.spices,    "スパイス"),
    ]

    name_counts: dict[str, int] = {}
    rows = []
    for _ in range(count):
        method, category_name = random.choice(category_methods)
        base_name = method()
        name_counts[base_name] = name_counts.get(base_name, 0) + 1
        name = base_name if name_counts[base_name] == 1 else f"{base_name} {name_counts[base_name]}"
        rows.append((
            name,
            category_id_map[category_name],
            _round_price(int(finance.price())),
            start_date,
            start_date,
        ))

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO food (name, category_id, price, created_at, updated_at)
        VALUES %s
        """,
        rows,
    )
    print(f"  food: {len(rows)} 件挿入しました")


def get_member_count(cur: psycopg2.extensions.cursor) -> int:
    """現在の会員数を取得する"""
    cur.execute("SELECT COUNT(*) FROM member")
    return cur.fetchone()[0]


def insert_members_for_day(
    cur: psycopg2.extensions.cursor,
    count: int,
    target_date: date,
    person: Person,
    address: Address,
) -> list[int]:
    """指定日の会員を挿入し、採番された id のリストを返す"""
    members = [
        (
            person.last_name(),
            person.first_name(),
            generate_birth_date(),
            generate_gender(),
            address.state() + address.city() + address.address(),
            0,            # status: 無料会員
            None,         # last_login_at
            target_date,  # created_at
            target_date,  # updated_at
        )
        for _ in range(count)
    ]

    inserted = psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO member
            (last_name, first_name, birth_date, gender, address, status,
             last_login_at, created_at, updated_at)
        VALUES %s
        RETURNING id
        """,
        members,
        fetch=True,
    )
    return [row[0] for row in inserted]


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def seed(start_date: date) -> None:
    today = date.today()

    # 年間成長率を 30%〜70% の範囲でランダムに決定（元の 1.3〜1.7 倍）
    annual_multiplier = random.uniform(1.3, 1.7)
    daily_rate = annual_multiplier ** (1 / 365) - 1

    print(f"  開始日      : {start_date}")
    print(f"  終了日      : {today}")
    print(f"  年間成長率  : {(annual_multiplier - 1) * 100:.1f}%")
    print(f"  日次成長率  : {daily_rate * 100:.4f}%")
    print()

    person = Person(locale=Locale.JA)
    address = Address(locale=Locale.JA)

    conn = psycopg2.connect(**CONN_PARAMS)
    try:
        cur = conn.cursor()

        # 全テーブルを初期化（CASCADE で参照先も連鎖削除）
        cur.execute("TRUNCATE TABLE member, category CASCADE")
        conn.commit()
        print("  全テーブルをクリアしました")

        print("カテゴリデータを投入中...")
        insert_categories(cur, start_date)
        conn.commit()

        print("食品データを投入中...")
        category_id_map = get_category_id_map(cur)
        insert_foods(cur, 1000, start_date, category_id_map)
        conn.commit()
        print()

        current_date = start_date
        total_inserted = 0

        while current_date <= today:
            days_elapsed = (current_date - start_date).days
            member_count = get_member_count(cur)

            if days_elapsed < 10:
                # 開始後 10 日間: 50〜100 人のランダム値
                new_count = random.randint(50, 100)
            else:
                # 11 日目以降: max(0〜3 のランダム値, floor(現在の会員数 × 日次成長率))
                random_new = random.randint(0, 3)
                growth_new = int(member_count * daily_rate)
                new_count = max(random_new, growth_new)

            if new_count > 0:
                member_ids = insert_members_for_day(
                    cur, new_count, current_date, person, address
                )
                properties = [generate_member_property(mid) for mid in member_ids]
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO member_property (id, to_paid_days, to_sleep_days, to_quit_days)
                    VALUES %s
                    """,
                    properties,
                )
                conn.commit()

            total_inserted += new_count
            print(f"  {current_date}: {new_count:4d} 件（累計 {member_count + new_count} 件）")
            current_date += timedelta(days=1)

        print()
        print(f"  合計 {total_inserted} 件挿入しました")
    finally:
        conn.close()


def prompt_start_date() -> date:
    """開始日を対話形式で入力させる（デフォルト: 今日から 5 日前）"""
    default = date.today() - timedelta(days=5)
    user_input = input(
        f"テストデータ作成開始日を入力してください（YYYY-MM-DD）[{default}]: "
    ).strip()
    if not user_input:
        return default
    try:
        return date.fromisoformat(user_input)
    except ValueError:
        print(f"[エラー] 日付の形式が正しくありません: {user_input}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    print("=== テストデータ生成 ===")
    print()

    start_date = prompt_start_date()
    print()

    try:
        seed(start_date)
    except psycopg2.OperationalError as e:
        print(f"\n[エラー] データベースに接続できません: {e}", file=sys.stderr)
        print("init.py を実行済みか確認してください", file=sys.stderr)
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n[エラー] {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=== データ生成完了 ===")


if __name__ == "__main__":
    main()
