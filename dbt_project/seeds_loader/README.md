# seeds_loader

dbt 標準の seeds 機能の代替として、Python プログラムによってデータウェアハウスの `public_raw` スキーマにローデータを投入するツールです。

## dbt seeds との違い

dbt の seeds は CSV ファイルをデータウェアハウスに読み込む機能ですが、seeds_loader では以下の理由から Python プログラムによる実装を採用しています。

- ローデータのソースがデータベース（`db`）であり、CSV ファイルではない
- `db` から `dwh-db` へのデータ転送ロジックをコードで明示的に管理する

## ツール構成

| ファイル | 説明 |
|---|---|
| `design.md` | ツールの仕様書 |
| `init.py` | 初期化ツール。`public_raw` スキーマを作成する |
| `psql.sh` | データウェアハウス（`dwh-db`）に psql で接続するスクリプト |

## 前提条件

- `docker-compose.yml` の `db` コンテナおよび `dwh-db` コンテナが起動していること
- プロジェクトルートに `.env` ファイルが存在すること

## 使い方

### 初期化

`public_raw` スキーマを作成します。すでに存在する場合はテーブルごと削除して再作成します。

```bash
uv run python dbt_project/seeds_loader/init.py
```

### psql 接続

```bash
bash dbt_project/seeds_loader/psql.sh
```
