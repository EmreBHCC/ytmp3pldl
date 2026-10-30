import hashlib
import io
import os
import zipfile

import pytest

import durum
import guncelleyici as g

TAG = "2026.10.26"
SAYFA = "https://github.com/EmreBHCC/ytmp3pldl/releases/tag/"


def zip_bayt():
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("yt_dlp/__init__.py", "")
    return b.getvalue()


class SahteGitHub:
    def __init__(self, tag=TAG, icerik=None, ozet=None, uygulama_tag="v1.0.0", hata=None):
        self.tag, self.uygulama_tag, self.hata = tag, uygulama_tag, hata
        self.icerik = zip_bayt() if icerik is None else icerik
        ozet = hashlib.sha256(self.icerik).hexdigest() if ozet is None else ozet
        self.sums = f"{ozet}  yt-dlp\n{'0' * 64}  yt-dlp.exe\n".encode()
        self.istekler = []

    def json(self, url):
        self.istekler.append(url)
        if self.hata:
            raise self.hata
        if "yt-dlp/yt-dlp" in url:
            return {"tag_name": self.tag, "assets": [
                {"name": "yt-dlp", "browser_download_url": "https://x/yt-dlp"},
                {"name": "yt-dlp.exe", "browser_download_url": "https://x/yt-dlp.exe"},
                {"name": "SHA2-256SUMS", "browser_download_url": "https://x/SHA2-256SUMS"}]}
        return {"tag_name": self.uygulama_tag, "html_url": SAYFA + self.uygulama_tag}

    def bayt(self, url):
        self.istekler.append(url)
        return self.sums if url.endswith("SHA2-256SUMS") else self.icerik


def guncelle(veri, gh, mevcut="2026.08.19", **kw):
    return g.ytdlp_guncelle(str(veri), mevcut, gh.json, gh.bayt, **kw)


def klasorler(veri):
    kok = veri / "yt-dlp"
    return sorted(os.listdir(kok)) if kok.exists() else []


def test_surum_karsilastirma():
    assert g.surum_tuple("2026.10.26") == (2026, 10, 26)
    assert g.surum_tuple("v1.2.0") == (1, 2, 0)
    assert g.daha_yeni("2026.10.26", "2026.8.19")
    assert not g.daha_yeni("2026.10.26", "2026.10.26")
    assert g.daha_yeni("1.0.1", "1.0.0")
    assert g.daha_yeni("2026.01.01", None)


def test_kontrol_zamani():
    assert g.kontrol_zamani_geldi(None, 1000)
    assert not g.kontrol_zamani_geldi(1000, 1000 + 86399)
    assert g.kontrol_zamani_geldi(1000, 1000 + 86400)
    assert g.kontrol_zamani_geldi(5000, 1000)  # saat geri alinmis


def test_yeni_surum_indirilir_ve_aktif_olur(tmp_path):
    assert guncelle(tmp_path, SahteGitHub()) == TAG
    assert (tmp_path / "yt-dlp" / TAG / "yt-dlp").read_bytes() == zip_bayt()
    assert not (tmp_path / "yt-dlp" / TAG / "yt-dlp.tmp").exists()
    d = durum.oku(str(tmp_path))
    assert (d["aktif"], d["onceki"]) == (TAG, None)


def test_ayni_surum_indirilmez(tmp_path):
    gh = SahteGitHub()
    assert guncelle(tmp_path, gh, mevcut=TAG) is None
    assert gh.istekler == ["https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"]


def test_zaten_aktif_bekleyen_tekrar_indirilmez(tmp_path):
    durum.yaz(str(tmp_path), {**durum.oku(str(tmp_path)), "aktif": TAG})
    assert guncelle(tmp_path, SahteGitHub()) is None


def test_zorla_ayni_surumu_indirir(tmp_path):
    assert guncelle(tmp_path, SahteGitHub(), mevcut=TAG, zorla=True) == TAG
    assert durum.oku(str(tmp_path))["aktif"] == TAG


