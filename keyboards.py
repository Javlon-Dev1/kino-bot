from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

# ---------- user panel ----------

def user_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Kod orqali qidirish"), KeyboardButton(text="🔍 Nomi orqali qidirish")],
            [KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="🎬 Men qo'shgan kinolar")],
        ],
        resize_keyboard=True,
    )


def search_results_kb(movies: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{m['title']} ({m['code']})", callback_data=f"getmovie:{m['code']}")]
        for m in movies
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscribe_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        link = ch["invite_link"] or f"https://t.me/{str(ch['title']).lstrip('@')}"
        rows.append([InlineKeyboardButton(text=f"➕ {ch['title']}", url=link)])
    rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- admin panel ----------

def admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="➖ Kino o'chirish")],
            [KeyboardButton(text="📢 Kanal qo'shish"), KeyboardButton(text="📢 Kanal o'chirish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📥 Takliflar")],
            [KeyboardButton(text="⬅️ Chiqish")],
        ],
        resize_keyboard=True,
    )


def submission_review_kb(submission_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Joylash", callback_data=f"sub_approve:{submission_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"sub_reject:{submission_id}"),
            ]
        ]
    )
