// =====================================================================
//  ExtraKeyboard MK1 — ENKODER DÜĞMESİ (knob)
//  Dosya  : mechanical/knob.scad
//  Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2 (ENC) ve 2.1
//
//  EC11 döner enkoderin 6 mm D-shaft miline geçen düğme.
//    · Dış çap 17.00 mm  → 19.05 mm tuş adımına sığar, K10'a çarpmaz
//    · Yükseklik 15.00 mm
//    · Mil yuvası: ⌀6.15 silindir ∩ 4.65 mm D düzlüğü, 12.00 mm derin
//    · Altta ⌀13.00 × 3.20 M7 somun havşası (somun + rondela = 2.90 mm)
//    · Çevrede 24 adet ⌀1.60 tutuş oluğu (tırtıl)
//    · Üstte 1.20 mm genişliğinde konum gösterge oluğu
//
//  Mil ölçüsü nominal 6.00 mm / düzlük 4.50 mm'dir; yuvaya 0.15 mm
//  baskı toleransı eklenmiştir (FDM'de delikler daralır).
//
//  Tek başına açıldığında düğmeyi render eder.
// =====================================================================

EK_SESSIZ = true;              // parameters.scad önizlemesini bastır
include <parameters.scad>

// ---------------------------------------------------------------------
//  D-shaft mil yuvası (ÇIKARILAN hacim)
//  Tam silindirin bir tarafı düzlemle kesilir; düzlem merkeze
//  (knob_shaft_flat − knob_shaft_d/2) kadar uzaklıktadır.
//    6.15/2 = 3.075 → düzlem ofseti = 4.65 − 3.075 = 1.575 mm
// ---------------------------------------------------------------------
module d_mil_yuvasi(derinlik = knob_shaft_dep) {
    flat_off = knob_shaft_flat - knob_shaft_d / 2;   // 1.575
    intersection() {
        cylinder(d = knob_shaft_d, h = derinlik);
        translate([-knob_shaft_d, -knob_shaft_d, -eps])
            cube([2 * knob_shaft_d,
                  knob_shaft_d + flat_off,
                  derinlik + 2 * eps]);
    }
}

// ---------------------------------------------------------------------
//  Düğme dış gövdesi: alt pah + silindir + üst pah
// ---------------------------------------------------------------------
module dugme_govdesi() {
    // Alt pah (masaya/plakaya bakan kenar yumuşatılır)
    cylinder(d1 = knob_d - 2 * knob_bot_ch, d2 = knob_d, h = knob_bot_ch);

    // Ana silindir
    translate([0, 0, knob_bot_ch])
        cylinder(d = knob_d, h = knob_h - knob_bot_ch - knob_top_ch);

    // Üst pah
    translate([0, 0, knob_h - knob_top_ch])
        cylinder(d1 = knob_d, d2 = knob_d - knob_top_ch_d, h = knob_top_ch);
}

// ---------------------------------------------------------------------
//  Çevre tutuş olukları (tırtıl) — ÇIKARILAN hacim
// ---------------------------------------------------------------------
module tutus_oluklari() {
    for (i = [0 : knob_flutes - 1])
        rotate([0, 0, i * 360 / knob_flutes])
            translate([knob_d / 2, 0, -eps])
                cylinder(d = knob_flute_d, h = knob_h + 2 * eps);
}

// ---------------------------------------------------------------------
//  Düğme altındaki M7 somun havşası — ÇIKARILAN hacim
//  EC11'in somunu + rondelası plaka üstünde 2.90 mm yer kaplar; bu cep
//  olmadan düğme somunun üstüne oturur ve mile tam geçmez.
//  Havşadan sonra mile gerçekten geçen D-yuvası boyu knob_shaft_grip'tir.
// ---------------------------------------------------------------------
module somun_havsasi() {
    translate([0, 0, -eps])
        cylinder(d = knob_nut_d, h = knob_nut_dep + eps);
}

// ---------------------------------------------------------------------
//  Üst yüzeydeki konum gösterge oluğu — ÇIKARILAN hacim
//  D düzlüğünün baktığı yöne (+Y) doğru uzanır: montajda düzlük ile
//  gösterge aynı tarafa bakar (d_mil_yuvasi düzlemi y = +1.575'tedir).
// ---------------------------------------------------------------------
module gosterge_olugu() {
    translate([-knob_mark_w / 2,
               1.50,
               knob_h - knob_mark_dep])
        cube([knob_mark_w,
              (knob_d / 2 - knob_top_ch_d / 2) - 1.50,
              knob_mark_dep + eps]);
}

// ---------------------------------------------------------------------
//  DÜĞME — birleşik parça
// ---------------------------------------------------------------------
module dugme() {
    render()
    color(col_knob)
    difference() {
        dugme_govdesi();
        tutus_oluklari();
        translate([0, 0, -eps]) d_mil_yuvasi(knob_shaft_dep + eps);
        somun_havsasi();
        gosterge_olugu();
    }
}

// ---------------------------------------------------------------------
//  Doğrulama çıktısı
// ---------------------------------------------------------------------
module dugme_rapor() {
    echo(str("KNOB: cap=", knob_d, " h=", knob_h,
             "  mil yuvasi=", knob_shaft_d, " duzluk=", knob_shaft_flat,
             " derinlik=", knob_shaft_dep));
    echo(str("  Tavan et kalinligi = ", knob_h - knob_shaft_dep, " mm"));
    echo(str("  Tus adimina pay    = ", key_pitch - knob_d, " mm"));
    echo(str("  Somun havsasi      = ", knob_nut_d, " x ", knob_nut_dep,
             " mm (somun 2.40 + rondela 0.50 = 2.90 icin ",
             knob_nut_dep - 2.90, " mm hava)"));
    echo(str("  Mile gecen boy     = ", knob_shaft_grip, " mm"));
    echo(str("  Havsa yan et       = ", (knob_d - knob_nut_d) / 2, " mm"));
}

// ---------------------------------------------------------------------
//  Tek başına açıldığında düğmeyi render et
// ---------------------------------------------------------------------
if (is_undef(EK_MONTAJ)) {
    dugme();
    dugme_rapor();
}