def test_hash_tutmazsa_reddedilir(tmp_path):
    with pytest.raises(g.GuncellemeHatasi):
        guncelle(tmp_path, SahteGitHub(ozet="0" * 64))
    assert not (tmp_path / "yt-dlp" / TAG / "yt-dlp").exists()
    assert not (tmp_path / "yt-dlp" / TAG / "yt-dlp.tmp").exists()
    assert durum.oku(str(tmp_path))["aktif"] is None


def test_zip_degilse_reddedilir(tmp_path):
    with pytest.raises(g.GuncellemeHatasi):
        guncelle(tmp_path, SahteGitHub(icerik=b"zip degil"))
    assert not (tmp_path / "yt-dlp" / TAG / "yt-dlp").exists()
    assert not (tmp_path / "yt-dlp" / TAG / "yt-dlp.tmp").exists()
    assert durum.oku(str(tmp_path))["aktif"] is None


def test_kara_listedeki_tag_atlanir(tmp_path):
    durum.yaz(str(tmp_path), {**durum.oku(str(tmp_path)), "kara_liste": [TAG]})
    assert guncelle(tmp_path, SahteGitHub(), zorla=True) is None


def test_onceki_kaydirilir_en_cok_iki_surum(tmp_path):
    for s in ("2026.07.01", "2026.08.19"):
        (tmp_path / "yt-dlp" / s).mkdir(parents=True)
    durum.yaz(str(tmp_path), {**durum.oku(str(tmp_path)), "aktif": "2026.08.19", "onceki": "2026.07.01"})
    guncelle(tmp_path, SahteGitHub(), mevcut="2026.08.19")
    d = durum.oku(str(tmp_path))
    assert (d["aktif"], d["onceki"]) == (TAG, "2026.08.19")
    assert klasorler(tmp_path) == ["2026.08.19", TAG]


def test_kara_listedeki_aktif_oncekini_korur(tmp_path):
    for s in ("2026.08.19", "2026.09.01"):
        (tmp_path / "yt-dlp" / s).mkdir(parents=True)
    durum.yaz(str(tmp_path), {**durum.oku(str(tmp_path)), "aktif": "2026.09.01",
                              "onceki": "2026.08.19", "kara_liste": ["2026.09.01"]})
    guncelle(tmp_path, SahteGitHub(), mevcut="2026.08.19")
    d = durum.oku(str(tmp_path))
    assert (d["aktif"], d["onceki"]) == (TAG, "2026.08.19")
    assert klasorler(tmp_path) == ["2026.08.19", TAG]


def test_uygulama_yeni_surum(tmp_path):
    assert g.uygulama_kontrol(SahteGitHub(uygulama_tag="v1.2.0").json, mevcut="1.0.0") == (
        "1.2.0", SAYFA + "v1.2.0")
    assert g.uygulama_kontrol(SahteGitHub(uygulama_tag="v1.0.0").json, mevcut="1.0.0") is None


def test_kontrol_et_gunde_bir_kez(tmp_path):
    gh = SahteGitHub(uygulama_tag="v9.0.0")
    assert g.kontrol_et(str(tmp_path), "2026.08.19", gh.json, gh.bayt, simdi=lambda: 1000.0) == (
        "9.0.0", SAYFA + "v9.0.0")
    assert durum.oku(str(tmp_path))["son_kontrol"] == 1000.0
    istek_sayisi = len(gh.istekler)
    assert g.kontrol_et(str(tmp_path), TAG, gh.json, gh.bayt, simdi=lambda: 1060.0) is None
    assert len(gh.istekler) == istek_sayisi


def test_kontrol_et_ag_hatasinda_sessiz_ve_son_kontrol_yazilmaz(tmp_path):
    gh = SahteGitHub(hata=OSError("ag yok"))
    assert g.kontrol_et(str(tmp_path), "2026.08.19", gh.json, gh.bayt, simdi=lambda: 1000.0) is None
    assert durum.oku(str(tmp_path))["son_kontrol"] is None


def test_kontrol_et_hash_hatasinda_sessiz(tmp_path):
    gh = SahteGitHub(ozet="0" * 64)
    assert g.kontrol_et(str(tmp_path), "2026.08.19", gh.json, gh.bayt, simdi=lambda: 1000.0) is None
    assert durum.oku(str(tmp_path))["son_kontrol"] is None
