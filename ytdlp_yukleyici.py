"""yt-dlp'yi `import yt_dlp`'den once dogru kaynaktan yukler.

Sira: indirilmis aktif -> indirilmis onceki -> paketteki yedek -> sistemde kurulu.
yt-dlp release dosyasi bir zip'tir; yolu sys.path'e konunca zipimport ile yuklenir.
Import edilemeyen indirilmis surum kara listeye alinir ve bir daha denenmez.
"""
import importlib
import logging
import os
import sys
from dataclasses import dataclass

import durum

log = logging.getLogger(__name__)

PYTHON_IPUCU = "unsupported version of Python"


@dataclass
class YuklemeSonucu:
    kaynak: str | None  # aktif / onceki / yedek / sistem / None
    surum: str | None
    python_yetersiz: bool = False


def _temizle(modul):
    for ad in list(sys.modules):
        if ad == modul or ad.startswith((modul + ".", modul + "_")):
            del sys.modules[ad]


def _yol_altinda(dosya, yol):
    """dosya yol'un kendisi ya da altindaysa True. Windows'ta / ve \\ farkini ve harf durumunu yok sayar."""
    if not dosya:
        return False
    n_dosya = os.path.normcase(os.path.abspath(dosya))
    n_yol = os.path.normcase(os.path.abspath(yol))
    return n_dosya == n_yol or n_dosya.startswith(n_yol + os.sep)


def _dene(yol, modul):
    """yol None ise sys.path'e dokunmaz. Basarida surumu dondurur, hatada temizleyip yukseltir."""
    if yol is not None:
        sys.path.insert(0, yol)
    try:
        importlib.invalidate_caches()
        paket = importlib.import_module(modul)
        if yol is not None and not _yol_altinda(getattr(paket, "__file__", None), yol):
            raise ImportError(f"{modul} {yol} disinda yuklendi: {getattr(paket, '__file__', None)}")
        return importlib.import_module(modul + ".version").__version__
    except Exception:
        if yol is not None:
            while yol in sys.path:
                sys.path.remove(yol)
            sys.path_importer_cache.pop(yol, None)
        _temizle(modul)
        raise


def _python_sebebi(hata):
    return isinstance(hata, SyntaxError) or PYTHON_IPUCU in str(hata)


def yukle(veri_dir, yedek_yolu, modul="yt_dlp", uygulama_surum=None) -> YuklemeSonucu:
    d = durum.oku(veri_dir)
    if uygulama_surum is not None and d["uygulama_surum"] != uygulama_surum:
        # Yeni uygulama surumu (belki yeni Python): kara liste ve bayrak yeniden denenir.
        d["kara_liste"] = []
        d["python_yetersiz"] = None
        d["uygulama_surum"] = uygulama_surum
        try:
            durum.yaz(veri_dir, d)
        except OSError as yazma_hatasi:
            log.warning("durum yazilamadi: %r", yazma_hatasi)
    python_yetersiz = bool(d["python_yetersiz"])
    for kaynak in ("aktif", "onceki"):
        surum = d[kaynak]
        if not surum or surum in d["kara_liste"]:
            continue
        yol = durum.ytdlp_dosyasi(veri_dir, surum)
        if not os.path.isfile(yol):
            continue
        try:
            return YuklemeSonucu(kaynak, _dene(yol, modul), python_yetersiz)
        except Exception as hata:
            log.warning("yt-dlp %s yuklenemedi, kara listeye: %r", surum, hata)
            if _python_sebebi(hata):
                python_yetersiz = True
                d["python_yetersiz"] = surum
            d["kara_liste"].append(surum)
            try:
                durum.yaz(veri_dir, d)
            except OSError as yazma_hatasi:
                log.warning("kara liste yazilamadi, bu calistirmada gecerli: %r", yazma_hatasi)
    for kaynak, yol in (("yedek", yedek_yolu), ("sistem", None)):
        if yol is not None and not os.path.isfile(yol):
            continue
        try:
            return YuklemeSonucu(kaynak, _dene(yol, modul), python_yetersiz)
        except Exception as hata:
            log.warning("yt-dlp (%s) yuklenemedi: %r", kaynak, hata)
    return YuklemeSonucu(None, None, python_yetersiz)
