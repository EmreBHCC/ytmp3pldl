"""YouTube Indirici - giris noktasi.

Sira: cikis akislari -> log -> yt-dlp yukleme -> (oz test | GUI + arka plan guncelleyici).
yt_dlp'yi import eden moduller (downloader, gui) yalnizca yuklemeden SONRA import edilir.

Gelistirme:
    pip install -r requirements-dev.txt
    python main.py
"""
import json
import logging
import os
import sys
import tempfile
import traceback
from dataclasses import asdict
from logging.handlers import RotatingFileHandler

import yollar
import ytdlp_yukleyici
from surum import __version__

OZ_TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

log = logging.getLogger("main")


def akislari_duzelt():
    # console=False paketli exe'de stdout/stderr None olur; yazan kutuphaneler cokmesin.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def log_kur(veri_dir):
    isleyici = RotatingFileHandler(os.path.join(veri_dir, "log.txt"), maxBytes=1_000_000,
                                   backupCount=2, encoding="utf-8")
    isleyici.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[isleyici])


def json_yaz(yol, veri):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


def oz_test(veri_dir, yukleme, cikti):
    """Kapi icin, GUI acmadan: yt-dlp guncellemesini zorlar, kisa videoyu MP3 indirir."""
    sonuc = {"ok": False, "yukleme": asdict(yukleme), "deno": yollar.deno_yolu()}
    try:
        import downloader
        import guncelleyici
        sonuc["guncellenen"] = guncelleyici.ytdlp_guncelle(veri_dir, yukleme.surum, zorla=True)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as klasor:
            bilgi = downloader.download_item(OZ_TEST_URL, "mp3", "192", klasor, lambda d: None)
            mp3ler = [os.path.join(klasor, ad) for ad in os.listdir(klasor) if ad.endswith(".mp3")]
            sonuc["mp3_bayt"] = os.path.getsize(mp3ler[0]) if mp3ler else 0
        sonuc["formatlar"] = str(bilgi.get("format_id", "")).split("+")
        sonuc["ok"] = sonuc["mp3_bayt"] > 0
    except Exception:
        sonuc["hata"] = traceback.format_exc()
        log.error("oz test basarisiz:\n%s", sonuc["hata"])
    json_yaz(cikti, sonuc)
    return sonuc["ok"]


def hata_goster(metin):
    from tkinter import Tk, messagebox
    kok = Tk()
    kok.withdraw()
    messagebox.showerror("YouTube İndirici", metin)
    kok.destroy()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    akislari_duzelt()
    veri_dir = yollar.veri_klasoru()
    log_kur(veri_dir)
    log.info("ytmp3pldl %s basliyor", __version__)
    yukleme = ytdlp_yukleyici.yukle(veri_dir, yollar.yedek_ytdlp_yolu())
    log.info("yt-dlp yuklendi: %s", yukleme)

    if len(argv) == 2 and argv[0] == "--oz-test-yukle":
        modul = sys.modules.get("yt_dlp")
        json_yaz(argv[1], {"ok": yukleme.kaynak is not None, "yukleme": asdict(yukleme),
                           "yt_dlp_dosyasi": getattr(modul, "__file__", None)})
        return 0 if yukleme.kaynak else 1
    if len(argv) == 2 and argv[0] == "--oz-test":
        return 0 if oz_test(veri_dir, yukleme, argv[1]) else 1

    if yukleme.kaynak is None:
        hata_goster("İndirme bileşeni (yt-dlp) yüklenemedi.\n\nUygulamayı yeniden kurun. "
                    f"Sorun sürerse şu dosyayı gönderin:\n{os.path.join(veri_dir, 'log.txt')}")
        return 1

    import guncelleyici
    from gui import App

    app = App(ytdlp_surum=yukleme.surum, python_yetersiz=yukleme.python_yetersiz)
    guncelleyici.arka_planda_calistir(
        veri_dir, yukleme.surum, lambda s, u: app.after(0, app.yeni_surum_goster, s, u))
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
