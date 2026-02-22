# dbt + Lightdash データ基盤プロジェクト

dbtとLightdashの学習・技術検証を目的としたデータ基盤プロジェクトです。ECサイト（食品EC）をテーマにしたサンプルデータを使用し、DWHにPostgreSQLを利用します。

## 構成

| コンポーネント | 技術 | 用途 |
|---|---|---|
| デモDB | PostgreSQL 15.4 | サンプルデータの格納元 |
| DWH | PostgreSQL 15.4 | dbt出力先 / Lightdashクエリ対象 |
| Lightdash DB | PostgreSQL 15.4 | Lightdashメタデータ用 |
| BIツール | Lightdash (セルフホスト) | データ可視化 |
| データ変換 | dbt-postgres 1.8 | ELTのT |
| パッケージ管理 | uv | Python依存管理 |

## データフロー

```
demo-db（デモデータ）
  ↓ demo/init.py    ← テーブル作成
  ↓ demo/seed.py    ← サンプルデータ生成

dwh-db（public_raw スキーマ）
  ↓ seeds_loader/init.py   ← スキーマ作成
  ↓ seeds_loader/load.py   ← demo-db からデータ転送

dwh-db（public スキーマ）
  ↓ dbt run   ← staging / marts モデル実行

Lightdash (http://localhost:8080)
  ↑ dwh-db の marts テーブルにクエリ
```

## セットアップ

### 1. 環境変数ファイルの準備

```bash
cp .env.example .env
cp .env.local.example .env.local
```

必要に応じて `.env` および `.env.local` の値を編集してください。

### 2. Python環境構築

```bash
uv sync
```

### 3. Docker Compose起動

```bash
docker compose up -d
```

以下のサービスが起動します:

| サービス | ローカルポート | 用途 |
|---|---|---|
| `db` | 5433 | Lightdashメタデータ用 |
| `dwh-db` | 5434 | DWH（dbt出力先） |
| `demo-db` | 5435 | デモデータ格納元 |
| `minio` | 9000, 9001 | S3互換ストレージ |
| `lightdash` | 8080 | BIツール |

### 4. デモデータ生成

```bash
# demo-db にテーブルを作成
uv run python demo/init.py

# サンプルデータを生成・投入
uv run python demo/seed.py
```

### 5. DWHへのデータ転送

```bash
# dwh-db に public_raw スキーマを作成
uv run python dbt_project/seeds_loader/init.py

# demo-db から dwh-db にデータ転送
uv run python dbt_project/seeds_loader/load.py
```

### 6. dbt実行

```bash
cd dbt_project

# 接続確認
uv run dbt debug --profiles-dir .

# モデル実行
uv run dbt run --profiles-dir .

# テスト実行
uv run dbt test --profiles-dir .

# ドキュメント生成（Lightdash接続前に必要）
uv run dbt docs generate --profiles-dir .
```

### 7. Lightdash接続

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
├── dbt_project.yml    # プロジェクト設定
├── profiles.yml       # 接続先設定
├── models/
│   ├── staging/       # ソースデータの参照 (view)
│   └── marts/         # Lightdash公開用テーブル (table)
└── seeds_loader/      # demo-db → dwh-db データ転送ツール
```

### モデル一覧

| レイヤー | モデル | 説明 |
|---|---|---|
| staging | stg_member | 会員マスタ |
| staging | stg_member_status_log | 会員ステータス変更履歴 |
| staging | stg_category | カテゴリマスタ |
| staging | stg_food | 食品マスタ |
| staging | stg_purchase | 購入データ |
| staging | stg_purchase_detail | 購入明細データ |
| marts | fct_purchase | 購入ファクトテーブル |
| marts | dim_member | 会員ディメンション |
| marts | dim_food | 食品ディメンション（カテゴリ含む） |

## コマンドリファレンス

```bash
# Docker操作
docker compose up -d       # 起動
docker compose down         # 停止
docker compose logs -f      # ログ確認

# デモデータ操作
uv run python demo/init.py              # テーブル作成
uv run python demo/seed.py              # サンプルデータ生成

# seeds_loader操作
uv run python dbt_project/seeds_loader/init.py   # スキーマ作成
uv run python dbt_project/seeds_loader/load.py   # データ転送

# dbt操作（dbt_projectディレクトリ内で実行）
uv run dbt run --profiles-dir .                        # モデル実行
uv run dbt run --select marts --profiles-dir .         # martsのみ実行
uv run dbt test --profiles-dir .                       # テスト実行
uv run dbt docs generate --profiles-dir .              # ドキュメント生成
uv run dbt docs serve --profiles-dir .                 # ドキュメントサーバー起動

# psql接続
bash demo/psql.sh                          # demo-db に接続
bash dbt_project/seeds_loader/psql.sh     # dwh-db に接続
```
