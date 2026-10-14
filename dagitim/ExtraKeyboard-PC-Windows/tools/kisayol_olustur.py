"""
ExtraKeyboard MK1 — masaüstü kısayolu ve uygulama simgesi üretici.

Başlatıcılar (Baslat.command / Baslat.bat) kurulum sonrasında bunu çağırır;
kullanıcının masaüstüne uygun simgeli bir kısayol kurulur:

* **macOS** — proje klasöründe gerçek bir ``ExtraKeyboard.app`` paketi
  oluşturulur (çift tıklanınca ``ExtraKeyboard-Baslat.command`` /
  ``Baslat.command`` zincirini çalıştırır) ve masaüstüne sembolik
  bağlantısı konur. Simge: PIL ile üretilen PNG'lerden ``iconutil`` ile
  ``.icns`` (ikisi de macOS'ta hazırdır).
* **Windows** — masaüstüne ``ExtraKeyboard.lnk`` kısayolu (PowerShell
  WScript.Shell) konur; hedef konsolsuz ``pythonw.exe run_app.py``,
  simge PIL ile üretilen çok boyutlu ``.ico``.

Betik İDEMPOTENTTİR: kısayol zaten kuruluysa hiçbir şey yapmadan çıkar
(``--yenile`` bayrağı zorla yeniden üretir). Hata durumunda sessizce
uyarı yazar ama asla sıfırdan farklı kodla çıkıp başlatıcıyı kesmez.
"""

from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import sys

PROJE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARLIK = os.path.join(PROJE, "varliklar")
APP_ADI = "ExtraKeyboard"

# Kart/uygulama temasıyla uyumlu renkler (app/ui/theme.py ile aynı aile)
_ZEMIN = (26, 26, 26, 255)        # koyu zemin
_KART = (33, 33, 33, 255)         # yuvarlak kare
_VURGU = (59, 142, 208, 255)      # "EK" yazısı — mavi
_LED = [(30, 144, 255, 255),      # mavi (OS)
        (255, 149, 0, 255),       # turuncu (COMBO)
        (44, 201, 133, 255)]      # yeşil (bağlantı)


def _yazi_tipi(boyut: int):
    """Kalın bir TrueType yazı tipi bulmaya çalışır; olmazsa varsayılan."""
    from PIL import ImageFont

    adaylar = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for yol in adaylar:
        try:
            return ImageFont.truetype(yol, boyut)
        except Exception:
            continue
    return ImageFont.load_default()


