import json
import os
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_oz_test_yukle_bos_veri(tmp_path):
    cikti = tmp_path / "yukle.json"
    ortam = dict(os.environ, YTMP3PLDL_VERI=str(tmp_path / "veri"))
    p = subprocess.run([sys.executable, os.path.join(KOK, "main.py"), "--oz-test-yukle", str(cikti)],
                       env=ortam, cwd=KOK, timeout=120)
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert p.returncode == 0
    assert sonuc["ok"] is True
    assert sonuc["yukleme"]["kaynak"] in ("yedek", "sistem")
    assert sonuc["yukleme"]["surum"]
    assert sonuc["yt_dlp_dosyasi"]
    assert (tmp_path / "veri" / "log.txt").is_file()
