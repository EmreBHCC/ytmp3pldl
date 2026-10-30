# Derleme: venv -> bagimliliklar -> vendor (hazirla) -> PyInstaller -> Inno Setup.
# Cikti: dist\ytmp3pldl\ (onedir) ve dist\ytmp3pldl-kurulum-<surum>.exe
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$kok = Split-Path $PSScriptRoot -Parent
Push-Location $kok
try {
    $venv = Join-Path $kok '.venv-build'
    $py = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path $py)) {
        # python.org kurulumu varsa o; Store Python yedek.
        $taban = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
        if (Test-Path $taban) { & $taban -m venv $venv } else { & py -3.13 -m venv $venv }
    }
    & $py -m pip install --disable-pip-version-check -q --upgrade -r requirements-dev.txt
    & "$PSScriptRoot\hazirla.ps1"
    & $py -m PyInstaller --noconfirm --clean --distpath "$kok\dist" --workpath "$kok\build" "$PSScriptRoot\ytmp3pldl.spec"
    $surum = (& $py -c "import surum; print(surum.__version__)").Trim()
    & "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" /Q "/DSurum=$surum" "$PSScriptRoot\ytmp3pldl.iss"
    Write-Host "Kurulum: dist\ytmp3pldl-kurulum-$surum.exe"
}
finally { Pop-Location }
