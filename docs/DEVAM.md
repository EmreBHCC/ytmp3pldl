# Devam notu (2026-10-30, plan yazilmadan durduruldu)

Tasarim: ayri tasarim notunda (onayli, repoda degil). Bitti kapisi: `paketleme/kapi.ps1`
(donduruldu, degistirilmez). Inno Setup 6.7.3 kurulu: `%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe`.

## Siradaki

1. `superpowers:writing-plans` ile tam plani `docs/superpowers/plans/2026-10-30-kurulabilir-paket.md`'ye yaz
   (asagidaki gorev listesi + arayuzler hazir, tam kodla doldur).
2. Emre "subagent'larla calis" dedi: `superpowers:subagent-driven-development`, gorev basina commit, sirayla.
3. Kapi PASS -> Emre onayiyla public repo `EmreBHCC/ytmp3pldl` + `v1.0.0` release.

## Gorevler ve arayuzler (taslak)

1. **Temel:** `surum.py` (`__version__="1.0.0"`, `GITHUB_REPO="EmreBHCC/ytmp3pldl"`, `YTDLP_REPO="yt-dlp/yt-dlp"`);
   `yollar.py` (`veri_klasoru()` - `YTMP3PLDL_VERI` ortam degiskeni ya da `%LOCALAPPDATA%\ytmp3pldl`;
   `paket_klasoru()` - `sys._MEIPASS` ya da repo koku; `yedek_ytdlp_yolu()` = `<paket>/vendor/yt-dlp`;
   `deno_yolu()` = `<paket>/vendor/deno.exe` ya da `shutil.which("deno")`);
   `durum.py` (`oku/yaz(veri_dir)` atomik, anahtarlar aktif/onceki/kara_liste/son_kontrol;
   `ytdlp_dosyasi(veri_dir, surum)` = `<veri>/yt-dlp/<surum>/yt-dlp`); `pytest.ini` (pythonpath=.);
   `requirements.txt` (customtkinter, imageio-ffmpeg) + `requirements-dev.txt` (+yt-dlp, pytest, pyinstaller);
   `.venv-build` = `py -3.13 -m venv`; `.gitignore`'a `vendor/`.
2. **`ytdlp_yukleyici.py`:** `yukle(veri_dir, yedek_yolu, modul="yt_dlp") -> YuklemeSonucu(kaynak, surum, python_yetersiz)`;
   sira aktif -> onceki -> yedek -> sistem; basarisiz indirilmis surum kara listeye; "unsupported version of Python"
   ya da SyntaxError -> python_yetersiz. Testler sahte zip paketiyle (`modul="sahte_ytdlp"`).
3. **`guncelleyici.py`:** `surum_tuple`, `daha_yeni`, `kontrol_zamani_geldi` (24 sa),
   `ytdlp_guncelle(veri_dir, mevcut, getir_json, getir_bayt, zorla=False) -> tag|None`
   (SHA2-256SUMS dogrula, `.tmp` -> `os.replace`, `zipfile.is_zipfile`, onceki<-aktif, en cok 2 surum),
   `uygulama_kontrol() -> (surum, url)|None`, `kontrol_et(...)` (son_kontrol yalniz basarili yt-dlp kontrolunde),
   `arka_planda_calistir(veri_dir, mevcut_ytdlp, bildir)`. Ag fonksiyonlari enjekte, testte sahte GitHub.
4. **`downloader.py`:** `extractor_args` (android) kalkar; deno varsa `js_runtimes={"deno":{"path":...}}`;
   video `bestvideo[vcodec^=avc1][height<=Q]+bestaudio[ext=m4a]/...`; `playlist.py` silinir.
5. **`main.py` + `gui.py`:** sira log (`RotatingFileHandler` -> `<veri>/log.txt`) -> stdout/stderr None ise devnull ->
   `yukle` -> `--oz-test-yukle <json>` / `--oz-test <json>` (zorla guncelle + jNQXAC9IVRw MP3, formatlar, mp3_bayt, ok) ->
   `App(ytdlp_surum, python_yetersiz)` + guncelleyici thread (`app.after(0, app.yeni_surum_goster, s, u)`).
   GUI: top_bar row 1'de gizli banner (`_banner_ac(metin, buton, komut)`), row 7 sagda `v<surum> · yt-dlp <surum>`.
6. **Paketleme:** `hazirla.ps1` (vendor: son yt-dlp + SUMS dogrulama; Deno v2.9.8 zip sha256
   `cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf`); `ytmp3pldl.spec` (onedir, console=False,
   yt_dlp analiz edilir ama `a.pure`'dan cikarilir, stdlib hiddenimports, customtkinter + imageio_ffmpeg collect,
   vendor/yt-dlp + deno.exe data); `ytmp3pldl.iss` (UTF-8 BOM, PrivilegesRequired=lowest,
   `{localappdata}\Programs\ytmp3pldl`, Turkish.isl, task `masaustu`, cikti `dist\ytmp3pldl-kurulum-<surum>.exe`);
   `derle.ps1` (venv -> pip -> hazirla -> PyInstaller -> ISCC /DSurum=). Store Python sorun cikarirsa
   python.org 3.13 (`winget install Python.Python.3.13 --scope user`).
7. **README/IMPLEMENTATION** guncelle (kullanici: Releases + SmartScreen notu; gelistirici bolumu),
   `baslat.bat` kalkar, `kapi.ps1` PASS.

Elle bakilacak: Deno/ffmpeg alt sureci pencere modunda konsol penceresi aciyor mu.
