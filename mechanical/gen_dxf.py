#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Üst plaka DXF üretici
=========================================

Dosya  : mechanical/gen_dxf.py
Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2 ve 2.1 (TEK DOĞRULUK KAYNAĞI)

NE YAPAR
--------
Lazer kesim / CNC için üst plakanın (switch plate) konturunu ve bütün
deliklerini **AutoCAD R12 (AC1009)** metin DXF formatında yazar.
HİÇBİR HARİCİ KÜTÜPHANE KULLANMAZ — yalnızca Python standart kütüphanesi.

ÖLÇÜLER NEREDEN GELİR
---------------------
Ölçüler `parameters.scad` dosyasından okunur (basit `ad = sayı;` satırları).
Dosya bulunamazsa veya bir değer eksikse aşağıdaki VARSAYILAN sözlüğü
kullanılır. Böylece OpenSCAD kaynağı ile DXF çıktısı asla ayrışmaz.

ÜRETİLEN GEOMETRİ
-----------------
    KONTUR   : 88.20 × 69.15 dikdörtgen              →  4 LINE
    MX_DELIK : 11 adet 14.00 × 14.00 kare            → 44 LINE
    ENKODER  : 1 adet ⌀7.20                          →  1 CIRCLE
    ENK_PIM  : 2 adet ⌀1.50 (merkezden ±5.00)        →  2 CIRCLE
    LED      : 3 adet ⌀3.00 (8.00 aralık)            →  3 CIRCLE
    VIDA     : 4 adet ⌀3.20 (kenardan 4.50 içeride)  →  4 CIRCLE
    ------------------------------------------------------------
    TOPLAM   : 48 LINE + 10 CIRCLE

KOORDİNAT SİSTEMİ
-----------------
Orijin (0, 0) = plakanın SOL-ALT köşesi. +X sağa, +Y yukarı (arkaya).

KULLANIM
--------
    python3 gen_dxf.py                 # mechanical/plate.dxf üretir
    python3 gen_dxf.py --out /yol/x.dxf
    python3 gen_dxf.py --kerf 0.10     # lazer kerf telafisi (delikler büyür)


UYARI: Bu betik ESKI geometriye gore uretim yapar (88.20 x 69.15, bolmesiz).
Guncel tasarim 88.20 x 99.15 mm + arkada 30 mm elektronik bolmesidir.
Guncel delik koordinatlari: docs/BASIT-YAPIM.md bolum 3.1
Ayrinti: mechanical/OKU-ONCE.md
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys

# ---------------------------------------------------------------------------
# 1) VARSAYILAN ÖLÇÜLER  (parameters.scad okunamazsa devreye girer)
#    Değerler docs/00-CEKIRDEK-SPEC.md Bölüm 2.1 ile birebir aynıdır.
# ---------------------------------------------------------------------------
VARSAYILAN = {
    "key_pitch":     19.05,   # Tuş adımı
    "bezel":          6.00,   # Kenar bezeli
    "plate_w":       88.20,   # Plaka genişliği
    "plate_d":       69.15,   # Plaka derinliği
    "plate_t":        1.50,   # Plaka kalınlığı (yalnızca başlık bilgisi)
    "mx_hole":       14.00,   # MX anahtar deliği (kare)
    "enc_hole_d":     7.20,   # Enkoder deliği çapı
    "enc_pin_d":      1.50,   # Enkoder konumlandırma pimi çapı
    "enc_pin_r":      5.00,   # Pim deliklerinin merkeze uzaklığı
    "enc_pin_ang":    0.00,   # Pim ekseninin açısı (derece)
    "led_hole_d":     3.00,   # LED penceresi çapı
    "led_count":      3,      # LED adedi
    "led_spacing":    8.00,   # LED merkezleri arası
    "led_y":         63.40,   # LED merkezlerinin Y koordinatı
    "screw_inset":    4.50,   # Vida merkezinin kenardan içeri mesafesi
    "plate_screw_d":  3.20,   # Plakadaki M3 geçme deliği
    "uretim_telafi":  0.00,   # Üretim telafisi (FDM için 0.15) — parameters.scad
}

