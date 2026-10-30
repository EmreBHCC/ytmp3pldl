"""yt-dlp tabanli indirme mantigi. GUI'den bagimsiz, tekrar kullanilabilir katman.

yt_dlp bu modul import edilmeden once ytdlp_yukleyici ile yuklenmis olmalidir.
"""
import os
import re
import yt_dlp
import imageio_ffmpeg

import yollar

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

INVALID_CHARS = re.compile(r'[\\/*?:"<>|]')


def sanitize_filename(name: str) -> str:
    return INVALID_CHARS.sub("_", name).strip()


def _temel_ayarlar():
    """YouTube'un varsayilan istemcileri JS cozumu ister; Deno varsa yt-dlp'ye verilir."""
    opts = {"quiet": True, "no_warnings": True}
    deno = yollar.deno_yolu()
    if deno:
        opts["js_runtimes"] = {"deno": {"path": deno}}
    return opts


def fetch_entries(url: str):
    """Verilen URL bir video ise tek elemanli, playlist ise tum elemanlarin
    listesini dondurur. Donen deger: (items, playlist_title_or_None)."""
    ydl_opts = {
        **_temel_ayarlar(),
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
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


def video_formati(quality: str) -> str:
    """H.264 (avc1) once: AV1/VP9 eski oynaticilarda acilmaz."""
    sinir = "" if quality == "best" else f"[height<={quality}]"
    return (
        f"bestvideo[vcodec^=avc1]{sinir}+bestaudio[ext=m4a]/"
        f"bestvideo[ext=mp4]{sinir}+bestaudio[ext=m4a]/"
        f"best[ext=mp4]{sinir}/best"
    )


def build_ydl_opts(fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    target_dir = os.path.join(output_dir, sanitize_filename(subfolder)) if subfolder else output_dir
    os.makedirs(target_dir, exist_ok=True)
    outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")

    opts = {
        **_temel_ayarlar(),
        "outtmpl": outtmpl,
        "ffmpeg_location": FFMPEG_PATH,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "ignoreerrors": False,
        "restrictfilenames": False,
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
        opts["format"] = video_formati(quality)
        opts["merge_output_format"] = "mp4"

    return opts


def download_item(url: str, fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    """Indirir ve yt-dlp info sozlugunu dondurur (format_id: kullanilan kaynak formatlar)."""
    opts = build_ydl_opts(fmt, quality, output_dir, progress_hook, subfolder)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)


_HATA_ESLEME = (
    (("getaddrinfo", "urlopen error", "timed out", "connection", "network is unreachable",
      "unable to download api page"),
     "İnternet bağlantısı yok gibi görünüyor. Bağlantıyı kontrol edip tekrar deneyin."),
    (("private video", "video unavailable", "has been removed", "not available"),
     "Video kaldırılmış ya da gizli."),
    (("sign in to confirm your age", "age-restricted"),
     "Yaş doğrulaması isteyen videolar indirilemiyor."),
    (("is not a valid url", "unsupported url"),
     "Bu bir YouTube linki değil gibi görünüyor."),
)
_HATA_DIGER = "Bu video indirilemedi. Sorun sürerse log.txt dosyasını gönderin."


def hata_metni(e) -> str:
    """yt-dlp hatasini kullaniciya gosterilecek Turkce, eylem soyleyen metne cevirir."""
    ham = str(e).lower()
    for ipuclari, metin in _HATA_ESLEME:
        if any(i in ham for i in ipuclari):
            return metin
    return _HATA_DIGER