def simge_uret(boyut: int = 1024):
    """Uygulama simgesini (PIL Image) üretir: koyu kart + LED'ler + EK."""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (boyut, boyut), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    kenar = int(boyut * 0.06)
    r = int(boyut * 0.22)
    d.rounded_rectangle([kenar, kenar, boyut - kenar, boyut - kenar],
                        radius=r, fill=_KART, outline=_ZEMIN,
                        width=max(2, boyut // 128))

    # Üstte üç durum LED'i
    led_r = int(boyut * 0.045)
    led_y = int(boyut * 0.30)
    aralik = int(boyut * 0.16)
    bas_x = boyut // 2 - aralik
    for i, renk in enumerate(_LED):
        cx = bas_x + i * aralik
        d.ellipse([cx - led_r, led_y - led_r, cx + led_r, led_y + led_r],
                  fill=renk)

    # Ortada "EK"
    font = _yazi_tipi(int(boyut * 0.42))
    metin = "EK"
    try:
        bbox = d.textbbox((0, 0), metin, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((boyut / 2 - tw / 2 - bbox[0],
                boyut * 0.60 - th / 2 - bbox[1]), metin,
               font=font, fill=_VURGU)
    except Exception:
        d.text((boyut * 0.3, boyut * 0.45), metin, fill=_VURGU)
    return img


def _png_kaydet() -> str:
    os.makedirs(VARLIK, exist_ok=True)
    yol = os.path.join(VARLIK, "simge-1024.png")
    if not os.path.exists(yol):
        simge_uret(1024).save(yol)
    return yol


# ---------------------------------------------------------------------------
#  macOS
# ---------------------------------------------------------------------------

def _simge_ata(hedef: str, png: str) -> bool:
    """NSWorkspace ile bir dosyaya özel simge basar (Finder'da görünür)."""
    betik = (
        'use framework "AppKit"\n'
        f'set img to current application\'s NSImage\'s alloc()\'s '
        f'initWithContentsOfFile:"{png}"\n'
        f'current application\'s NSWorkspace\'s sharedWorkspace()\'s '
        f'setIcon:img forFile:"{hedef}" options:0\n'
    )
    yol = os.path.join(VARLIK, "_simge_ata.scpt.txt")
    try:
        with open(yol, "w", encoding="utf-8") as f:
            f.write(betik)
        sonuc = subprocess.run(["osascript", yol], capture_output=True,
                               text=True, timeout=30)
        return sonuc.returncode == 0
    except Exception:
        return False
    finally:
        try:
            os.remove(yol)
        except OSError:
            pass


def mac_kur(yenile: bool = False) -> None:
    """Uygulamalar klasörüne özel simgeli, çift tıklanabilir kısayol kurar.

    NEDEN .app PAKETİ DEĞİL: macOS gizlilik koruması (TCC), Masaüstü /
    Belgeler / İndirilenler altındaki betikleri YENİ bir uygulama
    kimliğinden çalıştırmayı sormadan reddeder ("Operation not
    permitted") — imzasız/ad-hoc imzalı el yapımı paketlerde izin
    penceresi bile çıkmaz. Bu yüzden kısayol, kullanıcının ZATEN izinli
    olan Terminal'i üzerinden çalışan başlatıcı .command dosyasına
    yapılan bir Finder alias'ıdır; hem alias'a hem .command'a PIL ile
    üretilen uygulama simgesi basılır.
    """
    # Kısayol Uygulamalar klasörüne kurulur (Masaüstü'ne DEĞİL). ~/Applications
    # kullanıcıya aittir; yönetici şifresi gerektirmez ve Finder kenar
    # çubuğunda "Uygulamalar" altında görünür. Yoksa oluşturulur.
    hedef_dizin = os.path.expanduser("~/Applications")
    try:
        os.makedirs(hedef_dizin, exist_ok=True)
    except OSError:
        # ~/Applications oluşturulamazsa son çare olarak masaüstüne düş.
        hedef_dizin = os.path.expanduser("~/Desktop")
    kisayol = os.path.join(hedef_dizin, APP_ADI)  # Finder alias adı (uzantısız)

    masaustu = os.path.expanduser("~/Desktop")

    # Eski (çalışmayan) .app stratejisinin ve ESKİ MASAÜSTÜ kısayolunun
    # kalıntılarını temizle (artık kısayol Uygulamalar'da duruyor).
    for eski in (os.path.join(masaustu, f"{APP_ADI}.app"),
                 os.path.join(PROJE, f"{APP_ADI}.app"),
                 os.path.join(masaustu, APP_ADI),
                 os.path.join(masaustu, f"{APP_ADI}.command")):
        try:
            if os.path.islink(eski) or os.path.isfile(eski):
                os.remove(eski)
            elif os.path.isdir(eski):
                shutil.rmtree(eski, ignore_errors=True)
        except OSError:
            pass

    if os.path.exists(kisayol) and not yenile:
        return  # zaten kurulu

    baslatici = None
    for aday in ("ExtraKeyboard-Baslat.command", "Baslat.command"):
        tam = os.path.join(PROJE, aday)
        if os.path.exists(tam):
            baslatici = tam
            break
    if baslatici is None:
        print("UYARI: başlatıcı .command bulunamadı; kısayol kurulmadı.")
        return

    png = _png_kaydet()
    _simge_ata(baslatici, png)  # hedefin kendisi de doğru simgeyle görünsün

    # Finder alias'ı oluştur (Otomasyon izni bir kez sorulabilir).
    alias_ok = False
    try:
        if os.path.exists(kisayol):
            os.remove(kisayol)
        sonuc = subprocess.run(
            ["osascript",
             "-e", 'tell application "Finder"',
             "-e", f'set hedefKlasor to (POSIX file "{hedef_dizin}") as alias',
             "-e", f'set yeni to make new alias file at hedefKlasor to '
                   f'(POSIX file "{baslatici}")',
             "-e", f'set name of yeni to "{APP_ADI}"',
             "-e", "end tell"],
            capture_output=True, text=True, timeout=60)
        alias_ok = sonuc.returncode == 0
        if not alias_ok:
            print(f"UYARI: Finder alias kurulamadı: {sonuc.stderr.strip()[:120]}")
    except Exception as hata:
        print(f"UYARI: Finder alias kurulamadı ({hata}).")

    if not alias_ok:
        # Yedek: sembolik bağlantı (çift tıklanınca yine Terminal'de açılır).
        try:
            yedek = os.path.join(hedef_dizin, f"{APP_ADI}.command")
            if not os.path.exists(yedek):
                os.symlink(baslatici, yedek)
            kisayol = yedek
        except OSError as hata:
            print(f"UYARI: Uygulamalar kısayolu kurulamadı ({hata}).")
            return

    _simge_ata(kisayol, png)
    print(f"Uygulamalar kısayolu kuruldu: {kisayol}")


# ---------------------------------------------------------------------------
#  Windows
# ---------------------------------------------------------------------------

def _ico_uret() -> str | None:
    ico = os.path.join(VARLIK, "simge.ico")
    if os.path.exists(ico):
        return ico
    try:
        simge_uret(256).save(
            ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                        (64, 64), (128, 128), (256, 256)])
        return ico
    except Exception as hata:
        print(f"UYARI: .ico üretilemedi ({hata}).")
        return None


def win_kur(yenile: bool = False) -> None:
    """Masaüstüne ExtraKeyboard.lnk kısayolu kurar (PowerShell ile)."""
    pythonw = os.path.join(PROJE, ".venv", "Scripts", "pythonw.exe")
    hedef = pythonw if os.path.exists(pythonw) else os.path.join(
        PROJE, "Baslat.bat")
    arguman = "run_app.py" if hedef == pythonw else ""
    ico = _ico_uret()

    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        "$masa = $ws.SpecialFolders('Desktop'); "
        f"$yol = Join-Path $masa '{APP_ADI}.lnk'; "
        + ("" if yenile else "if (Test-Path $yol) { exit 0 }; ")
        + "$s = $ws.CreateShortcut($yol); "
        f"$s.TargetPath = '{hedef}'; "
        + (f"$s.Arguments = '{arguman}'; " if arguman else "")
        + f"$s.WorkingDirectory = '{PROJE}'; "
        + (f"$s.IconLocation = '{ico},0'; " if ico else "")
        + f"$s.Description = 'ExtraKeyboard MK1'; $s.Save()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True, capture_output=True, timeout=30)
        print("Masaüstü kısayolu kuruldu (ExtraKeyboard.lnk).")
    except Exception as hata:
        print(f"UYARI: masaüstü kısayolu kurulamadı ({hata}).")


def main() -> int:
    yenile = "--yenile" in sys.argv
    try:
        _png_kaydet()
        if sys.platform == "darwin":
            mac_kur(yenile)
        elif sys.platform.startswith("win"):
            win_kur(yenile)
        else:
            print("Bu platformda masaüstü kısayolu desteklenmiyor (atlandı).")
    except Exception as hata:
        # Kısayol üretimi hiçbir zaman uygulamanın açılmasını engellememeli.
        print(f"UYARI: kısayol kurulumunda beklenmeyen hata: {hata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
