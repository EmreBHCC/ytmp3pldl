# ytmp3pldl Kurulabilir Paket — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python bilmeyen bir Windows kullanıcısının çift tıklayıp kurduğu, yt-dlp'yi kendi kendine güncelleyen `ytmp3pldl-kurulum-<sürüm>.exe` üretmek ve `paketleme/kapi.ps1`'i PASS ettirmek.

**Architecture:** PyInstaller `--onedir` çıktısı Inno Setup ile kullanıcı başına kurulur. yt-dlp gömülü modül olarak paketlenmez; `ytdlp_yukleyici` açılışta `%LOCALAPPDATA%\ytmp3pldl\yt-dlp\<sürüm>\yt-dlp` (indirilmiş, zipimport) → önceki → paketteki `vendor/yt-dlp` → sistem sırasıyla `sys.path`'e koyup import eder. `guncelleyici` arka plan thread'inde günde bir kez yt-dlp'nin GitHub release'ini SHA256 ile doğrulayıp indirir ve uygulamanın yeni sürümünü GUI şeridiyle haber verir.

**Tech Stack:** Python 3.13, customtkinter, yt-dlp (zipimport), imageio-ffmpeg, Deno 2.9.8 (gömülü JS çalıştırıcı), pytest, PyInstaller ≥6.10, Inno Setup 6.7.3, PowerShell 7.

Tasarım onaylı (ayrı tasarım notunda, repoda değil). Devam notu: `docs/DEVAM.md`.

## Global Constraints

