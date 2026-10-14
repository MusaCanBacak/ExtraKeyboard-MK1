// =====================================================================
//  ExtraKeyboard MK1 — Mekanik Parametreler
//  Dosya  : mechanical/parameters.scad
//  Sürüm  : 3.0.0        (FW 3.0.0 · APP 3.0.0 · HW_REV = MK1)
//  Kaynak : docs/00-CEKIRDEK-SPEC.md — Bölüm 2 ve 2.1 (TEK DOĞRULUK KAYNAĞI)
//
//  BU DOSYA TÜM ÖLÇÜLERİN TEK ADRESİDİR.
//  plate.scad / case.scad / knob.scad / assembly.scad bu dosyayı
//  "include <parameters.scad>" ile çağırır. Hiçbiri kendi ölçüsünü
//  yeniden tanımlamaz. Bir ölçüyü değiştirmek istiyorsan SADECE burayı
//  değiştir — bütün parçalar birlikte güncellenir.
//
//  ---------------------------------------------------------------------
//  KOORDİNAT SİSTEMİ
//  ---------------------------------------------------------------------
//    Orijin (0,0,0) = gövdenin SOL-ÖN-ALT köşesi.
//    +X  sağa            (plaka genişliği   88.20 mm)
//    +Y  geriye/arkaya   (plaka derinliği   69.15 mm)
//    +Z  yukarı          (toplam yükseklik  22.00 mm)
//
//    Spesifikasyondaki yerleşim şemasında SATIR 1 en üsttedir; bu
//    modelde SATIR 1 en ARKADAKİ satırdır (en büyük Y). SÜTUN 1 en
//    soldaki sütundur (en küçük X).
//
//        Y=69.15 ┌──────────────────────────────────────┐  ARKA
//                │  LED1  LED2  LED3   (üst bezel)      │
//                │  K1    K2    K3     ENC   ← SATIR 1  │
//                │  K4    K5    K6     K10   ← SATIR 2  │
//                │  K7    K8    K9     K11   ← SATIR 3  │
//        Y=0.00  └──────────────────────────────────────┘  ÖN
//                X=0.00                            X=88.20
//
//  ---------------------------------------------------------------------
//  ÖNİZLEME KORUMASI
//  ---------------------------------------------------------------------
//    Bu dosya TEK BAŞINA açıldığında bir "yerleşim önizlemesi" render
//    eder. Başka bir dosya tarafından include edildiğinde, o dosya
//    include'dan ÖNCE "EK_SESSIZ = true;" atadığı için önizleme çalışmaz.
// =====================================================================

// ---------------------------------------------------------------------
// 0) GENEL RENDER AYARLARI
// ---------------------------------------------------------------------
$fn = 64;                 // Silindir/çember çözünürlüğü (makul + hızlı)
eps = 0.01;               // Yüzey çakışmasını (z-fighting) önleyen pay

// ---------------------------------------------------------------------
// 1) TUŞ IZGARASI                      [SPEC 2.1]
// ---------------------------------------------------------------------
key_pitch   = 19.05;      // Tuş adımı (0.75"), X ve Y aynı
col_count   = 4;          // Sütun sayısı
row_count   = 3;          // Satır sayısı
key_area_w  = 76.20;      // Tuş alanı genişliği  = 4 × 19.05
key_area_d  = 57.15;      // Tuş alanı derinliği  = 3 × 19.05

// ---------------------------------------------------------------------
// 2) PLAKA                             [SPEC 2.1]
// ---------------------------------------------------------------------
bezel       = 6.00;       // Her kenardaki bezel
plate_w     = 88.20;      // Plaka dış genişliği = 76.20 + 2×6.00
plate_d     = 69.15;      // Plaka dış derinliği = 57.15 + 2×6.00
plate_t     = 1.50;       // Plaka kalınlığı — MX klipsinin tutması için ZORUNLU

// ---------------------------------------------------------------------
// 3) GÖVDE (tepsi tipi)                [SPEC 2.1]
// ---------------------------------------------------------------------
wall        = 3.00;       // Duvar kalınlığı
cavity_w    = 82.20;      // İç boşluk genişliği = 88.20 − 2×3.00
cavity_d    = 63.15;      // İç boşluk derinliği = 69.15 − 2×3.00
inner_h     = 18.00;      // İç yükseklik: taban iç yüzeyi → plaka alt yüzeyi
base_t      = 2.50;       // Taban kalınlığı
body_h      = 22.00;      // Toplam gövde yüksekliği = 1.50 + 18.00 + 2.50
case_h      = base_t + inner_h;   // = 20.50 — plaka hariç kasa yüksekliği

