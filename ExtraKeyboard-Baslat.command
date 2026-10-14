#!/bin/bash
# ExtraKeyboard MK1 — çift tıkla başlatıcı (macOS)
# Finder'da bu dosyaya çift tıklayınca uygulama açılır.
# İlk seferde Finder "tanımlanamayan geliştirici" derse: sağ tık → Aç.
#
# Bağımlılık kurulumu KENDİLİĞİNDEN yapılır:
#   - Tcl/Tk (tkinter) destekli bir Python 3 aranır — Homebrew'un python3'ü
#     çoğu kurulumda tkinter'sızdır ve "_tkinter" hatasına yol açar; bu
#     yüzden adaylar tek tek denenir ve tkinter'ı içe aktarabilen ilki seçilir.
#   - .venv yoksa (veya tkinter'sız bir Python ile yanlış kurulmuşsa)
#     doğru Python ile yeniden oluşturulur.
#   - requirements.txt her değiştiğinde eksik paketler otomatik kurulur
#     (karşılaştırma: .venv/kurulum-imza.txt kopyası).

cd "$(dirname "$0")"

# --- Hazir uygulama paketi varsa onu ac ---------------------------------
# Bu betik kaynak koddan calistirma yoludur ve Python 3.9+ ile Tcl/Tk 8.6
# ister. Kurulum paketinde ayni klasorde, kendi Python ve Tk'sini iceren
# ExtraKeyboard.app da bulunur. Kullanici hangi dosyaya tiklarsa tiklasin
# uygulamanin acilmasi gerekir: paket varsa dogrudan o acilir, boylece
# "Tcl/Tk 8.6 destekli Python bulunamadi" hatasi bosuna gorunmez.
if [ -d "ExtraKeyboard.app" ]; then
    # Karantina damgasi (internetten indirilmis dosya isareti) mutlaka
    # temizlenmeli. Aksi halde macOS ya uygulamayi hic acmaz ("dogrulanamadi"
    # uyarisi), ya da her acilista adi degisen gecici bir kopyadan calistirir
    # (App Translocation). Ikinci durumda uygulama calisir ama verilen
    # Erisilebilirlik izni bir sonraki acilista kaybolur; kullaniciya "izin
    # verdim, yine soruyor, makro/metin calismiyor" olarak gorunur.
    if xattr "ExtraKeyboard.app" 2>/dev/null | grep -q "com.apple.quarantine"; then
        echo "İndirme karantinası kaldırılıyor (izinlerin kalıcı olması için)..."
        xattr -cr "ExtraKeyboard.app" 2>/dev/null
    fi
    echo "Hazır uygulama paketi bulundu — açılıyor (Python gerekmez)."
    open "ExtraKeyboard.app" 2>/dev/null && exit 0
    echo "Paket açılamadı, kaynak koddan başlatmaya geçiliyor..."
fi

# --- Tcl/Tk 8.6+ destekli Python 3'ü bul --------------------------------
# Bir Python adayinin ise yarayip yaramadigini belirleyen kosul.
# SADECE "import tkinter" YETMEZ: macOS'un kendi Python 3.9'u
# (/usr/bin/python3) tkinter'i icerir ama 2010 yapimi Tk 8.5.9 ile gelir.
# CustomTkinter'in tuval tabanli widget'lari o surumde HIC CIZILMEZ;
# uygulama hatasiz acilir, tiklamalar bile calisir, ama kullanici bombos
# (acik temada bembeyaz) bir pencere gorur. Bu yuzden Tk 8.6 sarti aranir.
TK_KONTROL='import sys, tkinter; sys.exit(0 if float(tkinter.TkVersion) >= 8.6 else 1)'

PYTHON3=""
for aday in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
            /usr/local/bin/python3 \
            "$(command -v python3 2>/dev/null)" \
            /opt/homebrew/bin/python3 \
            /usr/bin/python3; do
    [ -n "$aday" ] && [ -x "$aday" ] || continue
    if "$aday" -c "$TK_KONTROL" >/dev/null 2>&1; then
        PYTHON3="$aday"
        break
    fi
done
if [ -z "$PYTHON3" ]; then
    echo "HATA: Tcl/Tk 8.6 destekli Python 3 bulunamadı."
    echo "Çözüm: https://www.python.org adresinden Python kurun (Tcl/Tk dahildir)."
    echo "Not: macOS'un kendi Python 3.9'u (/usr/bin/python3) YETERLİ DEĞİLDİR;"
    echo "     Tk 8.5.9 ile gelir ve arayüz o sürümde çizilmez (boş/beyaz pencere)."
    echo "Homebrew Python'u kullanıyorsanız:  brew install python-tk"
    echo ""
    echo "KOLAY YOL: Kurulum paketindeki ExtraKeyboard.app dosyasına çift"
    echo "tıklayın — kendi Python ve Tcl/Tk'sini içinde taşır, hiçbir şey"
    echo "kurmanız gerekmez."
    read -r -p "Kapatmak için Enter..."
    exit 1
fi

# --- Yanlış (tkinter'sız) Python ile kurulmuş sanal ortamı onar -----------
if [ -x ".venv/bin/python" ] && ! .venv/bin/python -c "$TK_KONTROL" >/dev/null 2>&1; then
    echo "Sanal ortam eski Tcl/Tk'li (8.5) bir Python ile kurulmuş — yeniden kuruluyor..."
    rm -rf .venv
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "Sanal ortam oluşturuluyor ($PYTHON3)..."
    "$PYTHON3" -m venv .venv || exit 1
    .venv/bin/pip install --quiet --upgrade pip
fi

# --- Gereksinimler değiştiyse paketleri kur -------------------------------
if ! cmp -s requirements.txt .venv/kurulum-imza.txt; then
    echo "Bağımlılıklar kuruluyor/güncelleniyor (internet gerekir)..."
    if .venv/bin/pip install --quiet -r requirements.txt; then
        cp requirements.txt .venv/kurulum-imza.txt
        echo "Bağımlılıklar hazır."
    else
        echo "UYARI: bağımlılık kurulumu tamamlanamadı (internet yok olabilir)."
        echo "Uygulama yine de başlatılıyor; eksik özellikler kapalı kalabilir."
    fi
fi

# Uygulamalar kısayolu (ilk çalıştırmada kurar; sonrakiler anında geçer,
# hata olursa açılışı asla engellemez)
.venv/bin/python tools/kisayol_olustur.py 2>/dev/null || true

# Uygulamayı bu pencereden BAĞIMSIZ başlat: Terminal penceresi
# kapatılsa bile uygulama çalışmaya devam eder. Günlük dosyaya yazılır.
echo "ExtraKeyboard açılıyor..."
mkdir -p "$HOME/Library/Logs"
nohup .venv/bin/python run_app.py > "$HOME/Library/Logs/ExtraKeyboard.log" 2>&1 &
disown 2>/dev/null || true
sleep 2
if pgrep -f "run_app.py" >/dev/null 2>&1; then
    echo "Uygulama açıldı. Bu pencereyi kapatabilirsiniz."
else
    echo "UYARI: uygulama açılamamış görünüyor. Günlük dosyasına bakın:"
    echo "  ~/Library/Logs/ExtraKeyboard.log"
    tail -5 "$HOME/Library/Logs/ExtraKeyboard.log" 2>/dev/null
    read -r -p "Kapatmak için Enter..."
fi
exit 0
