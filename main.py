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
import threading
import traceback
from dataclasses import asdict
from logging.handlers import RotatingFileHandler

import yollar
import ytdlp_yukleyici
from surum import __version__

OZ_TEST_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

log = logging.getLogger("main")

_veri_dir = None  # calistir() cokme mesajinda log yolunu gostermek icin


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


def _veri_klasoru_guvenli():
    """Veri klasoru olusturulamazsa gecici klasore duser; uygulama her kosulda acilir."""
    global _veri_dir
    try:
        _veri_dir = yollar.veri_klasoru()
    except OSError:
        _veri_dir = os.path.join(tempfile.gettempdir(), "ytmp3pldl")
        try:
            os.makedirs(_veri_dir, exist_ok=True)
        except OSError:
            pass
    return _veri_dir


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    akislari_duzelt()
    veri_dir = _veri_klasoru_guvenli()
    try:
        log_kur(veri_dir)
    except OSError:
        pass  # log'suz devam; uygulama yine acilir
    log.info("ytmp3pldl %s basliyor", __version__)
    yukleme = ytdlp_yukleyici.yukle(
        veri_dir, yollar.yedek_ytdlp_yolu(), uygulama_surum=__version__)
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
    app.report_callback_exception = lambda tur, deger, iz: log.error(
        "Tk callback hatasi", exc_info=(tur, deger, iz))
    threading.excepthook = lambda a: log.error(
        "thread hatasi: %s", a.thread.name if a.thread else "?",
        exc_info=(a.exc_type, a.exc_value, a.exc_traceback))
    # Thread mainloop basladiktan sonra acilir; Tcl'e yalniz kuyruk uzerinden dokunur.
    app.after(0, lambda: guncelleyici.arka_planda_calistir(
        veri_dir, yukleme.surum, lambda s, u: app.update_queue.put(("__surum__", s, u))))
    app.mainloop()
    return 0


def calistir(argv=None):
    """main'i sarar: yakalanmayan hata log'a yazilir, Turkce diyalog gosterilir, cikis kodu 1."""
    try:
        return main(argv)
    except Exception:
        try:
            log.exception("uygulama acilamadi")
        except Exception:
            pass
        log_yolu = os.path.join(_veri_dir or os.path.join(tempfile.gettempdir(), "ytmp3pldl"),
                                "log.txt")
        try:
            hata_goster("Uygulama açılamadı.\n\nUygulamayı yeniden kurun. Sorun sürerse şu "
                        f"dosyayı gönderin:\n{log_yolu}")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(calistir())
