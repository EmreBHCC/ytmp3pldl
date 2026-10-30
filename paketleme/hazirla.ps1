# vendor/: guncel yt-dlp (SHA2-256SUMS ile dogrulanir) + sabit surum Deno (sha256 sabit).
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$ProgressPreference = 'SilentlyContinue'
$kok = Split-Path $PSScriptRoot -Parent
$vendor = Join-Path $kok 'vendor'
New-Item -ItemType Directory -Force $vendor | Out-Null

function Sha256($yol) { (Get-FileHash -Algorithm SHA256 $yol).Hash.ToLowerInvariant() }

# yt-dlp: zipimport'lu tek dosya; yt_dlp_ejs cozucusunu icinde tasir
$rel = Invoke-RestMethod 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
$varlik = @{}
$rel.assets | ForEach-Object { $varlik[$_.name] = $_.browser_download_url }
$sums = Join-Path $vendor 'SHA2-256SUMS'
$gecici = Join-Path $vendor 'yt-dlp.tmp'
Invoke-WebRequest $varlik['SHA2-256SUMS'] -OutFile $sums
Invoke-WebRequest $varlik['yt-dlp'] -OutFile $gecici
$beklenen = (Select-String -Path $sums -Pattern '^([0-9a-f]{64})\s+\*?yt-dlp$').Matches[0].Groups[1].Value
Remove-Item $sums
if ((Sha256 $gecici) -ne $beklenen) { Remove-Item $gecici; throw "yt-dlp $($rel.tag_name) SHA256 tutmadi" }
Move-Item -Force $gecici (Join-Path $vendor 'yt-dlp')
Write-Host "vendor/yt-dlp: $($rel.tag_name)"

# Deno: sabit surum, kendini guncellemez (v1)
$denoSurum = 'v2.9.8'
$denoSha = 'cba84b26e0df5ae7f74fc66b86a95b866872a86292ebd84fa1e959927edd93bf'
$deno = Join-Path $vendor 'deno.exe'
$isaret = Join-Path $vendor 'deno.surum'
$hazir = (Test-Path $deno) -and (Test-Path $isaret) -and ((Get-Content $isaret -Raw).Trim() -eq $denoSurum)
if (-not $hazir) {
    $zip = Join-Path $vendor 'deno.zip'
    Invoke-WebRequest "https://github.com/denoland/deno/releases/download/$denoSurum/deno-x86_64-pc-windows-msvc.zip" -OutFile $zip
    if ((Sha256 $zip) -ne $denoSha) { Remove-Item $zip; throw "Deno $denoSurum SHA256 tutmadi" }
    Expand-Archive -Force $zip $vendor
    Remove-Item $zip
    Set-Content -NoNewline -Path $isaret -Value $denoSurum
}
Write-Host "vendor/deno.exe: $denoSurum"
