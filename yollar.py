"""Veri ve paket klasorleri. Paketli (PyInstaller) ve gelistirme calismasinda ayni arayuz."""
import os
import shutil
import sys

UYGULAMA_ADI = "ytmp3pldl"


def veri_klasoru() -> str:
    """YTMP3PLDL_VERI (kapi/test) ya da %LOCALAPPDATA%\\ytmp3pldl. Yoksa olusturur."""
    yol = os.environ.get("YTMP3PLDL_VERI")
    if not yol:
        taban = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        yol = os.path.join(taban, UYGULAMA_ADI)
    os.makedirs(yol, exist_ok=True)
    return yol


def paket_klasoru() -> str:
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def yedek_ytdlp_yolu() -> str:
    return os.path.join(paket_klasoru(), "vendor", "yt-dlp")


def deno_yolu() -> str | None:
    yol = os.path.join(paket_klasoru(), "vendor", "deno.exe")
    if os.path.isfile(yol):
        return yol
    return shutil.which("deno")
