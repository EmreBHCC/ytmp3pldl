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
