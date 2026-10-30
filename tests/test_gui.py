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
