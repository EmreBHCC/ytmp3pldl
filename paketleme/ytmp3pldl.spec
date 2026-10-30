# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir. yt-dlp analiz edilir (bagimliliklari ve kullandigi stdlib paketlensin)
# ama gomulu modul olarak paketlenmez: PyInstaller'in gomulu yukleyicisi sys.path'ten once
# gelir ve indirilen guncel yt-dlp'yi golgelerdi. yt-dlp, vendor/yt-dlp zip'inden
# ytdlp_yukleyici ile yuklenir.
import os

from PyInstaller.utils.hooks import collect_data_files

KOK = os.path.dirname(SPECPATH)
VENDOR = os.path.join(KOK, "vendor")
DISLA = ("yt_dlp", "yt_dlp_ejs")

# Yeni yt-dlp surumleri bugunku surumun kullanmadigi stdlib modullerini isteyebilir.
EK_STDLIB = [
    "asyncio", "bz2", "concurrent.futures", "csv", "ctypes.wintypes", "getpass", "hmac",
    "http.cookiejar", "http.cookies", "lzma", "netrc", "secrets", "shlex", "sqlite3",
    "unicodedata", "uuid", "xml.dom.minidom", "xml.etree.ElementTree", "zipimport",
]


def ytdlp_mi(ad):
    ad = ad.replace("\\", "/")
    return any(ad == d or ad.startswith((d + ".", d + "/")) for d in DISLA)


a = Analysis(
    [os.path.join(KOK, "main.py")],
    pathex=[KOK],
    datas=[
        (os.path.join(VENDOR, "yt-dlp"), "vendor"),
        (os.path.join(VENDOR, "deno.exe"), "vendor"),
        *collect_data_files("customtkinter"),
        *collect_data_files("imageio_ffmpeg"),
    ],
    hiddenimports=["yt_dlp", *EK_STDLIB],
)
a.pure = [e for e in a.pure if not ytdlp_mi(e[0])]
a.datas = [e for e in a.datas if not ytdlp_mi(e[0])]

pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ytmp3pldl", console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="ytmp3pldl", upx=False)
