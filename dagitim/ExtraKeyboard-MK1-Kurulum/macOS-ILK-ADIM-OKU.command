#!/bin/bash
# =====================================================================
#  macOS KARANTINA KALDIRICI
#
#  macOS, internetten indirilen imzasiz betikleri "hasarli" diyerek
#  engeller (Gatekeeper karantinasi). Dosyalar aslinda saglamdir.
#  Bu betik paketteki karantina damgasini kaldirir ve calistirma
#  izinlerini geri verir. BIR KEZ calistirmaniz yeterlidir.
#
#  BU DOSYA DA ENGELLENIYORSA:
#  Terminal'i acin, asagidaki komutu yazin (sonunda BOSLUK birakin),
#  sonra bu klasoru Terminal penceresine SURUKLEYIP birakin ve Enter:
#
#      xattr -cr 
#
# =====================================================================
cd "$(dirname "$0")"
echo "=============================================="
echo " macOS karantina damgasi kaldiriliyor..."
echo "=============================================="
xattr -cr . 2>/dev/null
find . -name "*.command" -exec chmod +x {} \; 2>/dev/null
echo
echo "TAMAM. Artik su dosyalara cift tiklayabilirsiniz:"
echo "  1-BILGISAYAR-UYGULAMASI/macOS/Baslat.command   (uygulamayi baslatir)"
echo "  2-FIRMWARE/Yukle-macOS.command                 (firmware yukler)"
echo
read -r -p "Kapatmak icin Enter..."
