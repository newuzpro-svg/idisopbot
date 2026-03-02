import os
import re
import uuid
import asyncio
import yt_dlp


DOWNLOAD_DIR = "downloads"

def ensure_download_dir():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def is_instagram_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(instagram\.com|instagr\.am)/(p|reel|tv|stories)/[\w-]+'
    return bool(re.search(pattern, url))


def is_tiktok_url(url: str) -> bool:
    pattern = r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/[\w@/\-\.]+'
    return bool(re.search(pattern, url))


def extract_url_from_text(text: str) -> str | None:
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        if is_instagram_url(url) or is_tiktok_url(url):
            return url
    return None


async def download_video(url: str) -> dict:
    ensure_download_dir()
    file_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        },
        'socket_timeout': 30,
        'retries': 3,
    }

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info

    try:
        info = await loop.run_in_executor(None, _download)
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"Yuklab bo'lmadi: {str(e)}")

    # Find the downloaded file
    downloaded_file = None
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(file_id):
            downloaded_file = os.path.join(DOWNLOAD_DIR, f)
            break

    if not downloaded_file or not os.path.exists(downloaded_file):
        raise FileNotFoundError("Fayl topilmadi")

    file_size = os.path.getsize(downloaded_file)
    # Telegram limit: 50MB
    if file_size > 50 * 1024 * 1024:
        os.remove(downloaded_file)
        raise ValueError("Video hajmi juda katta (50MB dan oshiq)")

    title = info.get('title', '') if info else ''
    uploader = info.get('uploader', '') if info else ''

    return {
        'file_path': downloaded_file,
        'title': title,
        'uploader': uploader,
        'file_size': file_size,
    }


def cleanup_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
