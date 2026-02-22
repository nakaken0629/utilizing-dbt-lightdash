# seeds_loader

`demo-db`（デモデータ）から `dwh-db`（DWH）の `public_raw` スキーマにデータを転送するツールです。

## 概要

dbt 標準の seeds 機能はCSVファイルを読み込む機能ですが、このプロジェクトではソースデータがデータベース（`demo-db`）であるため、Pythonによるデータ転送ツールを採用しています。

## ツール構成

| ファイル | 説明 |
|---|---|
| `init.py` | `dwh-db` に `public_raw` スキーマを初期化する |
| `load.py` | `demo-db` から `dwh-db` にデータを転送する |
| `psql.sh` | dwh-db に psql で接続するスクリプト |
| `design.md` | ツール仕様書 |

## 転送対象テーブル

`demo-db` の以下のテーブルを `dwh-db` の `public_raw` スキーマにコピーします。

| テーブル | 説明 |
|---|---|
| `member` | 会員マスタ |
| `member_status_log` | 会員ステータス変更履歴 |
| `category` | 食品カテゴリマスタ |
| `food` | 食品マスタ |
| `purchase` | 購入ヘッダ |
| `purchase_detail` | 購入明細 |

## 前提条件

- `docker-compose.yml` の `demo-db` および `dwh-db` コンテナが起動していること
- `demo/seed.py` が実行済みで `demo-db` にデータが存在すること
- プロジェクトルートに `.env.local` ファイルが存在すること（`.env.local.example` を参照）

## 使い方

### 1. 初期化

`dwh-db` に `public_raw` スキーマを作成します。すでに存在する場合はテーブルごと削除して再作成します。

```bash
uv run python dbt_project/seeds_loader/init.py
```

### 2. データ転送

`demo-db` の各テーブルを `public_raw` スキーマにコピーします。既存データは実行のたびに洗い替えされます。

```bash
uv run python dbt_project/seeds_loader/load.py
```

### 3. psql接続

```bash
bash dbt_project/seeds_loader/psql.sh
```

## データフロー

```
demo-db (demo_db データベース)
  └── member, member_status_log, category, food, purchase, purchase_detail
        ↓ load.py
dwh-db (dbt_warehouse データベース)
  └── public_raw.member, public_raw.member_status_log, ...
        ↓ dbt run
  └── public.stg_*, public.fct_*, public.dim_*
```
