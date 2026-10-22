#!/usr/bin/env python3
"""ExtraKeyboard — dağıtım imajlarını üretir (her varyant TEK dosya, 0x0'a yazılır).

Her varyant için PlatformIO ortamını derler, esptool merge_bin ile
bootloader + bölüm tablosu + boot_app0 + uygulamayı tek imajda birleştirir
ve başlığa DIO / 40 MHz / flash boyutunu gömer (bu kartlardaki Boya flash
çipleri QIO / 80 MHz ile açılmaz — bkz. firmware/platformio.ini). Sonra her
imajı doğrular: başlık, 0x10000'de uygulama, klavyede üst sıra tuş eşlemesi.

  .venv/bin/python tools/imaj-olustur.py                 # derle + birleştir
  .venv/bin/python tools/imaj-olustur.py --derleme-atla  # yalnızca birleştir

Çıktı: dagitim/ExtraKeyboard-Firmware/imajlar/  (+ SHA256SUMS.txt)
Bu imajlar GENEL birimler içindir; birime özel ortamlar (ör. e74610, üst
sırası takaslı) buraya girmez — onlar tools/yukle-kutusuz.py ile yüklenir.
"""

import argparse
import hashlib
import os
import subprocess
import sys

PROJE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CIKTI = os.path.join(PROJE, "dagitim", "ExtraKeyboard-Firmware", "imajlar")
PIOPKG = os.path.expanduser("~/.platformio/packages")
PIO = os.path.expanduser("~/.platformio/penv/bin/pio")
PY = os.path.expanduser("~/.platformio/penv/bin/python")
ESPTOOL = os.path.join(PIOPKG, "tool-esptoolpy", "esptool.py")
BOOT_APP0 = os.path.join(PIOPKG, "framework-arduinoespressif32",
                         "tools", "partitions", "boot_app0.bin")

#  (imaj adı, proje, pio ortamı, flash boyutu, tür)
VARYANTLAR = [
    ("ExtraKeyboard-klavye-n16r8.bin", "firmware", "n16r8", "16MB", "klavye"),
    ("ExtraKeyboard-klavye-n8r2.bin", "firmware", "quad", "8MB", "klavye"),
    ("ExtraKeyboard-numpad-n16r8.bin", "firmware-numpad", "numpad_n16r8", "16MB", "numpad"),
    ("ExtraKeyboard-numpad-n8r2.bin", "firmware-numpad", "extrakeyboard", "8MB", "numpad"),
]

# keys.cpp KEY_PINS dizisinin derlenmiş hâli (GPIO numaraları, uint8_t).
# Genel imajlarda ORİJİNAL sıra olmalı; TAKASLI sıra yalnızca E74610'a aittir.
TUS_ORIJINAL = bytes([4, 5, 6, 7, 15, 16, 17, 18, 10, 9, 8, 21])
TUS_TAKASLI = bytes([4, 5, 6, 7, 15, 16, 17, 18, 21, 8, 9, 10])

MODLAR = {0: "QIO", 1: "QOUT", 2: "DIO", 3: "DOUT"}
BOYUTLAR = {2: "4MB", 3: "8MB", 4: "16MB"}
HIZLAR = {0x0: "40m", 0xF: "80m"}


def dogrula(yol, beklenen_boyut, tur):
    veri = open(yol, "rb").read()
    hatalar = []
    if veri[0] != 0xE9:
        hatalar.append("0x0'da bootloader yok")
    mod, hiz, boy = MODLAR.get(veri[2], "?"), HIZLAR.get(veri[3] & 0xF, "?"), BOYUTLAR.get(veri[3] >> 4, "?")
    if (mod, hiz, boy) != ("DIO", "40m", beklenen_boyut):
        hatalar.append(f"başlık {mod}/{hiz}/{boy} (beklenen DIO/40m/{beklenen_boyut})")
    if len(veri) <= 0x10000 or veri[0x10000] != 0xE9:
        hatalar.append("0x10000'de uygulama yok")
    if tur == "klavye":
        if veri.count(TUS_TAKASLI) or not veri.count(TUS_ORIJINAL):
            hatalar.append("üst sıra tuş eşlemesi ORİJİNAL değil")
    return hatalar, f"{mod}/{hiz}/{boy}", hashlib.sha256(veri).hexdigest(), len(veri)


def main():
    ap = argparse.ArgumentParser(description="Genel dağıtım imajlarını üretir.")
    ap.add_argument("--derleme-atla", action="store_true",
                    help="pio run çalıştırma (ortamlar zaten derlenmişse)")
    a = ap.parse_args()

    for gerekli in (PY, ESPTOOL, BOOT_APP0):
        if not os.path.exists(gerekli):
            sys.exit(f"HATA: {gerekli} yok (PlatformIO kurulu mu?)")
    os.makedirs(CIKTI, exist_ok=True)

    ozetler, sorun = [], False
    for ad, proje, ortam, boyut, tur in VARYANTLAR:
        derleme = os.path.join(PROJE, proje, ".pio", "build", ortam)
        if not a.derleme_atla:
            print(f"derleniyor: {proje} -e {ortam} ...", flush=True)
            r = subprocess.run([PIO, "run", "-e", ortam, "-d", os.path.join(PROJE, proje)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stdout[-1500:], r.stderr[-800:])
                sys.exit(f"HATA: {ortam} derlenemedi.")
        hedef = os.path.join(CIKTI, ad)
        r = subprocess.run(
            [PY, ESPTOOL, "--chip", "esp32s3", "merge_bin", "-o", hedef,
             "--flash_mode", "dio", "--flash_freq", "40m", "--flash_size", boyut,
             "0x0", os.path.join(derleme, "bootloader.bin"),
             "0x8000", os.path.join(derleme, "partitions.bin"),
             "0xe000", BOOT_APP0,
             "0x10000", os.path.join(derleme, "firmware.bin")],
            capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-1500:], r.stderr[-800:])
            sys.exit(f"HATA: {ad} birleştirilemedi.")
        hatalar, baslik, ozet, uzunluk = dogrula(hedef, boyut, tur)
        durum = "TAMAM" if not hatalar else "SORUN: " + "; ".join(hatalar)
        sorun |= bool(hatalar)
        print(f"  {ad:32} {uzunluk // 1024:4} KB  {baslik:12}  {durum}")
        ozetler.append(f"{ozet}  {ad}")

    with open(os.path.join(CIKTI, "SHA256SUMS.txt"), "w") as f:
        f.write("\n".join(ozetler) + "\n")
    print(f"\nÇıktı: {CIKTI}")
    return 1 if sorun else 0


if __name__ == "__main__":
    sys.exit(main())
