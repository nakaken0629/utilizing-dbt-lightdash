# dbt + Lightdash データ基盤プロジェクト

dbtとLightdashの学習・技術検証を目的としたデータ基盤プロジェクトです。ECサイトをテーマにしたサンプルデータを使用し、DWHにPostgreSQLを利用します。

## 構成

| コンポーネント | 技術 | 用途 |
|---|---|---|
| DWH | PostgreSQL 15.4 | dbt出力先 / Lightdashクエリ対象 |
| Lightdash DB | PostgreSQL 15.4 | Lightdashメタデータ用 |
| BIツール | Lightdash (セルフホスト) | データ可視化 |
| データ変換 | dbt-postgres 1.8 | ELTのT |
| パッケージ管理 | uv | Python依存管理 |

## セットアップ

### 1. Python環境構築

```bash
uv sync
```

### 2. Docker Compose起動

```bash
docker compose up -d
```

PostgreSQLが2つ起動します:
- `localhost:5433` — Lightdashメタデータ用
- `localhost:5434` — DWH用（dbt出力先）

### 3. dbt実行

```bash
cd dbt_project

# 接続確認
uv run dbt debug --profiles-dir .

# シードデータ投入
uv run dbt seed --profiles-dir .

# モデル実行
uv run dbt run --profiles-dir .

# テスト実行
uv run dbt test --profiles-dir .

# ドキュメント生成（Lightdash接続前に必要）
uv run dbt docs generate --profiles-dir .
```

### 4. Lightdash接続

1. ブラウザで http://localhost:8080 にアクセス
2. 管理者アカウントを作成
3. Warehouse接続設定:
   - Type: PostgreSQL
   - Host: `dwh-db`
   - Port: `5432`
   - Database: `dbt_warehouse`
   - User: `dbt_user`
   - Password: `dbt_password`
4. dbt project path: `/usr/app/dbt`

## dbtプロジェクト構成

```
dbt_project/
├── seeds/          # サンプルCSVデータ（顧客・商品・注文）
└── models/
    ├── staging/    # ソースデータのクレンジング (view)
    ├── intermediate/  # ビジネスロジック結合 (ephemeral)
    └── marts/      # Lightdash公開用テーブル (table)
```

### モデル一覧

| レイヤー | モデル | 説明 |
|---|---|---|
| staging | stg_customers | 顧客マスタ（full_name生成） |
| staging | stg_orders | 注文データ |
| staging | stg_products | 商品マスタ |
| intermediate | int_orders_with_products | 注文×商品結合、注文金額算出 |
| marts | fct_orders | 注文ファクトテーブル |
| marts | dim_customers | 顧客ディメンション（集約情報付き） |

## コマンドリファレンス

```bash
# Docker操作
docker compose up -d      # 起動
docker compose down        # 停止
docker compose logs -f     # ログ確認

# dbt操作（dbt_projectディレクトリ内で実行）
uv run dbt seed --profiles-dir .           # シードデータ投入
uv run dbt run --profiles-dir .            # モデル実行
uv run dbt test --profiles-dir .           # テスト実行
uv run dbt run --select marts --profiles-dir .  # marts のみ実行
uv run dbt docs generate --profiles-dir .  # ドキュメント生成
uv run dbt docs serve --profiles-dir .     # ドキュメントサーバー起動
```
