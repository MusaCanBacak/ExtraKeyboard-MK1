#!/usr/bin/env python3
"""ExtraKeyboard — kartı KUTUYU AÇMADAN indirme (flash) moduna alır.

Neden: kartlar kapalı kutuda; BOOT+RST tutmak her seferinde vida sökmek demek.
Bu araç iki yoldan birini kullanır ve ikisi de fiziksel temas gerektirmez:

  1) YENİ firmware (içinde `CMD BOOTLOADER CONFIRM` var):
     komut gönderilir, kart kendini indirme moduna alır. TERCİH EDİLEN yol.

  2) ESKİ firmware (`enableReboot(false)` yok):
     arduino-esp32 çekirdeğinin DTR/RTS durum makinesi yürütülür
     (0,1)->(1,1)->(1,0)->(0,0). Bu dizi kartı bootloader'a atar — ki zaten
     "bağlandı/koptu" salınımının kök nedeni buydu; burada KASITLI kullanıyoruz.

Kullanım:
    python3 tools/indirme-moduna-al.py
Çıktı: indirme portunun yolu (esptool'a verilecek port).
"""

import glob
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial yok. Proje .venv'i ile calistir: .venv/bin/python")

FIRMWARE_ACILIS_SN = 20.0   # komut/dizi sonrasi indirme portu bekleme suresi


def portlar():
    return sorted(glob.glob("/dev/cu.usbmodem*"))


def _esp_portlari():
    """(port, rom_mu) — YALNIZCA Espressif (VID 0x303A) portlari, KIMLIGE gore.
    Port adina bakmak YANLIS: baska kartlarin (orn. XIAO: usbmodem201201) portu
    da rakamli olabilir (2026-09-29 yakalandi)."""
    from serial.tools import list_ports
    out = []
    for pi in list_ports.comports():
        if pi.vid != 0x303A:
            continue
        urun = f"{pi.product or ''} {pi.description or ''}".lower()
        rom = "jtag" in urun or ":" in (pi.serial_number or "")
        if rom or "extrakeyboard" in urun:
            out.append((pi.device, rom))
    return out


def indirme_portu(hepsi=None):
    """ESP32-S3 ROM indirme portu (USB JTAG/serial debug unit)."""
    return [d for d, rom in _esp_portlari() if rom]


def firmware_portu(hepsi=None):
    """Calisan ExtraKeyboard firmware portu."""
    return [d for d, rom in _esp_portlari() if not rom]


def guvenli_ac(yol):
    """DTR/RTS'i acilistan ONCE ayarlar; dogrudan Serial(yol) kartı sifirlar."""
    s = serial.Serial()
    s.port = yol
    s.baudrate = 115200
    s.dtr = True
    s.rts = False
    s.timeout = 0.3
    s.open()
    return s


def indirme_portunu_bekle(onceki, sure=FIRMWARE_ACILIS_SN):
    t0 = time.time()
    while time.time() - t0 < sure:
        yeni = indirme_portu()
        if yeni and yeni != indirme_portu(onceki):
            return yeni[0]
        if yeni:
            return yeni[0]
        time.sleep(0.25)
    return None


def yol1_komut(port):
    """CMD BOOTLOADER CONFIRM — yeni firmware."""
    print("  yol 1: CMD BOOTLOADER CONFIRM deneniyor...")
    try:
        s = guvenli_ac(port)
    except Exception as e:
        print("     port acilamadi:", e)
        return False
    try:
        s.reset_input_buffer()
        s.write(b"CMD BOOTLOADER CONFIRM\n")
        s.flush()
        t0 = time.time()
        while time.time() - t0 < 2.0:
            satir = s.readline().decode(errors="replace").strip()
            if not satir:
                continue
            if "BOOTLOADER" in satir:
                print("     cihaz yaniti:", satir)
                if satir.startswith("ACK"):
                    return True
                if satir.startswith("ERR"):
                    return False
    except Exception as e:
        print("     komut hatasi:", e)
    finally:
        try:
            s.close()
        except Exception:
            pass
    return False


def yol2_dtr_rts(port):
    """4 adimli DTR/RTS dizisi — eski firmware."""
    print("  yol 2: DTR/RTS dizisi uygulaniyor (eski firmware)...")
    try:
        s = serial.Serial()
        s.port = port
        s.baudrate = 115200
        s.dtr = False
        s.rts = False
        s.timeout = 0.2
        s.open()
    except Exception as e:
        print("     port acilamadi:", e)
        return False
    time.sleep(0.3)
    try:
        for alan, deger in (("rts", True), ("dtr", True),
                            ("rts", False), ("dtr", False)):
            setattr(s, alan, deger)
            time.sleep(0.15)
    except Exception as e:
        print("     dizi hatasi:", e)
    finally:
        try:
            s.close()
        except Exception:
            pass
    return True


def main():
    hepsi = portlar()
    print("Portlar:", hepsi or "(yok)")

    hazir = indirme_portu(hepsi)
    if hazir:
        print("Kart ZATEN indirme modunda.")
        print(hazir[0])
        return 0

    fw = firmware_portu(hepsi)
    if not fw:
        print("HATA: ne firmware ne de indirme portu var. Kablo takili mi?")
        return 1

    port = fw[0]
    print("Firmware portu:", port)

    if yol1_komut(port):
        p = indirme_portunu_bekle(hepsi)
        if p:
            print("\nINDIRME MODU (komutla):", p)
            print(p)
            return 0
        print("  komut kabul edildi ama indirme portu gelmedi; yol 2'ye geciliyor")

    yol2_dtr_rts(port)
    p = indirme_portunu_bekle(hepsi)
    if p:
        print("\nINDIRME MODU (DTR/RTS ile):", p)
        print(p)
        return 0

    print("\nHATA: kart indirme moduna alinamadi.")
    print("Son portlar:", portlar())
    return 1


if __name__ == "__main__":
    sys.exit(main())
