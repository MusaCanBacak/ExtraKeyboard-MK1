// =====================================================================
//  ExtraKeyboard MK1 — ÜST PLAKA (switch plate)
//  Dosya  : mechanical/plate.scad
//  Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2 / 2.1
//
//  İÇERİK
//    · 11 adet MX anahtar deliği (14.00 × 14.00) — K1..K11
//    · 1 adet enkoder deliği ⌀7.20 + 2 adet ⌀1.50 dönme engelleyici pim deliği
//    · 3 adet LED penceresi ⌀3.00 (üst bezelde, 8.00 mm aralıklı)
//    · 4 adet M3 geçme deliği ⌀3.20 (köşelerde, kenardan 4.50 içeride)
//
//  Plaka kalınlığı 1.50 mm'dir ve bu ölçü ZORUNLUDUR: MX anahtarın yan
//  klipsleri ancak 1.4–1.6 mm aralığında plakanın altına oturup kilitlenir.
//
//  2D / 3D
//    plaka_2d()  → lazer kesim ve DXF için 2 boyutlu kontur (gen_dxf.py ile
//                  birebir aynı geometriyi üretir)
//    plaka()     → plaka_2d()'nin plate_t kadar ekstrüzyonu (3D parça)
//
//  Tek başına açıldığında 3D plakayı render eder.
// =====================================================================

EK_SESSIZ = true;              // parameters.scad önizlemesini bastır
include <parameters.scad>

// Üretim telafisi uygulanmış efektif ölçüler
// (uretim_telafi = 0.00 iken nominal ölçülerle birebir aynı)
mx_yan     = mx_hole       + uretim_telafi;   // MX kare kenarı
enc_cap    = enc_hole_d    + uretim_telafi;   // Enkoder burç deliği
pim_cap    = enc_pin_d     + uretim_telafi;   // Konumlandırma pimi deliği
led_cap    = led_hole_d    + uretim_telafi;   // LED penceresi
vida_cap   = plate_screw_d + uretim_telafi;   // M3 geçme deliği

// ---------------------------------------------------------------------
//  2D: MX anahtar deliği (kare)
// ---------------------------------------------------------------------
module mx_delik_2d(cx, cy) {
    translate([cx - mx_yan / 2, cy - mx_yan / 2])
        square([mx_yan, mx_yan]);
}

// ---------------------------------------------------------------------
//  2D: Enkoder deliği + iki adet dönme engelleyici pim deliği
//  EC11'in gövdesindeki 2 konumlandırma pimi merkezden enc_pin_r (5.00 mm)
//  uzaklıkta, karşılıklı olarak yerleşir.
// ---------------------------------------------------------------------
module enkoder_delik_2d(cx, cy) {
    translate([cx, cy]) circle(d = enc_cap);
    for (s = [-1, 1])
        translate([cx + s * enc_pin_r * cos(enc_pin_ang),
                   cy + s * enc_pin_r * sin(enc_pin_ang)])
            circle(d = pim_cap);
}

// ---------------------------------------------------------------------
//  2D: LED pencereleri — üst bezelde, merkezden simetrik, 8.00 mm aralık
// ---------------------------------------------------------------------
module led_pencereleri_2d() {
    for (i = [0 : led_count - 1])
        translate([led_cx(i), led_y])
            circle(d = led_cap);
}

// ---------------------------------------------------------------------
//  2D: Köşe vida delikleri (M3 geçme, ⌀3.20)
// ---------------------------------------------------------------------
module vida_delikleri_2d() {
    for (p = screw_positions())
        translate([p[0], p[1]])
            circle(d = vida_cap);
}

// ---------------------------------------------------------------------
//  2D: Plakanın tam konturu — DXF ile birebir aynı
//  Dış kontur keskin köşeli dikdörtgendir (gen_dxf.py 4 adet LINE üretir).
// ---------------------------------------------------------------------
module plaka_2d() {
    difference() {
        square([plate_w, plate_d]);

        // 11 MX deliği (K1..K11) — döngü ile, elle kopyalama yok
        for (k = key_map)
            mx_delik_2d(key_cx(k[1]), key_cy(k[2]));

        // Enkoder (sütun 4 / satır 1) + pim delikleri
        enkoder_delik_2d(enc_cx, enc_cy);

        // LED pencereleri
        led_pencereleri_2d();

        // Vida delikleri
        vida_delikleri_2d();
    }
}

// ---------------------------------------------------------------------
//  3D: Plaka
// ---------------------------------------------------------------------
module plaka() {
    render()
    color(col_plate)
        linear_extrude(height = plate_t)
            plaka_2d();
}

// ---------------------------------------------------------------------
//  Doğrulama çıktısı — konsola delik konumlarını yazar
// ---------------------------------------------------------------------
module plaka_rapor() {
    echo(str("PLAKA: ", plate_w, " x ", plate_d, " x ", plate_t, " mm"));
    echo(str("  Uretim telafisi = ", uretim_telafi,
             "  -> MX kenari ", mx_yan, "  ENC ", enc_cap,
             "  LED ", led_cap, "  VIDA ", vida_cap));
    for (k = key_map)
        echo(str("  ", k[0], "  X=", key_cx(k[1]), "  Y=", key_cy(k[2])));
    echo(str("  ENC  X=", enc_cx, "  Y=", enc_cy, "  cap=", enc_hole_d));
    for (i = [0 : led_count - 1])
        echo(str("  LED", i + 1, " X=", led_cx(i), "  Y=", led_y));
    for (p = screw_positions())
        echo(str("  VIDA X=", p[0], "  Y=", p[1]));
}

// ---------------------------------------------------------------------
//  Tek başına açıldığında plakayı render et
// ---------------------------------------------------------------------
if (is_undef(EK_MONTAJ)) {
    plaka();
    plaka_rapor();
}
