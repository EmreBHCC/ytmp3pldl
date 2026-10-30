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
