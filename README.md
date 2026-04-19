# sendmail

Gmail SMTP 命令列發信工具，支援命令列參數、JSON 設定檔、批次寄送三種模式。

## 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 設定 .env
在專案根目錄建立 `.env` 檔案：
```
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

### 3. 寄出第一封信
```bash
python sendmail.py -t kevincsl@gmail.com -s "Hello" -bdy "Test message"
```

---

## 取得 Gmail App Password

Gmail 不允許使用一般密碼登入，需要申請 App Password：

1. 前往 [Google 帳戶](https://myaccount.google.com) → 安全性
2. 開啟「兩步驟驗證」
3. 搜尋「應用程式密碼」→ 建立一個
4. 選取「郵件」→ 「其他裝置（Python）」
5. 複製產生的 16 位密碼，貼入 `.env` 的 `GMAIL_APP_PASSWORD`

---

## 三種使用模式

### 模式一：命令列參數模式

```bash
python sendmail.py -t <收件者> -s <主旨> -bdy <內容或檔案路徑>
```

#### 參數說明

| 參數 | 說明 |
|------|------|
| `-t`, `--to` | 收件者 email |
| `-c`, `--cc` | CC 副本（可重複，如 `-c a@mail.com -c b@mail.com`） |
| `-bc`, `--bcc` | BCC 密件副本（可重複） |
| `-a`, `--attachment` | 附件檔案路徑（可重複） |
| `-s`, `--subject` | 信件主旨 |
| `-bdy`, `--body` | 信件內容或內文檔案路徑 |
| `-f`, `--format` | `plain`（預設）或 `html` |
| `-rt`, `--reply-to` | 回覆地址（收件者回信時送到此地址） |
| `-fn`, `--from-name` | 寄件者顯示名稱（如 `My Bot`） |

#### CLI 範例

**基本寄信**
```bash
python sendmail.py -t kevin@whsh.tc.edu.tw -s "測試郵件" -bdy "這是內容"
```

**自訂寄件者名稱與回覆地址**
```bash
python sendmail.py -t kevin@whsh.tc.edu.tw -s "Hello" -bdy "內容" -fn "My Bot" -rt support@company.com
```

**HTML 富文字 + 附件**
```bash
python sendmail.py -t kevin@whsh.tc.edu.tw -s "報告" -bdy email.html -f html -a report.pdf
```

---

### 模式二：JSON 設定檔模式

```bash
python sendmail.py sample.json
```

#### JSON 欄位說明

| 欄位 | 說明 | 必填 |
|------|------|------|
| `to` | 收件者 email | 是 |
| `subject` | 信件主旨 | 是 |
| `body` | 內文文字 | 否 |
| `body_file` | 內文檔案路徑（優先於 body） | 否 |
| `format` | `plain` 或 `html` | 否 |
| `cc` | CC 字串陣列 | 否 |
| `bcc` | BCC 字串陣列 | 否 |
| `attachments` | 附件路徑陣列 | 否 |
| `reply_to` | 回覆地址 | 否 |
| `from_name` | 寄件者顯示名稱 | 否 |
| `vars` | 範本變數字典 | 否 |

#### JSON 範例

```json
{
  "to": "kevin@whsh.tc.edu.tw",
  "cc": ["kevin@mirai.tw"],
  "bcc": [],
  "attachments": ["report.pdf"],
  "subject": "每週報告",
  "body": "你好 {{name}}，請查閱報告。",
  "body_file": "",
  "format": "html",
  "reply_to": "support@company.com",
  "from_name": "自動化系統",
  "vars": {
    "name": "Kevin"
  }
}
```

---

### 模式三：批次寄送模式

從 CSV 檔案讀取多位收件者，結合 JSON 設定檔批次寄送。

```bash
python sendmail.py batch recipients.csv base_config.json
```

#### CSV 格式

第一列為標題，支援以下欄位：

| 欄位 | 說明 |
|------|------|
| `to` 或 `email` 或 `mail` | 收件者（必要） |
| `subject` | 主旨（可空白繼承 JSON 設定） |
| `body` | 內文 |
| `body_file` | 內文檔案路徑 |
| `format` | `plain` 或 `html` |
| `cc` | CC（逗號分隔） |
| `bcc` | BCC（逗號分隔） |
| `reply_to` | 回覆地址 |
| `from_name` | 顯示名稱 |
| 其他自訂欄位 | 自動做為範本變數 |

#### CSV 範例

```csv
to,subject,vars
kevin@whsh.tc.edu.tw,Hello {{name}},{"name":"Kevin"}
kevin@mirai.tw,Hi {{name}},{"name":"Mirai"}
```

#### JSON 範例（base_config.json）

```json
{
  "subject": "通知",
  "body": "親愛的 {{name}}，您的訂單已處理完畢。",
  "format": "html",
  "from_name": "客服系統",
  "attachments": ["invoice.pdf"]
}
```

#### 執行結果

每列 CSV 會套用 JSON 設定，並用 CSV 中的值覆寫，最後渲染範本變數後寄送。

---

## 範本變數

在 `body` 或 `body_file` 中使用 `{{變數名}}`，會被 `vars` 中的值替換。

**JSON 設定：**
```json
{
  "body": "你好 {{name}}，歡迎來到 {{company}}！",
  "vars": {
    "name": "Kevin",
    "company": "ABC Corp"
  }
}
```

**批次模式：**
CSV 中額外欄位會自動加入 vars：
```csv
to,subject,name,order_id
kevin@mail.com,訂單通知,Kevin,12345
```

結果：`"你好 Kevin，請查收訂單 #12345"`

---

## 環境變數

在 `.env` 中設定：

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `GMAIL_USER` | Gmail 信箱 | （必填） |
| `GMAIL_APP_PASSWORD` | Gmail App Password | （必填） |
| `GMAIL_FROM_NAME` | 預設寄件者顯示名稱 | （空） |
| `SMTP_SERVER` | SMTP 伺服器 | smtp.gmail.com |
| `SMTP_PORT` | SMTP 連接埠 | 587 |
| `SMTP_TIMEOUT` | 連線逾時（秒） | 30 |

---

## 常見問題

**Q: 出現 `SMTPAuthenticationError`？**
A: 檢查 `.env` 設定是否正確，確認已使用 App Password 而非一般密碼。

**Q: 附件無法寄送？**
A: 確認檔案路徑正確，檔案必須存在。

**Q: 如何發送 HTML 郵件？**
A: 使用 `-f html`（CLI）或 `"format": "html"`（JSON）。

**Q: 如何讓收件者回信到不同地址？**
A: 使用 `-rt` 參數（CLI）或 `"reply_to"` 欄位（JSON）。

**Q: 如何自訂寄件者顯示名稱？**
A: 使用 `-fn` 參數（CLI）、`"from_name"` 欄位（JSON），或在 `.env` 中設定 `GMAIL_FROM_NAME`。

**Q: 批次寄送支援範本變數嗎？**
A: 支援。CSV 中任何非預設欄位都會做為 vars，結合 JSON 中的 vars 一起替換。
