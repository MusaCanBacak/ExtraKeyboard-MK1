#!/usr/bin/env python3
"""ExtraKeyboard — KUTUYU AÇMADAN firmware yükler (uçtan uca).

Zinciri tek komutta yürütür:
  1) kartı indirme moduna alır  (CMD BOOTLOADER CONFIRM, yoksa DTR/RTS)
  2) esptool ile TAM FLASH atar (bootloader + partition + boot_app0 + app)
  3) DÜZGÜN reset atar          (bkz. aşağıdaki NOT — esptool'unki yetmez)
  4) kalp atışını ölçüp doğrular

NOT — 3. adım neden ayrı:
  ESP32-S3'ün ROM USB-Serial-JTAG'inde DTR -> IO0(BOOT), RTS -> EN(reset)
  hatlarına bağlıdır. esptool'un `--after hard_reset`'i IO0'ı DÜŞÜK bırakıyor,
  bu yüzden kart resetten sonra tekrar indirme moduna giriyor ve "yükleme
  bozuldu" gibi görünüyor. Doğrusu: DTR'yi DÜŞÜK (IO0 yüksek) tutup yalnızca
  RTS'i darbelemek. Bu betik onu yapar.

ÖNCE `pio run` ile derle. Varsayılan flash bayrakları E74610 (N16R8 + Boya
flash) içindir; başka birimde `--flash-mode/--flash-freq/--flash-size` ver.
Birim farklarına dikkat: yanlış değer kartı BOOT DÖNGÜSÜNE sokar.
"""

import argparse
import glob
import os
import subprocess
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial yok. Proje .venv'i ile calistir: .venv/bin/python")

PROJE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# BIRIM TABLOSU — kart USB seri numarasindan (MAC, iki noktasiz) taninir.
# Her birim FARKLI donanim: yanlis ortam/bayrak kartı BOOT DONGUSUNE sokar
# (2026-09-17). Degerler `esptool flash_id` ile OLCULMUSTUR, tahmin degildir.
# Yeni birim: flash_id oku -> uygun ortami sec -> buraya ekle.
#   seri: (ad, proje, pio ortami, flash_mode, flash_freq, flash_size)
# ---------------------------------------------------------------------------
BIRIMLER = {
    "A085E3E74610": ("E74610 klavye (N16R8, Octal, tuslar TAKASLI)",
                     "firmware", "e74610", "dio", "40m", "16MB"),
    "3C0F026F0B98": ("6F0B98 klavye (2MB Quad, Boya)",
                     "firmware", "quad", "dio", "40m", "8MB"),
    "A4CB8F9A2408": ("9A2408 klavye (2MB Quad, EON)",
                     "firmware", "quad", "dio", "40m", "8MB"),
    "3C0F026F0568": ("6F0568 numpad (2MB Quad, Boya)",
                     "firmware-numpad", "extrakeyboard", "dio", "40m", "8MB"),
}
PIO = os.path.expanduser("~/.platformio/penv/bin/pio")


def seri_normal(s):
    """ROM MAC'i iki noktali verir (A0:85:..), firmware iki noktasiz."""
    return (s or "").replace(":", "").upper()


def kart_bul():
    """Takili ExtraKeyboard'u (firmware VEYA ROM modunda) bulur.
    Doner: (port, normal_seri, rom_mu) ya da hata mesaji (str)."""
    from serial.tools import list_ports
    adaylar = []
    for pi in list_ports.comports():
        urun = f"{pi.product or ''} {pi.description or ''}".lower()
        if pi.vid != 0x303A:
            continue                       # Espressif degil (orn. XIAO) -> atla
        rom = "jtag" in urun or ":" in (pi.serial_number or "")
        if rom or "extrakeyboard" in urun:
            adaylar.append((pi.device, seri_normal(pi.serial_number), rom))
    if not adaylar:
        return "Takili ExtraKeyboard bulunamadi."
    if len(adaylar) > 1:
        return ("Birden fazla ExtraKeyboard takili: "
                + ", ".join(f"{a[1]}" for a in adaylar)
                + " — yuklenecek olani tek birak.")
    return adaylar[0]
BUILD = os.path.join(PROJE, "firmware", ".pio", "build", "extrakeyboard")
PIOPKG = os.path.expanduser("~/.platformio/packages")
ESPTOOL = os.path.join(PIOPKG, "tool-esptoolpy", "esptool.py")
PY = os.path.expanduser("~/.platformio/penv/bin/python")
BOOT_APP0 = os.path.join(PIOPKG, "framework-arduinoespressif32",
                         "tools", "partitions", "boot_app0.bin")


def portlar():
    return sorted(glob.glob("/dev/cu.usbmodem*"))


# main() tarafindan ayarlanir: yalnizca BU kartin portlari dikkate alinir.
HEDEF_SERI = None


