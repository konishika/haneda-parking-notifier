# 羽田空港 駐車場空き通知ツール

羽田空港の駐車場（P2・P3・P4・P4P・P5・P5P）の予約空き状況を定期的に確認し、空きが見つかったら LINE と Gmail で通知するツールです。通知のみですので、通知を受けたらご自身でログインして予約操作が必要です。Cloud Codeに相談しながら書いてるし、なんなら、コミットもしてもらっている。めんどくさいから。

## 機能

- 複数駐車場の空き状況を約55秒ごとに自動チェック（最大12時間）
- 指定した日程のすべての日に空きがあったときに通知
- LINE Messaging API によるプッシュ通知
- Gmail による代替通知（LINE の月間送信上限に達した場合に自動切り替え）
- ヘッドレス Chrome で動作（GUI なし環境対応）

## 対応駐車場

| ID   | 駐車場名      |
|------|-------------|
| P2   | 第1ターミナル駐車場（P2） |
| P3   | 第2ターミナル駐車場（P3） |
| P4   | 第2ターミナル駐車場（P4 一般） |
| P4P  | 第2ターミナル駐車場（P4P 個室） |
| P5   | 第3ターミナル駐車場（P5 一般） |
| P5P  | 第3ターミナル駐車場（P5P 個室） |

## 必要なもの

- Python 3.11 以上
- Google Chrome
- LINE Messaging API チャンネル（通知先として使用）
- Gmail アカウント（アプリパスワードを使用）

## セットアップ

### 1. リポジトリのクローンと依存パッケージのインストール

```bash
git clone <このリポジトリのURL>
cd haneda

python3 -m venv venv
source venv/bin/activate

pip install selenium webdriver-manager line-bot-sdk python-dotenv pytest
```

### 2. 環境変数の設定

`sample.env` をコピーして `.env` を作成し、各値を設定します。

```bash
cp sample.env .env
```

```env
LINE_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_USER_ID=your_line_user_id_here

GMAIL_USER=your_gmail_address@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
EMAIL_TO=recipient@example.com
```

**LINE の設定方法**
1. [LINE Developers](https://developers.line.biz/) でチャンネルを作成（Messaging API）
2. チャンネルアクセストークンを `LINE_ACCESS_TOKEN` に設定
3. 通知を受け取るアカウントのユーザー ID を `LINE_USER_ID` に設定

**Gmail の設定方法**
1. Google アカウントで2段階認証を有効にする
2. [アプリパスワード](https://myaccount.google.com/apppasswords) を発行する（16文字）
3. 発行したパスワードを `GMAIL_APP_PASSWORD` に設定

## 使い方

```bash
cd haneda
source venv/bin/activate

python check_ng.py --date 2026/08/10 --period 5 --lots P5 P5P
```

### オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--date`  | `2026/03/18` | チェック開始日（YYYY/MM/DD 形式） |
| `--period` | `5` | チェックする日数 |
| `--interval` | `55` | チェック間隔（秒）。P2・P3を監視する場合は長め（例: `120`）を推奨 |
| `--hours` | `12` | 監視時間（時間） |
| `--lots` | 全駐車場 | チェックする駐車場（例: `--lots P5 P4`）。省略時は全駐車場 |

### 実行例

```bash
# 8月10日から5日間、P5 と P5P のみチェック
python check_ng.py --date 2026/08/10 --period 5 --lots P5 P5P

# 全駐車場を3日間チェック
python check_ng.py --date 2026/08/10 --period 3

# P2・P3 をアクセス間隔2分、6時間だけ監視
python check_ng.py --date 2026/08/10 --period 5 --lots P2 P3 --interval 120 --hours 6
```

### 結果の見かた

コンソールには以下の形式で結果が表示されます。

```
2026/08/10 12:34:56  Parking 5 :  O O X C O
```

| 記号 | 意味 |
|------|------|
| O    | 空きあり |
| C    | 空きあり（混雑） |
| X    | 満車または予約不可 |

指定した日数のすべての日で空きがあると（O または C が period 個揃うと）、LINE と Gmail に通知が届きます。

## テスト

実際のブラウザは不要です（WebDriver をモック）。

```bash
cd haneda
source venv/bin/activate

pytest tests/

# 特定のテストクラスだけ実行
pytest tests/test_parking_checker.py::TestAllFull
```

## 注意事項

- 各駐車場の公式予約サイトの公開ページを定期的に参照します。ご利用前に各サービスの利用規約をご確認の上、自己責任でお使いください。
- **P2・P3（hnd-rsv.aeif.or.jp）についての注意：** 同サービスの利用規約（第12条）には「本サービス又は予約ホームページの運営又は利用に支障を与える行為」の禁止があります。スクレイピングの明示的な禁止ではありませんが、複数の駐車場を長時間連続で監視する場合はグレーゾーンになり得ます。アクセス間隔の延長や、監視対象をP2・P3以外の駐車場に絞ることも選択肢として検討してください。
- P4についても第14条(3)に「その他管理者が本サービスの利用者として不適当と判断した場合」、P5についても第14条(3)「その他管理者が不適当と判断した場合」に会員のサービス利用を停止するとあります。スクレイピングの明示的な禁止ではありませんが、常識の範囲内でご利用ください。
- LINE Messaging API の無料プランには月間送信数の上限があります。上限に達した場合は自動的にメール通知に切り替わります。
- 指定日が30日以上先の場合、予約受付期間外の可能性があります（実行時に警告が表示されます）。
- `.env` ファイルには認証情報が含まれます。**絶対にコミットしないでください**（`.gitignore` で除外済み）。

## ライセンス

MIT
