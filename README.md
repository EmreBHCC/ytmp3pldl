# YouTube İndirici

Tek video ya da tüm oynatma listesini **MP3** (ses) veya **MP4** (video) olarak indirmeni sağlayan, sade ve modern arayüzlü bir masaüstü uygulaması.

## Özellikler

- Video linki veya playlist linki — otomatik algılar, playlist'teki tüm videoları listeye ekler
- Aynı anda birden fazla link ekleyebilme (alt alta / boşlukla ayırarak yapıştır)
- MP3 (128/192/256/320 kbps) veya MP4 (360p – en yüksek kalite) seçimi
- Listeden istediğin videoları seçip/kaldırıp toplu indirme
- Aynı anda 3 indirmeye kadar paralel çalışma, her video için ayrı ilerleme çubuğu
- İptal etme desteği (tek video ya da tüm kuyruk)
- Kayıt klasörünü seçebilme; playlist indirmelerinde her playlist kendi alt klasörüne kaydedilir
- **ffmpeg kurulumu gerekmez** — `imageio-ffmpeg` paketiyle otomatik gelir

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
python main.py
```

## Kullanım

1. Üstteki kutuya bir YouTube video veya playlist linkini yapıştır, **Ekle**'ye bas (veya Enter'a bas).
2. **Format** olarak MP3 ya da MP4 seç, ardından **Kalite** seç.
3. Gerekirse **Kayıt Klasörü**'nü değiştir.
4. Listede indirmek istemediğin videoların kutusunu işaretini kaldır ya da ✕ ile listeden çıkar.
5. **İndir**'e bas. Her satırda ilerleme yüzdesi ve hızı görünür.
6. Gerekirse **İptal Et** ile devam eden indirmeleri durdurabilirsin.

## Notlar

- Sadece indirme/kopyalama izniniz olan ya da telif hakkı size ait içerikleri indirin; YouTube'un kullanım şartlarına uyun.
- Çok uzun playlist'lerde (yüzlerce video) ilk listeleme birkaç saniye sürebilir; bu normaldir.
- İnternet bağlantınız veya YouTube'un video kısıtlamaları nedeniyle bazı videolar indirilemeyebilir; bu durumda ilgili satırda "Hata: ..." mesajı görünür.

## Bilinen sınırlama: MP4 çözünürlüğü

YouTube, Temmuz 2026 itibarıyla yüksek çözünürlüklü (720p/1080p) video akışlarını yalnızca "doğrulanmış" (PO token) isteklere açıyor. Bu doğrulama olmadan (uygulamamızın kullandığı yöntemle) bazı videolar yalnızca **360p** olarak indirilebiliyor — bu bir hata değil, YouTube tarafındaki kısıtlamadır. Ses (MP3) indirmeleri bu kısıtlamadan etkilenmez, her zaman seçilen kalitede iner.
