"""MilkLab Caption Generator (S1).

Usage:
    python caption_generator.py --menu "นมสดเย็น"
    python caption_generator.py --menu "นมชมพู" --n 3

Reads GOOGLE_API_KEY from env. Generates a Thai caption for a milk menu item.
"""

import os
import sys
import argparse

from dotenv import load_dotenv
from google import genai

# 3. ข้อมูล Menu แบบ Nested Dict เพื่อให้ caption เจาะจงขึ้น
MENU_DATA = {
    "นมสดเย็น": {"price": 45, "ingredients": "นมสดแท้ 100%"},
    "นมชมพู": {"price": 50, "ingredients": "น้ำแดงสละและนมสดแท้"},
    "โกโก้หนึบ": {"price": 60, "ingredients": "ผงโกโก้พรีเมียมนำเข้าและซอสโกโก้หนึบ"},
}

# ปรับ Prompt ให้รับข้อมูลราคาและส่วนผสม
PROMPT_TEMPLATE = """\
คุณคือ social media manager ของร้าน MilkLab° ร้านนมสดกลางคืน

จงเขียนแคปชั่นภาษาไทย 2 ถึง 3 ประโยคโปรโมตเมนู: {menu}
ข้อมูลสำหรับเมนูนี้: ราคา {price} บาท, ส่วนผสมหลักคือ {ingredients}

เงื่อนไข:
- โทนสนุก ใช้คำง่าย ใส่ emoji ได้
- ต้องมี call-to-action ปิดท้าย เช่น สั่งเลย หรือ ทักแชท
- ห้ามใช้ em dash
"""


def build_prompt(menu: str, ingredients: str, price: int) -> str:
    """Build the Gemini prompt for a menu item."""
    return PROMPT_TEMPLATE.format(menu=menu, price=price, ingredients=ingredients)


def generate_caption_with_client(
    client,
    prompt: str,
    *,
    max_attempts: int = 3,
    max_length: int = 280,
    log=print,
) -> str:
    """Generate a caption using an injected client so the loop is easy to test."""
    caption = ""

    for attempt in range(1, max_attempts + 1):
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
        )
        caption = response.text or ""

        if len(caption) <= max_length:
            return caption

        if log is not None:
            log(f"รอบที่ {attempt}: แคปชั่นยาวเกินไป ({len(caption)} ตัวอักษร) จะลองใหม่")

    return caption


def generate_caption(
    menu: str,
    price: int,
    ingredients: str,
    api_key: str | None = None,
) -> str:
    """Generate a Thai caption for the given milk menu item."""
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY not set in env or argument")

    client = genai.Client(api_key=key)
    prompt = build_prompt(menu, ingredients, price)
    return generate_caption_with_client(client, prompt)


def main() -> int:
    load_dotenv()

    # 1. & 2. เพิ่ม CLI flag --menu และ --n
    parser = argparse.ArgumentParser(
        description="MilkLab Caption Generator (S1)")
    parser.add_argument("--menu", type=str, required=True,
                        help="ชื่อเมนูที่จะโปรโมต")
    parser.add_argument("--n", type=int, default=1,
                        help="จำนวน caption ที่ต้องการ (default 1)")

    args = parser.parse_args()
    menu_name = args.menu.strip()
    num_captions = args.n

    if not menu_name:
        print("กรุณาใส่ชื่อเมนู")
        return 1

    # ค้นหาข้อมูลจาก Dictionary (หากไม่มีข้อมูลเมนูที่ระบุ ให้ใช้ค่า Default)
    menu_info = MENU_DATA.get(
        menu_name, {"price": 50, "ingredients": "นมสดคุณภาพดี"})

    print(
        f"กำลังสร้างแคปชั่นสำหรับเมนู '{menu_name}' จำนวน {num_captions} รายการ...\n")

    for i in range(num_captions):
        caption = generate_caption(
            menu_name, menu_info["price"], menu_info["ingredients"])
        print(f"--- Caption {i + 1} ---")
        print(caption)
        print(f"(ความยาว: {len(caption)} ตัวอักษร)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
