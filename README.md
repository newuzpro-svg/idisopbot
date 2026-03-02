# 📥 Save Bot — Instagram & TikTok Video Yuklovchi

## O'rnatish

### 1. Python o'rnatish
Python 3.10+ versiyasi kerak: https://python.org

### 2. Kerakli kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. FFmpeg o'rnatish (majburiy)
- Windows: https://ffmpeg.org/download.html dan yuklab, PATH ga qo'shing
- Yoki: `choco install ffmpeg` (Chocolatey orqali)

### 4. Bot tokenini olish
1. Telegramda @BotFather ga boring
2. `/newbot` yuboring
3. Bot nomini kiriting: `Save Bot`
4. Bot username ni kiriting: `SaveVideoBot` (yoki boshqa)
5. Token olasiz: `123456:ABC-DEF...`

### 5. .env faylini sozlash
`.env` faylini oching va token ni kiriting:
```
BOT_TOKEN=123456:ABC-DEF...
BOT_USERNAME=SaveVideoBot
```

### 6. Botni ishga tushirish
```bash
python bot.py
```

---

## Xususiyatlari
- ✅ Instagram Reels, Posts yuklab olish
- ✅ TikTok videolarni yuklab olish
- ✅ Har bir video caption da bot linki bo'ladi
- ✅ Videoni forward qilganda ham bot linki ko'rinadi
- ✅ 50MB gacha video qo'llab-quvvatlanadi

## Fayl tuzilmasi
```
save bot telegram/
├── bot.py          # Asosiy bot kodi
├── downloader.py   # Video yuklovchi
├── requirements.txt
├── .env            # Bot token (yashirin)
└── downloads/      # Vaqtinchalik fayllar (avtomatik tozalanadi)
```
