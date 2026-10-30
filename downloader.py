"""yt-dlp tabanli indirme mantigi. GUI'den bagimsiz, tekrar kullanilabilir katman."""
import os
import re
import yt_dlp
import imageio_ffmpeg

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

INVALID_CHARS = re.compile(r'[\\/*?:"<>|]')


def sanitize_filename(name: str) -> str:
    return INVALID_CHARS.sub("_", name).strip()


def fetch_entries(url: str):
    """Verilen URL bir video ise tek elemanli, playlist ise tum elemanlarin
    listesini dondurur. Donen deger: (items, playlist_title_or_None)."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise ValueError("Video/playlist bilgisi alinamadi. URL'yi kontrol edin.")

    items = []
    playlist_title = None

    if info.get("entries"):
        playlist_title = info.get("title")
        for entry in info["entries"]:
            if entry is None:
                continue
            video_id = entry.get("id")
            items.append({
                "id": video_id,
                "title": entry.get("title") or video_id or "Bilinmeyen",
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                "duration": entry.get("duration"),
            })
    else:
        items.append({
            "id": info.get("id"),
            "title": info.get("title") or "Bilinmeyen",
            "url": info.get("webpage_url") or url,
            "duration": info.get("duration"),
        })

    if not items:
        raise ValueError("Indirilebilecek video bulunamadi.")

    return items, playlist_title


def build_ydl_opts(fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    target_dir = os.path.join(output_dir, sanitize_filename(subfolder)) if subfolder else output_dir
    os.makedirs(target_dir, exist_ok=True)
    outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "ffmpeg_location": FFMPEG_PATH,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "ignoreerrors": False,
        "restrictfilenames": False,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "retries": 15,
        "fragment_retries": 15,
        "socket_timeout": 30,
    }

    if fmt == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        }]
    else:
        if quality == "best":
            opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            opts["format"] = (
                f"bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/"
                f"best[ext=mp4][height<={quality}]/best"
            )
        opts["merge_output_format"] = "mp4"

    return opts


def download_item(url: str, fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    opts = build_ydl_opts(fmt, quality, output_dir, progress_hook, subfolder)
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
