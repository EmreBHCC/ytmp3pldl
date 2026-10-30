"""durum.json: aktif/onceki yt-dlp surumu, kara liste, son kontrol zamani. Atomik yazilir."""
import json
import os

ANAHTARLAR = ("aktif", "onceki", "kara_liste", "son_kontrol", "python_yetersiz", "uygulama_surum")


def _yol(veri_dir):
    return os.path.join(veri_dir, "durum.json")


def _str_ya_da_none(v):
    return v if isinstance(v, str) else None


def oku(veri_dir) -> dict:
    durum = {"aktif": None, "onceki": None, "kara_liste": [], "son_kontrol": None,
             "python_yetersiz": None, "uygulama_surum": None}
    try:
        with open(_yol(veri_dir), encoding="utf-8") as f:
            veri = json.load(f)
    except (OSError, ValueError):
        return durum
    if isinstance(veri, dict):
        durum.update({k: veri[k] for k in ANAHTARLAR if k in veri})
    for k in ("aktif", "onceki", "python_yetersiz", "uygulama_surum"):
        durum[k] = _str_ya_da_none(durum[k])
    if not isinstance(durum["kara_liste"], list):
        durum["kara_liste"] = []
    son = durum["son_kontrol"]
    if isinstance(son, bool) or not isinstance(son, (int, float)):
        durum["son_kontrol"] = None
    return durum


def yaz(veri_dir, durum: dict) -> None:
    os.makedirs(veri_dir, exist_ok=True)
    gecici = _yol(veri_dir) + ".tmp"
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)
    os.replace(gecici, _yol(veri_dir))


def ytdlp_dosyasi(veri_dir, surum) -> str:
    return os.path.join(veri_dir, "yt-dlp", surum, "yt-dlp")
