// =====================================================================
//  ExtraKeyboard MK1 — MONTAJ GÖRÜNÜMÜ
//  Dosya  : mechanical/assembly.scad
//  Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2 / 2.1 / 3
//
//  Gövde + plaka + 11 keycap + enkoder düğmesi + 4 vida + DevKitC-1
//  temsilini bir arada gösterir.
//
//  GÖRÜNÜM SEÇENEKLERİ (dosyanın başındaki değişkenleri değiştir):
//    patlatilmis = false → normal montaj
//    patlatilmis = true  → patlatılmış (exploded) görünüm
//    kesit       = true  → gövdeyi ortadan kesip iç yerleşimi gösterir
//    kapaklar    = false → keycap'ler gizlenir, plaka delikleri görünür
//
//  DİKKAT: Alt dosyalar "use <>" ile çağrılır; böylece onların kendi
//  tek-başına-render blokları çalışmaz, sadece modülleri içeri alınır.
// =====================================================================

EK_SESSIZ = true;              // parameters.scad önizlemesini bastır
EK_MONTAJ = true;              // alt dosyaların tekil render'ını bastır

include <parameters.scad>
use <plate.scad>
use <case.scad>
use <knob.scad>

// ---------------------------------------------------------------------
//  GÖRÜNÜM AYARLARI
// ---------------------------------------------------------------------
patlatilmis = false;   // patlatılmış görünüm
patlama     = 22.00;   // patlatma adımı (mm)
kesit       = false;   // kesit görünümü
kapaklar    = true;    // keycap'leri göster
devkit      = true;    // DevKitC-1 temsilini göster
vidalar     = true;    // vidaları göster

// Patlatma yardımcısı: kat numarasına göre Z ötelemesi
function patlat(kat) = patlatilmis ? kat * patlama : 0;

// Plaka üst yüzeyinin normal (patlatılmamış) kotu
plaka_ust = case_h + plate_t;      // 22.00

// ---------------------------------------------------------------------
//  Temsilî keycap (DSA benzeri kesik piramit) — sadece görsel amaçlı
// ---------------------------------------------------------------------
module keycap() {
    hull() {
        translate([-cap_bottom / 2, -cap_bottom / 2, 0])
            cube([cap_bottom, cap_bottom, eps]);
        translate([-cap_top / 2, -cap_top / 2, cap_h - eps])
            cube([cap_top, cap_top, eps]);
    }
}

// ---------------------------------------------------------------------
//  Temsilî M3 × 12 silindir başlı vida
//  Baş plakanın üstünde durur, gövde aşağı doğru iner.
// ---------------------------------------------------------------------
module vida_m3x12() {
    color(col_screw) {
        // Baş
        cylinder(d = screw_head_d, h = screw_head_h);
        // Gövde (aşağı doğru)
        translate([0, 0, -screw_len])
            cylinder(d = 3.00, h = screw_len + eps);
    }
}

// ---------------------------------------------------------------------
//  Temsilî ESP32-S3-DevKitC-1 (63.00 × 25.50 × 1.60) + USB-C soketi
// ---------------------------------------------------------------------
module devkit_temsili() {
    color(col_pcb) {
        // Kart
        translate([pcb_x1, pcb_y1, base_t + pcb_standoff_h])
            cube([pcb_w, pcb_d, pcb_t]);
        // WROOM modülü (kabaca)
        translate([pcb_x1 + 2, pcb_cy - 9, base_t + pcb_standoff_h + pcb_t])
            cube([18, 18, 3.2]);
    }
    // USB-C soketi (sağ kenar, açıklığın hizası)
    color("#9aa4b2")
        translate([pcb_x2 - 7.0, usb_center_y - 4.45,
                   base_t + pcb_standoff_h + pcb_t])
            cube([8.0, 8.9, 3.26]);
}

// ---------------------------------------------------------------------
//  MONTAJ
// ---------------------------------------------------------------------
module montaj() {
    // 1) Gövde
    translate([0, 0, 0])
        govde();

    // 2) DevKitC-1 (gövdenin içinde)
    if (devkit)
        translate([0, 0, -patlat(1.0)])
            devkit_temsili();

    // 3) Plaka
    translate([0, 0, case_h + patlat(1.0)])
        plaka();

    // 4) Keycap'ler — 11 adet, döngü ile
    if (kapaklar)
        color(col_cap)
            for (k = key_map)
                translate([key_cx(k[1]), key_cy(k[2]),
                           plaka_ust + cap_lift + patlat(2.0)])
                    keycap();

    // 5) Enkoder düğmesi
    translate([enc_cx, enc_cy, plaka_ust + knob_gap + patlat(2.6)])
        dugme();

    // 6) M3 × 12 vidalar
    if (vidalar)
        for (p = screw_positions())
            translate([p[0], p[1], plaka_ust + patlat(3.4)])
                vida_m3x12();
}

// ---------------------------------------------------------------------
//  Kesit görünümü: Y = plate_d / 2 düzleminin arkasını keser
// ---------------------------------------------------------------------
module montaj_kesit() {
    difference() {
        montaj();
        translate([-20, plate_d / 2, -60])
            cube([plate_w + 40, plate_d, 200]);
    }
}

// ---------------------------------------------------------------------
//  Doğrulama çıktısı
// ---------------------------------------------------------------------
module montaj_rapor() {
    echo("=== ExtraKeyboard MK1 — MONTAJ ===");
    echo(str("Dis olcu (G x D x Y): ", plate_w, " x ", plate_d, " x ", body_h, " mm"));
    echo(str("Kasa ", case_h, " + plaka ", plate_t, " = ", case_h + plate_t));
    echo(str("Tus sayisi: ", len(key_map), "  (K1..K11)"));
    echo(str("Enkoder merkezi: X=", enc_cx, " Y=", enc_cy));
    echo(str("Gorunum: patlatilmis=", patlatilmis, "  kesit=", kesit));
}

// ---------------------------------------------------------------------
//  RENDER
// ---------------------------------------------------------------------
if (kesit) montaj_kesit(); else montaj();

// İsteğe bağlı eğim kaması, montajın önüne serilir
if (tilt_enable)
    translate([0, -plate_d - 12, 0])
        egim_kamasi();

montaj_rapor();