# Tuş haritası: (isim, sütun, satır) — SATIR 1 arkadadır (en büyük Y).
# SÜTUN 4 / SATIR 1 enkoderdir, MX deliği değildir.
TUS_HARITASI = [
    ("K1",  1, 1), ("K2",  2, 1), ("K3", 3, 1),
    ("K4",  1, 2), ("K5",  2, 2), ("K6", 3, 2),
    ("K7",  1, 3), ("K8",  2, 3), ("K9", 3, 3),
    ("K10", 4, 2),
    ("K11", 4, 3),
]
ENKODER_SUTUN = 4
ENKODER_SATIR = 1

# Beklenen entity sayıları — üretim sonrası doğrulanır.
BEKLENEN_LINE = 4 + 4 * len(TUS_HARITASI)          # 4 kontur + 44 MX = 48
BEKLENEN_CIRCLE = 1 + 2 + 3 + 4                    # enk + pim + LED + vida = 10

SCAD_ATAMA = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([-+]?(?:\d+\.\d*|\.\d+|\d+))\s*;"
)


# ---------------------------------------------------------------------------
# 2) parameters.scad OKUYUCU
# ---------------------------------------------------------------------------
def scad_parametrelerini_oku(yol: str) -> dict:
    """`ad = sayı;` biçimindeki basit atamaları sözlük olarak döndürür.

    Yorum satırları (`//`) temizlenir. İfade içeren atamalar (örn.
    `case_h = base_t + inner_h;`) bilinçli olarak atlanır — bu betiğin
    ihtiyaç duyduğu tüm ölçüler düz sayıdır.
    """
    bulunan: dict = {}
    if not os.path.isfile(yol):
        return bulunan
    with open(yol, "r", encoding="utf-8") as f:
        for satir in f:
            temiz = satir.split("//", 1)[0]
            m = SCAD_ATAMA.match(temiz)
            if m:
                bulunan[m.group(1)] = float(m.group(2))
    return bulunan


def olculeri_topla(scad_yolu: str) -> tuple[dict, list]:
    """Varsayılanları scad dosyasındaki değerlerle günceller."""
    p = dict(VARSAYILAN)
    scad = scad_parametrelerini_oku(scad_yolu)
    farklar = []
    for anahtar in VARSAYILAN:
        if anahtar in scad:
            eski = float(VARSAYILAN[anahtar])
            yeni = scad[anahtar]
            p[anahtar] = yeni
            if abs(eski - yeni) > 1e-9:
                farklar.append((anahtar, eski, yeni))
    p["led_count"] = int(round(p["led_count"]))
    return p, farklar


# ---------------------------------------------------------------------------
# 3) GEOMETRİ HESABI
# ---------------------------------------------------------------------------
def tus_merkez_x(p: dict, sutun: int) -> float:
    return p["bezel"] + (sutun - 0.5) * p["key_pitch"]


def tus_merkez_y(p: dict, satir: int) -> float:
    return p["plate_d"] - p["bezel"] - (satir - 0.5) * p["key_pitch"]


def led_merkez_x(p: dict, i: int) -> float:
    return p["plate_w"] / 2.0 + (i - (p["led_count"] - 1) / 2.0) * p["led_spacing"]


def vida_merkezleri(p: dict) -> list:
    a = p["screw_inset"]
    return [
        (a, a),
        (p["plate_w"] - a, a),
        (a, p["plate_d"] - a),
        (p["plate_w"] - a, p["plate_d"] - a),
    ]


