import os
import logging
import threading
import time
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from hydrogram import Client, filters
from hydrogram.enums import ParseMode, ChatAction
from hydrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from downloader import (
    download_video,
    extract_url_from_text,
    is_instagram_url,
    is_youtube_url,
    cleanup_file,
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "SaveVideoBot")

CAPTION_TEMPLATE = (
    "{title}"
    "\n\n"
    "📥 <a href='https://t.me/{bot_username}'>@{bot_username}</a> orqali ko'chirildi"
)

WELCOME_TEXT = (
    "👋 <b>Salom! Men video yuklovchi botman.</b>\n\n"
    "📲 Havola yuboring — videoni yuklab beraman.\n\n"
    "✅ <b>Qo'llab-quvvatlanadi:</b>\n"
    "• Instagram Reels, Posts, Stories\n"
    "• TikTok Videos\n"
    "• YouTube Videos & Shorts\n\n"
    "🔗 Havola yuboring!"
)

HELP_TEXT = (
    "📖 <b>Yordam</b>\n\n"
    "<b>Qanday ishlatish:</b>\n"
    "• Havola yuboring — bot avtomatik yuklab jo'natadi\n\n"
    "<b>Misollar:</b>\n"
    "• <code>https://www.instagram.com/reel/xxxxx/</code>\n"
    "• <code>https://vm.tiktok.com/xxxxx/</code>\n"
    "• <code>https://youtube.com/shorts/xxxxx</code>\n"
    "• <code>https://youtu.be/xxxxx</code>\n\n"
    "<b>Muammo bo'lsa:</b>\n"
    "• Havola to'g'ri ekanligini tekshiring\n"
    "• Video ochiq (public) bo'lishi kerak\n\n"
    "🤖 Bot: @{bot_username}"
)

bot = Client(
    "idisopbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)


@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Yordam", callback_data="help"),
         InlineKeyboardButton("📥 Yuklab ko'ring", callback_data="example")]
    ])
    await message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    await message.reply_text(
        HELP_TEXT.format(bot_username=BOT_USERNAME),
        parse_mode=ParseMode.HTML,
    )


@bot.on_callback_query()
async def button_callback(client: Client, query: CallbackQuery):
    await query.answer()
    if query.data == "help":
        await query.message.reply_text(
            HELP_TEXT.format(bot_username=BOT_USERNAME),
            parse_mode=ParseMode.HTML,
        )
    elif query.data == "example":
        await query.message.reply_text(
            "🔗 Havola yuboring:\n\n"
            "<code>https://www.instagram.com/reel/xxxxx/</code>\n"
            "<code>https://vm.tiktok.com/xxxxx/</code>\n"
            "<code>https://youtu.be/xxxxx</code>",
            parse_mode=ParseMode.HTML,
        )


@bot.on_message(filters.text & ~filters.command(["start", "help"]))
async def handle_message(client: Client, message: Message):
    text = message.text or message.caption or ""
    url = extract_url_from_text(text)

    if not url:
        await message.reply_text(
            "❌ Havola topilmadi.\n\n"
            "Instagram, TikTok yoki YouTube havolasini yuboring.",
            parse_mode=ParseMode.HTML,
        )
        return

    if is_instagram_url(url):
        platform = "Instagram"
        platform_emoji = "📸"
    elif is_youtube_url(url):
        platform = "YouTube"
        platform_emoji = "▶️"
    else:
        platform = "TikTok"
        platform_emoji = "🎵"

    status_msg = await message.reply_text(
        f"{platform_emoji} <b>{platform}</b> video yuklanmoqda...\n"
        "⏳ Iltimos kuting...",
        parse_mode=ParseMode.HTML,
    )

    await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    file_path = None
    try:
        result = await download_video(url)
        file_path = result['file_path']

        title = result.get('title', '').strip()
        uploader = result.get('uploader', '').strip()

        title_line = ""
        if title and title.lower() not in ('', 'none'):
            short_title = title[:80] + "..." if len(title) > 80 else title
            title_line = f"🎬 <b>{short_title}</b>"
        if uploader:
            title_line += f"\n👤 {uploader}" if title_line else f"👤 {uploader}"

        caption = CAPTION_TEMPLATE.format(
            title=title_line,
            bot_username=BOT_USERNAME,
        ).strip()

        await status_msg.edit_text(f"{platform_emoji} Video jo'natilmoqda...")

        await message.reply_video(
            video=file_path,
            caption=caption,
            parse_mode=ParseMode.HTML,
            supports_streaming=True,
        )

        await status_msg.delete()

    except ValueError as e:
        error_text = str(e)
        if "Yuklab bo'lmadi" in error_text:
            msg = (
                "❌ Videoni yuklab bo'lmadi.\n\n"
                "Video yopiq (private) yoki havola noto'g'ri bo'lishi mumkin."
            )
        else:
            msg = f"❌ Xatolik: {error_text}"
        await status_msg.edit_text(msg, parse_mode=ParseMode.HTML)

    except FileNotFoundError:
        await status_msg.edit_text(
            "❌ Video yuklanmadi. Iltimos qayta urinib ko'ring."
        )

    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ Kutilmagan xatolik yuz berdi.\n"
            "Iltimos bir oz kutib qayta urinib ko'ring."
        )

    finally:
        if file_path:
            cleanup_file(file_path)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health check server port {port} da ishlamoqda")
    server.serve_forever()


def run_self_ping():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url, timeout=10)
            logger.info("Self-ping OK")
        except Exception as e:
            logger.warning(f"Self-ping xato: {e}")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")
    if not API_ID or not API_HASH:
        raise ValueError("API_ID va API_HASH topilmadi!")

    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    ping_thread = threading.Thread(target=run_self_ping, daemon=True)
    ping_thread.start()

    logger.info(f"Save Bot ishga tushdi! @{BOT_USERNAME}")
    bot.run()


if __name__ == "__main__":
    main()
