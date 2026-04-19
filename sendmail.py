#!/usr/bin/env python3
import argparse
import csv
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from dotenv import load_dotenv
import os

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_FROM_NAME = os.getenv("GMAIL_FROM_NAME", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "30"))


def read_body(body: str, fmt: str) -> str:
    """讀取郵件內文。如果是檔案路徑則讀取檔案，否則直接返回文字。"""
    if os.path.isfile(body):
        with open(body, "r", encoding="utf-8") as f:
            return f.read()
    return body


def render_template(body: str, vars: dict) -> str:
    """將 body 中的 {{var}} 替換為 vars 中的值。"""
    for key, value in vars.items():
        body = body.replace(f"{{{{{key}}}}}", str(value))
    return body


def format_from(from_email: str, from_name: str = "") -> str:
    """格式化寄件者地址，可帶顯示名稱。"""
    if from_name:
        return formataddr((from_name, from_email))
    return from_email


def send_email(to: str, subject: str, body: str, fmt: str = "plain",
               cc: list = None, bcc: list = None, attachments: list = None,
               reply_to: str = None, from_name: str = None) -> bool:
    msg = MIMEMultipart()
    msg["Subject"] = subject

    # 寄件者（可自訂顯示名稱）
    sender_name = from_name or GMAIL_FROM_NAME or ""
    msg["From"] = format_from(GMAIL_USER, sender_name)
    msg["To"] = to

    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    if reply_to:
        msg["Reply-To"] = reply_to

    content = read_body(body, fmt)
    msg.attach(MIMEText(content, fmt, "utf-8"))

    if attachments:
        for filepath in attachments:
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(filepath)
                    part.add_header("Content-Disposition", f"attachment; filename={filename}")
                    msg.attach(part)

    all_recipients = [to]
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg, to, all_recipients)
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def send_from_json(config_path: str) -> bool:
    """從 JSON 檔案讀取設定並發送郵件。"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    to = config.get("to")
    subject = config.get("subject")
    body = config.get("body", "")
    body_file = config.get("body_file")
    fmt = config.get("format", "plain")
    cc = config.get("cc")
    bcc = config.get("bcc")
    attachments = config.get("attachments")
    reply_to = config.get("reply_to")
    from_name = config.get("from_name")

    # 範本變數
    vars_dict = config.get("vars", {})

    if body_file:
        body = body_file

    content = read_body(body, fmt)
    content = render_template(content, vars_dict)

    return send_email(to, subject, body, fmt, cc, bcc, attachments, reply_to, from_name)


def send_batch(csv_path: str, json_config_path: str) -> bool:
    """批次寄送：讀取 CSV 檔案，結合 JSON 設定檔，寄送給每位收件者。"""
    # 讀取 JSON 設定
    with open(json_config_path, "r", encoding="utf-8") as f:
        base_config = json.load(f)

    base_subject = base_config.get("subject", "")
    base_body = base_config.get("body", "")
    base_body_file = base_config.get("body_file")
    base_fmt = base_config.get("format", "plain")
    base_cc = base_config.get("cc") or []
    base_bcc = base_config.get("bcc") or []
    base_attachments = base_config.get("attachments") or []
    base_reply_to = base_config.get("reply_to")
    base_from_name = base_config.get("from_name")

    if base_body_file:
        base_body = read_body(base_body_file, base_fmt)

    # 讀取 CSV
    success_count = 0
    fail_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            to = row.get("to") or row.get("email") or row.get("mail")
            if not to:
                continue

            # 合併：CSV 內容覆寫 base
            subject = row.get("subject", base_subject)
            body = row.get("body", base_body)
            body_file = row.get("body_file", base_body_file)
            fmt = row.get("format", base_fmt)
            cc = row.get("cc", "").split(",") if row.get("cc") else base_cc
            bcc = row.get("bcc", "").split(",") if row.get("bcc") else base_bcc
            reply_to = row.get("reply_to", base_reply_to)
            from_name = row.get("from_name", base_from_name)

            # 讀取 body_file
            if body_file and os.path.isfile(body_file):
                body = read_body(body_file, fmt)

            # 範本變數：CSV 每列 + base vars
            vars_dict = {**base_config.get("vars", {}), **row}
            body = render_template(body, vars_dict)

            if send_email(to, subject, body, fmt, cc, bcc, base_attachments, reply_to, from_name):
                success_count += 1
            else:
                fail_count += 1

    print(f"Batch complete: {success_count} sent, {fail_count} failed")
    return fail_count == 0


def main():
    # 批次模式：sendmail.py batch recipients.csv config.json
    if len(os.sys.argv) >= 3 and os.sys.argv[1] == "batch":
        csv_path = os.sys.argv[2]
        json_path = os.sys.argv[3]
        if send_batch(csv_path, json_path):
            exit(0)
        else:
            exit(1)
        return

    # JSON 模式：sendmail.py config.json
    if len(os.sys.argv) == 2 and os.sys.argv[1].endswith(".json"):
        if send_from_json(os.sys.argv[1]):
            print("Email sent successfully!")
        else:
            print("Failed to send email.")
            exit(1)
        return

    # CLI 模式
    parser = argparse.ArgumentParser(description="Send email via Gmail SMTP")
    parser.add_argument("-t", "--to", required=True, help="Recipient email address")
    parser.add_argument("-c", "--cc", action="append", default=[], help="CC recipient (can be used multiple times)")
    parser.add_argument("-bc", "--bcc", action="append", default=[], help="BCC recipient (can be used multiple times)")
    parser.add_argument("-a", "--attachment", action="append", default=[], help="Attachment file path (can be used multiple times)")
    parser.add_argument("-s", "--subject", required=True, help="Email subject")
    parser.add_argument("-bdy", "--body", required=True, help="Email body or path to body file")
    parser.add_argument("-f", "--format", choices=["plain", "html"], default="plain",
                        help="Email format: plain (default) or html")
    parser.add_argument("-rt", "--reply-to", help="Reply-To email address")
    parser.add_argument("-fn", "--from-name", help="Sender display name")

    args = parser.parse_args()

    if send_email(args.to, args.subject, args.body, args.format,
                  args.cc, args.bcc, args.attachment, args.reply_to, args.from_name):
        print("Email sent successfully!")
    else:
        print("Failed to send email.")
        exit(1)


if __name__ == "__main__":
    main()