// ---------------------------------------------------------------------
// 4) ANAHTAR / ENKODER / LED DELİKLERİ [SPEC 2.1]
// ---------------------------------------------------------------------
mx_hole     = 14.00;      // MX anahtar plaka deliği (kare) — NOMİNAL
mx_tol_min  = 13.95;      // Kabul edilebilir alt sınır
mx_tol_max  = 14.05;      // Kabul edilebilir üst sınır

// ÜRETİM TELAFİSİ — plakadaki BÜTÜN deliklerin çapına / kenar uzunluğuna
// eklenir. Nominal ölçüler yukarıda değişmeden kalır.
//   0.00  → lazer kesim / CNC / hazır alüminyum plaka (varsayılan)
//   0.15  → FDM 3D baskı (ekstrüzyon genişliği yüzünden delikler daralır)
// gen_dxf.py bu değeri de okur; SCAD ile DXF asla ayrışmaz.
uretim_telafi = 0.00;

enc_hole_d  = 7.20;       // EC11 M7 burç deliği ⌀7.20
enc_pin_d   = 1.50;       // EC11 dönme engelleyici konumlandırma pimi ⌀1.50
enc_pin_r   = 5.00;       // Pim deliklerinin enkoder merkezine uzaklığı
enc_pin_ang = 0;          // Pim ekseninin açısı (0° = X ekseni, sağ/sol)

led_hole_d  = 3.00;       // LED penceresi ⌀3.00
led_count   = 3;          // LED1..LED3
led_spacing = 8.00;       // LED merkezleri arası mesafe
led_y       = 63.40;      // LED merkezlerinin Y koordinatı (üst bezel bandı)
                          // Bant: MX üst kenarı 60.625 ↔ iç duvar 66.15
                          // Bandın gerçek ortası 63.3875; 63.40 bu değere en
                          // yakın yuvarlak koordinattır. Et payları:
                          // MX kenarına 1.275 mm, iç arka duvara 1.250 mm.

// ---------------------------------------------------------------------
// 5) VİDA / INSERT                      [SPEC 2.1: M3×12, M3×5 insert]
// ---------------------------------------------------------------------
screw_inset     = 4.50;   // Vida merkezinin her iki kenardan içeri mesafesi
plate_screw_d   = 3.20;   // Plakadaki M3 geçme (clearance) deliği
screw_shaft_d   = 3.40;   // Kule içindeki gövde boşluk deliği
insert_d        = 4.20;   // M3×5 heat-set insert yuvası ⌀
insert_depth    = 6.00;   // Insert yuvası derinliği (5 mm insert + 1 mm pay)
screw_clear_dep = 8.00;   // Insert altındaki ⌀3.40 gövde boşluğunun derinliği
post_d          = 7.60;   // Köşe kulesi dış çapı (insert etrafında 1.70 et)
screw_len       = 12.00;  // M3 × 12 havşasız silindir başlı vida
screw_head_d    = 5.50;   // M3 silindir baş çapı (montaj görünümü için)
screw_head_h    = 3.00;   // M3 silindir baş yüksekliği

// ---------------------------------------------------------------------
// 6) AYAK ÇUKURLARI (silikon tampon yuvaları)
// ---------------------------------------------------------------------
foot_d      = 8.00;       // Ayak çukuru çapı (⌀8 silikon tampon)
foot_depth  = 1.00;       // Çukur derinliği (2.50 tabandan 1.50 kalır)
foot_inset  = 10.00;      // Çukur merkezinin her iki kenardan içeri mesafesi

// ---------------------------------------------------------------------
// 7) DEVKIT YERLEŞİMİ (ESP32-S3-DevKitC-1)
// ---------------------------------------------------------------------
pcb_w          = 63.00;   // DevKitC-1 uzun kenar
pcb_d          = 25.50;   // DevKitC-1 kısa kenar
pcb_t          = 1.60;    // Kart kalınlığı
pcb_standoff_h = 4.00;    // Kart altındaki destek pedi yüksekliği
pcb_clear      = 0.40;    // Kart ile kaburga arasındaki yanal boşluk
rib_t          = 1.20;    // Tutucu kaburga et kalınlığı
pcb_pad_d      = 6.00;    // Destek pedi çapı

// Kart, uzun kenarı X ekseni boyunca olacak şekilde SAĞ iç duvara dayanır.
// USB-C soketleri kartın +X kısa kenarındadır → açıklık SAĞ duvardadır.
pcb_x2 = plate_w - wall;              // 85.20 — kart sağ kenarı (iç duvar yüzeyi)
pcb_x1 = pcb_x2 - pcb_w;              // 22.20 — kart sol kenarı
pcb_y1 = 30.00;                       // kart ön kenarı (köşe kulelerinden uzak)
pcb_y2 = pcb_y1 + pcb_d;              // 55.50 — kart arka kenarı
pcb_cx = (pcb_x1 + pcb_x2) / 2;       // 53.70
pcb_cy = (pcb_y1 + pcb_y2) / 2;       // 42.75
rib_h  = pcb_standoff_h + pcb_t;      // 5.60 — kaburga üstü kart üstü ile aynı hizada

