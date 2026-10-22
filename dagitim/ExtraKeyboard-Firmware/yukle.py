#!/usr/bin/env python3
"""ExtraKeyboard MK1 — firmware yükleyici (macOS / Windows / Linux).

Kartı kutusunu açmadan kurar ya da günceller:
  1) takılı ExtraKeyboard'u USB kimliğinden bulur (port adına bakmaz),
  2) indirme moduna alır: CMD BOOTLOADER CONFIRM; eski firmware'de DTR/RTS;
     ikisi de olmazsa BOOT+RST tarifini gösterip bekler,
  3) modülü esptool ile tanır (PSRAM tipi + flash boyutu), doğru imajı seçer,
  4) imajı yazar — cihazdaki ayarlar (NVS bölümü) güncellemede korunur,
  5) indirme bayrağını temizleyip yeniden başlatır, kalp atışını doğrular.

Gereken: Python 3.8+, esptool 4.x/5.x, pyserial. Yukle-macOS.command ve
Yukle-Windows.bat bunları ilk çalıştırmada kendileri kurar.

  python3 yukle.py                     # sorarak ilerler
  python3 yukle.py --tani              # yalnızca kartı tanı, hiçbir şey yazma
  python3 yukle.py --tur numpad --evet
  python3 yukle.py --imaj kendi.bin    # kendi derlemeniz (0x0'dan birleşik imaj)
"""

import argparse
import os
import re
import struct
import subprocess
import sys
import tempfile
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("pyserial bulunamadı. Kurun:  python3 -m pip install pyserial esptool")
# esptool (GPL-2.0) yalnızca ayrı süreç olarak çalıştırılır, içe aktarılmaz;
# sürümü paket bilgisinden okunur.
try:
    from importlib.metadata import PackageNotFoundError, version
    ESPTOOL_SURUM = version("esptool")
except PackageNotFoundError:
    sys.exit("esptool bulunamadı. Kurun:  python3 -m pip install esptool pyserial")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")   # eski Windows konsollarında Türkçe

BURASI = os.path.dirname(os.path.abspath(__file__))
IMAJLAR = os.path.join(BURASI, "imajlar")
ESPRESSIF_VID = 0x303A

# CMD BOOTLOADER yolu çekirdekte FORCE_DOWNLOAD_BOOT bayrağını kurar ve bu
# bayrak yazmadan sonra da durur: temizlenmezse kart her resette yine indirme
# moduna açılır. ESP32-S3: RTC_CNTL_OPTION1_REG (0x60008000 + 0x12C), bit0.
OPTION1_REG = "0x6000812C"

# Hazır imajı olan (ve donanımda denenmiş) modüller:
#   (PSRAM MB, PSRAM tipi, flash MB) -> (imaj soneki, açıklama)
# "8MB AP_3v3" ESP32-S3R8 = Octal PSRAM; "2MB AP_3v3" ESP32-S3R2 = Quad PSRAM.
# AP_1v8 (WROOM-2, octal flash) ve diğer bileşimler için imaj YOKTUR: yanlış
# bellek ayarı kartı boot döngüsüne sokar.
MODULLER = {
    (8, "AP_3v3", 16): ("n16r8", "N16R8 — 16 MB flash + 8 MB Octal PSRAM"),
    (2, "AP_3v3", 8): ("n8r2", "N8R2 — 8 MB flash + 2 MB Quad PSRAM"),
}
TURLER = {
    "klavye": "Klavye — 12 tuş + enkoder + 3 LED",
    "numpad": "Numpad — 16 tuş, enkoder yok",
}
# Montajda üst sırası farklı bağlanmış birimler: genel imaj tuşları karıştırır.
OZEL_BIRIMLER = {
    "A085E3E74610": "E74610 (üst sıra takaslı) — tools/yukle-kutusuz.py ile güncelleyin",
}
MODLAR = {0: "qio", 1: "qout", 2: "dio", 3: "dout"}
BOYUTLAR = {2: 4, 3: 8, 4: 16}            # başlık bayt 3, üst yarım bayt -> MB
HIZLAR = {0x0: "40m", 0xF: "80m"}