def geometriyi_uret(p: dict, kerf: float = 0.0):
    """(cizgiler, cemberler) döndürür.

    cizgiler : [(katman, x1, y1, x2, y2), ...]
    cemberler: [(katman, cx, cy, yaricap, aciklama), ...]

    kerf > 0 ise lazer ışını kalınlığı telafi edilir: delikler kerf kadar
    büyütülür, dış kontur her kenardan kerf/2 kadar küçültülür.

    Ayrıca parameters.scad'deki `uretim_telafi` değeri (FDM için 0.15)
    deliklerin çapına/kenarına eklenir. Böylece plate.scad ile bu betiğin
    ürettiği geometri her koşulda birebir aynı kalır.
    """
    buyume = kerf + p.get("uretim_telafi", 0.0)   # delik çapı/kenar artışı
    yari = buyume / 2.0                            # delikler için yarıçap payı
    kontur_yari = kerf / 2.0                       # dış kontur için kerf payı
    cizgiler = []
    cemberler = []

    # --- Dış kontur: 4 LINE ------------------------------------------------
    x0, y0 = kontur_yari, kontur_yari
    x1, y1 = p["plate_w"] - kontur_yari, p["plate_d"] - kontur_yari
    cizgiler += [
        ("KONTUR", x0, y0, x1, y0),
        ("KONTUR", x1, y0, x1, y1),
        ("KONTUR", x1, y1, x0, y1),
        ("KONTUR", x0, y1, x0, y0),
    ]

    # --- 11 MX deliği: her biri 4 LINE ------------------------------------
    yan = p["mx_hole"] + buyume        # telafi uygulanmış kenar uzunluğu
    for _isim, sutun, satir in TUS_HARITASI:
        cx = tus_merkez_x(p, sutun)
        cy = tus_merkez_y(p, satir)
        ax, ay = cx - yan / 2.0, cy - yan / 2.0
        bx, by = cx + yan / 2.0, cy + yan / 2.0
        cizgiler += [
            ("MX_DELIK", ax, ay, bx, ay),
            ("MX_DELIK", bx, ay, bx, by),
            ("MX_DELIK", bx, by, ax, by),
            ("MX_DELIK", ax, by, ax, ay),
        ]

    # --- Enkoder deliği + 2 konumlandırma pimi ----------------------------
    ecx = tus_merkez_x(p, ENKODER_SUTUN)
    ecy = tus_merkez_y(p, ENKODER_SATIR)
    cemberler.append(("ENKODER", ecx, ecy, p["enc_hole_d"] / 2.0 + yari, "ENC burc"))

    aci = math.radians(p["enc_pin_ang"])
    for isaret in (-1, +1):
        px = ecx + isaret * p["enc_pin_r"] * math.cos(aci)
        py = ecy + isaret * p["enc_pin_r"] * math.sin(aci)
        cemberler.append(
            ("ENK_PIM", px, py, p["enc_pin_d"] / 2.0 + yari, "ENC donme engelleyici pim")
        )

    # --- LED pencereleri ---------------------------------------------------
    for i in range(p["led_count"]):
        cemberler.append(
            ("LED", led_merkez_x(p, i), p["led_y"],
             p["led_hole_d"] / 2.0 + yari, "LED%d" % (i + 1))
        )

    # --- Vida delikleri ----------------------------------------------------
    for vx, vy in vida_merkezleri(p):
        cemberler.append(
            ("VIDA", vx, vy, p["plate_screw_d"] / 2.0 + yari, "M3 gecme")
        )

    return cizgiler, cemberler


# ---------------------------------------------------------------------------
# 4) DXF R12 YAZICI  (ham metin, harici kütüphane yok)
# ---------------------------------------------------------------------------
KATMAN_RENKLERI = {
    "KONTUR":   7,   # beyaz/siyah
    "MX_DELIK": 1,   # kırmızı
    "ENKODER":  2,   # sarı
    "ENK_PIM":  6,   # macenta
    "LED":      3,   # yeşil
    "VIDA":     5,   # mavi
}
KATMAN_SIRASI = ["KONTUR", "MX_DELIK", "ENKODER", "ENK_PIM", "LED", "VIDA"]


def _g(kod: int, deger) -> str:
    """Tek bir DXF grup kodu + değer çifti (iki satır)."""
    if isinstance(deger, float):
        return "%d\r\n%.6f\r\n" % (kod, deger)
    return "%d\r\n%s\r\n" % (kod, deger)


