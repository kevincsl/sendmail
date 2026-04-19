# sendmail 規格書

## 1. 專案概述
- **名稱**: sendmail
- **類型**: 命令列發信工具
- **功能**: 使用 Gmail SMTP 發送郵件
- **語言**: Python 3

## 2. 使用方式

支援三種模式：**命令列參數模式**、**JSON 設定檔模式**、**批次寄送模式**。

### 2.1 命令列參數模式
```bash
python sendmail.py -t <收件者> -s <主旨> -bdy <內容>
```

### 2.2 JSON 設定檔模式
```bash
python sendmail.py config.json
```

### 2.3 批次寄送模式
```bash
python sendmail.py batch recipients.csv config.json
```

## 3. 命令列參數
| 參數 | 說明 | 必填 |
|------|------|------|
| `-t`, `--to` | 收件者 email | 是 |
| `-c`, `--cc` | CC 副本（可用多次） | 否 |
| `-bc`, `--bcc` | BCC 密件副本（可用多次） | 否 |
| `-a`, `--attachment` | 附件檔案路徑（可用多次） | 否 |
| `-s`, `--subject` | 信件主旨 | 是 |
| `-bdy`, `--body` | 信件內容或內文檔案路徑 | 是 |
| `-f`, `--format` | 郵件格式：`plain`（預設）或 `html` | 否 |
| `-rt`, `--reply-to` | 回覆地址 | 否 |
| `-fn`, `--from-name` | 寄件者顯示名稱 | 否 |

## 4. JSON 格式
```json
{
  "to": "收件者 email",
  "cc": ["cc1@example.com"],
  "bcc": ["bcc@example.com"],
  "attachments": ["file.pdf"],
  "subject": "主旨",
  "body": "內文",
  "body_file": "內文檔案路徑",
  "format": "plain 或 html",
  "reply_to": "回覆地址",
  "from_name": "顯示名稱",
  "vars": { "name": "Kevin" }
}
```

## 5. 範本變數

內文中的 `{{變數名}}` 會被 `vars` 字典中的值替換。

**範例：**
- 內文：`"Hello {{name}}, your order #{{order_id}} is ready"`
- vars：`{"name": "Kevin", "order_id": "12345"}`
- 結果：`"Hello Kevin, your order #12345 is ready"`

## 6. 環境變數 (.env)
| 變數 | 說明 | 預設值 |
|------|------|--------|
| `GMAIL_USER` | Gmail 信箱 | - |
| `GMAIL_APP_PASSWORD` | Gmail App Password | - |
| `GMAIL_FROM_NAME` | 預設寄件者顯示名稱 | （空） |
| `SMTP_SERVER` | SMTP 伺服器 | smtp.gmail.com |
| `SMTP_PORT` | SMTP 連接埠 | 587 |
| `SMTP_TIMEOUT` | 連線逾時（秒） | 30 |

## 7. 批次寄送 (CSV)

CSV 欄位：
- `to` 或 `email` 或 `mail`：收件者
- `subject`：主旨（可空白使用 JSON 設定）
- `body`：內文
- `body_file`：內文檔案路徑
- `format`：格式
- `cc`、`bcc`：副本（逗號分隔）
- `reply_to`、`from_name`：回覆地址、顯示名稱
- 其他欄位：自動成為範本變數

## 8. 輸出
- 成功：顯示 `Email sent successfully!`
- 失敗：顯示錯誤訊息並以 exit code 1 結束
- 批次模式：顯示 `Batch complete: X sent, Y failed`

## 9. 支援附件格式
- 圖片（jpg, png, gif, bmp）
- 文件（pdf, doc, docx, txt）
- 任何檔案類型

## 10. 測試案例
- [x] 基本純文字郵件
- [x] HTML 富文字郵件
- [x] 附件（圖片、文件）
- [x] CC、BCC 副本
- [x] Reply-To 回覆地址
- [x] 寄件者顯示名稱（From Name）
- [x] JSON 設定檔模式
- [x] 批次寄送（CSV + JSON）
- [x] 範本變數替換

## 11. Git 準備
- `.env` 檔案已加入 `.gitignore`，不會被 commit
