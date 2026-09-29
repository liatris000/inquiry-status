#!/usr/bin/env python3
"""問い合わせスレッドの対応状況を集計して一覧化する。

使い方:
    python3 inquiry_status.py sample_inquiries.json
    SLACK_WEBHOOK_URL=https://hooks.slack.com/... python3 inquiry_status.py sample_inquiries.json --post

標準ライブラリのみ。Python 3.9 以上で動く。
"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime

# 「対応中」の宣言とみなす定型句。返信本文ではなく、着手の合図として使う
CLAIM_MARKERS = ("対応中", "確認します", "👀")
# 未対応がこの分数を超えたら警告を付ける
STALE_MINUTES = 60

SCHEMA = """
CREATE TABLE messages (
    thread_id TEXT NOT NULL,
    ts        TEXT NOT NULL,          -- ISO 8601
    role      TEXT NOT NULL,          -- 'customer' or 'staff'
    author    TEXT NOT NULL,
    body      TEXT NOT NULL
);
"""


def load(db: sqlite3.Connection, path: str) -> None:
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    db.executemany(
        "INSERT INTO messages VALUES (:thread_id, :ts, :role, :author, :body)", rows
    )


def is_claim(body: str) -> bool:
    return any(m in body for m in CLAIM_MARKERS) and len(body) <= 30


def summarize(db: sqlite3.Connection, now: datetime) -> list[dict]:
    """スレッドごとに状態を判定する。判定の基準は「顧客の最後の発言より後に何があるか」。"""
    threads = []
    for (tid,) in db.execute("SELECT DISTINCT thread_id FROM messages ORDER BY thread_id"):
        msgs = db.execute(
            "SELECT ts, role, author, body FROM messages WHERE thread_id=? ORDER BY ts", (tid,)
        ).fetchall()
        last_customer = max(i for i, m in enumerate(msgs) if m[1] == "customer")
        after = msgs[last_customer + 1:]
        replies = [m for m in after if not is_claim(m[3])]
        claims = [m for m in after if is_claim(m[3])]

        if replies:
            status, owner = "返信済み", replies[-1][2]
        elif claims:
            status, owner = "対応中", claims[-1][2]
        else:
            status, owner = "未対応", "-"

        waited = (now - datetime.fromisoformat(msgs[last_customer][0])).total_seconds() / 60
        threads.append({
            "thread_id": tid,
            "status": status,
            "owner": owner,
            "waited_min": int(waited),
            "subject": msgs[0][3].splitlines()[0][:30],
            "stale": status != "返信済み" and waited > STALE_MINUTES,
        })
    return threads


def render(threads: list[dict]) -> str:
    icon = {"未対応": ":red_circle:", "対応中": ":large_yellow_circle:", "返信済み": ":white_check_mark:"}
    order = {"未対応": 0, "対応中": 1, "返信済み": 2}
    lines = []
    for t in sorted(threads, key=lambda t: (order[t["status"]], -t["waited_min"])):
        warn = f" ⚠️ {t['waited_min']}分経過" if t["stale"] else ""
        lines.append(f"{icon[t['status']]} {t['thread_id']} {t['status']} (担当: {t['owner']}) {t['subject']}{warn}")
    counts = {s: sum(1 for t in threads if t["status"] == s) for s in order}
    header = "問い合わせ対応状況: " + " / ".join(f"{s} {n}" for s, n in counts.items())
    return header + "\n" + "\n".join(lines)


def post_slack(text: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        sys.exit("SLACK_WEBHOOK_URL が未設定です")
    req = urllib.request.Request(
        url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=10).read()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--now", default="2026-10-05T12:00:00", help="経過時間の基準時刻 (ISO 8601)")
    ap.add_argument("--post", action="store_true", help="Slack Incoming Webhook に投稿する")
    args = ap.parse_args()

    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    load(db, args.input)
    text = render(summarize(db, datetime.fromisoformat(args.now)))
    print(text)
    if args.post:
        post_slack(text)


if __name__ == "__main__":
    main()