def dxf_uret(cizgiler, cemberler, p: dict) -> str:
    out = []

    # ---- HEADER -----------------------------------------------------------
    out.append(_g(0, "SECTION"))
    out.append(_g(2, "HEADER"))
    out.append(_g(9, "$ACADVER"));  out.append(_g(1, "AC1009"))
    out.append(_g(9, "$INSBASE"))
    out.append(_g(10, 0.0)); out.append(_g(20, 0.0)); out.append(_g(30, 0.0))
    out.append(_g(9, "$EXTMIN"))
    out.append(_g(10, 0.0)); out.append(_g(20, 0.0)); out.append(_g(30, 0.0))
    out.append(_g(9, "$EXTMAX"))
    out.append(_g(10, float(p["plate_w"])))
    out.append(_g(20, float(p["plate_d"])))
    out.append(_g(30, 0.0))
    out.append(_g(9, "$INSUNITS")); out.append(_g(70, 4))   # 4 = milimetre
    out.append(_g(9, "$MEASUREMENT")); out.append(_g(70, 1))  # 1 = metrik
    out.append(_g(0, "ENDSEC"))

    # ---- TABLES / LAYER ---------------------------------------------------
    out.append(_g(0, "SECTION"))
    out.append(_g(2, "TABLES"))
    out.append(_g(0, "TABLE"))
    out.append(_g(2, "LAYER"))
    out.append(_g(70, len(KATMAN_SIRASI) + 1))
    # 0 katmanı her DXF'te bulunmalıdır
    out.append(_g(0, "LAYER")); out.append(_g(2, "0"))
    out.append(_g(70, 0)); out.append(_g(62, 7)); out.append(_g(6, "CONTINUOUS"))
    for ad in KATMAN_SIRASI:
        out.append(_g(0, "LAYER")); out.append(_g(2, ad))
        out.append(_g(70, 0))
        out.append(_g(62, KATMAN_RENKLERI[ad]))
        out.append(_g(6, "CONTINUOUS"))
    out.append(_g(0, "ENDTAB"))
    out.append(_g(0, "ENDSEC"))

    # ---- BLOCKS (boş ama R12 okuyucuları için bulunması iyi) --------------
    out.append(_g(0, "SECTION"))
    out.append(_g(2, "BLOCKS"))
    out.append(_g(0, "ENDSEC"))

    # ---- ENTITIES ---------------------------------------------------------
    out.append(_g(0, "SECTION"))
    out.append(_g(2, "ENTITIES"))

    for katman, x1, y1, x2, y2 in cizgiler:
        out.append(_g(0, "LINE"))
        out.append(_g(8, katman))
        out.append(_g(62, KATMAN_RENKLERI[katman]))
        out.append(_g(10, float(x1))); out.append(_g(20, float(y1))); out.append(_g(30, 0.0))
        out.append(_g(11, float(x2))); out.append(_g(21, float(y2))); out.append(_g(31, 0.0))

    for katman, cx, cy, r, _aciklama in cemberler:
        out.append(_g(0, "CIRCLE"))
        out.append(_g(8, katman))
        out.append(_g(62, KATMAN_RENKLERI[katman]))
        out.append(_g(10, float(cx))); out.append(_g(20, float(cy))); out.append(_g(30, 0.0))
        out.append(_g(40, float(r)))

    out.append(_g(0, "ENDSEC"))
    out.append(_g(0, "EOF"))
    return "".join(out)


# ---------------------------------------------------------------------------
# 5) DOĞRULAMA — üretilen dosyayı geri okuyup entity sayar
# ---------------------------------------------------------------------------
def dxf_dogrula(yol: str) -> dict:
    """Yazılan DXF'i geri okur, ENTITIES bölümündeki entity'leri sayar."""
    with open(yol, "r", encoding="ascii", newline="") as f:
        ham = f.read()
    satirlar = [s.strip() for s in ham.replace("\r\n", "\n").split("\n")]

    sayim = {"LINE": 0, "CIRCLE": 0}
    katman_sayim: dict = {}
    entities_icinde = False
    i = 0
    son_tip = None
    while i < len(satirlar) - 1:
        kod, deger = satirlar[i], satirlar[i + 1]
        if kod == "0":
            if deger == "SECTION" and i + 3 < len(satirlar):
                entities_icinde = (satirlar[i + 3] == "ENTITIES")
            elif deger == "ENDSEC":
                entities_icinde = False
                son_tip = None
            elif entities_icinde and deger in sayim:
                sayim[deger] += 1
                son_tip = deger
            else:
                son_tip = None
        elif kod == "8" and entities_icinde and son_tip:
            katman_sayim[deger] = katman_sayim.get(deger, 0) + 1
        i += 2

    return {"sayim": sayim, "katman": katman_sayim, "bayt": len(ham)}


