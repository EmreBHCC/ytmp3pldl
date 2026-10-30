import json
import os
import subprocess
import sys

import pytest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def log_isleyicilerini_kapat():
    """main() process icinde log_kur'u cagirir; actigi dosyayi test sonunda kapat."""
    import logging
    once = list(logging.getLogger().handlers)
    yield
    kok = logging.getLogger()
    for h in list(kok.handlers):
        if h not in once:
            kok.removeHandler(h)
            h.close()


def test_oz_test_yukle_bos_veri(tmp_path):
    cikti = tmp_path / "yukle.json"
    ortam = dict(os.environ, YTMP3PLDL_VERI=str(tmp_path / "veri"))
    p = subprocess.run([sys.executable, os.path.join(KOK, "main.py"), "--oz-test-yukle", str(cikti)],
                       env=ortam, cwd=KOK, timeout=120)
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert p.returncode == 0
    assert sonuc["ok"] is True
    assert sonuc["yukleme"]["kaynak"] in ("yedek", "sistem")
    assert sonuc["yukleme"]["surum"]
    assert sonuc["yt_dlp_dosyasi"]
    assert (tmp_path / "veri" / "log.txt").is_file()


def test_veri_klasoru_oserror_verirse_gecici_klasorle_acilir(tmp_path, monkeypatch):
    import main
    import yollar

    def bozuk():
        raise OSError("yazilamaz")

    monkeypatch.setattr(yollar, "veri_klasoru", bozuk)
    monkeypatch.setattr(main.tempfile, "gettempdir", lambda: str(tmp_path))
    cikti = tmp_path / "yukle.json"
    assert main.main(["--oz-test-yukle", str(cikti)]) == 0
    assert json.loads(cikti.read_text(encoding="utf-8"))["ok"] is True


def test_log_kurulamazsa_logsuz_devam(tmp_path, monkeypatch):
    import main

    def bozuk(veri_dir):
        raise OSError("log kilitli")

    monkeypatch.setattr(main, "log_kur", bozuk)
    monkeypatch.setenv("YTMP3PLDL_VERI", str(tmp_path / "veri"))
    cikti = tmp_path / "yukle.json"
    assert main.main(["--oz-test-yukle", str(cikti)]) == 0
    assert json.loads(cikti.read_text(encoding="utf-8"))["ok"] is True


def test_calistir_yakalanmayan_hatada_turkce_diyalog_ve_1(monkeypatch):
    import main
    mesajlar = []

    def patlak(argv=None):
        raise RuntimeError("beklenmedik")

    monkeypatch.setattr(main, "main", patlak)
    monkeypatch.setattr(main, "hata_goster", mesajlar.append)
    assert main.calistir([]) == 1
    assert len(mesajlar) == 1
    assert mesajlar[0].startswith("Uygulama açılamadı.")
    assert "log.txt" in mesajlar[0]


def test_calistir_hata_goster_de_patlasa_1_doner(monkeypatch):
    import main

    def patlak(argv=None):
        raise RuntimeError("x")

    def tk_yok(metin):
        raise RuntimeError("Tk yok")

    monkeypatch.setattr(main, "main", patlak)
    monkeypatch.setattr(main, "hata_goster", tk_yok)
    assert main.calistir([]) == 1