// ---------------------------------------------------------------------
// 8) USB-C AÇIKLIĞI (sağ duvar)
// ---------------------------------------------------------------------
usb_w        = 12.00;     // Açıklık genişliği (Y yönünde)
usb_h        =  7.00;     // Açıklık yüksekliği (Z yönünde)
usb_center_y = pcb_cy;    // 42.75 — kart merkez hattı
usb_center_z = 7.20;      // Taban İÇ yüzeyinden ölçülü soket merkez yüksekliği
                          // = 4.00 ped + 1.60 kart + 1.63 soket yarı yüksekliği
usb_wide_w   = 22.00;     // Alternatif: DevKit'in HER İKİ USB-C soketini açar

// ---------------------------------------------------------------------
// 9) ENKODER DÜĞMESİ (knob) — 6 mm D-shaft
// ---------------------------------------------------------------------
knob_d          = 17.00;  // Düğme dış çapı (< 19.05 adım, K10'a çarpmaz)
knob_h          = 15.00;  // Düğme toplam yüksekliği
knob_shaft_d    =  6.15;  // 6.00 mm mil + 0.15 baskı toleransı
knob_shaft_flat =  4.65;  // D düzlüğü karşılıklı ölçüsü (4.50 nominal + 0.15)
knob_shaft_dep  = 12.00;  // Mil yuvası derinliği
knob_top_ch     =  1.00;  // Üst pah yüksekliği
knob_top_ch_d   =  2.00;  // Üst pahta çaptan düşülen miktar
knob_bot_ch     =  0.60;  // Alt pah yüksekliği
knob_flutes     = 24;     // Çevredeki tutuş oluğu sayısı
knob_flute_d    =  1.60;  // Oluk çapı
knob_mark_w     =  1.20;  // Üst gösterge oluğu genişliği
knob_mark_dep   =  0.60;  // Üst gösterge oluğu derinliği

// M7 SOMUN HAVŞASI (counterbore) — ZORUNLU
//  EC11'in M7 somunu + rondelası plaka ÜSTÜNDE 2.90 mm yer kaplar
//  (docs/02-MEKANIK-TASARIM.md §5.3: somun 2.40 + rondela 0.50).
//  Düğmenin altında bu yığın için bir cep açılmazsa düğme somunun üstüne
//  oturur, mile tam geçmez ve sürterek döner. Havşa sayesinde düğme altı
//  plakadan yalnızca knob_gap kadar yukarıda kalabilir.
knob_nut_d      = 13.00;  // Havşa çapı (M7 somunun köşegeni ~11.5 mm + pay)
knob_nut_dep    =  3.20;  // Havşa derinliği (2.90 yığın + 0.30 hava)
knob_gap        =  1.00;  // Düğme altı ile plaka üstü arası hava boşluğu
                          // (somun + rondela yığını havşanın İÇİNDE kalır)
// Havşa sonrası mile gerçekten geçen D-yuvası boyu:
knob_shaft_grip = knob_shaft_dep - knob_nut_dep;        // 8.80 mm

// ---------------------------------------------------------------------
// 10) KEYCAP (yalnızca montaj görünümü için temsilî)
// ---------------------------------------------------------------------
cap_bottom  = 18.00;      // Keycap alt ölçüsü
cap_top     = 14.00;      // Keycap üst ölçüsü
cap_h       = 10.00;      // Keycap yüksekliği
cap_lift    = 6.00;       // Plaka üstünden keycap altına mesafe (MX üst gövde)

// ---------------------------------------------------------------------
// 11) KLAVYE EĞİMİ (typing angle) — İSTEĞE BAĞLI
// ---------------------------------------------------------------------
tilt_enable = false;      // true → arka kama (takoz) parçası da üretilir
tilt_angle  = 6.00;       // Derece cinsinden öne doğru eğim
tilt_front  = 2.50;       // Kamanın ön kenar kalınlığı (ayak çukuru için yeterli)
// Ayak merkezleri arası mesafe: (plate_d − 2×foot_inset) = 49.15 mm
tilt_span   = plate_d - 2 * foot_inset;                 // 49.15
tilt_rise   = tilt_span * tan(tilt_angle);              // 6° → 5.166 mm
tilt_rear   = tilt_front + tilt_rise;                   // 2.50 + 5.166 = 7.666 mm

