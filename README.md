# inquiry-status

複数人で対応する問い合わせスレッドについて、「未対応 / 対応中 / 返信済み」を判定して一覧にするスクリプト。

記事: https://zenn.dev/liatris/articles/20261022-inquiry-status-visibility

## 前提

- Python 3.9 以上(標準ライブラリのみ。3.14.6 で確認)
- 追加のインストールは不要

## 動かし方

```bash
git clone https://github.com/liatris000/inquiry-status.git
cd inquiry-status
python3 inquiry_status.py sample_inquiries.json --now 2026-10-05T12:00:00
```

`--now` は経過時間の基準時刻。省略すると現在時刻を使うので、経過分数が下の例と変わる。

## 期待される出力

```text
問い合わせ対応状況: 未対応 2 / 対応中 1 / 返信済み 2
:red_circle: T-105 未対応 (担当: -) 領収書が欲しい ⚠️ 200分経過
:red_circle: T-103 未対応 (担当: -) 見積書の有効期限を教えてください ⚠️ 120分経過
:large_yellow_circle: T-102 対応中 (担当: 鈴木) パスワードリセットのメールが届かない ⚠️ 150分経過
:white_check_mark: T-101 返信済み (担当: 佐藤) 請求書の宛名を変更したい
:white_check_mark: T-104 返信済み (担当: 田中) 利用プランの変更方法を知りたい
```

`sample_inquiries.json` はダミーデータ。

## Slack に投稿する

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... python3 inquiry_status.py sample_inquiries.json --post
```

## 確かめていない範囲

- `--post` での Slack への投稿は実行していない(Webhook を使っていない)
- テストコードは無い。上の出力例で確かめている
