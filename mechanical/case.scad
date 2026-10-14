// =====================================================================
//  ExtraKeyboard MK1 — GÖVDE (tepsi tipi kasa)
//  Dosya  : mechanical/case.scad
//  Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2.1 ve 3
//
//  İÇERİK
//    · 3.00 mm duvarlar + 2.50 mm taban  → dış ölçü 88.20 × 69.15 × 20.50
//    · 4 köşede M3×5 heat-set insert yuvalı kule (⌀7.60, 18.00 mm yüksek)
//    · Sağ duvarda 12.00 × 7.00 mm USB-C açıklığı (DevKitC-1 soket hizası)
//    · ESP32-S3-DevKitC-1 için destek pedleri + 3 yönlü tutucu kaburgalar
//    · Tabanda 4 adet ⌀8.00 × 1.00 silikon ayak çukuru
//    · İsteğe bağlı klavye eğimi kaması (tilt_enable = true)
//
//  Plaka bu gövdenin ÜSTÜNE oturur (kasa 20.50 + plaka 1.50 = 22.00).
//
//  Tek başına açıldığında gövdeyi render eder.
// =====================================================================

EK_SESSIZ = true;              // parameters.scad önizlemesini bastır
include <parameters.scad>

// ---------------------------------------------------------------------
//  Dış kabuk: duvarlar + taban (üstü açık tepsi)
// ---------------------------------------------------------------------
module kabuk() {
    difference() {
        // Dış blok — plaka ile aynı taban alanı
        cube([plate_w, plate_d, case_h]);

        // İç boşluk — üstten tamamen açık kalsın diye +1 mm taşırılır
        translate([wall, wall, base_t])
            cube([cavity_w, cavity_d, inner_h + 1]);
    }
}

// ---------------------------------------------------------------------
//  Köşe vida kuleleri (insert taşıyıcıları)
//  Taban iç yüzeyinden plaka alt yüzeyine kadar uzanır (18.00 mm).
//  Duvarla kesiştiği için köşede tek parça bir kütle oluşturur.
// ---------------------------------------------------------------------
module vida_kuleleri() {
    for (p = screw_positions())
        translate([p[0], p[1], base_t])
            cylinder(d = post_d, h = inner_h);
}

// ---------------------------------------------------------------------
//  Insert yuvaları + vida gövdesi boşlukları (ÇIKARILAN hacim)
//
//  Üstten aşağı doğru:
//    z = 20.50 → 14.50   ⌀4.20  heat-set insert yuvası (6.00 mm)
//    z = 14.50 →  6.50   ⌀3.40  vida gövdesi boşluğu   (8.00 mm)
//  M3×12 vida, 1.50 mm plakadan geçtikten sonra 10.50 mm iner
//  (uç kotu z = 10.00) → 6.50 mm'lik boşluk dibi ile 3.50 mm pay kalır.
// ---------------------------------------------------------------------
module insert_bosluklari() {
    for (p = screw_positions()) {
        // Insert yuvası
        translate([p[0], p[1], case_h - insert_depth])
            cylinder(d = insert_d, h = insert_depth + 1);

        // Insert altındaki vida gövdesi boşluğu
        translate([p[0], p[1], case_h - insert_depth - screw_clear_dep])
            cylinder(d = screw_shaft_d, h = screw_clear_dep + eps);
    }
}

// ---------------------------------------------------------------------
//  DevKitC-1 yatağı: 4 destek pedi + 3 yönlü tutucu kaburga
//  Kart uzun kenarı X ekseninde, sağ iç duvara dayalı.
//  SAĞ tarafta kaburga YOKTUR — USB-C soketi oradan duvara bakar.
// ---------------------------------------------------------------------
module pcb_yatagi() {
    // Destek pedleri (kart alt yüzeyi z = base_t + pcb_standoff_h = 6.50)
    for (px = [pcb_x1 + 5, pcb_x2 - 5])
        for (py = [pcb_y1 + 5, pcb_y2 - 5])
            translate([px, py, base_t])
                cylinder(d = pcb_pad_d, h = pcb_standoff_h);

    // Sol kaburga
    translate([pcb_x1 - pcb_clear - rib_t, pcb_y1 - pcb_clear - rib_t, base_t])
        cube([rib_t, pcb_d + 2 * (pcb_clear + rib_t), rib_h]);

