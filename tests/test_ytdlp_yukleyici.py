import sys
import zipfile
from pathlib import Path

import pytest

import durum
import ytdlp_yukleyici as yy

MODUL = "sahte_ytdlp"
PYTHON_HATASI = ('raise ImportError("You are using an unsupported version of Python. '
                 'Only Python versions 3.99 and above are supported by yt-dlp")\n')


def paket(yol: Path, surum: str, init: str = "") -> str:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(yol, "w") as z:
        z.writestr(f"{MODUL}/__init__.py", init)
        z.writestr(f"{MODUL}/version.py", f"__version__ = {surum!r}\n")
    return str(yol)


def indirilmis(veri: Path, surum: str, init: str = "") -> str:
    return paket(Path(durum.ytdlp_dosyasi(str(veri), surum)), surum, init)


def durum_yaz(veri: Path, **alanlar):
    d = durum.oku(str(veri))
    d.update(alanlar)
    durum.yaz(str(veri), d)


@pytest.fixture(autouse=True)
def temiz_import():
    once = list(sys.path)
    yield
    sys.path[:] = once
    for ad in [m for m in sys.modules if m.startswith(MODUL)]:
        del sys.modules[ad]


@pytest.fixture
def veri(tmp_path):
    return tmp_path / "veri"


@pytest.fixture
def yedek(tmp_path):
    return paket(tmp_path / "paket" / "vendor" / "yt-dlp", "2026.08.19")


def test_bos_veri_yedegi_yukler(veri, yedek):
    s = yy.yukle(str(veri), yedek, modul=MODUL)
    assert (s.kaynak, s.surum, s.python_yetersiz) == ("yedek", "2026.08.19", False)
    assert sys.modules[MODUL].__file__.startswith(yedek)


def test_aktif_once_gelir(veri, yedek):
    indirilmis(veri, "2026.10.26")
    durum_yaz(veri, aktif="2026.10.26")
    s = yy.yukle(str(veri), yedek, modul=MODUL)
    assert (s.kaynak, s.surum) == ("aktif", "2026.10.26")
    assert "2026.10.26" in sys.modules[MODUL].__file__


def test_bozuk_aktif_oncekine_duser_ve_kara_listeye_girer(veri, yedek):
    bozuk = Path(durum.ytdlp_dosyasi(str(veri), "2026.10.26"))
    bozuk.parent.mkdir(parents=True)
    bozuk.write_bytes(b"zip degil")
    indirilmis(veri, "2026.09.01")
    durum_yaz(veri, aktif="2026.10.26", onceki="2026.09.01")
    s = yy.yukle(str(veri), yedek, modul=MODUL)
    assert (s.kaynak, s.surum) == ("onceki", "2026.09.01")
    assert durum.oku(str(veri))["kara_liste"] == ["2026.10.26"]
    assert str(bozuk) not in sys.path


def test_kara_listedeki_denenmez(veri, yedek):
    indirilmis(veri, "2026.10.26")
    durum_yaz(veri, aktif="2026.10.26", kara_liste=["2026.10.26"])
    assert yy.yukle(str(veri), yedek, modul=MODUL).kaynak == "yedek"


def test_dosyasi_olmayan_aktif_atlanir(veri, yedek):
    durum_yaz(veri, aktif="2026.10.26")
    s = yy.yukle(str(veri), yedek, modul=MODUL)
    assert s.kaynak == "yedek"
    assert durum.oku(str(veri))["kara_liste"] == []


def test_python_yetersiz_isaretlenir(veri, yedek):
    indirilmis(veri, "2027.01.01", init=PYTHON_HATASI)
    durum_yaz(veri, aktif="2027.01.01")
    s = yy.yukle(str(veri), yedek, modul=MODUL)
    assert (s.kaynak, s.surum, s.python_yetersiz) == ("yedek", "2026.08.19", True)
    assert durum.oku(str(veri))["kara_liste"] == ["2027.01.01"]


def test_syntax_error_python_yetersiz_sayilir(veri, yedek):
    indirilmis(veri, "2027.01.01", init="def (:\n")
    durum_yaz(veri, aktif="2027.01.01")
    assert yy.yukle(str(veri), yedek, modul=MODUL).python_yetersiz is True


def test_hicbiri_yoksa_kaynak_none(veri, tmp_path):
    s = yy.yukle(str(veri), str(tmp_path / "yok" / "yt-dlp"), modul=MODUL)
    assert (s.kaynak, s.surum) == (None, None)