- Platform: Windows 10/11 x64. macOS/Linux kapsam dışı.
- Derleme Python 3.13 ile; venv `.venv-build` (repo kökünde, gitignore'da).
- `paketleme/kapi.ps1` **değiştirilmez** (dondurulmuş bitti kapısı). Hedefleri de değiştirilmez.
- Kullanıcıya görünen metin Türkçe, tam Türkçe karakterle, eylem söyler. Kod adları ASCII Türkçe (`veri_klasoru`), mevcut dosyalardaki gibi.
- İndirilen yt-dlp `SHA2-256SUMS` ile eşleşmezse ve geçerli zip değilse diske aktif olarak yazılmaz.
- Uygulama kendi .exe'sini değiştirmez; yalnız "Yeni sürüm var" der.
- Testler ağsızdır (tek istisna yok); ağ fonksiyonları enjekte edilir.
- Commit'ler repo'daki git kimliğiyle (Emre). **Commit mesajına `Co-Authored-By` satırı eklenmez.**
- Repo'yu public yapmak / push / release: bu planın dışında, Emre onayıyla.
- Sabitler: `GITHUB_REPO = "EmreBHCC/ytmp3pldl"`, `YTDLP_REPO = "yt-dlp/yt-dlp"`, `__version__ = "1.0.0"`, Deno `v2.9.8` zip sha256 `cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf`, öz test videosu `jNQXAC9IVRw`.
- Komutlar repo kökünden PowerShell 7 (`pwsh`) ile çalıştırılır. `$py = ".venv-build\Scripts\python.exe"`.

## Dosya haritası

| Dosya | Durum | Sorumluluk |
| --- | --- | --- |
| `surum.py` | yeni | sürüm + repo adları, tek kaynak |
| `yollar.py` | yeni | veri klasörü, paket klasörü, yedek yt-dlp ve Deno yolu |
| `durum.py` | yeni | `durum.json` okuma/atomik yazma |
| `ytdlp_yukleyici.py` | yeni | yt-dlp'yi doğru kaynaktan import etme, kara liste |
| `guncelleyici.py` | yeni | GitHub kontrolü, indirme + doğrulama, arka plan thread'i |
| `downloader.py` | değişir | android override kalkar, Deno, avc1, `download_item` info döndürür |
| `main.py` | değişir | log, yükleme, öz test bayrakları, GUI + güncelleyici |
| `gui.py` | değişir | yeni sürüm şeridi, sürüm etiketi |
| `playlist.py`, `baslat.bat` | silinir | kullanılmıyor / Python'lu başlatıcı |
| `pytest.ini`, `requirements*.txt` | yeni/değişir | test ve bağımlılıklar |
| `tests/` | yeni | birim testleri |
| `paketleme/hazirla.ps1`, `ytmp3pldl.spec`, `ytmp3pldl.iss`, `derle.ps1` | yeni | derleme zinciri |
| `README.md`, `IMPLEMENTATION.md` | değişir | kullanıcı + geliştirici belgeleri |

---

### Task 1: Temel modüller ve test altyapısı

**Files:**
- Create: `surum.py`, `yollar.py`, `durum.py`, `pytest.ini`, `requirements-dev.txt`
- Modify: `requirements.txt`
- Test: `tests/test_yollar.py`, `tests/test_durum.py`

**Interfaces:**
- Consumes: yok
- Produces:
  - `surum.__version__: str`, `surum.GITHUB_REPO: str`, `surum.YTDLP_REPO: str`
  - `yollar.veri_klasoru() -> str` (oluşturur), `yollar.paket_klasoru() -> str`, `yollar.yedek_ytdlp_yolu() -> str`, `yollar.deno_yolu() -> str | None`
  - `durum.oku(veri_dir: str) -> dict` (anahtarlar `aktif`, `onceki`, `kara_liste`, `son_kontrol`), `durum.yaz(veri_dir: str, durum: dict) -> None`, `durum.ytdlp_dosyasi(veri_dir: str, surum: str) -> str`

- [ ] **Step 1: Bağımlılık dosyalarını yaz ve venv kur**

`requirements.txt` (tamamen değiştir):

```
customtkinter>=5.2.2
imageio-ffmpeg>=0.5.1
```

`requirements-dev.txt`:

```
-r requirements.txt
yt-dlp[default]
pytest>=8
pyinstaller>=6.10
```

`pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Run:

```powershell
$taban = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
if (-not (Test-Path .venv-build\Scripts\python.exe)) { if (Test-Path $taban) { & $taban -m venv .venv-build } else { py -3.13 -m venv .venv-build } }
.venv-build\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements-dev.txt
.venv-build\Scripts\python.exe -c "import yt_dlp, customtkinter, imageio_ffmpeg, PyInstaller, pytest; print('ok')"
```

Expected: `ok`

- [ ] **Step 2: Failing testleri yaz**

`tests/test_yollar.py`:

```python
import sys

import yollar


def test_veri_klasoru_ortam_degiskeni(tmp_path, monkeypatch):
    hedef = tmp_path / "veri"
    monkeypatch.setenv("YTMP3PLDL_VERI", str(hedef))
    assert yollar.veri_klasoru() == str(hedef)
    assert hedef.is_dir()


def test_veri_klasoru_localappdata(tmp_path, monkeypatch):
    monkeypatch.delenv("YTMP3PLDL_VERI", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert yollar.veri_klasoru() == str(tmp_path / "ytmp3pldl")
    assert (tmp_path / "ytmp3pldl").is_dir()


def test_paket_klasoru_meipass(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert yollar.paket_klasoru() == str(tmp_path)
    assert yollar.yedek_ytdlp_yolu() == str(tmp_path / "vendor" / "yt-dlp")


def test_deno_yolu_pakettekini_tercih_eder(tmp_path, monkeypatch):
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "deno.exe").write_bytes(b"")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert yollar.deno_yolu() == str(tmp_path / "vendor" / "deno.exe")


def test_deno_yolu_pakette_yoksa_path(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(yollar.shutil, "which", lambda ad: None)
    assert yollar.deno_yolu() is None
```

`tests/test_durum.py`:

```python
import durum


def test_bos_klasor_varsayilan(tmp_path):
    assert durum.oku(str(tmp_path)) == {
        "aktif": None, "onceki": None, "kara_liste": [], "son_kontrol": None}


def test_yaz_oku(tmp_path):
    d = durum.oku(str(tmp_path))
    d["aktif"] = "2026.10.26"
    d["kara_liste"].append("2026.01.01")
    durum.yaz(str(tmp_path), d)
    okunan = durum.oku(str(tmp_path))
    assert okunan["aktif"] == "2026.10.26"
    assert okunan["kara_liste"] == ["2026.01.01"]
    assert not (tmp_path / "durum.json.tmp").exists()


def test_bozuk_json_varsayilana_doner(tmp_path):
    (tmp_path / "durum.json").write_text("{bozuk", encoding="utf-8")
    assert durum.oku(str(tmp_path))["aktif"] is None


def test_varsayilan_liste_paylasilmaz(tmp_path):
    durum.oku(str(tmp_path))["kara_liste"].append("x")
    assert durum.oku(str(tmp_path))["kara_liste"] == []


def test_ytdlp_dosyasi(tmp_path):
    assert durum.ytdlp_dosyasi(str(tmp_path), "2026.10.26") == str(
        tmp_path / "yt-dlp" / "2026.10.26" / "yt-dlp")
```

- [ ] **Step 3: Testlerin kırıldığını gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_yollar.py tests/test_durum.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'yollar'`

- [ ] **Step 4: Modülleri yaz**

`surum.py`:

```python
"""Uygulama surumu ve depo adlari: tek kaynak (uygulama + kurulum betigi)."""
__version__ = "1.0.0"
GITHUB_REPO = "EmreBHCC/ytmp3pldl"
YTDLP_REPO = "yt-dlp/yt-dlp"
```

`yollar.py`:

```python
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
```

`durum.py`:

```python
"""durum.json: aktif/onceki yt-dlp surumu, kara liste, son kontrol zamani. Atomik yazilir."""
import json
import os

ANAHTARLAR = ("aktif", "onceki", "kara_liste", "son_kontrol")


def _yol(veri_dir):
    return os.path.join(veri_dir, "durum.json")


def oku(veri_dir) -> dict:
    durum = {"aktif": None, "onceki": None, "kara_liste": [], "son_kontrol": None}
    try:
        with open(_yol(veri_dir), encoding="utf-8") as f:
            veri = json.load(f)
    except (OSError, ValueError):
        return durum
    if isinstance(veri, dict):
        durum.update({k: veri[k] for k in ANAHTARLAR if k in veri})
    return durum


def yaz(veri_dir, durum: dict) -> None:
    os.makedirs(veri_dir, exist_ok=True)
    gecici = _yol(veri_dir) + ".tmp"
    with open(gecici, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)
    os.replace(gecici, _yol(veri_dir))


def ytdlp_dosyasi(veri_dir, surum) -> str:
    return os.path.join(veri_dir, "yt-dlp", surum, "yt-dlp")
```

- [ ] **Step 5: Testlerin geçtiğini gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_yollar.py tests/test_durum.py -q`
Expected: `10 passed`

- [ ] **Step 6: Commit**

```powershell
git add surum.py yollar.py durum.py pytest.ini requirements.txt requirements-dev.txt tests/test_yollar.py tests/test_durum.py
git commit -m "Temel: surum, yollar, durum.json ve test altyapisi"
```

---

### Task 2: `ytdlp_yukleyici.py`

**Files:**
- Create: `ytdlp_yukleyici.py`
- Test: `tests/test_ytdlp_yukleyici.py`

**Interfaces:**
- Consumes: `durum.oku`, `durum.yaz`, `durum.ytdlp_dosyasi` (Task 1)
- Produces:
  - `@dataclass YuklemeSonucu(kaynak: str | None, surum: str | None, python_yetersiz: bool = False)`; `kaynak` ∈ `"aktif" | "onceki" | "yedek" | "sistem" | None`
  - `yukle(veri_dir: str, yedek_yolu: str, modul: str = "yt_dlp") -> YuklemeSonucu`. Başarıda `modul` `sys.modules`'tadır ve `surum` = `<modul>.version.__version__`.

Davranış: adaylar sırayla `aktif`, `onceki` (durum'da tanımlı, `kara_liste`'de değil, dosyası var), sonra `yedek_yolu` (dosyası varsa), sonra sistem (`sys.path`'e dokunmadan). İndirilmiş bir aday import edilemezse kara listeye yazılır. Hata `SyntaxError` ya da mesajında `unsupported version of Python` geçen bir istisnaysa `python_yetersiz=True`. Başarısız denemeden sonra `sys.path` ve `sys.modules` temizlenir (`modul`, `modul.*`, `modul_*` — gerçek kullanımda `yt_dlp_ejs` de gider).

- [ ] **Step 1: Failing testleri yaz**

`tests/test_ytdlp_yukleyici.py`:

```python
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
```

- [ ] **Step 2: Testlerin kırıldığını gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_ytdlp_yukleyici.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'ytdlp_yukleyici'`

- [ ] **Step 3: Modülü yaz**

`ytdlp_yukleyici.py`:

```python
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


def _dene(yol, modul):
    """yol None ise sys.path'e dokunmaz. Basarida surumu dondurur, hatada temizleyip yukseltir."""
    if yol is not None:
        sys.path.insert(0, yol)
    try:
        importlib.invalidate_caches()
        importlib.import_module(modul)
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


def yukle(veri_dir, yedek_yolu, modul="yt_dlp") -> YuklemeSonucu:
    d = durum.oku(veri_dir)
    python_yetersiz = False
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
            python_yetersiz = python_yetersiz or _python_sebebi(hata)
            d["kara_liste"].append(surum)
            durum.yaz(veri_dir, d)
    for kaynak, yol in (("yedek", yedek_yolu), ("sistem", None)):
        if yol is not None and not os.path.isfile(yol):
            continue
        try:
            return YuklemeSonucu(kaynak, _dene(yol, modul), python_yetersiz)
        except Exception as hata:
            log.warning("yt-dlp (%s) yuklenemedi: %r", kaynak, hata)
    return YuklemeSonucu(None, None, python_yetersiz)
```

- [ ] **Step 4: Testlerin geçtiğini gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_ytdlp_yukleyici.py -q`
Expected: `8 passed`

- [ ] **Step 5: Commit**

```powershell
git add ytdlp_yukleyici.py tests/test_ytdlp_yukleyici.py
git commit -m "ytdlp_yukleyici: aktif/onceki/yedek/sistem sirasi ve kara liste"
```

---

### Task 3: `guncelleyici.py`

**Files:**
- Create: `guncelleyici.py`
- Test: `tests/test_guncelleyici.py`

**Interfaces:**
- Consumes: `durum.*` (Task 1), `surum.GITHUB_REPO`, `surum.YTDLP_REPO`, `surum.__version__`
- Produces:
  - `getir_json(url: str) -> dict`, `getir_bayt(url: str, zaman_asimi: int = 60) -> bytes` (gerçek ağ, urllib)
  - `surum_tuple(surum: str) -> tuple[int, ...]`, `daha_yeni(aday: str, mevcut: str | None) -> bool`
  - `kontrol_zamani_geldi(son_kontrol: float | None, simdi: float, aralik: int = 86400) -> bool`
  - `class GuncellemeHatasi(Exception)`
  - `ytdlp_guncelle(veri_dir, mevcut, getir_json=getir_json, getir_bayt=getir_bayt, zorla=False) -> str | None` — yeni indirilen tag ya da None; hash/zip hatasında `GuncellemeHatasi`; ağ hatasını yukarı bırakır.
  - `uygulama_kontrol(getir_json=getir_json, mevcut=__version__) -> tuple[str, str] | None` — `(sürüm, release_sayfası_url)`
  - `kontrol_et(veri_dir, mevcut_ytdlp, getir_json=..., getir_bayt=..., simdi=time.time) -> tuple[str, str] | None` — hiç istisna yükseltmez.
  - `arka_planda_calistir(veri_dir, mevcut_ytdlp, bildir: Callable[[str, str], None]) -> threading.Thread`

Kurallar: `son_kontrol` yalnız yt-dlp kontrolü (indirme gerekse de gerekmese de) istisnasız bittiğinde yazılır. Aktif kara listedeyse yeni sürüm aktif olur, `onceki` korunur; değilse `onceki ← aktif`. `<veri>/yt-dlp/` altında `aktif`, `onceki` ve şu an çalışan (`mevcut`) dışındaki klasörler silinir.

- [ ] **Step 1: Failing testleri yaz**

`tests/test_guncelleyici.py`:

```python
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
```

- [ ] **Step 2: Testlerin kırıldığını gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_guncelleyici.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'guncelleyici'`

- [ ] **Step 3: Modülü yaz**

`guncelleyici.py`:

```python
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
```

- [ ] **Step 4: Testlerin geçtiğini gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_guncelleyici.py -q`
Expected: `15 passed`

- [ ] **Step 5: Commit**

```powershell
git add guncelleyici.py tests/test_guncelleyici.py
git commit -m "guncelleyici: yt-dlp SHA256 dogrulamali indirme, uygulama surum kontrolu"
```

---

### Task 4: `downloader.py` — Deno, varsayılan istemciler, avc1

**Files:**
- Modify: `downloader.py` (tamamı aşağıda)
- Delete: `playlist.py`
- Test: `tests/test_downloader.py`

**Interfaces:**
- Consumes: `yollar.deno_yolu()` (Task 1). `downloader` `yollar`'ı modül olarak import eder (`import yollar`), testler `downloader.yollar.deno_yolu`'nu yamalar.
- Produces (GUI'nin kullandığı imzalar korunur):
  - `fetch_entries(url) -> (list[dict], str | None)` (değişmez)
  - `build_ydl_opts(fmt, quality, output_dir, progress_hook, subfolder=None) -> dict`
  - `video_formati(quality: str) -> str`
  - `download_item(url, fmt, quality, output_dir, progress_hook, subfolder=None) -> dict` — **artık yt-dlp info sözlüğünü döndürür** (`format_id` öz testte kullanılır).

- [ ] **Step 1: Failing testleri yaz**

`tests/test_downloader.py`:

```python
import downloader


def ayarlar(tmp_path, fmt="mp3", kalite="192"):
    return downloader.build_ydl_opts(fmt, kalite, str(tmp_path), lambda d: None)


def test_android_istemci_zorlamasi_yok(tmp_path):
    assert "extractor_args" not in ayarlar(tmp_path)


def test_deno_varsa_js_runtimes(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader.yollar, "deno_yolu", lambda: r"C:\x\deno.exe")
    assert ayarlar(tmp_path)["js_runtimes"] == {"deno": {"path": r"C:\x\deno.exe"}}


def test_deno_yoksa_js_runtimes_yok(tmp_path, monkeypatch):
    monkeypatch.setattr(downloader.yollar, "deno_yolu", lambda: None)
    assert "js_runtimes" not in ayarlar(tmp_path)


def test_mp3_ayarlari(tmp_path):
    o = ayarlar(tmp_path, "mp3", "192")
    assert o["format"] == "bestaudio/best"
    assert o["postprocessors"][0]["preferredquality"] == "192"


def test_video_avc1_tercihli(tmp_path):
    o = ayarlar(tmp_path, "mp4", "720")
    assert o["format"].startswith("bestvideo[vcodec^=avc1][height<=720]+bestaudio[ext=m4a]/")
    assert o["format"].endswith("/best")
    assert o["merge_output_format"] == "mp4"


def test_video_en_yuksek_sinirsiz(tmp_path):
    o = ayarlar(tmp_path, "mp4", "best")
    assert "height<=" not in o["format"]
    assert o["format"].startswith("bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/")


def test_alt_klasor(tmp_path):
    o = downloader.build_ydl_opts("mp3", "192", str(tmp_path), lambda d: None, subfolder="Liste: 1")
    assert (tmp_path / "Liste_ 1").is_dir()
    assert o["outtmpl"].startswith(str(tmp_path / "Liste_ 1"))
```

- [ ] **Step 2: Testlerin kırıldığını gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_downloader.py -q`
Expected: FAIL (`test_android_istemci_zorlamasi_yok` assert, `downloader.yollar` AttributeError)

- [ ] **Step 3: `downloader.py`'yi yeniden yaz**

`downloader.py` (tamamı):

```python
"""yt-dlp tabanli indirme mantigi. GUI'den bagimsiz, tekrar kullanilabilir katman.

yt_dlp bu modul import edilmeden once ytdlp_yukleyici ile yuklenmis olmalidir.
"""
import os
import re
import yt_dlp
import imageio_ffmpeg

import yollar

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

INVALID_CHARS = re.compile(r'[\\/*?:"<>|]')


def sanitize_filename(name: str) -> str:
    return INVALID_CHARS.sub("_", name).strip()


def _temel_ayarlar():
    """YouTube'un varsayilan istemcileri JS cozumu ister; Deno varsa yt-dlp'ye verilir."""
    opts = {"quiet": True, "no_warnings": True}
    deno = yollar.deno_yolu()
    if deno:
        opts["js_runtimes"] = {"deno": {"path": deno}}
    return opts


def fetch_entries(url: str):
    """Verilen URL bir video ise tek elemanli, playlist ise tum elemanlarin
    listesini dondurur. Donen deger: (items, playlist_title_or_None)."""
    ydl_opts = {
        **_temel_ayarlar(),
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise ValueError("Video/playlist bilgisi alinamadi. URL'yi kontrol edin.")

    items = []
    playlist_title = None

    if info.get("entries"):
        playlist_title = info.get("title")
        for entry in info["entries"]:
            if entry is None:
                continue
            video_id = entry.get("id")
            items.append({
                "id": video_id,
                "title": entry.get("title") or video_id or "Bilinmeyen",
                "url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                "duration": entry.get("duration"),
            })
    else:
        items.append({
            "id": info.get("id"),
            "title": info.get("title") or "Bilinmeyen",
            "url": info.get("webpage_url") or url,
            "duration": info.get("duration"),
        })

    if not items:
        raise ValueError("Indirilebilecek video bulunamadi.")

    return items, playlist_title


def video_formati(quality: str) -> str:
    """H.264 (avc1) once: AV1/VP9 eski oynaticilarda acilmaz."""
    sinir = "" if quality == "best" else f"[height<={quality}]"
    return (
        f"bestvideo[vcodec^=avc1]{sinir}+bestaudio[ext=m4a]/"
        f"bestvideo[ext=mp4]{sinir}+bestaudio[ext=m4a]/"
        f"best[ext=mp4]{sinir}/best"
    )


def build_ydl_opts(fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    target_dir = os.path.join(output_dir, sanitize_filename(subfolder)) if subfolder else output_dir
    os.makedirs(target_dir, exist_ok=True)
    outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")

    opts = {
        **_temel_ayarlar(),
        "outtmpl": outtmpl,
        "ffmpeg_location": FFMPEG_PATH,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        "ignoreerrors": False,
        "restrictfilenames": False,
        "retries": 15,
        "fragment_retries": 15,
        "socket_timeout": 30,
    }

    if fmt == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        }]
    else:
        opts["format"] = video_formati(quality)
        opts["merge_output_format"] = "mp4"

    return opts


def download_item(url: str, fmt: str, quality: str, output_dir: str, progress_hook, subfolder: str | None = None):
    """Indirir ve yt-dlp info sozlugunu dondurur (format_id: kullanilan kaynak formatlar)."""
    opts = build_ydl_opts(fmt, quality, output_dir, progress_hook, subfolder)
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True)
```

Sonra: `git rm playlist.py`

- [ ] **Step 4: Testlerin geçtiğini gör**

Run: `.venv-build\Scripts\python.exe -m pytest -q`
Expected: tüm testler PASS (`40 passed`)

- [ ] **Step 5: Gerçek indirmeyi elle doğrula (ağ gerekir, test paketinde değil)**

```powershell
.venv-build\Scripts\python.exe -c "import tempfile, downloader as d; t=tempfile.mkdtemp(); i=d.download_item('https://www.youtube.com/watch?v=jNQXAC9IVRw','mp3','192',t,lambda x:None); print(i['format_id'], __import__('os').listdir(t))"
```

Expected: `format_id` `18` değil (ör. `251` ya da `140`), listede bir `.mp3`. Deno yoksa (vendor henüz yok, PATH'te deno yoksa) yine de `18` olmamalı; `18` çıkarsa dur ve raporla.

- [ ] **Step 6: Commit**

```powershell
git add downloader.py tests/test_downloader.py
git commit -m "downloader: android zorlamasi kalkti, Deno js_runtimes, avc1 video; playlist.py silindi"
```

---

### Task 5: `main.py` + `gui.py` — açılış sırası, öz test, sürüm şeridi

**Files:**
- Modify: `main.py` (tamamı), `gui.py` (aşağıdaki parçalar)
- Test: `tests/test_main.py`, `tests/test_gui.py`

**Interfaces:**
- Consumes: `yollar.*`, `ytdlp_yukleyici.yukle`, `YuklemeSonucu`, `guncelleyici.ytdlp_guncelle`, `guncelleyici.arka_planda_calistir`, `downloader.download_item` (info döndürür), `surum.__version__`, `surum.GITHUB_REPO`
- Produces:
  - Komut satırı: `main.py --oz-test-yukle <json>` → `{"ok": bool, "yukleme": {"kaynak", "surum", "python_yetersiz"}, "yt_dlp_dosyasi": str|None}`; `main.py --oz-test <json>` → `{"ok", "yukleme", "deno", "guncellenen", "mp3_bayt", "formatlar": [str], "hata"?}`. Çıkış kodu 0 = ok. (Kapı bu alanları okur: `ok`, `yukleme.kaynak`, `yukleme.surum`, `guncellenen`, `mp3_bayt`, `formatlar`.)
  - `gui.App(ytdlp_surum: str | None = None, python_yetersiz: bool = False)`, `App.yeni_surum_goster(surum: str, url: str)`, `App._banner_ac(metin, buton, komut)`, öznitelikler `App.banner`, `App.banner_label`, `App.surum_label`.

- [ ] **Step 1: Failing testleri yaz**

`tests/test_main.py`:

```python
import json
import os
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
```

`tests/test_gui.py`:

```python
import tkinter

import pytest

from surum import __version__


def yeni_app(**kw):
    from gui import App
    try:
        app = App(**kw)
    except tkinter.TclError as e:
        pytest.skip(f"ekran yok: {e}")
    app.withdraw()
    return app


@pytest.fixture
def app():
    a = yeni_app(ytdlp_surum="2026.10.26")
    yield a
    a.destroy()


def test_surum_etiketi(app):
    assert app.surum_label.cget("text") == f"v{__version__} · yt-dlp 2026.10.26"


def test_banner_gizli_baslar(app):
    assert app.banner.winfo_manager() == ""


def test_yeni_surum_banner(app):
    app.yeni_surum_goster("1.2.0", "https://example.invalid/r")
    assert app.banner.winfo_manager() == "grid"
    assert "1.2.0" in app.banner_label.cget("text")


def test_python_yetersiz_banner():
    a = yeni_app(python_yetersiz=True)
    try:
        assert a.banner.winfo_manager() == "grid"
        assert "yeni sürümü gerekiyor" in a.banner_label.cget("text")
    finally:
        a.destroy()
```

- [ ] **Step 2: Testlerin kırıldığını gör**

Run: `.venv-build\Scripts\python.exe -m pytest tests/test_main.py tests/test_gui.py -q`
Expected: FAIL (`yukle.json` yok / `App() got an unexpected keyword argument 'ytdlp_surum'`)

- [ ] **Step 3: `main.py`'yi yeniden yaz**

`main.py` (tamamı):

```python
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
```

- [ ] **Step 4: `gui.py`'yi değiştir**

4a. Import bloğu (satır 1-11) şöyle olur:

```python
"""Modern, sade bir YouTube indirici arayuzu (customtkinter)."""
import os
import threading
import queue
import itertools
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox

import customtkinter as ctk

import downloader
from surum import GITHUB_REPO, __version__

SURUMLER_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
```

4b. `App.__init__` başı (eski satır 100-115):

```python
class App(ctk.CTk):
    def __init__(self, ytdlp_surum=None, python_yetersiz=False):
        super().__init__()
        self.title("YouTube İndirici")
        self.geometry("1000x700")
        self.minsize(860, 560)

        self.ytdlp_surum = ytdlp_surum
        self.rows_by_uid = {}
        self.update_queue = queue.Queue()
        self.executor = None
        self.active_futures = []
        self.total_count = 0
        self.done_count = 0
        self.default_output = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube Indirilenler")

        self._build_ui()
        if python_yetersiz:
            self._banner_ac("YouTube'daki değişikliklere uymak için uygulamanın yeni sürümü gerekiyor.",
                            "İndir", lambda: webbrowser.open(SURUMLER_URL))
        self.after(100, self._drain_queue)
```

4c. `_build_ui` içinde `self.theme_switch.grid(row=0, column=1, sticky="e")` satırından hemen sonra ekle (şerit oluşturulur ama yerleştirilmez):

```python
        # Gizli bilgi seridi: yeni surum / uygulama guncellemesi gerekiyor
        self.banner = ctk.CTkFrame(top_bar, fg_color=("#fff4ce", "#4a3f12"), corner_radius=8)
        self.banner.grid_columnconfigure(0, weight=1)
        self.banner_label = ctk.CTkLabel(self.banner, text="", anchor="w", justify="left")
        self.banner_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        self.banner_btn = ctk.CTkButton(self.banner, text="", width=90)
        self.banner_btn.grid(row=0, column=1, padx=(0, 12), pady=8)
```

4d. `_build_ui` sonundaki row 7 etiketini (eski satır 222-224) şununla değiştir:

```python
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=7, column=0, sticky="ew", padx=26, pady=(0, 10))
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(footer, text="Yalnızca indirme izniniz olan veya telif hakkı size ait içerikleri indirin.",
                     text_color=("gray45", "gray55"), font=ctk.CTkFont(size=10)).grid(row=0, column=0, sticky="w")
        self.surum_label = ctk.CTkLabel(footer, text=f"v{__version__} · yt-dlp {self.ytdlp_surum or '?'}",
                                         text_color=("gray45", "gray55"), font=ctk.CTkFont(size=10))
        self.surum_label.grid(row=0, column=1, sticky="e")
```

4e. `_on_theme_change` metodundan önce yeni bölüm ekle:

```python
    # ----------------------------------------------------------- banner --
    def _banner_ac(self, metin, buton, komut):
        self.banner_label.configure(text=metin)
        self.banner_btn.configure(text=buton, command=komut)
        self.banner.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def yeni_surum_goster(self, surum, url):
        self._banner_ac(f"Yeni sürüm var ({surum}). İndirip kurmanız yeterli.", "İndir",
                        lambda: webbrowser.open(url))
```

- [ ] **Step 5: Testlerin geçtiğini gör**

Run: `.venv-build\Scripts\python.exe -m pytest -q`
Expected: tüm testler PASS (`45 passed`)

- [ ] **Step 6: Öz testi elle koş (ağ gerekir)**

```powershell
$env:YTMP3PLDL_VERI = "$env:TEMP\ytmp3pldl-elle"; .venv-build\Scripts\python.exe main.py --oz-test "$env:TEMP\oz.json"; Remove-Item Env:YTMP3PLDL_VERI
Get-Content "$env:TEMP\oz.json"
```

Expected: `"ok": true`, `"guncellenen"` = yt-dlp son tag'i (ör. `2026.10.26`), `"formatlar"` içinde `"18"` yok, `"mp3_bayt"` > 50000. Sonra GUI'yi `.venv-build\Scripts\python.exe main.py` ile aç, alt sağda `v1.0.0 · yt-dlp <sürüm>` göründüğünü kontrol et, kapat.

- [ ] **Step 7: Commit**

```powershell
git add main.py gui.py tests/test_main.py tests/test_gui.py
git commit -m "main/gui: yukleme sirasi, oz test bayraklari, yeni surum seridi ve surum etiketi"
```

---

### Task 6: Paketleme zinciri

**Files:**
- Create: `paketleme/hazirla.ps1`, `paketleme/ytmp3pldl.spec`, `paketleme/ytmp3pldl.iss` (UTF-8 BOM), `paketleme/derle.ps1`
- **Değiştirilmez:** `paketleme/kapi.ps1`

**Interfaces:**
- Consumes: `main.py` giriş noktası, `surum.__version__`, `yollar.yedek_ytdlp_yolu()` → `<_MEIPASS>/vendor/yt-dlp`, `yollar.deno_yolu()` → `<_MEIPASS>/vendor/deno.exe`
- Produces: `pwsh -File paketleme\derle.ps1` → `dist\ytmp3pldl\ytmp3pldl.exe` (onedir) ve `dist\ytmp3pldl-kurulum-<sürüm>.exe`. Kapı `derle.ps1`'i argümansız çağırır ve `.venv-build\Scripts\python.exe` bekler.

- [ ] **Step 1: `paketleme/hazirla.ps1`**

```powershell
# vendor/: guncel yt-dlp (SHA2-256SUMS ile dogrulanir) + sabit surum Deno (sha256 sabit).
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$ProgressPreference = 'SilentlyContinue'
$kok = Split-Path $PSScriptRoot -Parent
$vendor = Join-Path $kok 'vendor'
New-Item -ItemType Directory -Force $vendor | Out-Null

function Sha256($yol) { (Get-FileHash -Algorithm SHA256 $yol).Hash.ToLowerInvariant() }

# yt-dlp: zipimport'lu tek dosya; yt_dlp_ejs cozucusunu icinde tasir
$rel = Invoke-RestMethod 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
$varlik = @{}
$rel.assets | ForEach-Object { $varlik[$_.name] = $_.browser_download_url }
$sums = Join-Path $vendor 'SHA2-256SUMS'
$gecici = Join-Path $vendor 'yt-dlp.tmp'
Invoke-WebRequest $varlik['SHA2-256SUMS'] -OutFile $sums
Invoke-WebRequest $varlik['yt-dlp'] -OutFile $gecici
$beklenen = (Select-String -Path $sums -Pattern '^([0-9a-f]{64})\s+\*?yt-dlp$').Matches[0].Groups[1].Value
Remove-Item $sums
if ((Sha256 $gecici) -ne $beklenen) { Remove-Item $gecici; throw "yt-dlp $($rel.tag_name) SHA256 tutmadi" }
Move-Item -Force $gecici (Join-Path $vendor 'yt-dlp')
Write-Host "vendor/yt-dlp: $($rel.tag_name)"

# Deno: sabit surum, kendini guncellemez (v1)
$denoSurum = 'v2.9.8'
$denoSha = 'cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf'
$deno = Join-Path $vendor 'deno.exe'
$isaret = Join-Path $vendor 'deno.surum'
$hazir = (Test-Path $deno) -and (Test-Path $isaret) -and ((Get-Content $isaret -Raw).Trim() -eq $denoSurum)
if (-not $hazir) {
    $zip = Join-Path $vendor 'deno.zip'
    Invoke-WebRequest "https://github.com/denoland/deno/releases/download/$denoSurum/deno-x86_64-pc-windows-msvc.zip" -OutFile $zip
    if ((Sha256 $zip) -ne $denoSha) { Remove-Item $zip; throw "Deno $denoSurum SHA256 tutmadi" }
    Expand-Archive -Force $zip $vendor
    Remove-Item $zip
    Set-Content -NoNewline $isaret $denoSurum
}
Write-Host "vendor/deno.exe: $denoSurum"
```

Run: `pwsh -File paketleme\hazirla.ps1; Get-ChildItem vendor`
Expected: `vendor/yt-dlp: <tag>`, `vendor/deno.exe: v2.9.8`; `vendor` içinde `yt-dlp`, `deno.exe`, `deno.surum`.

Ardından: `.venv-build\Scripts\python.exe -m pytest tests/test_main.py -q` → PASS ve `kaynak` artık `yedek` olmalı (isteğe bağlı kontrol: testi `-s` ile koşmak gerekmez).

- [ ] **Step 2: `paketleme/ytmp3pldl.spec`**

```python
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
```

- [ ] **Step 3: `paketleme/ytmp3pldl.iss` (UTF-8 BOM ile kaydedilir)**

```ini
; Inno Setup 6. Surum derle.ps1'den gelir: ISCC /DSurum=<surum>
#ifndef Surum
  #define Surum "0.0.0"
#endif

[Setup]
AppId={{967E9B7A-B818-4AAA-9C57-8C7F48B3101E}
AppName=YouTube İndirici
AppVersion={#Surum}
AppVerName=YouTube İndirici {#Surum}
AppPublisher=Emre Bahçeci
AppPublisherURL=https://github.com/EmreBHCC/ytmp3pldl
DefaultDirName={localappdata}\Programs\ytmp3pldl
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=ytmp3pldl-kurulum-{#Surum}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=YouTube İndirici
UninstallDisplayIcon={app}\ytmp3pldl.exe
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "masaustu"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\ytmp3pldl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\YouTube İndirici"; Filename: "{app}\ytmp3pldl.exe"
Name: "{autodesktop}\YouTube İndirici"; Filename: "{app}\ytmp3pldl.exe"; Tasks: masaustu

[Run]
Filename: "{app}\ytmp3pldl.exe"; Description: "{cm:LaunchProgram,YouTube İndirici}"; Flags: nowait postinstall skipifsilent
```

Dosyayı yazdıktan sonra BOM ekle:

```powershell
$f = 'paketleme\ytmp3pldl.iss'; $t = [IO.File]::ReadAllText($f); [IO.File]::WriteAllText((Resolve-Path $f), $t, [Text.UTF8Encoding]::new($true))
```

- [ ] **Step 4: `paketleme/derle.ps1`**

```powershell
# Derleme: venv -> bagimliliklar -> vendor (hazirla) -> PyInstaller -> Inno Setup.
# Cikti: dist\ytmp3pldl\ (onedir) ve dist\ytmp3pldl-kurulum-<surum>.exe
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$kok = Split-Path $PSScriptRoot -Parent
Push-Location $kok
try {
    $venv = Join-Path $kok '.venv-build'
    $py = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path $py)) {
        # python.org kurulumu varsa o; Store Python yedek.
        $taban = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
        if (Test-Path $taban) { & $taban -m venv $venv } else { & py -3.13 -m venv $venv }
    }
    & $py -m pip install --disable-pip-version-check -q --upgrade -r requirements-dev.txt
    & "$PSScriptRoot\hazirla.ps1"
    & $py -m PyInstaller --noconfirm --clean --distpath "$kok\dist" --workpath "$kok\build" "$PSScriptRoot\ytmp3pldl.spec"
    $surum = (& $py -c "import surum; print(surum.__version__)").Trim()
    & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" /Q "/DSurum=$surum" "$PSScriptRoot\ytmp3pldl.iss"
    Write-Host "Kurulum: dist\ytmp3pldl-kurulum-$surum.exe"
}
finally { Pop-Location }
```

- [ ] **Step 5: Derle ve paketli exe'yi doğrula**

Run: `pwsh -File paketleme\derle.ps1`
Expected: son satır `Kurulum: dist\ytmp3pldl-kurulum-1.0.0.exe`, dosya var.

Sonra paketli exe'nin yt-dlp'yi gömülü değil zip'ten yüklediğini kontrol et:

```powershell
$env:YTMP3PLDL_VERI = "$env:TEMP\ytmp3pldl-paket-$(Get-Random)"
Start-Process dist\ytmp3pldl\ytmp3pldl.exe -ArgumentList '--oz-test-yukle', "`"$env:TEMP\pk.json`"" -Wait
Remove-Item Env:YTMP3PLDL_VERI
Get-Content $env:TEMP\pk.json
```

Expected: `"kaynak": "yedek"` ve `"yt_dlp_dosyasi"` yolu `...\_internal\vendor\yt-dlp\yt_dlp\__init__.py` biçiminde (`vendor\yt-dlp` geçmeli). Geçmiyorsa yt_dlp PYZ'ye gömülmüş demektir: spec'teki `a.pure` filtresini düzelt.

Aynı biçimde `--oz-test` ile koş; `"ok": true`, `"formatlar"` içinde `"18"` yok, `"deno"` `_internal\vendor\deno.exe`'yi göstermeli.

**Store Python sorunu çıkarsa** (PyInstaller hatası ya da exe açılmıyor, log'da DLL/`python313.dll` hatası): `winget install Python.Python.3.13 --scope user`, `Remove-Item -Recurse .venv-build`, Step 5'i tekrarla (derle.ps1 python.org kurulumunu tercih eder).

- [ ] **Step 6: Elle bakılacak (Emre'ye rapor et, kapıyı bloklamaz)**

GUI'yi `dist\ytmp3pldl\ytmp3pldl.exe` ile aç, bir MP3 indir: indirme sırasında siyah konsol penceresi (ffmpeg/Deno) açılıyor mu? yt-dlp'nin `Popen`'ı `STARTF_USESHOWWINDOW` ile gizler; açılıyorsa raporla.

- [ ] **Step 7: Commit**

```powershell
git add paketleme/hazirla.ps1 paketleme/ytmp3pldl.spec paketleme/ytmp3pldl.iss paketleme/derle.ps1
git commit -m "Paketleme: vendor hazirlama, PyInstaller spec, Inno Setup betigi, derle.ps1"
```

---

### Task 7: Belgeler, temizlik ve bitti kapısı

**Files:**
- Modify: `README.md` (tamamı), `IMPLEMENTATION.md` (tamamı)
- Delete: `baslat.bat`
- Çalıştır (değiştirmeden): `paketleme/kapi.ps1`

**Interfaces:**
- Consumes: Task 1-6'nın tamamı.
- Produces: `KAPI: PASS`.

- [ ] **Step 1: `README.md`**

````markdown
# YouTube İndirici (ytmp3pldl)

Tek video ya da tüm oynatma listesini **MP3** (ses) veya **MP4** (video) olarak indiren, sade arayüzlü bir Windows uygulaması. Python ya da başka bir program kurmak gerekmez.

## Kurulum (Windows 10/11)

1. [Son sürüm](https://github.com/EmreBHCC/ytmp3pldl/releases/latest) sayfasından `ytmp3pldl-kurulum-<sürüm>.exe` dosyasını indir.
2. Dosyaya çift tıkla. Windows mavi bir "Bilgisayarınız korundu" (SmartScreen) penceresi gösterirse **Ek bilgi → Yine de çalıştır**'a bas. Uygulama dijital olarak imzalı olmadığı için bu uyarı ilk kurulumda çıkar.
3. Kurulum yönetici izni istemez. Başlat menüsüne (istersen masaüstüne de) **YouTube İndirici** kısayolu koyar.

Kaldırmak için: **Ayarlar → Uygulamalar → YouTube İndirici → Kaldır**.

## Güncellemeler

- YouTube'daki değişikliklere uyum sağlayan indirme bileşeni (yt-dlp) günde en çok bir kez kendiliğinden güncellenir; yenisi bir sonraki açılışta devreye girer. İndirilen dosya doğrulanmadan kullanılmaz.
- Uygulamanın yeni sürümü çıkınca pencerenin üstünde **"Yeni sürüm var"** şeridi görünür. **İndir**'e basıp yeni kurulum dosyasını çalıştırmak yeterli.
- İnternet yokken de açılır.

## Kullanım

1. Üstteki kutuya bir YouTube video veya oynatma listesi linkini yapıştır, **Ekle**'ye (ya da Enter'a) bas.
2. **Format** olarak MP3 ya da MP4 seç, ardından **Kalite** seç.
3. Gerekirse **Kayıt Klasörü**'nü değiştir.
4. İndirmek istemediğin videoların kutusunun işaretini kaldır ya da ✕ ile listeden çıkar.
5. **İndir**'e bas. Her satırda ilerleme yüzdesi ve hız görünür.
6. Gerekirse **İptal Et** ile devam eden indirmeleri durdur.

## Özellikler

- Video ya da oynatma listesi linkini otomatik algılar; birden fazla linki alt alta yapıştırabilirsin
- MP3 (128/192/256/320 kbps) veya MP4 (360p – en yüksek kalite); MP4'te her cihazda açılan H.264 tercih edilir
- Aynı anda 3 indirme, her video için ayrı ilerleme çubuğu, iptal
- Oynatma listeleri kendi alt klasörüne kaydedilir

## Notlar

- Yalnızca indirme izniniz olan ya da telif hakkı size ait içerikleri indirin; YouTube'un kullanım şartlarına uyun.
- Çok uzun oynatma listelerinde ilk listeleme birkaç saniye sürebilir.
- Bir video indirilemezse ilgili satırda "Hata: ..." yazar. Sorun sürerse `%LOCALAPPDATA%\ytmp3pldl\log.txt` dosyasını gönder.

## Geliştirici

Windows, Python 3.13, PowerShell 7, [Inno Setup 6](https://jrsoftware.org/isinfo.php).

```powershell
py -3.13 -m venv .venv-build
.venv-build\Scripts\python -m pip install -r requirements-dev.txt
.venv-build\Scripts\python -m pytest
.venv-build\Scripts\python main.py
```

- Kurulum dosyası: `pwsh -File paketleme\derle.ps1` → `dist\ytmp3pldl-kurulum-<sürüm>.exe`
- Bitti kapısı (derle + test + sessiz kurulum + öz testler + kaldırma): `pwsh -File paketleme\kapi.ps1`
- Yayın: `surum.py`'de `__version__`'ı artır → `derle.ps1` → GitHub'da `v<sürüm>` release'i aç, kurulum dosyasını ekle.
````

- [ ] **Step 2: `IMPLEMENTATION.md`**

````markdown
# ytmp3pldl — Implementasyon Kaydı

> "Ne yaptık"ı tutar. Tasarım ve karar gerekçesi ayrı tasarım notunda (repoda değil).
> Uygulama planı: `docs/superpowers/plans/2026-10-30-kurulabilir-paket.md`.

## Ne bu

YouTube video/oynatma listesi linklerini **MP3** veya **MP4** olarak indiren `customtkinter`
masaüstü uygulaması. Kullanıcıya `ytmp3pldl-kurulum-<sürüm>.exe` (Inno Setup) olarak gider;
Python gerekmez.

## Dosyalar

```
main.py             giriş: akışlar -> log -> yt-dlp yükleme -> (öz test | GUI + güncelleyici)
gui.py              arayüz; yeni sürüm şeridi, alt sağda sürüm etiketi
downloader.py       yt-dlp sarmalayıcısı (GUI'den bağımsız); Deno js_runtimes, avc1 video
ytdlp_yukleyici.py  yt-dlp'yi aktif -> önceki -> paketteki yedek -> sistem sırasıyla import eder
guncelleyici.py     günde bir: yt-dlp release'i SHA256 ile indir; uygulama yeni sürüm kontrolü
durum.py            <veri>/durum.json (aktif, onceki, kara_liste, son_kontrol), atomik yazım
yollar.py           veri klasörü, paket klasörü (_MEIPASS), vendor yolları
surum.py            __version__, GITHUB_REPO, YTDLP_REPO (tek kaynak)
paketleme/          hazirla.ps1, ytmp3pldl.spec, ytmp3pldl.iss, derle.ps1, kapi.ps1 (dondurulmuş)
tests/              pytest, ağsız
```

## Çalışma zamanı

- **Veri klasörü** `%LOCALAPPDATA%\ytmp3pldl\` (testte `YTMP3PLDL_VERI`): `yt-dlp\<sürüm>\yt-dlp`,
  `durum.json`, `log.txt` (1 MB, 2 yedek).
- **yt-dlp yükleme:** yt-dlp release dosyası bir zip; yolu `sys.path`'e konup zipimport ile
  yüklenir. PyInstaller'ın gömülü yükleyicisi `sys.path`'ten önce geldiği için `yt_dlp` ve
  `yt_dlp_ejs` spec'te `a.pure`'dan çıkarılır (analiz edilir ki bağımlılıkları paketlensin).
  İmport edilemeyen indirilmiş sürüm kara listeye girer; sebep Python sürümüyse GUI
  "uygulamanın yeni sürümü gerekiyor" şeridini gösterir.
- **Güncelleme:** `guncelleyici.arka_planda_calistir` daemon thread'i. yt-dlp'nin son release'i
  `SHA2-256SUMS` ile doğrulanır, `.tmp` → zip kontrolü → `os.replace`; bir sonraki açılışta aktif.
  En çok aktif + önceki (+ o an çalışan) tutulur. `son_kontrol` yalnız başarılı yt-dlp
  kontrolünde yazılır. Uygulamanın kendi release'i daha yeniyse şerit; exe kendini değiştirmez.
- **Deno** `vendor/deno.exe` (v2.9.8, sabit) `js_runtimes` ile verilir; varsayılan YouTube
  istemcileri JS çözümü ister. Eski `player_client: android` zorlaması yalnız format 18
  (~96 kbps) getiriyordu, kaldırıldı.
- **Öz test bayrakları** (kapı için, GUI açmaz): `--oz-test-yukle <json>`, `--oz-test <json>`.

## Derleme ve kapı

`pwsh -File paketleme\derle.ps1`: `.venv-build` (python.org 3.13 varsa o, yoksa `py -3.13`) →
`requirements-dev.txt` → `hazirla.ps1` (son yt-dlp + SUMS doğrulaması, Deno sha256) →
PyInstaller onedir (`console=False`) → `ISCC /DSurum=`. Bitti kapısı `paketleme\kapi.ps1`.

## Açık / sonra

- Kod imzalama yok: SmartScreen uyarısı ilk kurulumda beklenir.
- Paralellik sabiti (`max_workers=3`) GUI'den ayarlanamıyor.
- Deno kendini güncellemiyor (v1 kapsamı dışı).
````

- [ ] **Step 3: `baslat.bat`'ı sil, testleri koş**

```powershell
git rm baslat.bat
.venv-build\Scripts\python.exe -m pytest -q
```

Expected: tüm testler PASS.

- [ ] **Step 4: Bitti kapısını koş (değiştirmeden)**

Run: `pwsh -File paketleme\kapi.ps1`
Expected: 6 satırın hepsi `PASS`, son satır `KAPI: PASS`, çıkış kodu 0.

FAIL olursa: kapı betiğine ve hedeflerine dokunma; hatayı ilgili görevin dosyasında düzelt, o dosyanın testini koş, kapıyı tekrar koş. Kapı çıktısını olduğu gibi raporla.

- [ ] **Step 5: Commit**

```powershell
git add README.md IMPLEMENTATION.md
git commit -m "Belgeler: kurulum/guncelleme README'si, IMPLEMENTATION guncel; baslat.bat kalkti"
```

---

## Plan sonrası (bu planın dışında, Emre onayıyla)

Kapı PASS → Emre onaylarsa: GitHub'da public `EmreBHCC/ytmp3pldl`, push, `v1.0.0` release'i + `dist\ytmp3pldl-kurulum-1.0.0.exe`. Release çıkınca `uygulama_kontrol` 404 yerine gerçek cevap alır.
