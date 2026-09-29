# inquiry-status

複数人で対応する問い合わせスレッドについて、「未対応 / 対応中 / 返信済み」を判定して一覧にするスクリプト。
標準ライブラリのみ（Python 3.9 以上）。

```bash
python3 inquiry_status.py sample_inquiries.json
SLACK_WEBHOOK_URL=... python3 inquiry_status.py sample_inquiries.json --post
```

`sample_inquiries.json` はダミーデータです。