// ---------------------------------------------------------------------
// 12) RENKLER (montaj görünümü — SPEC 8 tema renkleri)
// ---------------------------------------------------------------------
col_case  = "#1a1a2e";    // Gövde
col_plate = "#16213e";    // Plaka
col_cap   = "#1e1e2e";    // Keycap
col_knob  = "#FF9500";    // Enkoder düğmesi (combo turuncusu)
col_led   = "#2CC985";    // LED pencereleri
col_screw = "#9aa4b2";    // Vida
col_pcb   = "#3B8ED0";    // DevKitC-1

// =====================================================================
//  YARDIMCI FONKSİYONLAR — tüm konumlar buradan türetilir
// =====================================================================

// Sütun numarasından (1..4) tuş merkezinin X koordinatı
function key_cx(col) = bezel + (col - 0.5) * key_pitch;

// Satır numarasından (1..3) tuş merkezinin Y koordinatı
// SATIR 1 en arkadadır → en büyük Y
function key_cy(row) = plate_d - bezel - (row - 0.5) * key_pitch;

// LED sırasından (0..led_count-1) LED merkezinin X koordinatı
function led_cx(i) = plate_w / 2 + (i - (led_count - 1) / 2) * led_spacing;

// Vida merkezleri — 4 köşe, her iki kenardan screw_inset içeride
function screw_positions() = [
    [screw_inset,           screw_inset          ],   // sol ön
    [plate_w - screw_inset, screw_inset          ],   // sağ ön
    [screw_inset,           plate_d - screw_inset],   // sol arka
    [plate_w - screw_inset, plate_d - screw_inset]    // sağ arka
];

// Ayak çukuru merkezleri
function foot_positions() = [
    [foot_inset,           foot_inset          ],
    [plate_w - foot_inset, foot_inset          ],
    [foot_inset,           plate_d - foot_inset],
    [plate_w - foot_inset, plate_d - foot_inset]
];

// =====================================================================
//  TUŞ HARİTASI  [SPEC 2 — yerleşim şeması]
//  [isim, sütun, satır]  — SATIR 1 arka, SÜTUN 1 sol
//  SÜTUN 4 / SATIR 1 = ENKODER (MX deliği değil, ayrı ele alınır)
// =====================================================================
key_map = [
    ["K1",  1, 1], ["K2",  2, 1], ["K3", 3, 1],
    ["K4",  1, 2], ["K5",  2, 2], ["K6", 3, 2],
    ["K7",  1, 3], ["K8",  2, 3], ["K9", 3, 3],
    ["K10", 4, 2],                                  // COMBO
    ["K11", 4, 3]                                   // OS SWITCH
];

enc_col = 4;              // Enkoderin sütunu
enc_row = 1;              // Enkoderin satırı
enc_cx  = key_cx(enc_col);   // 72.675
enc_cy  = key_cy(enc_row);   // 53.625

// =====================================================================
//  TEK BAŞINA AÇILDIĞINDA: YERLEŞİM ÖNİZLEMESİ
// =====================================================================

// Bütün delik konumlarını renkli işaretlerle gösteren düz önizleme.
module parametre_onizleme() {
    // Plaka konturu (ince levha)
    color(col_plate)
        cube([plate_w, plate_d, 1.0]);

    // 11 MX deliği — kırmızı kareler
    color("#E04F5F")
        for (k = key_map)
            translate([key_cx(k[1]) - mx_hole/2, key_cy(k[2]) - mx_hole/2, 1.0])
                cube([mx_hole, mx_hole, 0.6]);

    // Enkoder deliği + 2 konumlandırma pimi — turuncu
    color(col_knob) {
        translate([enc_cx, enc_cy, 1.0])
            cylinder(d = enc_hole_d, h = 0.6);
        for (s = [-1, 1])
            translate([enc_cx + s * enc_pin_r * cos(enc_pin_ang),
                       enc_cy + s * enc_pin_r * sin(enc_pin_ang), 1.0])
                cylinder(d = enc_pin_d, h = 0.6);
    }

    // 3 LED penceresi — yeşil
    color(col_led)
        for (i = [0 : led_count - 1])
            translate([led_cx(i), led_y, 1.0])
                cylinder(d = led_hole_d, h = 0.6);

    // 4 vida deliği — gri
    color(col_screw)
        for (p = screw_positions())
            translate([p[0], p[1], 1.0])
                cylinder(d = plate_screw_d, h = 0.6);

    // Tuş alanı sınırı — ince mavi çerçeve
    color(col_pcb)
        translate([bezel, bezel, 1.0])
            difference() {
                cube([key_area_w, key_area_d, 0.3]);
                translate([0.4, 0.4, -0.5])
                    cube([key_area_w - 0.8, key_area_d - 0.8, 1.3]);
            }
}

// EK_SESSIZ tanımlı değilse (yani bu dosya tek başına açıldıysa) önizle.
if (is_undef(EK_SESSIZ)) parametre_onizleme();
