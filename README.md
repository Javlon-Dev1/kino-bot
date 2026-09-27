# Kino Bot

## O'rnatish

```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini oching va to'ldiring:
- `BOT_TOKEN` — @BotFather dan olingan token
- `ADMIN_IDS` — admin(lar)ning Telegram user_id raqami(lari), vergul bilan ajratilgan

## Ishga tushirish

```bash
python main.py
```

## Muhim eslatmalar

1. **Majburiy obuna kanallari** uchun bot o'sha kanalda **admin** bo'lishi shart —
   aks holda `get_chat_member` orqali obunani tekshira olmaydi.
2. Admin panelga kirish: botga `/admin` buyrug'ini yozing (faqat `ADMIN_IDS`
   ro'yxatidagilar uchun ishlaydi).
3. Kino kodlari avtomatik generatsiya qilinadi (1001, 1002, ...).
4. Video fayllar Telegram serverida saqlanadi — bazada faqat `file_id` saqlanadi,
   shuning uchun baza juda kichik bo'ladi.
5. Statistika bo'limida eng ko'p ko'rilgan 5 ta kino va umumiy sonlar chiqadi.

## Loyihaning tuzilishi

```
kino_bot/
├── main.py            # bot ishga tushadigan joy
├── config.py          # token, admin ID lar
├── database.py        # SQLite bilan ishlash funksiyalari
├── keyboards.py        # inline/reply klaviaturalar
├── states.py           # FSM holatlar
├── middlewares.py      # majburiy obuna tekshiruvi
└── handlers/
    ├── user.py         # foydalanuvchi paneli
    └── admin.py        # admin paneli
```

## Keyingi qadamlar (o'zing qo'shishing mumkin bo'lgan narsalar)

- Kino qidiruvda sahifalash (pagination), agar natijalar 10 tadan ko'p bo'lsa
- Kinolarni janr/yil bo'yicha filtrlash
- "📥 Takliflar" bo'limida bitta xabar ichida oldinga/orqaga navigatsiya
- Statistikani kunlik/haftalik grafik shaklida ko'rsatish
