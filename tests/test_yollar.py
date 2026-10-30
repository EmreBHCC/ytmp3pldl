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