    // Ön kaburga
    translate([pcb_x1 - pcb_clear - rib_t, pcb_y1 - pcb_clear - rib_t, base_t])
        cube([pcb_w + pcb_clear + rib_t, rib_t, rib_h]);

    // Arka kaburga
    translate([pcb_x1 - pcb_clear - rib_t, pcb_y2 + pcb_clear, base_t])
        cube([pcb_w + pcb_clear + rib_t, rib_t, rib_h]);
}

// ---------------------------------------------------------------------
//  USB-C açıklığı (ÇIKARILAN hacim) — sağ duvar
//  Merkez: Y = 42.75 (kart merkez hattı), Z = base_t + 7.20 = 9.70
//  Ölçü  : 12.00 (Y) × 7.00 (Z), duvarı boydan boya deler.
//  Not   : usb_w yerine usb_wide_w (22.00) kullanılırsa DevKit'in
//          "UART" ve "USB" soketlerinin İKİSİ birden açılır.
// ---------------------------------------------------------------------
module usb_acikligi(genislik = undef) {
    w = is_undef(genislik) ? usb_w : genislik;
    translate([plate_w - wall - eps,
               usb_center_y - w / 2,
               base_t + usb_center_z - usb_h / 2])
        cube([wall + 2 * eps, w, usb_h]);
}

// ---------------------------------------------------------------------
//  Silikon ayak çukurları (ÇIKARILAN hacim) — taban alt yüzeyi
// ---------------------------------------------------------------------
module ayak_cukurlari() {
    for (p = foot_positions())
        translate([p[0], p[1], -eps])
            cylinder(d = foot_d, h = foot_depth + eps);
}

// ---------------------------------------------------------------------
//  GÖVDE — tüm parçaların birleşimi
// ---------------------------------------------------------------------
module govde(usb_genislik = undef) {
    render()
    color(col_case)
    difference() {
        union() {
            kabuk();
            vida_kuleleri();
            pcb_yatagi();
        }
        insert_bosluklari();
        usb_acikligi(usb_genislik);
        ayak_cukurlari();
    }
}

// ---------------------------------------------------------------------
//  İSTEĞE BAĞLI: Klavye eğimi kaması (ayrı basılan parça)
//  Alt yüzü düz (masaya oturur), üst yüzü tilt_angle kadar eğimlidir.
//  Gövde bu kamanın üstüne düz oturur; temas düzlem-düzlemdir.
//  Kamanın alt yüzünde de aynı konumlarda ayak çukurları vardır.
// ---------------------------------------------------------------------
module egim_kamasi() {
    color("#16213e")
    render()
    difference() {
        hull() {
            // Ön kenar (alçak)
            cube([plate_w, eps, tilt_front]);
            // Arka kenar (yüksek)
            translate([0, plate_d - eps, 0])
                cube([plate_w, eps, tilt_rear]);
        }
        // Ayak çukurları
        for (p = foot_positions())
            translate([p[0], p[1], -eps])
                cylinder(d = foot_d, h = foot_depth + eps);
    }
}

// ---------------------------------------------------------------------
//  Doğrulama çıktısı
// ---------------------------------------------------------------------
module kasa_rapor() {
    echo(str("GOVDE dis olcu : ", plate_w, " x ", plate_d, " x ", case_h, " mm"));
    echo(str("Ic bosluk      : ", cavity_w, " x ", cavity_d, " x ", inner_h, " mm"));
    echo(str("Plaka ile toplam: ", case_h + plate_t, " mm (hedef ", body_h, ")"));
    echo(str("USB acikligi   : ", usb_w, " x ", usb_h,
             "  Ymerkez=", usb_center_y, "  Zmerkez=", base_t + usb_center_z));
    echo(str("DevKit yatagi  : X ", pcb_x1, "..", pcb_x2,
             "  Y ", pcb_y1, "..", pcb_y2));
    echo(str("Egim kamasi    : on ", tilt_front, " arka ", tilt_rear,
             " mm  (", tilt_angle, " derece)"));
}

// ---------------------------------------------------------------------
//  Tek başına açıldığında gövdeyi render et
// ---------------------------------------------------------------------
if (is_undef(EK_MONTAJ)) {
    govde();
    if (tilt_enable)
        translate([0, -plate_d - 10, 0]) egim_kamasi();
    kasa_rapor();
}
