"""MilkLab Sales Logger (S2).

Usage:
    python sales_logger.py --menu "นมหมีฮอกไกโด" --qty 2 --price 65

Reads GOOGLE_SHEETS_CREDENTIALS and TELEGRAM_BOT_TOKEN (or LINE_CHANNEL_TOKEN) from env.
Appends row [timestamp, menu, qty, price, total] to a Google Sheet,
then sends a notification via Telegram or LINE bot.
"""

import argparse
import json
import os
import sys
from datetime import datetime

import gspread
import requests


def append_to_sheet(menu: str, qty: int, price: float) -> dict:
    """TODO 1: ใช้ gspread เปิด Sheet ของตัวเอง แล้ว append_row ด้วย [timestamp, menu, qty, price, total]

    Returns dict {timestamp, menu, qty, price, total} ที่ append แล้ว
    Raises RuntimeError ถ้า credentials ไม่มี หรือ Sheet ไม่ accessible
    """
    # 1. โหลด Credentials จาก Environment Variable
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_json:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_CREDENTIALS ใน Environment")

    try:
        # 2. แปลง JSON string เป็น Dictionary และเชื่อมต่อ gspread
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)

        # 3. เปิด Spreadsheet (แก้ชื่อ Sheet ในวงเล็บให้ตรงกับชื่อไฟล์ Google Sheets ของคุณ)
        # หรือถ้าต้องการให้ยืดหยุ่น สามารถตั้ง SPREADSHEET_NAME ใน Codespaces secret ก็ได้
        sheet_name = os.environ.get("SPREADSHEET_NAME", "MilkLab Sales")
        sh = gc.open(sheet_name)
        worksheet = sh.sheet1

        # 4. คำนวณยอดรวมและเตรียมข้อมูล
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = qty * price
        row_data = [timestamp, menu, qty, price, total]

        # 5. บันทึกลงแถวใหม่
        worksheet.append_row(row_data)

        return {
            "timestamp": timestamp,
            "menu": menu,
            "qty": qty,
            "price": price,
            "total": total
        }
    except Exception as e:
        raise RuntimeError(f"เชื่อมต่อหรือบันทึก Google Sheets ล้มเหลว: {e}")


def send_notification(message: str) -> str:
    """TODO 2: ส่ง message ไปยัง Telegram bot (ใช้ TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
    หรือ LINE bot (ใช้ LINE_CHANNEL_TOKEN) เลือกตัวใดตัวหนึ่ง

    Returns: provider name ที่ใช้ ("telegram" หรือ "line")
    Raises RuntimeError ถ้า no credentials
    """
    # ลองตรวจสอบ Telegram ก่อน
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if telegram_token and telegram_chat_id:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": message
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return "telegram"

    # ถ้าไม่มี Telegram ลองตรวจสอบ LINE
    line_token = os.environ.get("LINE_CHANNEL_TOKEN")
    # ต้องดึง User ID ของคุณมาใส่ด้วย
    line_user_id = os.environ.get("LINE_USER_ID")

    if line_token and line_user_id:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {line_token}"
        }
        payload = {
            "to": line_user_id,
            "messages": [{"type": "text", "text": message}]
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return "line"

    raise RuntimeError(
        "ไม่พบ Credentials สำหรับ Telegram หรือ LINE ใน Environment")


def main() -> int:
    parser = argparse.ArgumentParser(description="MilkLab Sales Logger")
    parser.add_argument("--menu", required=True, help="ชื่อเมนู")
    parser.add_argument("--qty", type=int, required=True, help="จำนวนขวด")
    parser.add_argument("--price", type=float,
                        required=True, help="ราคาต่อขวด")
    args = parser.parse_args()

    try:
        # TODO 3: เรียก append_to_sheet แล้ว extract total
        row = append_to_sheet(args.menu, args.qty, args.price)
        total = row["total"]
    except Exception as exc:
        print(f"[ERROR] บันทึก Sheet ล้มเหลว: {exc}", file=sys.stderr)
        print("[HINT] ตรวจ GOOGLE_SHEETS_CREDENTIALS และ share Sheet กับ service account email", file=sys.stderr)
        return 1

    try:
        # TODO 4: เรียก send_notification ด้วย message ที่บอกยอดที่บันทึก
        provider = send_notification(
            f"บันทึก {args.menu} x{args.qty} = {total} บาท")
    except Exception as exc:
        print(
            f"[WARN] บันทึก Sheet สำเร็จแต่ส่งแจ้งเตือนล้มเหลว: {exc}", file=sys.stderr)
        return 0

    print(f"[OK] บันทึกและแจ้งเตือนผ่าน {provider} เรียบร้อย ยอด {total} บาท")
    return 0


if __name__ == "__main__":
    sys.exit(main())