class Hata(Exception):
    """Kullanıcıya gösterilip çıkılacak, beklenen hata."""


# ---------------------------------------------------------------------------
#  Port bulma — Espressif portlarını KİMLİĞE göre sınıflandırır
# ---------------------------------------------------------------------------

def mac_normal(s):
    """'A0:85:E3:E7:46:10' ve 'A085E3E74610' -> 'A085E3E74610'."""
    return re.sub(r"[^0-9A-F]", "", (s or "").upper())


def mac_bicim(m):
    return ":".join(m[i:i + 2] for i in range(0, len(m), 2)) if len(m) == 12 else (m or "?")


def espressif_portlari():
    """[(port, mac, tur)] — tur: 'ek' ExtraKeyboard firmware'i, 'rom' ROM /
    USB-JTAG (indirme modu, boş kart ya da BAŞKA bir ESP32-S3 projesi),
    '?' ürün adı okunamayan port (Windows) -> kalp atışıyla yoklanır."""
    out = []
    for pi in list_ports.comports():
        if pi.vid != ESPRESSIF_VID:
            continue
        seri = pi.serial_number or ""
        metin = " ".join(filter(None, (pi.product, pi.description, pi.manufacturer))).lower()
        if "jtag" in metin or ":" in seri:
            tur = "rom"
        elif "extrakeyboard" in metin or "bluedevelopment" in metin:
            tur = "ek"
        else:
            tur = "?"
        out.append((pi.device, mac_normal(seri), tur))
    return out


def guvenli_ac(port, timeout=0.3):
    """DTR yüksek, RTS düşük açar. RTS ASLA yükseltilmez: ESP32-S3'te DTR/RTS
    geçişleri kartı resetler ya da indirme moduna atar."""
    s = serial.Serial()
    s.port, s.baudrate, s.timeout, s.write_timeout = port, 115200, timeout, 2.0
    s.dtr, s.rts = True, False
    s.open()
    return s