def _esp_portlari():
    """(port, normal_seri, rom_mu) — YALNIZCA Espressif (VID 0x303A) portlari.

    Port ADINA bakilmaz, KIMLIGE bakilir. Eskiden "usbmodem + yalnizca rakam =
    ROM indirme portu" sanilıyordu; ama baska kartlarin (orn. Seeed XIAO
    nRF52840: usbmodem201201) portu da rakamli oldugundan arac 2026-09-29'da
    XIAO'ya yazmaya kalkti (port mesguldu, zarar olmadi). ROM'u ayirt eden:
    urun adinda "JTAG" ya da seri no'nun iki noktali MAC olmasi.
    """
    from serial.tools import list_ports
    out = []
    for pi in list_ports.comports():
        if pi.vid != 0x303A:
            continue
        urun = f"{pi.product or ''} {pi.description or ''}".lower()
        rom = "jtag" in urun or ":" in (pi.serial_number or "")
        if rom or "extrakeyboard" in urun:
            out.append((pi.device, seri_normal(pi.serial_number), rom))
    return out


def indirme(ps=None):
    """HEDEF kartin ROM (indirme) portu — seri no (MAC) eslesmeli."""
    return [d for d, sr, rom in _esp_portlari()
            if rom and (HEDEF_SERI is None or sr == HEDEF_SERI)]


def firmware(ps=None):
    """HEDEF kartin firmware (ExtraKeyboard) portu — seri no eslesmeli."""
    return [d for d, sr, rom in _esp_portlari()
            if not rom and (HEDEF_SERI is None or sr == HEDEF_SERI)]


def bekle(kosul, sure, adim=0.5):
    t0 = time.time()
    while time.time() - t0 < sure:
        r = kosul()
        if r:
            return r
        time.sleep(adim)
    return None


def indirme_moduna_al():
    """CMD BOOTLOADER CONFIRM; olmazsa DTR/RTS dizisi (eski firmware)."""
    if indirme():
        print("  kart zaten indirme modunda")
        return indirme()[0]

    fw = firmware()
    if not fw:
        return None
    port = fw[0]
    print(f"  firmware portu: {port}")

    # Yol 1 — kasitli komut (yeni firmware)
    try:
        s = serial.Serial()
        s.port, s.baudrate, s.timeout = port, 115200, 0.3
        s.dtr, s.rts = True, False
        s.open()
        s.reset_input_buffer()
        s.write(b"CMD BOOTLOADER CONFIRM\n")
        s.flush()
        t0 = time.time()
        while time.time() - t0 < 2.0:
            satir = s.readline().decode(errors="replace").strip()
            if satir.startswith("ACK") and "BOOTLOADER" in satir:
                print("  komut kabul edildi:", satir)
                break
        s.close()
    except Exception as e:
        print("  komut denemesi basarisiz:", e)

    p = bekle(lambda: (indirme() or [None])[0], 8)
    if p:
        return p

    # Yol 2 — DTR/RTS dizisi (enableReboot hala aciksa, yani eski firmware)
    print("  DTR/RTS dizisine geciliyor (eski firmware)...")
    try:
        s = serial.Serial()
        s.port, s.baudrate, s.timeout = port, 115200, 0.2
        s.dtr, s.rts = False, False
        s.open()
        time.sleep(0.3)
        for alan, deger in (("rts", True), ("dtr", True),
                            ("rts", False), ("dtr", False)):
            setattr(s, alan, deger)
            time.sleep(0.15)
        s.close()
    except Exception as e:
        print("  dizi hatasi:", e)

    return bekle(lambda: (indirme() or [None])[0], 10)


# FORCE_DOWNLOAD_BOOT bayragi: RTC_CNTL_OPTION1_REG bit0
# (ESP32-S3: DR_REG_RTCCNTL_BASE 0x60008000 + 0x12C)
OPTION1_REG = "0x6000812C"


def duzgun_reset(port):
    """Indirme-boot bayragini SIFIRLAYIP resetler -> kart firmware'e acilir.

    NEDEN bayrak temizligi sart: `CMD BOOTLOADER CONFIRM` ->
    usb_persist_restart(RESTART_BOOTLOADER) yolu, cekirdekte
    REG_WRITE(RTC_CNTL_OPTION1_REG, FORCE_DOWNLOAD_BOOT) yapar. Bu bayrak
    flash sonrasi DA set kalir; temizlenmezse kart her resette yine indirme
    moduna acilir ve "yukleme bozuldu" gibi gorunur (olcum: bayrak = 0x1).
    write_mem ile bit0 sifirlanip ayni cagrida hard_reset atiliyor.
    """
    subprocess.run(
        [PY, ESPTOOL, "--chip", "esp32s3", "--port", port,
         "--before", "no_reset", "--after", "hard_reset", "--no-stub",
         "write_mem", OPTION1_REG, "0x0", "0x1"],
        capture_output=True, text=True)


def dogrula(sure=8.0):
    p = bekle(lambda: (firmware() or [None])[0], 25)
    if not p:
        print("  HATA: firmware portu gelmedi ->", portlar())
        return False
    time.sleep(1.0)
    try:
        s = serial.Serial()
        s.port, s.baudrate, s.timeout = p, 115200, 0.5
        s.dtr, s.rts = True, False
        s.open()
        time.sleep(0.3)
        hb, ilk = 0, None
        t0 = time.time()
        while time.time() - t0 < sure:
            satir = s.readline().decode(errors="replace").strip()
            if satir.startswith("HB"):
                hb += 1
                if ilk is None:
                    ilk = satir
        s.close()
    except Exception as e:
        print("  dogrulama hatasi:", e)
        return False
    print(f"  port: {p}   kalp atisi: {hb} / {sure:.0f} sn   ilk: {ilk}")
    return hb >= max(3, int(sure * 0.6))


