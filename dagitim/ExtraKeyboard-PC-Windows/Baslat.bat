@echo off
rem =====================================================================
rem  ExtraKeyboard MK1 - PC uygulamasi baslaticisi (Windows)
rem  Cift tiklayarak calistirin. Her sey KENDILIGINDEN olur:
rem   - Python 3 + Tcl/Tk denetlenir (eksikse anlasilir uyari)
rem   - Sanal ortam kurulur; bozuksa onarilir
rem   - requirements.txt degistikce eksik paketler kurulur
rem   - Masaustune simgeli ExtraKeyboard kisayolu konur
rem =====================================================================
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set "PYCMD=py -3") else (set "PYCMD=python")

%PYCMD% --version >nul 2>nul
if not %errorlevel%==0 (
    echo HATA: Python 3 bulunamadi.
    echo https://www.python.org adresinden kurun ve kurulumda
    echo "Add python.exe to PATH" kutusunu isaretleyin.
    pause
    exit /b 1
)

%PYCMD% -c "import tkinter" >nul 2>nul
if not %errorlevel%==0 (
    echo HATA: Python kurulumunuz Tcl/Tk icermiyor.
    echo python.org kurulumunu yeniden calistirip "tcl/tk and IDLE"
    echo seceneginin isaretli oldugundan emin olun.
    pause
    exit /b 1
)

rem NOT: Parantezli bloklarda yuzde-isaretli errorlevel, blok CALISMADAN
rem ONCE (ayristirma aninda) tek seferde genisletilir; bu yuzden blok ici
rem denetimler ESKI degeri gorur ve hep ayni sonucu verir. Bu yuzden blok
rem icindeki denetimler, calisma aninda degerlendirilen if errorlevel N
rem bicimiyle yazilmistir.
rem --- Bozuk (tkinter'siz) sanal ortami onar ---
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import tkinter" >nul 2>nul
    if errorlevel 1 (
        echo Sanal ortam bozuk gorunuyor - yeniden kuruluyor...
        rmdir /s /q .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Ilk kurulum: sanal ortam olusturuluyor, internet gerekir...
    %PYCMD% -m venv .venv
    if errorlevel 1 ( echo HATA: sanal ortam olusturulamadi. & pause & exit /b 1 )
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
)

rem --- Gereksinim listesi degismisse paketleri kur ---
fc /b requirements.txt ".venv\kurulum-imza.txt" >nul 2>nul
if not %errorlevel%==0 (
    echo Bagimliliklar kuruluyor/guncelleniyor...
    ".venv\Scripts\pip.exe" install --quiet -r requirements.txt
    if errorlevel 1 ( echo HATA: bagimliliklar kurulamadi. Internet baglantinizi kontrol edin. & pause & exit /b 1 )
    copy /y requirements.txt ".venv\kurulum-imza.txt" >nul
    echo Kurulum tamam.
)

rem --- Masaustu kisayolu (yoksa kurar; acilisi engellemez) ---
".venv\Scripts\python.exe" tools\kisayol_olustur.py >nul 2>nul

start "" ".venv\Scripts\pythonw.exe" run_app.py
exit /b 0
