@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
REM =====================================================================
REM  ExtraKeyboard MK1 - KALDIRMA ARACI (Windows)
REM
REM  Bu dosyaya cift tiklayin. Bilgisayarinizdan sunlari kaldirir:
REM    1. Calisan ExtraKeyboard uygulamasi (durdurulur)
REM    2. Sanal ortam (.venv) - kurulan Python paketleri
REM    3. Masaustundeki ExtraKeyboard.lnk kisayolu
REM    4. Baslangicta calistirma girdisi (varsa)
REM    5. On bellek klasorleri (__pycache__)
REM    6. Istege bagli: ayarlariniz (tus atamalari, profiller)
REM    7. Istege bagli: program klasorunun tamami (Geri Donusum Kutusu)
REM
REM  DIKKAT: 6. adim tus atamalarinizi siler ve geri alinamaz.
REM  Klavyenin kendi bellegindeki firmware SILINMEZ.
REM =====================================================================
cd /d "%~dp0"
set "PROJE=%CD%"

echo.
echo ======================================================
echo    ExtraKeyboard MK1 - Kaldirma
echo ======================================================
echo.
echo Program klasoru: %PROJE%
echo.
echo Kaldirilacaklar:
echo   - Sanal ortam (.venv) ve kurulu Python paketleri
echo   - Masaustu kisayolu ve baslangic girdisi
echo   - On bellek klasorleri
echo.
echo Ayarlariniz ve program klasoru ayrica sorulacak.
echo.
set /p ONAY="Devam etmek icin EVET yazip Enter'a basin: "
if /i not "%ONAY%"=="EVET" (
    echo Iptal edildi. Hicbir sey silinmedi.
    pause
    exit /b 0
)
echo.

REM --- 1) Calisan uygulamayi durdur -----------------------------------
REM  Not: yalnizca run_app.py calistiran Python surecleri durdurulur.
REM  "taskkill /IM python.exe" yazilmaz - o, kullanicinin acik olan diger
REM  Python programlarini da kapatirdi. wmic de kullanilmaz: Windows 11
REM  24H2 ile birlikte sistemden kaldirildi.
echo [1/6] Calisan uygulama durduruluyor...
set "DURDU=0"
for /f %%p in ('powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run_app.py*' }).Count" 2^>nul') do set "SAYI=%%p"
if not "%SAYI%"=="0" if not "%SAYI%"=="" (
    powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*run_app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
    set "DURDU=1"
)
if "!DURDU!"=="1" (echo       durduruldu) else (echo       ^(zaten calismiyordu^))

REM --- 2) Sanal ortam --------------------------------------------------
echo [2/6] Sanal ortam ^(.venv^) siliniyor...
if exist "%PROJE%\.venv" (
    rmdir /s /q "%PROJE%\.venv" 2>nul
    if exist "%PROJE%\.venv" (echo       SILINEMEDI - uygulama hala acik olabilir) else (echo       silindi)
) else (
    echo       ^(yoktu^)
)

REM --- 3) Masaustu kisayolu -------------------------------------------
echo [3/6] Masaustu kisayolu siliniyor...
set "BULUNDU=0"
for %%K in ("%USERPROFILE%\Desktop\ExtraKeyboard.lnk" "%PUBLIC%\Desktop\ExtraKeyboard.lnk") do (
    if exist %%K (
        del /f /q %%K 2>nul && (echo       silindi: %%K & set "BULUNDU=1")
    )
)
if "!BULUNDU!"=="0" echo       ^(kisayol bulunamadi^)

REM --- 4) Baslangic girdisi -------------------------------------------
echo [4/6] Baslangic girdisi temizleniyor...
set "BASGIRDI=0"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ExtraKeyboard.lnk" (
    del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ExtraKeyboard.lnk" 2>nul && set "BASGIRDI=1"
)
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ExtraKeyboard >nul 2>&1
if not errorlevel 1 (
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ExtraKeyboard /f >nul 2>&1 && set "BASGIRDI=1"
)
if "!BASGIRDI!"=="1" (echo       temizlendi) else (echo       ^(girdi yoktu^))

REM --- 5) On bellek ----------------------------------------------------
echo [5/6] On bellek klasorleri temizleniyor...
for /d /r "%PROJE%" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" 2>nul
)
del /s /q "%PROJE%\*.pyc" >nul 2>&1
if exist "%PROJE%\varliklar\_simge_ata.scpt.txt" del /f /q "%PROJE%\varliklar\_simge_ata.scpt.txt" >nul 2>&1
echo       temizlendi

REM --- 6) Ayarlar (istege bagli) --------------------------------------
echo.
echo ------------------------------------------------------
echo Ayarlariniz ^(tus atamalari, profiller, LED ayarlari^)
echo Dosyalar: config.json, macro_config.json
echo Silerseniz GERI ALINAMAZ. Programi tekrar kuracaksaniz
echo saklamak isteyebilirsiniz.
echo ------------------------------------------------------
set /p AYAR="Ayarlar da silinsin mi? (e/H): "
if /i "%AYAR%"=="e" (
    del /f /q "%PROJE%\config.json" "%PROJE%\macro_config.json" >nul 2>&1
    echo       ayarlar silindi
) else (
    echo       ayarlar korundu ^(%PROJE%\config.json^)
)

REM --- 7) Program klasoru (istege bagli) ------------------------------
echo.
echo ------------------------------------------------------
echo Program klasorunun tamami Geri Donusum Kutusu'na
echo tasinsin mi?
echo   %PROJE%
echo ^(Kalici silinmez - fikrinizi degistirirseniz oradan
echo  geri alabilirsiniz.^)
echo ------------------------------------------------------
set /p KLASOR="Klasor Geri Donusum Kutusu'na tasinsin mi? (e/H): "
set "TASINDI=0"
if /i "%KLASOR%"=="e" (
    powershell -NoProfile -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory('%PROJE%','OnlyErrorDialogs','SendToRecycleBin')" >nul 2>&1
    if not exist "%PROJE%\run_app.py" (
        echo       klasor Geri Donusum Kutusu'na tasindi
        set "TASINDI=1"
    ) else (
        echo       tasinamadi - klasoru kendiniz silebilirsiniz
    )
) else (
    echo       klasor korundu
)

REM --- Ozet -------------------------------------------------------------
echo.
echo ======================================================
echo    Kaldirma tamamlandi.
echo ======================================================
echo.
if "!TASINDI!"=="0" (
    echo Program dosyalari hala burada:
    echo   %PROJE%
    echo Tamamen silmek icin bu klasoru Geri Donusum Kutusu'na surukleyin.
    echo.
)
echo KLAVYENIN KENDISI:
echo   Klavyedeki firmware silinmedi - cihaz bilgisayara takilinca
echo   tuslar calismaya devam eder ^(bilgisayar uygulamasi olmadan da
echo   kisayol/medya tuslari calisir^).
echo   Karti tamamen bosaltmak isterseniz ESP32'yi BOOT+RST ile
echo   yukleme moduna alip su komutu calistirin:
echo       esptool.py --chip esp32s3 erase_flash
echo.
pause
exit /b 0
