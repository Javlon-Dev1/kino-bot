from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

import database as db
import keyboards as kb
from states import UserSearchByCode, UserSearchByTitle, UserSubmitMovie
from middlewares import is_subscribed

router = Router()


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    ok, missing = await is_subscribed(callback.bot, callback.from_user.id)
    if ok:
        await callback.message.delete()
        await callback.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.", reply_markup=kb.user_main_menu())
    else:
        await callback.answer("Hali barcha kanallarga obuna bo'lmadingiz. ❌", show_alert=True)


@router.message(CommandStart())
async def start(message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "Salom! Kino botga xush kelibsiz. 🎬\nQuyidagi menyudan foydalaning:",
        reply_markup=kb.user_main_menu(),
    )


# ---------- search by code ----------

@router.message(F.text == "🔑 Kod orqali qidirish")
async def ask_code(message: Message, state: FSMContext):
    await state.set_state(UserSearchByCode.waiting_code)
    await message.answer("Kino kodini kiriting (masalan: 1001):")


@router.message(UserSearchByCode.waiting_code)
async def find_by_code(message: Message, state: FSMContext):
    await state.clear()
    movie = await db.get_movie_by_code(message.text.strip())
    if not movie:
        await message.answer("Bunday kodli kino topilmadi. ❌")
        return
    await db.increment_views(movie["id"])
    await message.answer_video(movie["file_id"], caption=f"🎬 {movie['title']}\nKod: {movie['code']}")


# ---------- search by title ----------

@router.message(F.text == "🔍 Nomi orqali qidirish")
async def ask_title(message: Message, state: FSMContext):
    await state.set_state(UserSearchByTitle.waiting_query)
    await message.answer("Kino nomini (yoki bir qismini) kiriting:")


@router.message(UserSearchByTitle.waiting_query)
async def find_by_title(message: Message, state: FSMContext):
    await state.clear()
    results = await db.search_movies_by_title(message.text.strip())
    if not results:
        await message.answer("Hech narsa topilmadi. Boshqa so'z bilan urinib ko'ring. ❌")
        return
    await message.answer("Topilgan natijalar:", reply_markup=kb.search_results_kb(results))


@router.callback_query(F.data.startswith("getmovie:"))
async def send_movie_from_search(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    movie = await db.get_movie_by_code(code)
    if not movie:
        await callback.answer("Kino topilmadi.", show_alert=True)
        return
    await db.increment_views(movie["id"])
    await callback.message.answer_video(movie["file_id"], caption=f"🎬 {movie['title']}\nKod: {movie['code']}")
    await callback.answer()


# ---------- submit a movie (user proposes a movie) ----------

@router.message(F.text == "➕ Kino qo'shish")
async def ask_submit_video(message: Message, state: FSMContext):
    await state.set_state(UserSubmitMovie.waiting_video)
    await message.answer("Kino videosini (fayl sifatida) yuboring:")


@router.message(UserSubmitMovie.waiting_video, F.video)
async def receive_submit_video(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(UserSubmitMovie.waiting_title)
    await message.answer("Endi kino nomini kiriting:")


@router.message(UserSubmitMovie.waiting_video)
async def wrong_video(message: Message):
    await message.answer("Iltimos, video fayl yuboring.")


@router.message(UserSubmitMovie.waiting_title)
async def receive_submit_title(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_submission(message.from_user.id, message.text.strip(), data["file_id"])
    await state.clear()
    await message.answer(
        "✅ Taklifingiz qabul qilindi va admin tomonidan ko'rib chiqiladi.",
        reply_markup=kb.user_main_menu(),
    )


# ---------- my submissions ----------

@router.message(F.text == "🎬 Men qo'shgan kinolar")
async def my_submissions(message: Message):
    subs = await db.get_user_submissions(message.from_user.id)
    if not subs:
        await message.answer("Siz hali kino qo'shmagansiz.")
        return
    status_map = {"pending": "⏳ Tekshirilmoqda", "approved": "✅ Qabul qilindi", "rejected": "❌ Rad etildi"}
    lines = [f"• {s['title']} — {status_map.get(s['status'], s['status'])}" for s in subs]
    await message.answer("Sizning takliflaringiz:\n\n" + "\n".join(lines))
