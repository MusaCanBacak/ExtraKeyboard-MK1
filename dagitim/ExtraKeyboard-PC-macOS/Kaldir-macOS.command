#!/bin/bash
# =====================================================================
#  ExtraKeyboard MK1 — KALDIRMA ARACI (macOS)
#
#  Bu dosyaya çift tıklayın. Bilgisayarınızdan şunları kaldırır:
#    1. Çalışan ExtraKeyboard uygulaması (durdurulur)
#    2. Sanal ortam (.venv) — kurulan Python paketleri
#    3. Masaüstündeki ExtraKeyboard kısayolu
#    4. Günlük dosyası (~/Library/Logs/ExtraKeyboard.log)
#    5. Ön bellek klasörleri (__pycache__) ve üretilen geçici varlıklar
#    6. İsteğe bağlı: ayarlarınız (tuş atamaları, profiller)
#    7. İsteğe bağlı: program klasörünün tamamı (Çöp Kutusu'na taşınır)
#
#  DİKKAT: 6. adım tuş atamalarınızı siler ve geri alınamaz.
#  Klavyenin kendi belleğindeki firmware SİLİNMEZ — cihaz takılıyken
#  çalışmaya devam eder (nasıl silineceği en altta yazıyor).
# =====================================================================
cd "$(dirname "$0")"
PROJE="$(pwd)"
KIRMIZI=$'\033[31m'; YESIL=$'\033[32m'; SARI=$'\033[33m'; NORMAL=$'\033[0m'

echo
echo "======================================================"
echo "   ExtraKeyboard MK1 — Kaldırma"
echo "======================================================"
echo
echo "Program klasörü: $PROJE"
echo
echo "Kaldırılacaklar:"
echo "  - Sanal ortam (.venv) ve kurulu Python paketleri"
echo "  - Masaüstü kısayolu"
echo "  - Günlük dosyası ve ön bellek klasörleri"
echo
echo "${SARI}Ayarlarınız ve program klasörü ayrıca sorulacak.${NORMAL}"
echo
read -r -p "Devam etmek için EVET yazıp Enter'a basın: " ONAY
if [ "$ONAY" != "EVET" ] && [ "$ONAY" != "evet" ] && [ "$ONAY" != "Evet" ]; then
    echo "İptal edildi. Hiçbir şey silinmedi."
    read -r -p "Kapatmak için Enter..."
    exit 0
fi
echo

# --- 1) Çalışan uygulamayı durdur ---------------------------------------
echo "[1/6] Çalışan uygulama durduruluyor..."
if pgrep -f "run_app.py" >/dev/null 2>&1 || pgrep -f "ExtraKeyboard.app" >/dev/null 2>&1; then
    pkill -f "run_app.py" 2>/dev/null
    pkill -f "ExtraKeyboard.app" 2>/dev/null
    sleep 1
    pkill -9 -f "run_app.py" 2>/dev/null
    pkill -9 -f "ExtraKeyboard.app" 2>/dev/null
    echo "      ${YESIL}durduruldu${NORMAL}"
else
    echo "      (zaten çalışmıyordu)"
fi

# --- 2) Sanal ortam -----------------------------------------------------
echo "[2/6] Sanal ortam (.venv) siliniyor..."
if [ -d "$PROJE/.venv" ]; then
    rm -rf "$PROJE/.venv" && echo "      ${YESIL}silindi${NORMAL}" \
        || echo "      ${KIRMIZI}silinemedi${NORMAL}"
else
    echo "      (yoktu)"
fi

# --- 3) Masaüstü kısayolu ----------------------------------------------
echo "[3/6] Kısayol ve uygulama paketi (.app) siliniyor..."
BULUNDU=0
for HEDEF in "$HOME/Desktop/ExtraKeyboard" \
             "$HOME/Desktop/ExtraKeyboard.app" \
             "$HOME/Desktop/ExtraKeyboard.command" \
             "$PROJE/ExtraKeyboard.app" \
             "/Applications/ExtraKeyboard.app" \
             "$HOME/Applications/ExtraKeyboard.app" \
             "$HOME/Applications/ExtraKeyboard" \
             "$HOME/Applications/ExtraKeyboard.command"; do
    if [ -e "$HEDEF" ] || [ -L "$HEDEF" ]; then
        rm -rf "$HEDEF" 2>/dev/null && { echo "      ${YESIL}silindi:${NORMAL} $HEDEF"; BULUNDU=1; }
    fi
