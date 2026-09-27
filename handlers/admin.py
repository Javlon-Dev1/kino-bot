from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

import database as db
import keyboards as kb
from config import ADMIN_IDS
from states import AdminAddMovie, AdminRemoveMovie, AdminAddChannel, AdminRemoveChannel

router = Router()
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


@router.message(Command("admin"))
async def admin_panel(message: Message):
    await message.answer("Admin panelga xush kelibsiz 👑", reply_markup=kb.admin_main_menu())


@router.message(F.text == "⬅️ Chiqish")
async def exit_admin(message: Message):
    await message.answer("Foydalanuvchi menyusiga qaytdingiz.", reply_markup=kb.user_main_menu())


# ---------- add movie ----------

@router.message(F.text == "➕ Kino qo'shish")
async def admin_add_movie_start(message: Message, state: FSMContext):
    await state.set_state(AdminAddMovie.waiting_video)
    await message.answer("Kino videosini yuboring:")


@router.message(AdminAddMovie.waiting_video, F.video)
async def admin_add_movie_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AdminAddMovie.waiting_title)
    await message.answer("Kino nomini kiriting:")


@router.message(AdminAddMovie.waiting_video)
async def admin_add_movie_wrong(message: Message):
    await message.answer("Iltimos, video fayl yuboring.")


@router.message(AdminAddMovie.waiting_title)
async def admin_add_movie_title(message: Message, state: FSMContext):
    data = await state.get_data()
    code = await db.generate_next_code()
    await db.add_movie(code, message.text.strip(), data["file_id"], message.from_user.id, status="approved")
    await state.clear()
    await message.answer(f"✅ Kino qo'shildi!\nNomi: {message.text.strip()}\nKodi: {code}", reply_markup=kb.admin_main_menu())


# ---------- remove movie ----------

@router.message(F.text == "➖ Kino o'chirish")
async def admin_remove_movie_start(message: Message, state: FSMContext):
    await state.set_state(AdminRemoveMovie.waiting_code)
    await message.answer("O'chiriladigan kino kodini kiriting:")


@router.message(AdminRemoveMovie.waiting_code)
async def admin_remove_movie_code(message: Message, state: FSMContext):
    await state.clear()
    ok = await db.remove_movie(message.text.strip())
    if ok:
        await message.answer("✅ Kino o'chirildi.", reply_markup=kb.admin_main_menu())
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.", reply_markup=kb.admin_main_menu())


# ---------- channels ----------

@router.message(F.text == "📢 Kanal qo'shish")
async def admin_add_channel_start(message: Message, state: FSMContext):
    await state.set_state(AdminAddChannel.waiting_channel)
    await message.answer(
        "Kanal username'ini (@kanal) yoki chat_id sini yuboring.\n"
        "Eslatma: bot o'sha kanalda admin bo'lishi shart!"
    )


@router.message(AdminAddChannel.waiting_channel)
async def admin_add_channel_finish(message: Message, state: FSMContext, bot):
    await state.clear()
    identifier = message.text.strip()
    try:
        chat = await bot.get_chat(identifier)
    except Exception:
        await message.answer("❌ Kanal topilmadi yoki bot u yerda admin emas.", reply_markup=kb.admin_main_menu())
        return
    invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
    await db.add_channel(chat.id, chat.title or identifier, invite_link)
    await message.answer(f"✅ Kanal qo'shildi: {chat.title}", reply_markup=kb.admin_main_menu())


@router.message(F.text == "📢 Kanal o'chirish")
async def admin_remove_channel_start(message: Message, state: FSMContext):
    channels = await db.get_channels()
    if not channels:
        await message.answer("Hozircha majburiy kanallar yo'q.")
        return
    lines = "\n".join(f"• {c['title']} — {c['chat_id']}" for c in channels)
    await state.set_state(AdminRemoveChannel.waiting_channel)
    await message.answer(f"Kanallar ro'yxati:\n{lines}\n\nO'chiriladigan kanalning chat_id sini yuboring:")


@router.message(AdminRemoveChannel.waiting_channel)
async def admin_remove_channel_finish(message: Message, state: FSMContext):
    await state.clear()
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("chat_id butun son bo'lishi kerak.", reply_markup=kb.admin_main_menu())
        return
    await db.remove_channel(chat_id)
    await message.answer("✅ Kanal o'chirildi.", reply_markup=kb.admin_main_menu())


# ---------- statistics ----------

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    users_count = await db.get_users_count()
    movies_count = await db.get_movies_count()
    top = await db.get_top_movies(5)
    pending = await db.get_pending_submissions()

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Foydalanuvchilar: {users_count}\n"
        f"🎬 Kinolar soni: {movies_count}\n"
        f"📥 Ko'rib chiqilmagan takliflar: {len(pending)}\n\n"
        f"🔥 <b>Eng ko'p ko'rilgan kinolar:</b>\n"
    )
    if top:
        text += "\n".join(f"{i+1}. {m['title']} — {m['views']} ko'rish ({m['code']})" for i, m in enumerate(top))
    else:
        text += "Hali ma'lumot yo'q."

    await message.answer(text, parse_mode="HTML")


# ---------- review submissions ----------

@router.message(F.text == "📥 Takliflar")
async def admin_review_submissions(message: Message):
    pending = await db.get_pending_submissions()
    if not pending:
        await message.answer("Ko'rib chiqilmagan takliflar yo'q. ✅")
        return
    for sub in pending:
        await message.answer_video(
            sub["file_id"],
            caption=f"Foydalanuvchi: {sub['user_id']}\nNomi: {sub['title']}",
            reply_markup=kb.submission_review_kb(sub["id"]),
        )


@router.callback_query(F.data.startswith("sub_approve:"))
async def approve_submission(callback: CallbackQuery):
    submission_id = int(callback.data.split(":", 1)[1])
    sub = await db.get_submission(submission_id)
    if not sub or sub["status"] != "pending":
        await callback.answer("Bu taklif allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    code = await db.generate_next_code()
    await db.add_movie(code, sub["title"], sub["file_id"], sub["user_id"], status="approved")
    await db.update_submission_status(submission_id, "approved", movie_code=code)
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ Qabul qilindi. Kod: {code}")
    await callback.bot.send_message(sub["user_id"], f"🎉 Sizning \"{sub['title']}\" kinongiz qabul qilindi! Kod: {code}")
    await callback.answer()


@router.callback_query(F.data.startswith("sub_reject:"))
async def reject_submission(callback: CallbackQuery):
    submission_id = int(callback.data.split(":", 1)[1])
    sub = await db.get_submission(submission_id)
    if not sub or sub["status"] != "pending":
        await callback.answer("Bu taklif allaqachon ko'rib chiqilgan.", show_alert=True)
        return
    await db.update_submission_status(submission_id, "rejected")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rad etildi.")
    await callback.bot.send_message(sub["user_id"], f"😔 Sizning \"{sub['title']}\" taklifingiz rad etildi.")
    await callback.answer()
