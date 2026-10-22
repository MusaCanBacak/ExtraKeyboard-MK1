@echo off
rem =====================================================================
rem  ExtraKeyboard MK1 - Firmware Yukleyici (Windows)
rem  Cift tiklayin. Karti tanir, dogru imaji secer, kutuyu acmadan yukler.
rem  Gereken: Python 3.8+ (esptool ve pyserial ilk calistirmada kurulur)
rem =====================================================================
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set "PYCMD=py -3") else (set "PYCMD=python")

%PYCMD% -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul
if not %errorlevel%==0 (
    echo HATA: Python 3.8+ bulunamadi.
    echo https://www.python.org adresinden kurun ve kurulumda
    echo "Add python.exe to PATH" kutusunu isaretleyin.
    pause
    exit /b 1
)

rem Paketler bu klasordeki .venv'e kurulur; sistemdeki Python'a dokunulmaz.
rem (Parantezli blokta errorlevel CALISMA aninda okunsun diye "if errorlevel 1".)
".venv\Scripts\python.exe" -c "import esptool, serial" >nul 2>nul
if not %errorlevel%==0 (
    echo Ilk calistirma: esptool ve pyserial kuruluyor, internet gerekir...
    if exist ".venv" rmdir /s /q ".venv"
    %PYCMD% -m venv .venv
    if errorlevel 1 ( echo HATA: sanal ortam olusturulamadi. & pause & exit /b 1 )
    ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r gereksinimler.txt
    if errorlevel 1 ( echo HATA: paketler kurulamadi. Internet baglantinizi kontrol edin. & pause & exit /b 1 )
)

".venv\Scripts\python.exe" yukle.py %*
echo.
pause
