#!/bin/bash
# =====================================================================
#  ExtraKeyboard MK1 — Uygulamalar klasörüne KURUCU (macOS)
#
#  Çift tıklayın. ExtraKeyboard.app'i Uygulamalar klasörüne kopyalar,
#  indirme karantinasını temizler ve çalıştırır.
#
#  NEDEN KURULUM GEREKLİ: Uygulama İndirilenler/Masaüstü gibi bir yerden
#  çalıştırılırsa macOS onu her açılışta adı değişen geçici bir kopyadan
#  çalıştırır (App Translocation) ve verilen Erişilebilirlik izni bir
#  sonraki açılışta KAYBOLUR ("izin verdim ama makro/metin yine çalışmıyor").
#  Uygulamalar klasörüne kurup karantinayı temizleyince izin KALICI olur.
# =====================================================================
cd "$(dirname "$0")"

APP="ExtraKeyboard.app"
if [ ! -d "$APP" ]; then
    osascript -e 'display alert "ExtraKeyboard.app bulunamadı" message "Bu kurucu, ExtraKeyboard.app ile AYNI klasörde olmalı. Önce ZIP dosyasını tamamen açın (çift tıklayıp çıkarın), sonra bu dosyayı çalıştırın."' 2>/dev/null
    echo "HATA: ExtraKeyboard.app bu klasörde yok. Önce ZIP'i tamamen açın."
    read -r -p "Kapatmak için Enter..."
    exit 1
fi

SRC="$(pwd)/$APP"
SYS="/Applications/ExtraKeyboard.app"
USR="$HOME/Applications/ExtraKeyboard.app"
HEDEF=""

echo "ExtraKeyboard, Uygulamalar klasörüne kuruluyor..."

# Çalışan bir kopya varsa kapat (dosya kilidi olmasın).
osascript -e 'quit app "ExtraKeyboard"' 2>/dev/null || true
sleep 1

# 1) /Applications'a şifresiz yazılabiliyorsa oraya kur.
if [ -w "/Applications" ]; then
    rm -rf "$SYS" 2>/dev/null
    if ditto "$SRC" "$SYS" 2>/dev/null; then
        xattr -cr "$SYS" 2>/dev/null || true
        HEDEF="$SYS"
    fi
fi

# 2) Değilse yönetici izniyle /Applications'a kur (macOS şifre penceresi çıkar;
#    iptal edilirse kullanıcı klasörüne düşülür). Kopyalama + karantina temizliği
#    TEK ayrıcalıklı komutta yapılır (kök sahipli pakette xattr sonradan çalışmaz).
if [ -z "$HEDEF" ]; then
    echo "  /Applications için yönetici izni isteniyor..."
    echo "  (Şifreyi macOS'un kendi penceresine girin. İptal ederseniz kişisel"
    echo "   Uygulamalar klasörünüze şifresiz kurulur.)"
    if osascript -e "do shell script \"/bin/rm -rf '$SYS'; /usr/bin/ditto '$SRC' '$SYS'; /usr/bin/xattr -cr '$SYS'\" with administrator privileges" >/dev/null 2>&1; then
        HEDEF="$SYS"
    fi
fi

# 3) O da olmazsa kullanıcının kendi Uygulamalar klasörü (şifresiz, güvenli).
if [ -z "$HEDEF" ]; then
    mkdir -p "$HOME/Applications"
    rm -rf "$USR" 2>/dev/null
    if ditto "$SRC" "$USR" 2>/dev/null; then
        xattr -cr "$USR" 2>/dev/null || true
        HEDEF="$USR"
    fi
fi

if [ -z "$HEDEF" ]; then
    echo "HATA: kurulum yapılamadı (Uygulamalar klasörüne yazılamadı)."
    read -r -p "Kapatmak için Enter..."
    exit 1
fi

echo "Kuruldu: $HEDEF"
echo "Açılıyor..."
open "$HEDEF" 2>/dev/null || true
osascript -e 'display notification "Uygulamalar klasörüne kuruldu." with title "ExtraKeyboard kuruldu"' 2>/dev/null || true

echo ""
echo "Bitti. Bundan sonra Launchpad'den veya Uygulamalar klasöründen açabilirsiniz."
echo "İlk açılışta Erişilebilirlik izni isterse verin — artık KALICI olacaktır."
echo "Bu pencereyi kapatabilirsiniz."
exit 0