# ---------------------------------------------------------------------------
# 6) ANA AKIŞ
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    burasi = os.path.dirname(os.path.abspath(__file__))

    ap = argparse.ArgumentParser(
        description="ExtraKeyboard MK1 üst plaka DXF üretici (R12, harici bağımlılık yok)"
    )
    ap.add_argument("--out", default=None,
                    help="Çıktı DXF yolu. Varsayılan: kerf yokken "
                         "mechanical/plate.dxf, kerf varken "
                         "mechanical/plate_kerf<NNN>.dxf")
    ap.add_argument("--scad", default=os.path.join(burasi, "parameters.scad"),
                    help="Ölçülerin okunacağı parameters.scad yolu")
    ap.add_argument("--kerf", type=float, default=0.0,
                    help="Lazer kerf telafisi (mm). 0 = telafi yok.")
    ap.add_argument("--sessiz", action="store_true", help="Ekrana rapor yazma")
    args = ap.parse_args(argv)

    # Kerf telafili çıktı, depodaki NOMİNAL plate.dxf dosyasının üzerine
    # yazılmaz: dosya adı ölçüyü yansıtmalıdır. Kullanıcı --out verirse
    # her zaman onun dediği olur.
    if args.out is None:
        if abs(args.kerf) > 1e-9:
            args.out = os.path.join(
                burasi, "plate_kerf%03d.dxf" % int(round(abs(args.kerf) * 1000)))
        else:
            args.out = os.path.join(burasi, "plate.dxf")

    p, farklar = olculeri_topla(args.scad)
    cizgiler, cemberler = geometriyi_uret(p, kerf=args.kerf)
    metin = dxf_uret(cizgiler, cemberler, p)

    with open(args.out, "w", encoding="ascii", newline="") as f:
        f.write(metin)

    dogrulama = dxf_dogrula(args.out)
    line_adet = dogrulama["sayim"]["LINE"]
    circle_adet = dogrulama["sayim"]["CIRCLE"]
    tamam = (line_adet == BEKLENEN_LINE and circle_adet == BEKLENEN_CIRCLE)

    if not args.sessiz:
        print("=" * 66)
        print("  ExtraKeyboard MK1 — ÜST PLAKA DXF ÜRETİCİ")
        print("=" * 66)
        print("Ölçü kaynağı : %s" % args.scad)
        if farklar:
            print("parameters.scad varsayılanlardan farklı değerler içeriyor:")
            for ad, eski, yeni in farklar:
                print("   %-16s %8.3f  ->  %8.3f" % (ad, eski, yeni))
        else:
            print("Ölçüler varsayılanlarla birebir aynı (SPEC 2.1).")
        print("-" * 66)
        print("Plaka        : %.2f x %.2f x %.2f mm"
              % (p["plate_w"], p["plate_d"], p["plate_t"]))
        print("Kerf telafisi: %.3f mm   Üretim telafisi: %.3f mm"
              % (args.kerf, p["uretim_telafi"]))
        print("Efektif MX kenarı: %.3f mm   Enkoder ⌀: %.3f mm"
              % (p["mx_hole"] + args.kerf + p["uretim_telafi"],
                 p["enc_hole_d"] + args.kerf + p["uretim_telafi"]))
        print("-" * 66)
        print("TUŞ MERKEZLERİ (plaka sol-alt köşesi orijin):")
        for isim, sutun, satir in TUS_HARITASI:
            print("   %-4s sütun %d satır %d   X=%8.3f  Y=%8.3f"
                  % (isim, sutun, satir,
                     tus_merkez_x(p, sutun), tus_merkez_y(p, satir)))
        print("   %-4s sütun %d satır %d   X=%8.3f  Y=%8.3f"
              % ("ENC", ENKODER_SUTUN, ENKODER_SATIR,
                 tus_merkez_x(p, ENKODER_SUTUN), tus_merkez_y(p, ENKODER_SATIR)))
        for i in range(p["led_count"]):
            print("   LED%d              X=%8.3f  Y=%8.3f"
                  % (i + 1, led_merkez_x(p, i), p["led_y"]))
        for n, (vx, vy) in enumerate(vida_merkezleri(p), start=1):
            print("   VIDA%d             X=%8.3f  Y=%8.3f" % (n, vx, vy))
        print("-" * 66)
        print("KATMAN BAZINDA ENTITY SAYISI:")
        for ad in KATMAN_SIRASI:
            print("   %-9s : %3d" % (ad, dogrulama["katman"].get(ad, 0)))
        print("-" * 66)
        print("LINE   : %3d  (beklenen %d: 4 kontur + %d MX × 4)"
              % (line_adet, BEKLENEN_LINE, len(TUS_HARITASI)))
        print("CIRCLE : %3d  (beklenen %d: 1 enkoder + 2 pim + %d LED + 4 vida)"
              % (circle_adet, BEKLENEN_CIRCLE, p["led_count"]))
        print("Dosya  : %s  (%d bayt)" % (args.out, dogrulama["bayt"]))
        print("SONUÇ  : %s" % ("DOĞRULANDI" if tamam else "HATALI ENTITY SAYISI"))
        print("=" * 66)

    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main())
