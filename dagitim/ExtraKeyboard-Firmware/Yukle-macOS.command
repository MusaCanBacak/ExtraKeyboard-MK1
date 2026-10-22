#!/bin/bash
# =====================================================================
#  ExtraKeyboard MK1 — Firmware Yukleyici (macOS)
#  Cift tiklayin. Karti tanir, dogru imaji secer, kutuyu acmadan yukler.
#  Gereken: Python 3.8+ (esptool ve pyserial ilk calistirmada kurulur)
# =====================================================================
cd "$(dirname "$0")" || exit 1

bitir() { echo; read -r -p "Kapatmak icin Enter..."; exit "${1:-0}"; }

# python.org > Homebrew > Apple (Xcode araclari) sirasiyla 3.8+ ara
PY=""
for aday in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
            /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$aday" ] && "$aday" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
        PY="$aday"; break
    fi
done
if [ -z "$PY" ]; then
    echo "HATA: Python 3.8+ bulunamadi."
    echo "https://www.python.org/downloads/macos/ adresinden kurun ve tekrar deneyin."
    bitir 1
fi

# Paketler bu klasordeki .venv'e kurulur; sistemdeki Python'a dokunulmaz.
if ! .venv/bin/python -c 'import esptool, serial' 2>/dev/null; then
    echo "Ilk calistirma: esptool ve pyserial kuruluyor (internet gerekir)..."
    rm -rf .venv
    "$PY" -m venv .venv || { echo "HATA: sanal ortam olusturulamadi."; bitir 1; }
    .venv/bin/python -m pip install --quiet --disable-pip-version-check -r gereksinimler.txt \
        || { echo "HATA: paketler kurulamadi. Internet baglantinizi kontrol edin."; bitir 1; }
fi

.venv/bin/python yukle.py "$@"
bitir $?
