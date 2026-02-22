# テーブル設計書

## member（会員）

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | SERIAL | PRIMARY KEY | 主キー（自動採番） | 自動採番 |
| last_name | VARCHAR(50) | NOT NULL | 苗字 | mimesis で日本語の苗字を生成 |
| first_name | VARCHAR(50) | NOT NULL | 名前 | mimesis で日本語の名前を生成 |
| birth_date | DATE | NOT NULL | 生年月日 | mimesis で 18〜70 歳の範囲でランダム生成。ただし分布は18〜30が50%、31〜60が40%。それ以上が10%になるようにする |
| gender | SMALLINT | NOT NULL | 性別（0: 男 / 1: 女 / 2: それ以外） | 0 / 1 / 2 をランダムに選択。ただし分布は男が7%、それ以外が1%、女は残り全てとなるようにする |
| address | VARCHAR(255) | NOT NULL | 住所 | mimesis で日本語の住所(県名＋市町村名＋番地など）を生成 |
| status | SMALLINT | NOT NULL | ステータス（0: 無料会員 / 1: 有料会員 / 9: 退会会員） | 0（無料会員）固定で挿入 |
| last_login_at | TIMESTAMP | | 最終ログイン日時 | NULL で挿入 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新日時 | DEFAULT NOW() |

## member_property（会員属性）

member テーブルと 1:1 の関係。会員の行動シミュレーション用パラメータを保持する。

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | INTEGER | PRIMARY KEY, REFERENCES member(id) | 会員ID（member テーブルと 1:1） | member テーブルの id と同値 |
| to_paid_days | INTEGER | | 有料会員になる登録日からの日数（NULL: 有料会員にならない） | 90%の確率でNULL、10%の確率で30から180の範囲でランダムに設定 |
| to_sleep_days | INTEGER | | 休眠会員になる登録日からの日数（NULL: 休眠しない） | to_paid_daysがNULLでなければNULL。そうでなければ80%の確率でNULL、20%の確率で30から180の範囲でランダムに設定 |
| to_quit_days | INTEGER | | 退会する登録日からの日数（NULL: 退会しない） | to_sleep_daysがNULLでなければNULL。そうでなければ95%の確率でNULL、5%の確率で20%の確率で30から180の範囲でランダムに設定した値か、to_paid_daysの日数に30を加えたもののうち、大きい方 |

## category（カテゴリ）

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | SERIAL | PRIMARY KEY | 主キー（自動採番） | 自動採番 |
| name | VARCHAR(100) | NOT NULL | カテゴリ名 |  |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新日時 | DEFAULT NOW() |

## food（食品）

category テーブルと 1:多 の関係（1つのカテゴリに複数の食品が属する）。

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | SERIAL | PRIMARY KEY | 主キー（自動採番） | 自動採番 |
| name | VARCHAR(100) | NOT NULL | 食品名 | mimesis の Food プロバイダーでカテゴリに対応するメソッドを使って生成（料理→dish(), 飲み物→drink(), 果物→fruit(), 野菜→vegetable(), スパイス→spices()）。同名が重複した場合は末尾に連番を付与（例: "りんご 2"） |
| category_id | INTEGER | NOT NULL, REFERENCES category(id) | カテゴリID | food の name を生成した Food メソッドに対応する category レコードを逆引きして id を設定（dish()→料理、drink()→飲み物、fruit()→果物、vegetable()→野菜、spices()→スパイス） |
| price | INTEGER | NOT NULL | 値段 | mimesis の Finance プロバイダーで生成し、1000円未満は10円単位で切り捨て、1000円以上は100円単位で切り捨て |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新日時 | DEFAULT NOW() |

## purchase（購入）

member テーブルと 1:多 の関係（1会員が複数回購入できる）。

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | SERIAL | PRIMARY KEY | 主キー（自動採番） | 自動採番 |
| member_id | INTEGER | NOT NULL, REFERENCES member(id) | 会員ID | member テーブルの id を設定 |
| member_name | VARCHAR(100) | NOT NULL | 会員名（購入時点） | 購入時点の member の last_name と first_name を結合して設定 |
| shipping_address | VARCHAR(255) | NOT NULL | 送付先住所 | 購入時点の member の address を設定 |
| purchased_at | TIMESTAMP | NOT NULL | 購入日時 | データ投入処理の中で設定 |
| total_amount | INTEGER | NOT NULL | 合計金額 | データ投入処理の中で設定 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新日時 | DEFAULT NOW() |

## purchase_detail（購入明細）

purchase テーブルと 1:多 の関係（1購入に複数の明細が紐づく）。

| カラム名 | データ型 | 制約 | 説明 | データ投入ルール |
|---|---|---|---|---|
| id | SERIAL | PRIMARY KEY | 主キー（自動採番） | 自動採番 |
| purchase_id | INTEGER | NOT NULL, REFERENCES purchase(id) | 購入ID | purchase テーブルの id を設定 |
| food_id | INTEGER | NOT NULL, REFERENCES food(id) | 商品ID | food テーブルの id を設定 |
| food_name | VARCHAR(100) | NOT NULL | 商品名（購入時点） | 購入時点の food の name を設定 |
| unit_price | INTEGER | NOT NULL | 単価（購入時点） | 購入時点の food の price を設定 |
| quantity | INTEGER | NOT NULL | 数量 | データ投入処理の中で設定 |
| subtotal | INTEGER | NOT NULL | 小計 | unit_price × quantity |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新日時 | DEFAULT NOW() |

## 注意

データ投入ルールはメタデータなので、対応する列は作成しない。