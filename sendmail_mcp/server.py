#!/usr/bin/env python3
"""
sendmail MCP Server
讓 Claude / Codex 透過 MCP 協定寄送郵件
"""
import argparse
import os
import sys

# 加入父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 延遲載入避免循環引用
_dotenv = None
def _get_dotenv():
    global _dotenv
    if _dotenv is None:
        import dotenv
        dotenv.load_dotenv()
        _dotenv = True
    return _dotenv

def _get_sendmail_funcs():
    """延遲載入 sendmail 函式"""
    _get_dotenv()
    from sendmail import send_email, read_body, render_template
    return send_email, read_body, render_template


async def main(transport: str = "stdio"):
    """主程式"""
    from mcp.server import Server
    from mcp.types import Tool, TextContent

    # 建立 Server
    server = Server("sendmail")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """MCP 工具清單"""
        return [
            Tool(
                name="sendmail",
                description="""使用 Gmail SMTP 寄送郵件。

【主要用途】
- 寄送純文字或 HTML 格式郵件
- 支援 CC、BCC 副本
- 支援附件
- 支援範本變數 ({{name}} 替換)
- 支援自訂寄件者名稱和回覆地址

【使用時機】
當使用者說「寄信」、「發送郵件」、「send email」、「寄 email」時使用。""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "收件者 email 地址"
                        },
                        "subject": {
                            "type": "string",
                            "description": "信件主旨"
                        },
                        "body": {
                            "type": "string",
                            "description": "郵件內容，可直接輸入文字或使用 {{變數}} 範本語法"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["plain", "html"],
                            "default": "plain",
                            "description": "郵件格式：plain（純文字）或 html（富文字）"
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "CC 副本 email 陣列",
                            "default": []
                        },
                        "bcc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "BCC 密件副本 email 陣列",
                            "default": []
                        },
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "附件檔案路徑陣列",
                            "default": []
                        },
                        "body_file": {
                            "type": "string",
                            "description": "內文檔案路徑（會讀取檔案內容作為郵件內文）"
                        },
                        "reply_to": {
                            "type": "string",
                            "description": "回覆地址（收件者回信時送到此地址）"
                        },
                        "from_name": {
                            "type": "string",
                            "description": "寄件者顯示名稱"
                        },
                        "vars": {
                            "type": "object",
                            "description": "範本變數，會替換 body 中的 {{key}} 為對應值",
                            "default": {}
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """處理工具呼叫"""
        if name != "sendmail":
            raise ValueError(f"Unknown tool: {name}")

        send_email, read_body, render_template = _get_sendmail_funcs()

        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body", "")
        fmt = arguments.get("format", "plain")
        cc = arguments.get("cc") or []
        bcc = arguments.get("bcc") or []
        attachments = arguments.get("attachments") or []
        body_file = arguments.get("body_file")
        reply_to = arguments.get("reply_to")
        from_name = arguments.get("from_name")
        vars_dict = arguments.get("vars") or {}

        # 讀取 body_file
        if body_file:
            body = read_body(body_file, fmt)

        # 範本變數替換
        if vars_dict:
            body = render_template(body, vars_dict)

        # 寄信
        success = send_email(
            to=to,
            subject=subject,
            body=body,
            fmt=fmt,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            reply_to=reply_to,
            from_name=from_name
        )

        if success:
            return [TextContent(type="text", text="郵件已成功寄出！")]
        else:
            raise RuntimeError("寄送失敗，請檢查設定或網路連線。")

    if transport == "stdio":
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    else:
        print("SSE transport not fully implemented yet")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="sendmail MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                        help="傳輸方式：stdio（預設）或 sse")
    args = parser.parse_args()

    import asyncio
    asyncio.run(main(args.transport))
