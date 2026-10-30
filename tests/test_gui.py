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


class SahteSatir:
    def __init__(self):
        import threading
        self.uid = "u1"
        self.item = {"url": "https://example.invalid/v"}
        self.cancel_event = threading.Event()
        self.state = "downloading"


def test_getirme_hatasi_log_a_yazilir(app, monkeypatch, caplog):
    import downloader

    def patlak(url):
        raise RuntimeError("ham hata")

    monkeypatch.setattr(downloader, "fetch_entries", patlak)
    with caplog.at_level("WARNING", logger="gui"):
        app._fetch_worker(["https://example.invalid/v"])
    assert any("https://example.invalid/v" in r.getMessage() and r.exc_info for r in caplog.records)


def test_indirme_hatasi_log_a_yazilir(app, monkeypatch, caplog):
    import downloader

    def patlak(*a, **k):
        raise RuntimeError("ham hata")

    monkeypatch.setattr(downloader, "download_item", patlak)
    with caplog.at_level("WARNING", logger="gui"):
        app._download_worker(SahteSatir(), "mp3", "192", ".", None)
    assert any("https://example.invalid/v" in r.getMessage() and r.exc_info for r in caplog.records)
