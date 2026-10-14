#!/usr/bin/env python3
"""
ExtraKeyboard MK1 — cihazsız otokontrol.

Uygulamanın çekirdeğini fiziksel klavye OLMADAN uçtan uca sınar:
yapılandırma, protokol ayrıştırma, combo mantığı, eylem normalizasyonu,
v2 taşıma, mobil ayar sunucusu ve arayüzün açılıp olay işleyebilmesi.

Kullanım (proje kökünden):
    .venv/bin/python tools/selfcheck.py           # çekirdek testleri
    .venv/bin/python tools/selfcheck.py --ui      # + arayüzü gerçekten açar (5 sn)

Her satır ✓/✗ ile biter; ✗ varsa çıkış kodu 1'dir.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)
os.chdir(KOK)

SONUCLAR: list[tuple[bool, str]] = []


def kontrol(ad: str, kosul: bool, detay: str = "") -> None:
    """Tek bir kontrolü kaydet ve yazdır."""
    SONUCLAR.append((kosul, ad))
    isaret = "✓" if kosul else "✗"
    ek = f"  [{detay}]" if detay and not kosul else ""
    print(f"  {isaret} {ad}{ek}")


# ---------------------------------------------------------------- yapılandırma
def test_config() -> None:
    print("\n[1] Yapılandırma (config.py)")
    from app.core.config import (ACTION_TYPES, COMBO_IDS, ENCODER_IDS, KEY_IDS,
                                 ConfigManager, combo_id, parse_combo_id)

    kontrol("10 tuş kimliği", KEY_IDS == [f"K{i}" for i in range(1, 11)])
    kontrol("45 combo kimliği", len(COMBO_IDS) == 45)
    kontrol("combo a<b normalize", combo_id(5, 2) == "C_2_5")
    kontrol("combo geri çözme", parse_combo_id("C_2_5") == (2, 5))
    kontrol("4 enkoder yuvası", ENCODER_IDS == ["cw", "ccw", "press", "long"])
    kontrol("10 eylem tipi", len(ACTION_TYPES) == 10)

    with tempfile.TemporaryDirectory() as d:
        yol = os.path.join(d, "config.json")
        cm = ConfigManager(yol)
        cm.load()
        cm.save()
        veri = json.load(open(yol))
        p = veri["profiles"][veri["active_profile"]]
        for osk in ("windows", "mac"):
            kontrol(f"{osk}: 10 tuş + 45 combo + enkoder",
                    len(p[osk]["keys"]) == 10 and len(p[osk]["combos"]) == 45
                    and {"cw", "ccw", "press", "long"} <= set(p[osk]["encoder"]))
        cm.set_action("windows", "K3", "url", "bluedevelopment.com", "Deneme")
        cm.save()
        cm2 = ConfigManager(yol)
        cm2.load()
        a = cm2.get_action("windows", "K3")
        kontrol("atama kaydet/geri oku", a["type"] == "url" and a["value"] == "bluedevelopment.com")
        m = cm2.get_mobile_settings()
        # Telefon sunucusu artık VARSAYILAN KAPALI (güvenlik denetimi
        # 2026-08-25): 0.0.0.0'da kimlik doğrulamasız dinlediği için
        # kullanıcı "Telefon" sekmesinden bilinçli olarak açmalıdır.
        # Ayrıca oturuma özel erişim jetonu alanı eklendi.
        kontrol("mobil ayar varsayılanı (enabled=False, port=8756)",
                m.get("enabled") is False and m.get("port") == 8756
                and "token" in m)

        # bozuk dosya çökertmemeli
        open(yol, "w").write("{bozuk json!!!")
        cm3 = ConfigManager(yol)
        try:
            cm3.load()
            kontrol("bozuk config'te çökmeme", True)
        except Exception as e:  # noqa: BLE001
            kontrol("bozuk config'te çökmeme", False, repr(e))


# ------------------------------------------------------------------- protokol
def test_protokol() -> None:
    print("\n[2] Protokol ayrıştırma (device.py)")
    from app.core import device

    beklenen = [
        ("EV KEY 3 UP", "key", "K3"),
        ("EV KEY 9 DOWN", "key", "K9"),
        ("EV KEY 10 DOWN", "key", "K10"),
        ("EV COMBO 2 5", "combo", "C_2_5"),
        ("EV COMBO 5 2", "combo", "C_2_5"),
        ("EV MODE COMBO_ON", "mode", None),
        ("EV OS MAC", "os", None),
        ("EV ENC CW", "enc", "cw"),
        ("EV ENC LONG", "enc", "long"),
        ("HB 12345", "hb", None),
        ("ID 3.0.0 MK1 EK1-A4C138 WIN", "id", None),
        ("ACK PING", "ack", None),
        ("ERR RANGE", "err", None),
    ]
    for satir, kind, slot in beklenen:
        ev = device.parse_line(satir)
        kontrol(f"{satir!r}",
                ev is not None and ev.kind == kind and ev.slot == slot,
                f"kind={getattr(ev,'kind',None)} slot={getattr(ev,'slot',None)}")
    kontrol("bilinmeyen satır sessizce yok sayılır",
            device.parse_line("ZIRVANA 42") is None and device.parse_line("") is None)
    kontrol("aralık dışı tuş geçersiz: 'EV KEY 11 UP'",
            device.parse_line("EV KEY 11 UP") is None)

    # hatalı sayılar çökertmemeli
    for kotu in ("EV KEY x UP", "EV COMBO 1", "EV KEY 99 UP", "CMD LED"):
        try:
            device.parse_line(kotu)
            kontrol(f"kötü girdi çökertmez: {kotu!r}", True)
        except Exception as e:  # noqa: BLE001
            kontrol(f"kötü girdi çökertmez: {kotu!r}", False, repr(e))


# --------------------------------------------------------------------- eylem
def test_eylem() -> None:
    print("\n[3] Eylem katmanı (actions.py) — yan etkisiz kontroller")
    from app.core.actions import ActionRunner
    from app.core.config import ConfigManager

    with tempfile.TemporaryDirectory() as d:
        cm = ConfigManager(os.path.join(d, "config.json"))
        cm.load()
        r = ActionRunner(cm)

        r.set_os_key("windows")
        kontrol("OS anahtarı windows", r.current_os_key() == "windows")
        r.set_os_key("mac")
        kontrol("OS anahtarı mac", r.current_os_key() == "mac")

        ok, mesaj = r.run_action({"type": "none", "value": "", "name": "boş"})
        kontrol("'none' eylemi sessiz başarı", ok)

        ok, mesaj = r.run_action({"type": "app", "value": "/olmayan/uygulama.app",
                                  "name": "yok"})
        kontrol("olmayan uygulama: çökmek yerine hata mesajı", not ok and bool(mesaj))

        ok, mesaj = r.run_action({"type": "olmayan_tip", "value": "", "name": "?"})
        kontrol("bilinmeyen tip: çökmek yerine hata mesajı", not ok)

        atanmamis = r.run("K7")  # varsayılanda boş tuş
        kontrol("atanmamış tuş çökertmez", isinstance(atanmamis, tuple))


# ------------------------------------------------------------------- taşıma
def test_tasima() -> None:
    print("\n[4] v2 → v3 taşıma (migrate_v2_config.py)")
    import subprocess

    # Dağıtım paketlerinde bu araç bulunmayabilir. Yoksa alt süreç "No such
    # file" ile döner ve otokontrol boşuna BAŞARISIZ verirdi; test_mobil()'deki
    # ImportError deseniyle aynı mantıkla ATLANDI diyoruz.
    arac = os.path.join(KOK, "tools", "migrate_v2_config.py")
    if not os.path.exists(arac):
        print("  - ATLANDI (migrate_v2_config.py bu pakette yok)")
        return

    with tempfile.TemporaryDirectory() as d:
        eski = os.path.join(d, "macro_config.json")
        yeni = os.path.join(d, "config.json")
        json.dump({
            "F13": {"type": "url", "value": "ornek.com", "name": "B1"},
            "F14": {"type": "shortcut", "value": "command+c", "name": "B2"},
        }, open(eski, "w"))
        sonuc = subprocess.run(
            [sys.executable, arac, "--input", eski, "--output", yeni],
            capture_output=True, text=True)
        kontrol("taşıma aracı hatasız bitti", sonuc.returncode == 0, sonuc.stderr[-200:])
        if sonuc.returncode == 0:
            v = json.load(open(yeni))
            p = v["profiles"][v["active_profile"]]
            kontrol("F13 → K1 (url)", p["mac"]["keys"]["K1"]["value"] == "ornek.com")
            kontrol("Windows profilinde command→ctrl",
                    p["windows"]["keys"]["K2"]["value"] == "ctrl+c")
            kontrol("mac profilinde command korunur",
                    p["mac"]["keys"]["K2"]["value"] == "command+c")


# -------------------------------------------------------------------- mobil
def test_mobil() -> None:
    print("\n[6] Mobil ayar sunucusu (mobile_server.py)")
    try:
        from app.core.mobile_server import Broadcaster, MobileServer
    except ImportError:
        print("  - ATLANDI (mobile_server henüz yok)")
        return

    import urllib.request

    sunucu = MobileServer(port=0)  # port=0: işletim sistemi boş port seçer
    try:
        ok, bilgi = sunucu.start()
        kontrol("sunucu boş portta başladı", ok, str(bilgi))
        if ok:
            url = str(sunucu.url or bilgi)
            kontrol("sunucu URL üretiyor", url.startswith("http"), url)
            try:
                with urllib.request.urlopen(url.rstrip("/") + "/state", timeout=3) as yanit:
                    veri = json.loads(yanit.read().decode("utf-8"))
                kontrol("/state JSON döndürür", isinstance(veri, dict), repr(veri)[:120])
            except Exception as e:  # noqa: BLE001
                kontrol("/state JSON döndürür", False, repr(e))
    finally:
        try:
            sunucu.stop()
            kontrol("sunucu temiz durdu", True)
        except Exception as e:  # noqa: BLE001
            kontrol("sunucu temiz durdu", False, repr(e))

    # Broadcaster publish/subscribe duman testi
    try:
        yayinci = Broadcaster()
        kuyruk = yayinci.subscribe()
        yayinci.publish({"olay": "test"})
        mesaj = kuyruk.get(timeout=1.0)
        kontrol("Broadcaster publish → subscribe (1 sn içinde)",
                isinstance(mesaj, dict) and mesaj.get("olay") == "test", repr(mesaj)[:120])
    except Exception as e:  # noqa: BLE001
        kontrol("Broadcaster publish → subscribe (1 sn içinde)", False, repr(e))


# ----------------------------------------------------------------- arayüz
def test_ui(gorunur_sn: float = 5.0) -> None:
    print(f"\n[5] Arayüz — pencere açılıyor, olay işliyor ({gorunur_sn:.0f} sn)")
    import threading
    import time

    from app.main import Application
    from app.core import device

    app = Application()
    hatalar: list[str] = []

    def senaryo() -> None:
        """Cihazdan gelmiş gibi olay bas; UI ana thread'de işlesin."""
        time.sleep(1.5)
        for satir in ("EV OS WIN", "EV KEY 3 DOWN", "EV KEY 3 UP",
                      "EV MODE COMBO_ON", "EV COMBO 2 5", "EV MODE COMBO_OFF",
                      "EV ENC CW", "HB 1000"):
            ev = device.parse_line(satir)
            if ev is not None:
                try:
                    app.window.push_device_event(ev)
                except Exception as e:  # noqa: BLE001
                    hatalar.append(f"{satir}: {e!r}")
            time.sleep(0.15)
        time.sleep(gorunur_sn - 1.5 - 8 * 0.15 if gorunur_sn > 3 else 0.5)
        try:
            app.window.after(0, app.window.quit)
        except Exception as e:  # noqa: BLE001
            hatalar.append(f"kapatma: {e!r}")

    threading.Thread(target=senaryo, daemon=True).start()
    app.run()
    kontrol("pencere açıldı, 8 cihaz olayı işlendi, temiz kapandı",
            not hatalar, "; ".join(hatalar))


# ------------------------------------------------------------------------ ana
def main() -> None:
    print("=" * 60)
    print("ExtraKeyboard MK1 — cihazsız otokontrol")
    print("=" * 60)
    test_config()
    test_protokol()
    test_eylem()
    test_tasima()
    if "--ui" in sys.argv:
        test_ui()
    test_mobil()

    basarili = sum(1 for ok, _ in SONUCLAR if ok)
    print("\n" + "=" * 60)
    print(f"SONUÇ: {basarili}/{len(SONUCLAR)} kontrol geçti")
    kotu = [ad for ok, ad in SONUCLAR if not ok]
    if kotu:
        print("BAŞARISIZ:")
        for ad in kotu:
            print("  ✗", ad)
    print("=" * 60)
    sys.exit(0 if not kotu else 1)


if __name__ == "__main__":
    main()