def portu_tutanlar(port):
    """macOS/Linux: portu açık tutan diğer süreçler. macOS aynı portun iki
    programca açılmasına izin verir; o zaman satırlar ikiye bölünür."""
    if os.name == "nt":
        return []
    try:
        r = subprocess.run(["lsof", "-t", port], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []
    adlar = []
    for pid in r.stdout.split():
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        try:
            ad = subprocess.run(["ps", "-p", pid, "-o", "comm="], capture_output=True,
                                text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            ad = "?"
        adlar.append(f"{os.path.basename(ad) or '?'} (PID {pid})")
    return adlar


def port_serbest_bekle(port, sure=180):
    """Port başka programdaysa (ör. ExtraKeyboard uygulaması) kapanmasını bekler."""
    tutanlar = portu_tutanlar(port)
    if not tutanlar:
        return
    print(f"  Port kullanımda: {', '.join(tutanlar)}")
    print("  ExtraKeyboard uygulamasını kapatın (menü çubuğu / sistem tepsisi"
          " simgesi > Çıkış). Bekleniyor...", flush=True)
    t0 = time.time()
    while time.time() - t0 < sure:
        time.sleep(1)
        if not portu_tutanlar(port):
            print("  Port serbest.")
            return
    raise Hata("Port serbest kalmadı. Uygulamayı kapatıp yeniden deneyin.")


def kalp_atisi_yokla(port, sure=2.5):
    """True: HB geldi (ExtraKeyboard), False: gelmedi, None: port açılamadı."""
    try:
        s = guvenli_ac(port)
    except (serial.SerialException, OSError):
        return None
    try:
        t0 = time.time()
        while time.time() - t0 < sure:
            if s.readline().decode(errors="replace").startswith("HB "):
                return True
        return False
    finally:
        s.close()


def uart_ipucu():
    for pi in list_ports.comports():
        if pi.vid in (0x1A86, 0x10C4, 0x0403):       # CH34x, CP210x, FTDI
            print(f"  Not: {pi.device} bir USB-UART köprüsü. Kartın 'UART' konnektörüne"
                  " takılı olabilir;\n        'USB' yazan konnektörü kullanın.")


def hedef_bul(a):
    """Yüklenecek kartı seçer. Döner: (port, mac, tur)."""
    if a.port:
        for p in espressif_portlari():
            if p[0] == a.port:
                if p[2] != "?":
                    return p
                if kalp_atisi_yokla(p[0]):
                    return (p[0], p[1], "ek")
                raise Hata(f"{a.port} ExtraKeyboard olarak tanınmadı (kalp atışı yok).")
        raise Hata(f"{a.port} bir Espressif (ESP32-S3) portu değil ya da takılı değil.")

    t0, yazildi, mesgul_bildirildi = time.time(), False, set()
    while True:
        ek, rom = [], []
        for port, mac, tur in espressif_portlari():
            if tur == "?":
                sonuc = kalp_atisi_yokla(port)
                if sonuc is None and port not in mesgul_bildirildi:
                    mesgul_bildirildi.add(port)
                    print(f"  {port} açılamadı (kullanımda). ExtraKeyboard uygulaması"
                          " açıksa kapatın; bekleniyor...")
                tur = "ek" if sonuc else tur
            if tur == "ek":
                ek.append((port, mac, tur))
            elif tur == "rom":
                rom.append((port, mac, tur))
        if ek or rom:
            break
        if not yazildi:
            print("Kart bekleniyor — klavyeyi USB ile takın ('USB' yazan konnektör)...")
            uart_ipucu()
            yazildi = True
        if time.time() - t0 > 120:
            raise Hata("Kart bulunamadı. Kabloyu (veri kablosu olmalı) ve konnektörü kontrol edin.")
        time.sleep(1)

    if ek and rom:
        print("  Not: indirme modundaki / tanınmayan ESP32-S3 port(lar)ı yok sayıldı: "
              + ", ".join(f"{p[0]} ({mac_bicim(p[1])})" for p in rom))
    adaylar = ek or rom
    if len(adaylar) == 1:
        return adaylar[0]
    print("Birden fazla kart takılı:")
    for i, (port, mac, tur) in enumerate(adaylar, 1):
        print(f"  {i}) {port}   MAC {mac_bicim(mac)}"
              f"   {'ExtraKeyboard' if tur == 'ek' else 'indirme modu / tanınmayan'}")
    if a.evet:
        raise Hata("Birden fazla kart var; --port ile seçin ya da yalnızca birini takılı bırakın.")
    secim = input("Hangisine yüklensin? (numara): ").strip()
    if not secim.isdigit() or not 1 <= int(secim) <= len(adaylar):
        raise Hata("Geçersiz seçim.")
    return adaylar[int(secim) - 1]


def rom_portu(mac):
    """Aynı kartın ROM (indirme) portu. Seri no'dan MAC okunamıyorsa (bazı
    Windows sürücüleri) tek ROM portu kabul edilir."""
    rom = [p for p in espressif_portlari() if p[2] == "rom"]
    eslesen = [p[0] for p in rom if p[1] == mac]
    if eslesen:
        return eslesen[0]
    if len(rom) == 1 and len(rom[0][1]) != 12:
        return rom[0][0]
    return None


def firmware_portu(mac):
    """Aynı kartın ExtraKeyboard firmware portu (yeniden başlatmadan sonra)."""
    adaylar = []
    for port, m, tur in espressif_portlari():
        if tur == "rom":
            continue
        if m == mac:
            return port
        adaylar.append(port)
    return adaylar[0] if len(adaylar) == 1 and len(mac) != 12 else None


def bekle(kosul, sure, adim=0.5):
    t0 = time.time()
    while time.time() - t0 < sure:
        r = kosul()
        if r:
            return r
        time.sleep(adim)
    return None


# ---------------------------------------------------------------------------
#  esptool — 4.x alt çizgili, 5.x tireli adlar kullanır
# ---------------------------------------------------------------------------

def esptool_calistir(port, komut, *arg, before="no_reset", after="no_reset",
                     stub=True, ilerleme=None, deneme=3, baud=None):
    """Döner: (çıkış kodu, tüm çıktı). `ilerleme(satır, önceki satırlar)` bir
    yüzde döndürürse yazma sırasında tek satırlık gösterge basılır."""
    tire = int(ESPTOOL_SURUM.split(".")[0]) >= 5
    ad = (lambda s: s.replace("_", "-")) if tire else (lambda s: s)
    argv = [sys.executable, "-m", "esptool", "--chip", "esp32s3", "--port", port,
            "--connect-attempts", str(deneme),
            "--before", ad(before), "--after", ad(after)]
    if baud:
        argv += ["--baud", str(baud)]
    if not stub:
        argv.append("--no-stub")
    argv.append(ad(komut))
    argv += [ad(x) if x.startswith("--") else x for x in arg]
    ortam = dict(os.environ, PYTHONUNBUFFERED="1")
    if not ilerleme:
        r = subprocess.run(argv, capture_output=True, env=ortam)
        return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")

    # Çıktıyı biriktirirken yalnızca yüzdeyi tek satırda göster.
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ortam)
    tampon, metin, son = b"", [], -1
    while True:
        parca = p.stdout.read1(512) if hasattr(p.stdout, "read1") else p.stdout.read(1)
        if not parca:
            break
        tampon += parca
        satirlar = re.split(rb"[\r\n]", tampon)
        tampon = satirlar.pop()
        for s in satirlar:
            s = s.decode("utf-8", "replace")
            yuzde = ilerleme(s, metin)
            metin.append(s)
            if yuzde is not None and yuzde != son:
                son = yuzde
                print(f"\r  yazılıyor: %{son:3d}", end="", flush=True)
    p.wait()
    if son >= 0:
        print()
    metin.append(tampon.decode("utf-8", "replace"))
    return p.returncode, "\n".join(metin)


BAGLANTI_HATASI = re.compile(r"Failed to connect|No serial data received|Wrong boot mode"
                             r"|could not open port|port is busy|Could not open", re.I)


def esptool_baglanarak(port, komut, *arg, beforelar=("no_reset",), **kw):
    """Bağlanamazsa sıradaki reset yöntemiyle yeniden dener (yalnızca BAĞLANTI
    hatasında; yazma başladıktan sonraki hata yeniden denenmez)."""
    rc, out = 1, ""
    for b in beforelar:
        rc, out = esptool_calistir(port, komut, *arg, before=b, **kw)
        if rc == 0 or not BAGLANTI_HATASI.search(out) or "Writing at" in out:
            break
    return rc, out


def son_satirlar(metin, n=25):
    return "\n".join("    " + s for s in metin.strip().splitlines()[-n:])


# ---------------------------------------------------------------------------
#  Adımlar
# ---------------------------------------------------------------------------

def rom_kararli_bekle(mac, sure=8.0, kararlilik=1.0):
    """ROM portunun en az `kararlilik` sn kesintisiz görünmesini bekler.
    Döner: (ROM portu ya da None, kart firmware'e geri mi açıldı)."""
    t0, gorulen, ilk, fw_gitti = time.time(), None, 0.0, False
    while time.time() - t0 < sure:
        rom, fw = rom_portu(mac), firmware_portu(mac)
        fw_gitti = fw_gitti or not fw
        if rom:
            if rom != gorulen:
                gorulen, ilk = rom, time.time()
            elif time.time() - ilk >= kararlilik:
                return rom, False
        else:
            gorulen = None
            if fw and fw_gitti:
                return None, True
        time.sleep(0.2)
    return None, False


def bootloader_komutu(port):
    """CMD BOOTLOADER CONFIRM gönderir. Döner: ACK geldi mi."""
    s = guvenli_ac(port)
    ack = False
    try:
        s.reset_input_buffer()
        s.write(b"CMD BOOTLOADER CONFIRM\n")
        t0 = time.time()
        while time.time() - t0 < 2.0 and not ack:
            satir = s.readline().decode(errors="replace").strip()
            ack = satir.startswith("ACK") and "BOOTLOADER" in satir
    finally:
        try:
            s.close()
        except (serial.SerialException, OSError):
            pass                                # port zaten kaybolmuş olabilir
    return ack


def indirme_moduna_al(port, mac):
    """Firmware'deki kartı ROM indirme moduna alır. Döner: ROM portu."""
    port_serbest_bekle(port)

    # Yol 1 — kasıtlı komut (2026-09 sonrası firmware). 2026-10-22 öncesi
    # firmware'de, bir önceki esptool oturumundan hemen sonra kart bir kez
    # indirme modu yerine firmware'e geri açılabiliyor: o zaman tekrar denenir.
    for deneme in range(3):
        try:
            ack = bootloader_komutu(port)
        except (serial.SerialException, OSError) as e:
            if "denied" in str(e).lower() or "busy" in str(e).lower():
                raise Hata(f"{port} kullanımda. ExtraKeyboard uygulamasını kapatıp yeniden deneyin.")
            print(f"  komut gönderilemedi: {e}")
            break
        if not ack:
            break                               # komutu bilmeyen eski firmware
        rom, geri_acildi = rom_kararli_bekle(mac)
        if rom:
            return rom
        if not geri_acildi:
            break
        print("  kart indirme modu yerine yeniden firmware ile açıldı; tekrar deneniyor...")
        port = bekle(lambda: firmware_portu(mac), 10, adim=0.2) or port
        time.sleep(1.5)                         # USB CDC'nin hazır olması için

    # Yol 2 — DTR/RTS dizisi (USB CDC yeniden başlatması açık kalan eski firmware)
    fw = firmware_portu(mac)
    if fw:
        print("  eski firmware yöntemi deneniyor (DTR/RTS)...")
        try:
            s = serial.Serial()
            s.port, s.baudrate, s.timeout = fw, 115200, 0.2
            s.dtr, s.rts = False, False
            s.open()
            time.sleep(0.3)
            for alan, deger in (("rts", True), ("dtr", True), ("rts", False), ("dtr", False)):
                setattr(s, alan, deger)
                time.sleep(0.15)
            s.close()
        except (serial.SerialException, OSError) as e:
            print(f"  dizi gönderilemedi: {e}")
        rom, _ = rom_kararli_bekle(mac, sure=10)
        if rom:
            return rom

    # Yol 3 — elle
    print("\n  Kart yazılımla indirme moduna alınamadı. Elle alın:")
    print("    1) BOOT düğmesini basılı tutun")
    print("    2) RST düğmesine bir kez basıp bırakın")
    print("    3) BOOT düğmesini bırakın")
    print("  Bekleniyor (2 dakika)...", flush=True)
    rom, _ = rom_kararli_bekle(mac, sure=120)
    if not rom:
        raise Hata("Kart indirme moduna girmedi.")
    return rom


def modul_tani(port, beforelar):
    rc, out = esptool_baglanarak(port, "flash_id", beforelar=beforelar,
                                 after="no_reset", stub=False)
    if rc != 0:
        raise Hata("Karta bağlanılamadı (esptool flash_id):\n" + son_satirlar(out))
    bul = lambda desen: re.search(desen, out, re.M)
    mac = bul(r"^MAC:\s+((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})")
    psram = bul(r"Embedded PSRAM (\d+)MB \(([^)]*)\)")
    flash = bul(r"Detected flash size:\s*(\d+)MB")
    cip = bul(r"(?:Chip is|Chip type:)\s*(.+)$")
    return {
        "mac": mac_normal(mac.group(1)) if mac else "",
        "psram": (int(psram.group(1)), psram.group(2)) if psram else None,
        "flash": int(flash.group(1)) if flash else None,
        "cip": cip.group(1).strip() if cip else "?",
    }, out


def modul_bul(bilgi):
    """Tanınan modülün (imaj soneki, açıklama) çifti; hazır imaj yoksa None."""
    psram_mb, psram_tip = bilgi["psram"] or (0, "")
    return MODULLER.get((psram_mb, psram_tip, bilgi["flash"]))


def imaj_oku(yol):
    """Birleşik imajı okuyup denetler. Döner: (veri, flash MB, nvs aralığı)."""
    try:
        veri = open(yol, "rb").read()
    except OSError as e:
        raise Hata(f"İmaj okunamadı: {e}")
    if len(veri) <= 0x10000 or veri[0] != 0xE9 or veri[0x10000] != 0xE9:
        raise Hata(f"{os.path.basename(yol)} birleşik imaj değil (0x0'da bootloader,"
                   " 0x10000'de uygulama olmalı).")
    boyut = BOYUTLAR.get(veri[3] >> 4)
    nvs = None
    for i in range(0x8000, 0x8C00, 32):             # bölüm tablosu
        kayit = veri[i:i + 32]
        if kayit[:2] != b"\xAA\x50":
            break
        if kayit[2] == 0x01 and kayit[3] == 0x02:   # data / nvs
            ofs, uz = struct.unpack_from("<II", kayit, 4)
            nvs = (ofs, ofs + uz)
    return veri, boyut, nvs


def onay(soru, a):
    if a.evet:
        return True
    return input(f"{soru} [e/H]: ").strip().lower() in ("e", "evet", "y", "yes")


def yeniden_baslat(rom, mac):
    """İndirme bayrağını temizleyip resetler. Döner: firmware portu ya da None.

    --before usb_reset şart: no_reset ile bağlanıp hard_reset atınca kart
    indirme modunda kaldı; USB-JTAG reset dizisinden sonra atılan hard_reset
    ise kartı her denemede ~1 sn'de firmware'e açtı (ölçüldü, esptool 5.6)."""
    for _ in range(2):
        rom = rom_portu(mac) or rom
        esptool_calistir(rom, "write_mem", OPTION1_REG, "0x0", "0x1",
                         before="usb_reset", after="hard_reset", stub=False)
        p = bekle(lambda: firmware_portu(mac), 10, adim=0.2)
        if p:
            return p
    return None


def dogrula(port, sure=6.0):
    """Döner: (kalp atışı sayısı, ID satırı)."""
    time.sleep(1.0)
    try:
        s = guvenli_ac(port, timeout=0.5)
    except (serial.SerialException, OSError) as e:
        print(f"  doğrulama portu açılamadı: {e}")
        return 0, None
    hb, kimlik = 0, None
    try:
        time.sleep(0.3)
        s.write(b"CMD ID\n")
        t0 = time.time()
        while time.time() - t0 < sure:
            satir = s.readline().decode(errors="replace").strip()
            if satir.startswith("HB "):
                hb += 1
            elif satir.startswith("ID "):
                kimlik = satir
    except (serial.SerialException, OSError) as e:
        print(f"  doğrulama sırasında hata: {e}")
    finally:
        s.close()
    return hb, kimlik


def tur_sor(a):
    if a.tur:
        return a.tur
    print()
    for i, aciklama in enumerate(TURLER.values(), 1):
        print(f"   {i}) {aciklama}")
    cevap = input("   Bu kart hangisi? (1/2): ").strip()
    secilen = {"1": "klavye", "2": "numpad"}.get(cevap)
    if not secilen:
        raise Hata("Geçersiz seçim.")
    return secilen


def ozel_birim_denetle(mac, a):
    if mac in OZEL_BIRIMLER and not a.imaj and not a.tani:
        raise Hata(f"Bu birim özel: {OZEL_BIRIMLER[mac]}.\n"
                   "  Genel imaj tuşları karıştırır; --imaj ile o birimin derlemesini verin.")


def imaj_hazirla(a, secilen, bilgi, tur):
    """Döner: (imaj yolu, veri, flash MB, yazılacak bölgeler, ayarlar korunuyor mu)."""
    modul = modul_bul(bilgi)
    if a.imaj:
        yol = os.path.abspath(a.imaj)
    elif not modul:
        raise Hata("Bu modül için hazır imaj yok. Kaynak koddan kendi ortamınızı derleyin\n"
                   "  (README → Firmware) ve --imaj ile verin.")
    else:
        yol = os.path.join(IMAJLAR, f"ExtraKeyboard-{secilen}-{modul[0]}.bin")
    veri, imaj_mb, nvs = imaj_oku(yol)
    if not imaj_mb:
        raise Hata("İmaj başlığındaki flash boyutu tanınmadı.")
    if bilgi["flash"] and imaj_mb > bilgi["flash"]:
        raise Hata(f"İmaj {imaj_mb} MB flash bekliyor, kartta {bilgi['flash']} MB var.")
    if a.imaj and imaj_mb != bilgi["flash"]:
        print(f"   UYARI: imaj başlığı {imaj_mb} MB, kartın flash'ı {bilgi['flash']} MB.")
    # Ayarlar yalnızca ExtraKeyboard firmware'inden güncellemede korunur (boş ya
    # da yabancı kartta o bölgede başka şey olabilir -> tam yazma).
    koru = bool(tur == "ek" and not a.ayarlari_sil and nvs and nvs[0] % 0x1000 == 0
                and nvs[1] % 0x1000 == 0 and nvs[1] < len(veri))
    bolgeler = [(0x0, veri[:nvs[0]]), (nvs[1], veri[nvs[1]:])] if koru else [(0x0, veri)]
    return yol, veri, imaj_mb, bolgeler, koru


def yaz(rom, beforelar, imaj_mb, bolgeler, baud):
    boylar = [len(parca) for _, parca in bolgeler]

    def ilerleme(satir, onceki):
        """esptool yüzdesi bölge başınadır; toplam bayta çevrilir. Biten
        bölge sayısı, esptool'un her bölge sonunda yazdığı 'Wrote' satırıdır."""
        m = re.search(r"Writing at .*?(\d+(?:\.\d+)?)\s?%", satir)
        if not m:
            return None
        biten = min(sum(x.startswith("Wrote ") for x in onceki), len(boylar) - 1)
        yazilan = sum(boylar[:biten]) + float(m.group(1)) / 100 * boylar[biten]
        return int(yazilan * 100 / sum(boylar))

    with tempfile.TemporaryDirectory() as gecici:
        arg = ["--flash_mode", "dio", "--flash_freq", "40m", "--flash_size", f"{imaj_mb}MB"]
        for i, (adres, parca) in enumerate(bolgeler):
            dosya = os.path.join(gecici, f"bolge{i}.bin")
            with open(dosya, "wb") as f:
                f.write(parca)
            arg += [hex(adres), dosya]
        rc, out = esptool_baglanarak(rom, "write_flash", *arg, beforelar=beforelar,
                                     after="no_reset", stub=True, ilerleme=ilerleme, baud=baud)
    dogrulanan = out.count("Hash of data verified")
    if rc != 0 or dogrulanan < len(bolgeler):
        raise Hata(f"Yazma başarısız ({dogrulanan}/{len(bolgeler)} bölge doğrulandı):\n"
                   + son_satirlar(out) + "\n  Yükleyiciyi yeniden çalıştırın; kart indirme"
                   " modunda kaldıysa USB'den çıkarıp takın.")
    print(f"   {dogrulanan}/{len(bolgeler)} bölge yazıldı ve doğrulandı")


def main():
    ap = argparse.ArgumentParser(
        description="ExtraKeyboard MK1 firmware yükleyici — kartı tanır, doğru imajı yazar.")
    ap.add_argument("--tur", choices=sorted(TURLER), help="klavye ya da numpad (sorulmaz)")
    ap.add_argument("--imaj", help="belirli bir birleşik imajı yaz (0x0'dan başlayan .bin)")
    ap.add_argument("--port", help="portu elle seç")
    ap.add_argument("--tani", action="store_true", help="yalnızca kartı tanı, hiçbir şey yazma")
    ap.add_argument("--ayarlari-sil", action="store_true",
                    help="cihazdaki ayarları (OS modu, LED, enkoder modu) da sıfırla")
    ap.add_argument("--evet", action="store_true", help="onay sorma")
    ap.add_argument("--baud", default="460800")
    a = ap.parse_args()

    print("=" * 62)
    print(f" ExtraKeyboard MK1 — firmware yükleyici   (esptool {ESPTOOL_SURUM})")
    print("=" * 62)

    # 1) Kartı bul — bu aşamada karta hiçbir şey yapılmaz
    port, mac, tur = hedef_bul(a)
    if tur == "ek":
        print(f"Kart   : ExtraKeyboard (firmware çalışıyor)  {port}")
    else:
        print(f"Kart   : indirme modunda ya da üzerinde ExtraKeyboard firmware'i yok  {port}")
        print("         Bu port BAŞKA bir ESP32-S3 projesine de ait olabilir.")
        soru = ("Kart tanıma için yeniden başlatılacak. Devam?" if a.tani
                 else "Bu karta ExtraKeyboard firmware'i yazılacak. Devam?")
        if not onay(soru, a):
            raise Hata("İptal edildi.")
    print(f"MAC    : {mac_bicim(mac)}")
    ozel_birim_denetle(mac, a)
    secilen = None if (a.tani or a.imaj) else tur_sor(a)

    # 2) İndirme moduna al
    print("\n1) İndirme moduna alınıyor...")
    if tur == "ek":
        rom = indirme_moduna_al(port, mac)
        beforelar = ("no_reset", "default_reset", "usb_reset")
    else:
        rom = port
        beforelar = ("default_reset", "usb_reset", "no_reset")
    print(f"   indirme portu: {rom}")

    # Buradan yazmaya kadar çıkan her hatada kart firmware'ine geri döndürülür;
    # aksi hâlde indirme modunda kalır (çıkarıp takmak gerekir).
    try:
        print("\n2) Modül tanınıyor...")
        bilgi, _ = modul_tani(rom, beforelar)
        mac = bilgi["mac"] or mac
        psram = (f"{bilgi['psram'][0]} MB ({bilgi['psram'][1] or 'sağlayıcı bilinmiyor'})"
                 if bilgi["psram"] else "yok")
        print(f"   çip: {bilgi['cip']}   flash: {bilgi['flash'] or '?'} MB   PSRAM: {psram}")
        modul = modul_bul(bilgi)
        print(f"   modül: {modul[1] if modul else 'TANINMADI — hazır imaj yok'}")
        if a.tani:
            print("\n3) Yazma yok (--tani). Kart yeniden başlatılıyor...")
            fw = yeniden_baslat(rom, mac)
            print(f"   {'kart firmware ile açıldı: ' + fw if fw else 'kart firmware portuyla dönmedi'}")
            return 0 if fw or tur != "ek" else 1
        ozel_birim_denetle(mac, a)
        yol, veri, imaj_mb, bolgeler, koru = imaj_hazirla(a, secilen, bilgi, tur)
        print(f"\n   imaj   : {os.path.basename(yol)}  ({len(veri) // 1024} KB,"
              f" {imaj_mb} MB, DIO/40 MHz)")
        print(f"   ayarlar: {'korunacak' if koru else 'sıfırlanacak'}")
        if not onay("   Yüklensin mi?", a):
            raise Hata("İptal edildi.")
    except (Hata, KeyboardInterrupt):
        if tur == "ek":
            print("\n  (kart firmware'ine geri döndürülüyor...)")
            yeniden_baslat(rom, mac)
        raise

    # 3) Yaz
    print("\n3) Yazılıyor...")
    yaz(rom, beforelar, imaj_mb, bolgeler, a.baud)

    # 4) Yeniden başlat ve doğrula
    print("\n4) Kart yeniden başlatılıyor...")
    fw = yeniden_baslat(rom, mac)
    if not fw:
        raise Hata("Kart firmware ile açılmadı. USB'den çıkarıp yeniden takın; firmware"
                   " yazıldı, bu genellikle yeterlidir.")
    hb, kimlik = dogrula(fw)
    print(f"   port: {fw}   kalp atışı: {hb}   {kimlik or ''}")
    if hb < 3:
        raise Hata("Kart açıldı ama kalp atışı gelmedi. USB'den çıkarıp takın ve"
                   " uygulamayı açın.")
    print("\n>>> TAMAM — firmware yüklendi. Şimdi bilgisayar uygulamasını açabilirsiniz.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Hata as e:
        print(f"\nHATA: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nİptal edildi. Kart indirme modunda kaldıysa USB'den çıkarıp takın.")
        sys.exit(130)