done
[ "$BULUNDU" = "0" ] && echo "      (kısayol bulunamadı)"

# --- 4) Günlük dosyası --------------------------------------------------
echo "[4/6] Günlük dosyası siliniyor..."
if [ -f "$HOME/Library/Logs/ExtraKeyboard.log" ]; then
    rm -f "$HOME/Library/Logs/ExtraKeyboard.log" && echo "      ${YESIL}silindi${NORMAL}"
else
    echo "      (yoktu)"
fi

# --- 5) Ön bellek ve üretilen geçici varlıklar --------------------------
echo "[5/6] Ön bellek klasörleri temizleniyor..."
find "$PROJE" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null
find "$PROJE" -type f -name "*.pyc" -delete 2>/dev/null
rm -f "$PROJE/varliklar/_simge_ata.scpt.txt" 2>/dev/null
echo "      ${YESIL}temizlendi${NORMAL}"

# --- 6) Ayarlar (isteğe bağlı) -----------------------------------------
echo
echo "------------------------------------------------------"
echo "${SARI}Ayarlarınız (tuş atamaları, profiller, LED ayarları)${NORMAL}"
echo "Dosyalar: config.json, macro_config.json"
echo "          ~/Library/Application Support/ExtraKeyboard (.app sürümü)"
echo "Silerseniz GERİ ALINAMAZ. Programı tekrar kuracaksanız"
echo "saklamak isteyebilirsiniz."
echo "------------------------------------------------------"
read -r -p "Ayarlar da silinsin mi? (e/H): " AYAR
if [ "$AYAR" = "e" ] || [ "$AYAR" = "E" ]; then
    rm -f "$PROJE/config.json" "$PROJE/macro_config.json" 2>/dev/null
    # Uygulama paketi (.app) sürümü ayarları burada tutar:
    rm -rf "$HOME/Library/Application Support/ExtraKeyboard" 2>/dev/null
    echo "      ${YESIL}ayarlar silindi${NORMAL}"
else
    echo "      ayarlar korundu ($PROJE/config.json)"
fi

# --- 7) Program klasörü (isteğe bağlı) ---------------------------------
echo
echo "------------------------------------------------------"
echo "Program klasörünün tamamı Çöp Kutusu'na taşınsın mı?"
echo "  $PROJE"
echo "(Çöp Kutusu'na taşınır, kalıcı silinmez — fikrinizi"
echo " değiştirirseniz oradan geri alabilirsiniz.)"
echo "------------------------------------------------------"
read -r -p "Klasör Çöp Kutusu'na taşınsın mı? (e/H): " KLASOR
TASINDI=0
if [ "$KLASOR" = "e" ] || [ "$KLASOR" = "E" ]; then
    if osascript -e "tell application \"Finder\" to delete POSIX file \"$PROJE\"" >/dev/null 2>&1; then
        echo "      ${YESIL}klasör Çöp Kutusu'na taşındı${NORMAL}"
        TASINDI=1
    else
        echo "      ${KIRMIZI}taşınamadı${NORMAL} — klasörü Finder'dan kendiniz silebilirsiniz."
    fi
else
    echo "      klasör korundu"
fi

# --- Özet ---------------------------------------------------------------
echo
echo "======================================================"
echo "   ${YESIL}Kaldırma tamamlandı.${NORMAL}"
echo "======================================================"
echo
if [ "$TASINDI" = "0" ]; then
    echo "Program dosyaları hâlâ burada:"
    echo "  $PROJE"
    echo "Tamamen silmek için bu klasörü Çöp Kutusu'na sürükleyin."
    echo
fi
echo "${SARI}KLAVYENİN KENDİSİ:${NORMAL}"
echo "  Klavyedeki firmware silinmedi — cihaz bilgisayara takılınca"
echo "  tuşlar çalışmaya devam eder (bilgisayar uygulaması olmadan da"
echo "  kısayol/medya tuşları çalışır)."
echo "  Kartı tamamen boşaltmak isterseniz ESP32'yi BOOT+RST ile"
echo "  yükleme moduna alıp şu komutu çalıştırın:"
echo "      esptool.py --chip esp32s3 erase_flash"
echo
echo "Sistem Ayarları > Gizlilik ve Güvenlik > Erişilebilirlik"
echo "listesinde \"Terminal\" izni verdiyseniz ve başka bir şey için"
echo "kullanmıyorsanız oradan kaldırabilirsiniz."
echo
read -r -p "Kapatmak için Enter..."
exit 0
