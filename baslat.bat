@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=python"
    ) else (
        echo Python bulunamadi.
        echo Lutfen https://www.python.org/downloads/ adresinden Python 3.10 veya uzerini kurun.
        echo Kurulum sirasinda "Add python.exe to PATH" secenegini isaretlemeyi unutmayin.
        echo.
        pause
        exit /b 1
    )
)

echo Gerekli kutuphaneler kontrol ediliyor / kuruluyor, bu ilk calistirmada birkac dakika surebilir...
%PYTHON% -m pip install --upgrade pip >nul 2>nul
%PYTHON% -m pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo.
    echo Kutuphaneler kurulurken bir hata olustu. Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo.
echo Uygulama baslatiliyor...
%PYTHON% "%~dp0main.py"
if %errorlevel% neq 0 (
    echo.
    echo Uygulama bir hatayla kapandi.
    pause
)

endlocal
