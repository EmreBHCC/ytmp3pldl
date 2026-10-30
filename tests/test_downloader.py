import pytest

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


INTERNET = "İnternet bağlantısı yok gibi görünüyor. Bağlantıyı kontrol edip tekrar deneyin."
KALDIRILMIS = "Video kaldırılmış ya da gizli."
YAS = "Yaş doğrulaması isteyen videolar indirilemiyor."
LINK = "Bu bir YouTube linki değil gibi görünüyor."
DIGER = "Bu video indirilemedi. Sorun sürerse log.txt dosyasını gönderin."


@pytest.mark.parametrize("ham,beklenen", [
    ("[Errno 11001] getaddrinfo failed", INTERNET),
    ("<urlopen error [WinError 10060]>", INTERNET),
    ("The read operation timed out", INTERNET),
    ("Connection reset by peer", INTERNET),
    ("Network is unreachable", INTERNET),
    ("Unable to download API page: x", INTERNET),
    ("Private video. Sign in", KALDIRILMIS),
    ("Video unavailable", KALDIRILMIS),
    ("This video has been removed by the uploader", KALDIRILMIS),
    ("This video is not available", KALDIRILMIS),
    ("Sign in to confirm your age", YAS),
    ("This video is age-restricted", YAS),
    ("'abc' is not a valid URL", LINK),
    ("Unsupported URL: https://x", LINK),
    ("tamamen baska bir sey", DIGER),
])
def test_hata_metni(ham, beklenen):
    assert downloader.hata_metni(Exception(ham)) == beklenen