def main():
    ap = argparse.ArgumentParser(
        description="Takili karti seri numarasindan tanir, KENDI ortamini "
                    "derler ve kutuyu acmadan yukler.")
    ap.add_argument("--baud", default="460800")
    ap.add_argument("--derleme-atla", action="store_true",
                    help="pio run calistirma (zaten derlenmisse)")
    a = ap.parse_args()

    # 0) Karti tani — tablo disi kart REDDEDILIR (yanlis ayar = boot dongusu)
    k = kart_bul()
    if isinstance(k, str):
        print("HATA:", k); return 1
    port0, seri, rom = k
    if seri not in BIRIMLER:
        print(f"HATA: {seri} tanimsiz birim. Once `esptool flash_id` ile donanimi")
        print("      oku, uygun ortami sec ve bu dosyadaki BIRIMLER tablosuna ekle.")
        return 1
    ad, proje, ortam, fmode, ffreq, fsize = BIRIMLER[seri]
    global BUILD, HEDEF_SERI
    HEDEF_SERI = seri   # bundan sonra yalnizca bu kartin portlarina dokunulur
    BUILD = os.path.join(PROJE, proje, ".pio", "build", ortam)
    print(f"Kart   : {ad}")
    print(f"Seri   : {seri}   ({'ROM/indirme' if rom else 'firmware'} modunda)")
    print(f"Ortam  : {proje} -e {ortam}   yazma: {fmode}/{ffreq}/{fsize}")

    # 1) Bu birimin ortamini derle (kaynak degistiyse ikili guncel olsun)
    if not a.derleme_atla:
        print(f"\n1) Derleniyor ({ortam})...")
        r = subprocess.run([PIO, "run", "-e", ortam, "-d", os.path.join(PROJE, proje)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-1500:], r.stderr[-800:]); print("   HATA: derleme basarisiz."); return 1
        print("   derleme tamam")
    for f in ("bootloader.bin", "partitions.bin", "firmware.bin"):
        if not os.path.exists(os.path.join(BUILD, f)):
            print(f"HATA: {BUILD}/{f} yok."); return 1

    print("\n2) Indirme moduna aliniyor...")
    port = indirme_moduna_al()
    if not port:
        print("   HATA: kart indirme moduna alinamadi.")
        print("   Firmware'de CMD BOOTLOADER yoksa ve enableReboot(false) ise")
        print("   fiziksel BOOT+RST gerekir.")
        return 1
    print("   indirme portu:", port)

    print(f"\n3) Tam flash ({fmode}/{ffreq}/{fsize})...")
    komut = [PY, ESPTOOL, "--chip", "esp32s3", "--port", port,
             "--baud", a.baud, "--before", "no_reset", "--after", "no_reset",
             "write_flash", "--flash_mode", fmode,
             "--flash_freq", ffreq, "--flash_size", fsize,
             "0x0", os.path.join(BUILD, "bootloader.bin"),
             "0x8000", os.path.join(BUILD, "partitions.bin"),
             "0xe000", BOOT_APP0,
             "0x10000", os.path.join(BUILD, "firmware.bin")]
    r = subprocess.run(komut, capture_output=True, text=True)
    dogrulanan = r.stdout.count("Hash of data verified")
    mac_ok = seri_normal(seri) in seri_normal(r.stdout.replace(":", ""))
    print(f"   hash dogrulanan bolum: {dogrulanan} / 4   MAC eslesmesi: {'OK' if mac_ok else '??'}")
    if r.returncode != 0 or dogrulanan < 4:
        print(r.stdout[-1500:]); print("   HATA: flash basarisiz."); return 1

    print("\n4) Indirme-boot bayragi temizlenip reset atiliyor...")
    duzgun_reset(port)
    if not bekle(lambda: (firmware() or [None])[0], 10):
        # Nadiren no_reset baglantisi tutmaz; usb_reset ile bir kez daha dene.
        print("   firmware'e donmedi, usb_reset ile tekrar deneniyor...")
        subprocess.run([PY, ESPTOOL, "--chip", "esp32s3", "--port", port,
                        "--before", "usb_reset", "--after", "hard_reset", "--no-stub",
                        "write_mem", OPTION1_REG, "0x0", "0x1"],
                       capture_output=True, text=True)

    print("\n5) Dogrulama...")
    ok = dogrula()
    geri = kart_bul()
    if ok and not isinstance(geri, str) and geri[1] == seri and not geri[2]:
        print(f"\n>>> TAMAM: {ad} calisiyor.")
        return 0
    print("\n>>> SORUN: kart beklendigi gibi acilmadi ->", geri)
    return 1


if __name__ == "__main__":
    sys.exit(main())
