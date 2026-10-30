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
