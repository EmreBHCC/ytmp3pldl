"""Arka plan guncelleme kontrolu (gunde en cok bir kez).

(a) yt-dlp'nin son release'i indirilir, SHA2-256SUMS ile dogrulanir ve bir sonraki
acilista devreye girer. (b) Uygulamanin son release'i daha yeniyse GUI'ye haber verilir;
uygulama kendi exe'sini degistirmez. Ag islevleri enjekte edilir, testler sahte GitHub kullanir.
"""
import hashlib
import json
import logging
import os
import re
import shutil
import threading
import time
import urllib.request
import zipfile

import durum
from surum import GITHUB_REPO, YTDLP_REPO, __version__

log = logging.getLogger(__name__)

KONTROL_ARALIGI = 24 * 60 * 60
API = "https://api.github.com/repos/{}/releases/latest"


class GuncellemeHatasi(Exception):
    pass


def getir_bayt(url, zaman_asimi=60) -> bytes:
    istek = urllib.request.Request(url, headers={"User-Agent": f"ytmp3pldl/{__version__}"})
    with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
        return yanit.read()


def getir_json(url) -> dict:
    return json.loads(getir_bayt(url, zaman_asimi=30))


def surum_tuple(surum) -> tuple:
    return tuple(int(p) for p in re.findall(r"\d+", surum or ""))


def daha_yeni(aday, mevcut) -> bool:
    if not mevcut:
        return True
    return surum_tuple(aday) > surum_tuple(mevcut)


def kontrol_zamani_geldi(son_kontrol, simdi, aralik=KONTROL_ARALIGI) -> bool:
    if son_kontrol is None:
        return True
    return not (0 <= simdi - son_kontrol < aralik)


def _ozet(sums_metni, ad):
    for satir in sums_metni.splitlines():
        parcalar = satir.split()
        if len(parcalar) == 2 and parcalar[1].lstrip("*") == ad:
            return parcalar[0].lower()
    raise GuncellemeHatasi(f"SHA2-256SUMS icinde {ad} yok")


def _eskileri_sil(veri_dir, tut):
    kok = os.path.join(veri_dir, "yt-dlp")
    for ad in os.listdir(kok):
        if ad not in tut:
            shutil.rmtree(os.path.join(kok, ad), ignore_errors=True)


def ytdlp_guncelle(veri_dir, mevcut, getir_json=getir_json, getir_bayt=getir_bayt, zorla=False):
    """Yeni yt-dlp indirildiyse tag'ini, gerek yoksa None dondurur.

    Dogrulama hatasinda GuncellemeHatasi; ag hatalari yukari birakilir.
    """
    surumu = getir_json(API.format(YTDLP_REPO))
    tag = surumu["tag_name"]
    if not isinstance(tag, str) or not re.fullmatch(r"\d{4}\.\d{2}\.\d{2}(\.\d+)?", tag):
        raise GuncellemeHatasi(f"gecersiz yt-dlp tag'i: {tag!r}")
    d = durum.oku(veri_dir)
    if tag in d["kara_liste"]:
        return None
    if not zorla and (tag == d["aktif"] or not daha_yeni(tag, mevcut)):
        return None
    varliklar = {v["name"]: v["browser_download_url"] for v in surumu.get("assets", [])}
    if "yt-dlp" not in varliklar or "SHA2-256SUMS" not in varliklar:
        raise GuncellemeHatasi(f"{tag} release'inde yt-dlp ya da SHA2-256SUMS yok")
    beklenen = _ozet(getir_bayt(varliklar["SHA2-256SUMS"]).decode("utf-8", "replace"), "yt-dlp")
    veri = getir_bayt(varliklar["yt-dlp"])
    if hashlib.sha256(veri).hexdigest() != beklenen:
        raise GuncellemeHatasi(f"yt-dlp {tag} SHA256 tutmadi")
    hedef = durum.ytdlp_dosyasi(veri_dir, tag)
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    gecici = hedef + ".tmp"
    with open(gecici, "wb") as f:
        f.write(veri)
    if not zipfile.is_zipfile(gecici):
        os.remove(gecici)
        raise GuncellemeHatasi(f"yt-dlp {tag} gecerli bir zip degil")
    os.replace(gecici, hedef)
    d = durum.oku(veri_dir)
    if d["aktif"] != tag:
        if d["aktif"] and d["aktif"] not in d["kara_liste"]:
            d["onceki"] = d["aktif"]
        d["aktif"] = tag
    durum.yaz(veri_dir, d)
    _eskileri_sil(veri_dir, {d["aktif"], d["onceki"], mevcut})
    log.info("yt-dlp %s indirildi, bir sonraki acilista aktif", tag)
    return tag


def uygulama_kontrol(getir_json=getir_json, mevcut=__version__):
    surumu = getir_json(API.format(GITHUB_REPO))
    tag = surumu["tag_name"].lstrip("vV")
    if daha_yeni(tag, mevcut):
        return tag, surumu["html_url"]
    return None


def kontrol_et(veri_dir, mevcut_ytdlp, getir_json=getir_json, getir_bayt=getir_bayt, simdi=time.time):
    """Gunde bir kez yt-dlp'yi gunceller; uygulamanin yeni surumu varsa (surum, url). Yukseltmez."""
    if not kontrol_zamani_geldi(durum.oku(veri_dir)["son_kontrol"], simdi()):
        return None
    try:
        ytdlp_guncelle(veri_dir, mevcut_ytdlp, getir_json, getir_bayt)
        d = durum.oku(veri_dir)
        d["son_kontrol"] = simdi()
        durum.yaz(veri_dir, d)
    except Exception:
        log.warning("yt-dlp guncelleme kontrolu basarisiz", exc_info=True)
    try:
        return uygulama_kontrol(getir_json)
    except Exception:
        log.info("uygulama surum kontrolu basarisiz", exc_info=True)
        return None


def arka_planda_calistir(veri_dir, mevcut_ytdlp, bildir):
    def calis():
        try:
            sonuc = kontrol_et(veri_dir, mevcut_ytdlp)
            if sonuc:
                bildir(*sonuc)
        except Exception:
            log.exception("guncelleyici thread'i hatayla bitti")

    thread = threading.Thread(target=calis, daemon=True, name="guncelleyici")
    thread.start()
    return thread
