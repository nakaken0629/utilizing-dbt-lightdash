# データウェアハウス設計

## staging

- seeds_loaderのdesign.mdで読み込んだテーブル全て
- 型の変換や欠損値の修正などは行わない

## intermediate

- 使用しない

## marts

スタースキーマ方式で作成する。

- ファクト
  - 購入
    - staging.購入
    - staging.購入明細
- ディメンション
  - 会員
    - staging.会員
  - 食品
    - staging.食品
    - staging.カテゴリ
