# Bitti kapisi: derle -> pytest -> sessiz kurulum -> oz testler -> kaldirma.
# Cikis kodu 0 = PASS. Bu dosya ve hedefleri uygulama gorevlerinde DEGISTIRILMEZ.
# Calistir: pwsh -File paketleme\kapi.ps1
$ErrorActionPreference = 'Stop'
$kok = Split-Path $PSScriptRoot -Parent
$sonuclar = [ordered]@{}

function Kontrol($ad, [scriptblock]$kosul) {
    try { $sonuclar[$ad] = [bool](& $kosul) }
    catch { $sonuclar[$ad] = $false; Write-Host "  $ad hata: $_" }
}

Push-Location $kok
try {
    & "$PSScriptRoot\derle.ps1"
    $py = "$kok\.venv-build\Scripts\python.exe"

    Kontrol 'pytest' { & $py -m pytest -q | Out-Host; $LASTEXITCODE -eq 0 }

    $surum = (& $py -c "import surum; print(surum.__version__)").Trim()
    $kurulum = "$kok\dist\ytmp3pldl-kurulum-$surum.exe"
    $gecici = Join-Path ([IO.Path]::GetTempPath()) ("ytmp3pldl-kapi-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
    $hedef = "$gecici\uygulama"
    New-Item -ItemType Directory -Force $gecici | Out-Null
    $exe = "$hedef\ytmp3pldl.exe"

    function OzTest($bayrak, $veriDir, $cikti) {
        $env:YTMP3PLDL_VERI = $veriDir
        try { Start-Process $exe -ArgumentList $bayrak, "`"$cikti`"" -Wait | Out-Null }
        finally { Remove-Item Env:YTMP3PLDL_VERI }
        Get-Content $cikti -Raw -Encoding utf8 | ConvertFrom-Json
    }

    Kontrol 'sessiz kurulum (admin yok)' {
        $p = Start-Process $kurulum -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', "/DIR=`"$hedef`"", '/MERGETASKS=!masaustu' -Wait -PassThru
        $p.ExitCode -eq 0 -and (Test-Path $exe)
    }

    $sonTag = (Invoke-RestMethod 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest').tag_name

    Kontrol 'bos veri: paketteki yedek yt-dlp yuklenir (agsiz yol)' {
        $r = OzTest '--oz-test-yukle' "$gecici\veri-bos" "$gecici\yukle-bos.json"
        $r.ok -and $r.yukleme.kaynak -eq 'yedek'
    }

    Kontrol "oz test: yt-dlp $sonTag indirilir + MP3 (format 18 degil)" {
        $r = OzTest '--oz-test' "$gecici\veri" "$gecici\oz.json"
        if (-not $r.ok) { Write-Host ($r | ConvertTo-Json -Depth 5) }
        $r.ok -and $r.guncellenen -eq $sonTag -and $r.mp3_bayt -gt 50000 -and ($r.formatlar -notcontains '18')
    }

    Kontrol 'ikinci acilis: indirilen yt-dlp aktif' {
        $r = OzTest '--oz-test-yukle' "$gecici\veri" "$gecici\yukle-2.json"
        $r.ok -and $r.yukleme.kaynak -eq 'aktif' -and $r.yukleme.surum -eq $sonTag
    }

    Kontrol 'sessiz kaldirma' {
        $p = Start-Process "$hedef\unins000.exe" -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES' -Wait -PassThru
        Start-Sleep -Seconds 3
        $p.ExitCode -eq 0 -and -not (Test-Path $exe)
    }
}
finally { Pop-Location }

$sonuclar.GetEnumerator() | ForEach-Object { '{0,-60} {1}' -f $_.Key, $(if ($_.Value) { 'PASS' } else { 'FAIL' }) }
if ($sonuclar.Count -lt 6 -or $sonuclar.Values -contains $false) { 'KAPI: FAIL'; exit 1 }
'KAPI: PASS'; exit 0
