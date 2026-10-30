# ytmp3pldl — Implementasyon Kaydı

> Bu dosya "ne yaptık"ı tutar. Tasarım niyeti değişirse burada güncellenir; ön-tasarım/karar
> gerekçesi ayrı tasarım notundadır (repoda değil; henüz açılmadıysa bu
> dosya o dosyanın da kaynağıdır).

## Ne bu

YouTube video/playlist linklerini **MP3** veya **MP4** olarak indiren, `customtkinter` ile
yazılmış masaüstü GUI uygulaması. Tek kullanıcılı, yerel çalışan bir araç — sunucu/backend yok.

## Mevcut durum (2026-09-16 itibarıyla)

Çalışır durumda, üretimde kullanılabilir seviyede. Dört dosyalık küçük bir kod tabanı:

```
main.py          # giriş noktası, App().mainloop()
gui.py           # tüm arayüz + iş akışı orkestrasyonu (customtkinter)
downloader.py    # yt-dlp sarmalayıcısı, GUI'den bağımsız/yeniden kullanılabilir katman
playlist.py      # boş — kullanılmıyor, muhtemelen playlist mantığı downloader.py'a taşındı
requirements.txt # yt-dlp, customtkinter, imageio-ffmpeg
baslat.bat       # Windows çift-tık başlatıcı
```

## Mimari

**İki katman, net ayrım:**
- `downloader.py`: yt-dlp etrafında ince bir sarmalayıcı. `fetch_entries(url)` bir video/playlist
  linkini video listesine çözer (metadata-only, indirme yok). `download_item(...)` tek bir
  videoyu indirir, ilerleme callback'i (`progress_hook`) alır. GUI'ye hiç bağımlı değil —
  CLI'dan da kullanılabilir.
- `gui.py`: `customtkinter` tabanlı pencere. `App` ana sınıf, `VideoRow` her video satırının
  state makinesi (`waiting → downloading → done/error/cancelled`).

**Eşzamanlılık modeli:**
- Fetch (metadata çözme) ayrı bir thread'de yapılır, sonuç `self.after(0, ...)` ile ana thread'e
  postalanır (tkinter thread-safe değil, bu yüzden UI güncellemeleri hep ana thread'den).
- İndirmeler `ThreadPoolExecutor(max_workers=3)` ile paralel — aynı anda en fazla 3 indirme.
- İlerleme bildirimleri `queue.Queue` üzerinden akar; `_drain_queue` her 100ms'de kuyruğu boşaltıp
  UI'yi günceller (worker thread'lerden doğrudan widget güncellemesi yapılmıyor — doğru desen).
- İptal, `threading.Event` (`cancel_event`) ile kooperatif: yt-dlp'nin progress_hook'u içinde
  event set edilmişse exception fırlatılıp indirme durur.

**ffmpeg bağımlılığı:** `imageio-ffmpeg` paketiyle geliyor, kullanıcı ayrıca kurmuyor. `downloader.py`
başında `FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()` ile çözülüyor.

**Format/kalite eşlemesi:** MP3 için `bestaudio/best` + `FFmpegExtractAudio` postprocessor
(128/192/256/320 kbps). MP4 için `bestvideo[ext=mp4]+bestaudio[ext=m4a]` merge, çözünürlük üst
sınırı ile (`height<=quality`).

## Bilinen sınırlama

YouTube, 2026 Temmuz'dan beri yüksek çözünürlüklü (720p/1080p) video akışlarını yalnızca
"doğrulanmış" (PO token) isteklere açıyor. Bu uygulama PO token doğrulaması yapmıyor, dolayısıyla
bazı videolar MP4'te yalnızca 360p olarak inebiliyor. **Bu bir bug değil, YouTube tarafı kısıtlama.**
MP3/ses bu kısıtlamadan etkilenmiyor. README'de belgelendi (`README.md` "Bilinen sınırlama" bölümü).

`playlist.py` boş dosya — silinmemiş ama kullanılmıyor. Muhtemelen erken taslak, `downloader.py`
içindeki `fetch_entries` playlist algılamasını da üstlendi.

## Geliştirmeye devam ederken

- **PO token / yüksek çözünürlük:** yt-dlp'nin PO token eklentileri (`bgutil-ytdlp-pot-provider`
  gibi) araştırılabilir; şu an bilinçli olarak es geçildi (karmaşıklık/bakım maliyeti).
- **`playlist.py`** temizlenebilir ya da gerçekten ayrı bir sorumluluk (örn. playlist-özel
  ayarlar: "her playlist kendi klasörüne" davranışını buraya taşımak) verilip doldurulabilir.
- **Paralellik sabiti** (`max_workers=3`) hardcoded — GUI'den ayarlanabilir kılmak küçük bir iş.
- **Test yok.** Küçük ve tek-kullanıcılı bir araç olduğu için şimdilik bilinçli tercih; genişlerse
  en azından `downloader.py` (GUI'siz katman) için birim test eklemek ucuz olur.
- Paketleme/dağıtım (`.exe`'ye derleme, PyInstaller vb.) hiç ele alınmadı — şu an yalnızca
  `python main.py` ile yerel çalıştırma var.
