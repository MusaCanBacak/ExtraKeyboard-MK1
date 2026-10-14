# ExtraKeyboard MK1 — Mekanik Tasarım (v3.0.0)

> **Ölçü kaynağı:** [`docs/00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) Bölüm 2 ve 2.1.
> Bu doküman o dosyadaki ölçüleri **birebir** uygular. Çelişki görürsen çekirdek spec kazanır.
> Parametrik kaynak: [`mechanical/parameters.scad`](../mechanical/parameters.scad) — **tüm ölçülerin tek adresi**.

> **Anahtar seçimi: Cherry MX Blue (clicky / tıklı) — parça no `MX1A-E1NN`.**
> MX Blue, MX ailesinin diğer üyeleriyle **boyutsal olarak birebir aynıdır**
> (plaka deliği 14.00 mm kare, adım 19.05 mm, gövde flanşı 15.6 mm).
> Bu yüzden **bu dokümandaki hiçbir plaka/kasa ölçüsü değişmemiştir ve
> `mechanical/plate.dxf` dosyasının yeniden üretilmesine gerek yoktur.**
> Anahtarın getirdiği gerçek farklar — 3/5 pin seçimi, akustik, debounce —
> **Bölüm 10**'da toplanmıştır.

---

## 0. Dosyalar ve Hızlı Başlangıç

| Dosya | İçerik |
|---|---|
| `mechanical/parameters.scad` | Tüm ölçüler, konum fonksiyonları, tuş haritası. Diğerleri bunu `include` eder. |
| `mechanical/plate.scad` | Üst plaka — 11 MX deliği + enkoder + LED pencereleri + vida delikleri |
| `mechanical/case.scad` | Tepsi tipi gövde — duvarlar, taban, USB açıklığı, insert kuleleri, ayak çukurları, eğim kaması |
| `mechanical/knob.scad` | Enkoder düğmesi, 6 mm D-shaft yuvası |
| `mechanical/assembly.scad` | Montaj + patlatılmış + kesit görünümü |
| `mechanical/gen_dxf.py` | Lazer kesim için `plate.dxf` üretir (harici kütüphane yok) |
| `mechanical/plate.dxf` | Üretilen DXF R12 — **48 LINE + 10 CIRCLE**, **kerf telafisi YOK (nominal ölçü)** |

```bash
# DXF üret ve doğrula (harici bağımlılık gerektirmez)
python3 mechanical/gen_dxf.py

# Lazer kerf telafisi ile (örn. 0.10 mm ışın kalınlığı)
# --out MUTLAKA verilmelidir: varsayılan çıktı yolu mechanical/plate.dxf'tir
# ve kerf'siz (nominal) dosyayı sessizce ezer.
python3 mechanical/gen_dxf.py --kerf 0.10 --out mechanical/plate_kerf010.dxf

# OpenSCAD ile parçaları dışa aktar
openscad -o plate.stl    mechanical/plate.scad
openscad -o case.stl     mechanical/case.scad
openscad -o knob.stl     mechanical/knob.scad
openscad -o assembly.stl mechanical/assembly.scad
```

Her `.scad` dosyası **tek başına** açıldığında anlamlı bir şey render eder:
`parameters.scad` → renkli yerleşim önizlemesi, `plate.scad` → plaka,
`case.scad` → gövde, `knob.scad` → düğme, `assembly.scad` → tam montaj.

---

## 1. Ölçülendirilmiş Yerleşim Diyagramı

### 1.1 Üstten görünüş (plan) — tüm ölçüler mm

Orijin **(0, 0)** = plakanın **sol-alt köşesi**. +X sağa, +Y arkaya (kullanıcıdan uzağa).

```
                                    X  (mm)
  0.00      6.00        25.05        44.10        63.15        82.20   88.20
   │          │           │            │            │            │       │
   ▼          ▼           ▼            ▼            ▼            ▼       ▼
  ┌───────────────────────────────────────────────────────────────────────┐  Y = 69.15
  │                                                                       │
  │  ○ M3                                                         M3 ○    │  Y = 64.65
  │  (4.50, 64.65)                                     (83.70, 64.65)     │
  │                                                                       │
  │              ● LED1        ● LED2        ● LED3                       │  Y = 63.40
  │               36.10         44.10         52.10     ⌀3.00 / aralık 8  │
  ├─────────────┬─────────────┬─────────────┬─────────────────────────────┤  Y = 63.15
  │             │             │             │            ◎                │
  │     K1      │     K2      │     K3      │      ENC  ⌀7.20             │  Y = 53.625
  │             │             │             │   pim ⌀1.50 @ ±5.00         │   SATIR 1
  │  14×14      │  14×14      │  14×14      │   (67.675 / 77.675)         │
  ├─────────────┼─────────────┼─────────────┼─────────────────────────────┤  Y = 44.10
  │             │             │             │                             │
  │     K4      │     K5      │     K6      │      K10   [COMBO]          │  Y = 34.575
  │             │             │             │                             │   SATIR 2
  ├─────────────┼─────────────┼─────────────┼─────────────────────────────┤  Y = 25.05
  │             │             │             │                             │
  │     K7      │     K8      │     K9      │      K11   [WIN/MAC]        │  Y = 15.525
  │             │             │             │                             │   SATIR 3
  ├─────────────┴─────────────┴─────────────┴─────────────────────────────┤  Y =  6.00
  │  ○ M3                                                         M3 ○    │  Y =  4.50
  │  (4.50, 4.50)                                      (83.70, 4.50)      │
  └───────────────────────────────────────────────────────────────────────┘  Y =  0.00
     X=15.525      X=34.575      X=53.625      X=72.675
      SÜTUN 1       SÜTUN 2       SÜTUN 3       SÜTUN 4

     │◄──────────── tuş alanı 76.20 ────────────►│
  │◄─────────────── plaka dış ölçü 88.20 ──────────────────────────────►│
```

Izgara çizgileri (tuş alanı sınırları) tam olarak **19.05 mm** adımdadır:
`X = 6.00 / 25.05 / 44.10 / 63.15 / 82.20` ve `Y = 6.00 / 25.05 / 44.10 / 63.15`.

### 1.2 Yan kesit (Z yığını)

```
   Z = 38.00  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  keycap üstü = knob üstü
              ┌────┐  ┌────┐  ┌────┐      ▐███▌
              │ cap│  │ cap│  │ cap│      ▐knob    keycap h=10.00, knob h=15.00
              └────┘  └────┘  └────┘      ▐███▌    knob plakadan 1.00 yukarıda
   Z = 35.00  ─── knob mil yuvası tavanı (knob altı + 12.00) ────────────
   Z = 28.00  ─── keycap alt yüzü (plaka üstü + 6.00 = MX üst gövdesi) ──
   Z = 26.20  ─── knob SOMUN HAVŞASI tavanı (knob altı + 3.20) ──────────
   Z = 25.50  ─── M7 burcun diş ucu (plaka üstünde 3.50 mm diş kalır) ───
   Z = 24.90  ─── M7 somunun üst yüzü (0.50 rondela + 2.40 somun) ───────
   Z = 23.00  ─── knob alt yüzü (knob_gap = 1.00; somun havşanın içinde) ─
  ╔═══════════════════════════════════════════════════════════════════╗
  ║ Z = 22.00     Ü S T   P L A K A   1.50 mm                         ║ ← plaka üst yüzü
  ╚═══════════════════════════════════════════════════════════════════╝
   Z = 20.50  ─── plaka alt yüzü = duvar üstü ───────────────────────────
   ║                                                                   ║
   ║   ⌀4.20 × 6.00 insert yuvası (Z 20.50 → 14.50)                    ║
   ║   ⌀3.40 × 8.00 vida gövde boşluğu (Z 14.50 →  6.50)               ║
   ║                                                                   ║
   ║        İÇ YÜKSEKLİK 18.00                          duvar 3.00 ────╢
   ║   ┌──────────────────────────────────────────┐                    ║
   ║   │ ESP32-S3-DevKitC-1  63.00 × 25.50 × 1.60 │  ← USB açıklığı    ║
   ║   │ kart alt yüzü Z = 6.50 (2.50 + 4.00 ped) │     Z 6.20 → 13.20 ║
   ║   └──────────────────────────────────────────┘                    ║
   ╠═══════════════════════════════════════════════════════════════════╣
   ║ Z =  2.50            T A B A N   2.50 mm                          ║
   ║ Z =  1.00   ⌀8.00 × 1.00 ayak çukuru  ○         ○                 ║
   ╚═══════════════════════════════════════════════════════════════════╝
   Z =  0.00  ─────────────────── masa yüzeyi ───────────────────────────

   TOPLAM GÖVDE:  2.50 (taban) + 18.00 (iç) + 1.50 (plaka) = 22.00 mm  ✔
```

> **Knob ile M7 somunu neden çakışmıyor:** `knob_gap = 1.00` düğmenin alt
> yüzünü Z = 23.00'a koyar, oysa rondela + somun yığını Z = 24.90'a kadar
> çıkar. Bu 1.90 mm'lik girişimi kapatan şey düğmenin altındaki
> **⌀13.00 × 3.20 mm somun havşasıdır (counterbore)**: havşanın tavanı
> Z = 26.20'dedir ve hem somunun üstünü (24.90) hem de burcun çıplak diş
> ucunu (25.50) içine alır. Hesabın tamamı **bölüm 5.3**'tedir.

### 1.3 Sağ duvar — USB-C açıklığı

```
        sağ duvar dış yüzü (X = 88.20)                Y →
   Z=20.50 ┌───────────────────────────────────────────────────┐
           │                                                   │
   Z=13.20 │              ┌───────────────────┐                │
           │              │   USB-C  12.00    │  merkez        │
   Z= 9.70 │              │   ×      7.00     │  Y = 42.75     │
           │              │                   │  Z =  9.70     │
   Z= 6.20 │              └───────────────────┘                │
           │              36.75           48.75                │
   Z= 0.00 └───────────────────────────────────────────────────┘
```

---

## 2. Tuş / Delik Merkez Koordinatları

**Orijin: plakanın sol-alt köşesi.** Değerler `gen_dxf.py` çıktısıyla birebir aynıdır
(`python3 mechanical/gen_dxf.py` çalıştırıp doğrulayabilirsin).

### 2.1 Anahtar ve enkoder merkezleri

| Slot | Görev | Sütun | Satır | X (mm) | Y (mm) | Delik |
|---|---|:--:|:--:|---:|---:|---|
| `K1` | İşlev tuşu 1 | 1 | 1 | **15.525** | **53.625** | 14.00 × 14.00 |
| `K2` | İşlev tuşu 2 | 2 | 1 | **34.575** | **53.625** | 14.00 × 14.00 |
| `K3` | İşlev tuşu 3 | 3 | 1 | **53.625** | **53.625** | 14.00 × 14.00 |
| `ENC` | Enkoder (ses) | 4 | 1 | **72.675** | **53.625** | ⌀7.20 |
| `K4` | İşlev tuşu 4 | 1 | 2 | **15.525** | **34.575** | 14.00 × 14.00 |
| `K5` | İşlev tuşu 5 | 2 | 2 | **34.575** | **34.575** | 14.00 × 14.00 |
| `K6` | İşlev tuşu 6 | 3 | 2 | **53.625** | **34.575** | 14.00 × 14.00 |
| `K10` | COMBO | 4 | 2 | **72.675** | **34.575** | 14.00 × 14.00 |
| `K7` | İşlev tuşu 7 | 1 | 3 | **15.525** | **15.525** | 14.00 × 14.00 |
| `K8` | İşlev tuşu 8 | 2 | 3 | **34.575** | **15.525** | 14.00 × 14.00 |
| `K9` | İşlev tuşu 9 | 3 | 3 | **53.625** | **15.525** | 14.00 × 14.00 |
| `K11` | OS SWITCH | 4 | 3 | **72.675** | **15.525** | 14.00 × 14.00 |

> Toplam **11 adet MX deliği** (K1…K11) + **1 adet enkoder deliği**.
> Formül: `X = 6.00 + (sütun − 0.5) × 19.05`, `Y = 69.15 − 6.00 − (satır − 0.5) × 19.05`.

### 2.2 Enkoder yardımcı delikleri

| Öğe | X (mm) | Y (mm) | Çap |
|---|---:|---:|---|
| EC11 burç deliği | 72.675 | 53.625 | ⌀7.20 |
| Konumlandırma pimi (sol) | **67.675** | 53.625 | ⌀1.50 |
| Konumlandırma pimi (sağ) | **77.675** | 53.625 | ⌀1.50 |

Pimler merkezden **±5.00 mm**, X ekseni boyunca. Burç deliği kenarı ile pim deliği
kenarı arasında **0.650 mm** et kalır — bu, tolerans bölümünde ayrıca ele alınıyor.

### 2.3 LED pencereleri (üst bezel)

| Öğe | X (mm) | Y (mm) | Çap | Anlamı (SPEC 6.4) |
|---|---:|---:|---|---|
| `LED1` | **36.10** | **63.40** | ⌀3.00 | OS modu (Mavi `#1E90FF` / Beyaz `#FFFFFF`) |
| `LED2` | **44.10** | **63.40** | ⌀3.00 | Combo (Turuncu `#FF9500` / Yeşil flaş `#2CC985`) |
| `LED3` | **52.10** | **63.40** | ⌀3.00 | Bağlantı (Yeşil `#2CC985` / Kırmızı `#E04F5F`) |

Aralık tam **8.00 mm**, dizi plaka merkezine (X = 44.10) göre simetriktir.

### 2.4 Vida delikleri (4 köşe)

| # | X (mm) | Y (mm) | Plakada | Kasada |
|---|---:|---:|---|---|
| 1 (sol ön) | **4.50** | **4.50** | ⌀3.20 geçme | ⌀4.20 × 6.00 insert |
| 2 (sağ ön) | **83.70** | **4.50** | ⌀3.20 geçme | ⌀4.20 × 6.00 insert |
| 3 (sol arka) | **4.50** | **64.65** | ⌀3.20 geçme | ⌀4.20 × 6.00 insert |
| 4 (sağ arka) | **83.70** | **64.65** | ⌀3.20 geçme | ⌀4.20 × 6.00 insert |

Her iki kenardan **4.50 mm** içeride. Delik kenarı ile plaka kenarı arasında **2.90 mm** et kalır.

### 2.5 Ayak çukurları (taban alt yüzü)

| # | X (mm) | Y (mm) | Ölçü |
|---|---:|---:|---|
| 1 | 10.00 | 10.00 | ⌀8.00 × 1.00 derin |
| 2 | 78.20 | 10.00 | ⌀8.00 × 1.00 derin |
| 3 | 10.00 | 59.15 | ⌀8.00 × 1.00 derin |
| 4 | 78.20 | 59.15 | ⌀8.00 × 1.00 derin |

---

## 3. Tam Ölçü Tablosu

### 3.1 Spec'ten gelen ölçüler (DEĞİŞTİRİLEMEZ — SPEC 2.1)

| Ölçü | Değer | Parametre adı | Not |
|---|---:|---|---|
| Tuş adımı (pitch) | 19.05 | `key_pitch` | 0.75", X ve Y aynı |
| Tuş alanı | 76.20 × 57.15 | `key_area_w`, `key_area_d` | 4×19.05 ve 3×19.05 |
| Bezel (her kenar) | 6.00 | `bezel` | |
| Plaka dış ölçü | 88.20 × 69.15 | `plate_w`, `plate_d` | tuş alanı + 2×6.00 |
| Plaka kalınlığı | 1.50 | `plate_t` | **MX klips tutması için ZORUNLU** |
| Duvar kalınlığı | 3.00 | `wall` | |
| İç boşluk (cavity) | 82.20 × 63.15 | `cavity_w`, `cavity_d` | plaka − 2×3.00 |
| İç yükseklik | 18.00 | `inner_h` | plaka altı → taban içi |
| Taban kalınlığı | 2.50 | `base_t` | |
| Toplam gövde yüksekliği | 22.00 | `body_h` | 1.50 + 18.00 + 2.50 |
| MX anahtar deliği | 14.00 × 14.00 | `mx_hole` | tolerans 13.95 – 14.05 |
| Enkoder deliği | ⌀7.20 | `enc_hole_d` | EC11 M7 burç |
| LED penceresi | ⌀3.00 × 3 adet | `led_hole_d`, `led_count` | aralık 8.00 |
| Vida | M3 × 12 | `screw_len` | 4 köşe, M3×5 heat-set insert |

### 3.2 Bu tasarımda türetilen / seçilen ölçüler

| Ölçü | Değer | Parametre adı | Gerekçe |
|---|---:|---|---|
| Kasa yüksekliği (plaka hariç) | 20.50 | `case_h` | 2.50 + 18.00 |
| LED merkez Y | 63.40 | `led_y` | MX üst kenarı (60.625) ile iç arka duvar (66.15) arasındaki bandın ortasına **en yakın yuvarlak değer** (gerçek orta 63.3875) |
| Vida merkezi kenardan | 4.50 | `screw_inset` | 2.90 mm kenar eti + köşe kulesi duvara kaynar |
| Plaka M3 geçme deliği | ⌀3.20 | `plate_screw_d` | M3 için standart geçme |
| Kule dış çapı | ⌀7.60 | `post_d` | insert etrafında 1.70 mm et |
| Insert yuvası | ⌀4.20 × 6.00 | `insert_d`, `insert_depth` | M3×5 pirinç insert + 1.00 pay |
| Vida gövde boşluğu | ⌀3.40 × 8.00 | `screw_shaft_d`, `screw_clear_dep` | M3×12'nin ucu Z=10.00'a iner, dip Z=6.50 |
| Enkoder pim deliği | ⌀1.50 @ ±5.00 | `enc_pin_d`, `enc_pin_r` | EC11 dönme engelleyici pimler |
| Ayak çukuru | ⌀8.00 × 1.00 @ 10.00 | `foot_d`, `foot_depth`, `foot_inset` | ⌀8 silikon tampon; tabanda 1.50 et kalır |
| USB-C açıklığı | 12.00 × 7.00 | `usb_w`, `usb_h` | merkez Y = 42.75, Z = 9.70 |
| USB geniş varyant | 22.00 × 7.00 | `usb_wide_w` | DevKit'in her iki USB-C soketini açar |
| DevKit yatağı | X 22.20–85.20, Y 30.00–55.50 | `pcb_x1/x2/y1/y2` | ped 4.00 + kaburga 1.20 |
| Knob | ⌀17.00 × 15.00 | `knob_d`, `knob_h` | 19.05 adıma 2.05 mm pay |
| Knob mil yuvası | ⌀6.15 / düzlük 4.65 / derinlik 12.00 | `knob_shaft_*` | 6 mm D-shaft + 0.15 pay; yuva tavanı Z = 35.00 |
| Knob somun havşası | ⌀13.00 × 3.20 | `knob_nut_d`, `knob_nut_dep` | M7 somun + rondela (2.90) düğmenin içine girer — bkz. 5.3.1 |
| Knob ↔ plaka hava boşluğu | 1.00 | `knob_gap` | Düğme alt yüzü Z = 23.00 |
| Üretim telafisi | 0.00 (FDM'de 0.15) | `uretim_telafi` | tüm plaka deliklerine eklenir |

### 3.3 Doğrulanmış kritik boşluklar

| Kontrol | Sonuç |
|---|---:|
| MX ↔ MX en dar et | 5.050 mm |
| MX ↔ plaka kenarı en dar | 8.525 mm |
| Vida deliği ↔ en yakın MX | 4.092 mm |
| Vida deliği ↔ plaka kenarı | 2.900 mm |
| LED ↔ MX üst kenarı | 1.275 mm |
| LED ↔ iç arka duvar | 1.250 mm |
| Enkoder deliği ↔ pim deliği | 0.650 mm |
| Köşe kulesi ↔ MX gövdesi (plaka altı) | 1.892 mm |
| Köşe kulesi ↔ EC11 gövdesi | 2.747 mm |
| Kaburga ↔ köşe kulesi | 3.750 mm |
| M3×12 ucu ↔ boşluk dibi | 3.500 mm |

---

## 4. Üretim Seçenekleri

Üç yol da aynı `parameters.scad` ölçülerini kullanır; fark **plakanın** nasıl
yapıldığı ve gövdenin nasıl bölündüğüdür.

| | (a) FDM 3D baskı | (b) Lazer sandviç | (c) CNC / hazır alüminyum |
|---|---|---|---|
| Maliyet | En düşük (~60 g filament) | Orta | En yüksek |
| Gereken ekipman | FDM yazıcı | Lazer kesim servisi | CNC / hazır plaka |
| Plaka riski | **Yüksek** (aşağıya bak) | Düşük | Yok |
| Görünüm | Mat, katmanlı | Şeffaf/renkli katmanlar | Endüstriyel |
| Süre | ~5–6 saat baskı | 1–3 gün servis | 3–10 gün |
| Toleransa duyarlılık | Yüksek | Düşük | Çok düşük |

### 4.a) FDM 3D baskı

**Parça bazında ayarlar**

| Parça | Katman | Duvar | Dolgu | Destek | Yönlendirme |
|---|---|---|---|---|---|
| `case.stl` | 0.20 mm | 3 çevrim (1.2 mm) | %25 gyroid | **Hayır** | Taban masaya, ağız yukarı |
| `plate.stl` | **0.15 mm** | 4 çevrim | %100 | Hayır | Düz yatık |
| `knob.stl` | 0.15 mm | 3 çevrim | %30 | Hayır | Mil deliği yukarı bakacak |
| `egim_kamasi` | 0.20 mm | 3 çevrim | %20 | Hayır | Düz taban masaya |

**Malzeme: PETG (önerilen).** Gerekçeleri:

1. **Cam geçiş sıcaklığı ~80 °C.** Klavye masada, gerekirse arabada/pencere
   kenarında kalır. PLA'nın Tg'si ~60 °C'dir; güneşte kalan siyah bir PLA kasa
   deforme olur ve o anda plakadaki 14.00 mm delikler bozulur → anahtarlar düşer.
2. **Sünek kırılma.** PETG bükülür, PLA çatlar. 1.50 mm'lik ince plakanın
   MX klipsleriyle sürekli zorlanan ince duvarları PLA'da yorulma çatlağı yapar.
3. **Katmanlar arası yapışma iyi.** Plakayı düz yatık bastığımızda MX deliği
   duvarları katman düzlemine dik yük alır; PETG bu yükü PLA'dan iyi taşır.
4. **Heat-set insert için ideal.** 230–250 °C havya ucuyla pirinç insert PETG'ye
   temiz gömülür; ABS gibi is yapmaz, PLA gibi kabarcık atmaz.

Alternatifler: **ABS/ASA** (daha ısıya dayanıklı ama çeker, kapalı hazne ister),
**PLA+** (yalnızca hızlı prototip için — kalıcı kullanma), **PA/Nylon** (en iyi
ama nemi emer, ayarı zordur).

**Plakayı 3D basmanın riski ve çözümü**

> **Risk:** 1.50 mm kalınlıkta FDM plaka = tipik olarak **7–10 katman**.
> MX anahtar takılırken yan klipsler plakanın altına geçip **dışa doğru yaylanır**
> ve deliğin kenarına ~4–6 N kuvvet uygular. PLA'da 1.50 mm et bu kuvvete
> **katmanlar arasından ayrılarak** cevap verir: delik ağzı beyazlaşır, çatlar,
> anahtar oturmaz veya keycap çekilirken anahtar plakayla birlikte yukarı fırlar.
> Ayrıca "elephant foot" ve ekstrüzyon genişliği yüzünden 14.00 mm delik
> gerçekte **13.80–13.90 mm** çıkar; anahtar hiç girmez ya da zorla girip
> plakayı çatlatır.

> **Çözüm (sırayla uygula):**
> 1. **PETG kullan** — sünekliği klips kuvvetini emer.
> 2. `parameters.scad` içinde **`uretim_telafi = 0.15;`** yap. Bu, MX kenarını
>    14.15, enkoder deliğini 7.35, LED'i 3.15, vida deliğini 3.35 mm'ye çıkarır;
>    baskıdaki daralmayı telafi eder ve nominal 14.00'e geri döner.
>    `gen_dxf.py` aynı değeri okuduğu için DXF de senkron kalır.
> 3. **Elephant foot compensation −0.15 mm** (veya ilk katman akışını %95'e çek).
> 4. Katman yüksekliğini **0.15 mm** yap → 1.50 mm tam 10 katman olur, üst
>    yüzey ince kabuk kalmaz.
> 5. **%100 dolgu + 4 çevrim** — 1.50 mm'de dolgu boşluğu bırakmak plakayı
>    kağıt gibi yapar.
> 6. **Kabul testi:** bastıktan sonra tek bir MX anahtarı bir deliğe tak-çıkar
>    yap. Klips "klik" sesiyle oturmuyor veya delik ağzı beyazlıyorsa
>    `uretim_telafi` değerini 0.05 adımlarla ayarla.
> 7. **Hâlâ tutmuyorsa:** plakayı basma. 1.50 mm alüminyum/akrilik/FR4 plakayı
>    `plate.dxf` ile kestir (seçenek b veya c). Kasa FDM kalabilir — asıl kritik
>    parça sadece plakadır.

**Baskı malzeme tahmini (PETG, 1.27 g/cm³)**

| Parça | Hacim | Ağırlık |
|---|---:|---:|
| Gövde | 35.3 cm³ | ~45 g |
| Plaka | 5.8 cm³ | ~7 g |
| Knob | 3.0 cm³ | ~4 g |
| **Toplam** | **44.1 cm³** | **~56 g** |

### 4.b) Lazer kesim sandviç (3 mm akrilik katmanlar)

Gövde tek parça basılmak yerine **düz katmanlara** bölünür ve 4 köşeden
uzun vidayla sıkılır. Tüm katmanların dış konturu aynı **88.20 × 69.15**'tir.

| Katman | Adet | Kalınlık | Kesilecek geometri |
|---|:--:|---:|---|
| **A — Plaka** | 1 | **1.50 mm** | `plate.dxf`'in tamamı (kontur + 11 MX + enkoder + 2 pim + 3 LED + 4 vida) |
| **B — Ara katman** | **6** | 3.00 mm | Dış kontur + 82.20 × 63.15 iç açıklık + 4 × ⌀3.20 vida deliği |
| **C — Taban** | 1 | 2.50 mm | Dış kontur + 4 × ⌀3.20 vida deliği (+ istenirse ⌀8.00 ayak cebi) |

`1.50 + 6 × 3.00 + 2.50 = **22.00 mm**` — spec ile **birebir**.

> **2.50 mm akrilik bulunamazsa** 3.00 mm kullan → toplam 22.50 mm olur
> (spec'ten +0.50 mm sapma; iç yükseklik 18.00 korunur, sadece taban kalınlaşır).

**USB-C açıklığı sandviçte:** açıklık Z = 6.20 – 13.20 arasındadır. Katman
Z aralıkları: B1 = 2.50–5.50, **B2 = 5.50–8.50**, **B3 = 8.50–11.50**,
**B4 = 11.50–14.50**, B5 = 14.50–17.50, B6 = 17.50–20.50.
→ **B2, B3 ve B4** katmanlarının sağ kenarına, Y = 36.75 – 48.75 arasında
12.00 mm genişliğinde çentik kes. Sonuç 9.00 mm yüksekliğinde açıklık olur
(FDM'deki 7.00 mm yerine) — kablo için sorun değildir, sadece görsel farktır.

**Kritik kural:** A katmanı **kesinlikle 1.50 mm** olmalıdır.
3 mm akrilik plakada MX klipsi plakanın altına ulaşamaz; anahtar sadece
sürtünmeyle durur ve keycap çekilince çıkar. 1.50 mm döküm akrilik bulunamazsa
1.50 mm **FR4 (epoksi cam)** veya 1.50 mm **alüminyum** kullan.

**Bağlantı elemanları (sandviç):** M3 × 12 yerine **M3 × 25 silindir başlı vida
+ M3 kilit somunu**. Taban katmanına somun için ⌀6.5 havşa/altıgen cep açılabilir.
Alternatif: 4 adet **M3 × 18 dişi-dişi ara pul (standoff)** + 2 kısa vida.

**Akrilik notları:** Akrilik gevrektir — vidayı **sıkma, sadece otur**. Kenardan
2.90 mm et akrilikte sınırdır; mümkünse `screw_inset` değerini 5.00'e çıkarıp
DXF'i yeniden üret (`gen_dxf.py` otomatik uyum sağlar).

### 4.c) CNC / hazır alüminyum plaka

| Parça | Yöntem | Malzeme |
|---|---|---|
| Plaka | Lazer/su jeti/CNC ile `plate.dxf` | **1.50 mm 5052 veya 6061 alüminyum** (en yaygın klavye plakası), 1.50 mm paslanmaz, veya 1.50 mm FR4 |
| Gövde | 3 eksen CNC cep frezeleme (tek kütükten) | 6061-T6 alüminyum bloktan |
| Gövde (ucuz yol) | FDM basılmış kasa + alüminyum plaka | Karma çözüm — **en iyi fiyat/performans** |

- Alüminyum plakada MX deliği **14.00 ± 0.05** hedeflenir; kerf telafisine gerek
  yoktur, servis kendi telafisini uygular. Yine de sipariş notuna
  *"delik ölçüleri bitmiş ölçüdür, kerf telafisi sizde"* yaz.
- Alüminyum plaka **iletkendir**. Anahtarların GND ucu plakaya değebilir;
  lehim uçlarına makaron geçir veya plaka altına 0.1 mm kapton bant çek.
  ESP32 tarafında tüm anahtarlar zaten GND'ye çekiliyor (SPEC 3.1), ama
  **LED veri hattı ve 5 V** plakaya kesinlikle değmemelidir.
- Anodize edilecekse deliklerin **+0.02 mm** büyümesini hesaba kat (kaplama içeri doğru büyür).
- Enkoder somunu alüminyum plakayı çizmesin diye **plastik/fiber rondela** kullan.

---

## 5. Tolerans Notları

### 5.1 MX deliği neden tam 14.00 mm?

Cherry MX ve uyumlularının (Gateron, Kailh, TTC…) plakaya oturan **boyun**
kesiti nominal **13.90 – 13.95 mm** karedir; bu boynun köşelerinde plakanın
altına geçen iki adet yaylı klips bulunur.

> **MX Blue bu tabloyu değiştirmez.** Cherry MX ailesinde anahtar tipini
> belirleyen şey **slider (ve MX Blue'da ayrıca click jacket)**, yani gövdenin
> *içi*dir; dış gövde, boyun kesiti, klips geometrisi ve flanş ölçüsü Blue /
> Brown / Red / Black varyantlarında **aynı kalıptan** çıkar. Yani 14.00 mm
> delik, 19.05 mm adım ve 1.50 mm plaka kalınlığı MX Blue için de aynen
> geçerlidir (bkz. Bölüm 10.2).

| Delik ölçüsü | Ne olur |
|---|---|
| **< 13.95** | Anahtar zorla girer. Boyun sıkışır, klipsler açılamaz, plaka çatlar (FDM/akrilik). Sökerken anahtar kırılır. |
| **13.95 – 14.05** | ✅ **Doğru.** 0.00 – 0.15 mm geçme boşluğu. Klips "klik" sesiyle kilitlenir, anahtar yanal oynamaz. |
| **> 14.05** | Anahtar boşluk yapar, tuşa basınca yalpalar. 14.30'un üstünde klipsler artık plaka altını tutamaz → keycap çekilince anahtar plakayla birlikte çıkar. |

Bu yüzden `mx_hole = 14.00` **nominal orta değerdir** ve tolerans bandı
`13.95 – 14.05` (yani **±0.05 mm**) olarak spec'te sabitlenmiştir.
Lazer/CNC bu bandı rahat tutar; FDM tutamaz — telafi şarttır (5.2).

### 5.2 3D baskıda delik küçülmesi ve telafisi (+0.15 mm)

FDM'de delikler üç sebeple **küçük** çıkar:

1. **Ekstrüzyon genişliği fazlalığı:** iç çevrim (perimeter) hattı, hedef
   konturun içine doğru ~0.03–0.08 mm taşar.
2. **Köşe yuvarlanması:** 0.4 mm nozül, 14.00 mm karenin iç köşelerini
   ~0.2 mm yarıçapla yuvarlar → köşe boşluğu kaybolur.
3. **Elephant foot:** ilk katman ezilir, alt ağız 0.1–0.2 mm daralır.

Ölçülen tipik sonuç: **14.00 mm modellenen delik → 13.80 – 13.90 mm basılır.**
Bu, kabul bandının (13.95) **altındadır** → anahtar girmez.

**Telafi mekanizması** `parameters.scad` içinde hazırdır:

```openscad
uretim_telafi = 0.15;   // FDM için; lazer/CNC için 0.00 bırak
```

Bu değer plakadaki **bütün** deliklerin çapına/kenarına eklenir:

| Delik | Nominal | `uretim_telafi = 0.15` ile modellenen | Basıldığında hedef |
|---|---:|---:|---:|
| MX kare | 14.00 | 14.15 | ≈ 14.00 |
| Enkoder | ⌀7.20 | ⌀7.35 | ≈ ⌀7.20 |
| Enkoder pimi | ⌀1.50 | ⌀1.65 | ≈ ⌀1.50 |
| LED | ⌀3.00 | ⌀3.15 | ≈ ⌀3.00 |
| M3 geçme | ⌀3.20 | ⌀3.35 | ≈ ⌀3.20 |

`gen_dxf.py` aynı parametreyi `parameters.scad`'den okur, dolayısıyla
OpenSCAD modeli ile DXF **hiçbir zaman ayrışmaz**. Lazer için ayrıca
`--kerf` ile ışın kalınlığı telafisi eklenebilir (delikler `kerf` kadar büyür,
dış kontur her kenardan `kerf/2` küçülür).

> **Dikkat — kerf'li çıktıyı ayrı dosyaya yaz.** `--kerf` bayrağı varsayılan
> çıktı yolunu değiştirmez; komutu `--out` vermeden çalıştırırsan depodaki
> **nominal** `mechanical/plate.dxf` üzerine yazılır ve dosya adı artık
> içeriğini anlatmaz. Daima ayrı bir ad ver:
> `python3 mechanical/gen_dxf.py --kerf 0.10 --out mechanical/plate_kerf010.dxf`

> **Kalibrasyon kuponu:** Tam plakayı basmadan önce sadece 2 MX deliği içeren
> 30 × 20 mm test parçası bas, anahtarı dene, `uretim_telafi` değerini
> 0.05 adımlarla ayarla. 5 dakikalık baskı, saatlerce hata önler.

### 5.3 Enkoder somunu: 1.50 mm plakada kaç mm diş kalıyor?

Yaygın EC11 varyantı: **M7 × 0.75 burç, gövdeden yukarı 5.00 mm diş boyu**.

```
        ┌──────────┐  ← M7 somun          2.40 mm
        ├──────────┤  ← rondela           0.50 mm
   ═════╪══════════╪═════  ← PLAKA        1.50 mm
        │          │
        └── EC11 gövdesi ──┘

   Toplam burç dişi              5.00 mm
   − Plaka kalınlığı             1.50 mm
   ─────────────────────────────────────
   = Plaka üstünde kalan diş     3.50 mm   ✔

   Gereken:  somun 2.40 + rondela 0.50 = 2.90 mm
   Kalan pay: 3.50 − 2.90 =            0.60 mm   ✔ YETERLİ
```

**Sonuç:** 1.50 mm plakada standart M7 somun **rahat sıkılır**, 0.60 mm pay kalır.

| Plaka kalınlığı | Kalan diş | Somun + rondela 2.90 mm | Sonuç |
|---:|---:|---|---|
| 1.50 (bu tasarım) | 3.50 | 2.90 | ✅ 0.60 mm pay |
| 2.00 | 3.00 | 2.90 | ⚠️ 0.10 mm — rondelayı çıkar |
| 3.00 (akrilik) | 2.00 | 2.90 | ❌ **Somun dişe yetişmez** |

> Bu, plaka kalınlığının **1.50 mm olmasının ikinci zorunlu sebebidir**
> (birincisi MX klipsi). 3 mm akrilik plaka hem anahtarı hem enkoderi tutamaz.

#### 5.3.1 Somun ↔ knob çakışması ve somun havşası (counterbore)

Yukarıdaki yığın plaka **üstünde** yer kaplar, dolayısıyla düğmenin alt yüzü
düz olamaz. Kotlar (plaka üst yüzü Z = 22.00):

| Öğe | Alt Z | Üst Z | Hesap |
|---|---:|---:|---|
| Plaka üst yüzü | — | 22.00 | taban 2.50 + iç 18.00 + plaka 1.50 |
| Rondela (0.50) | 22.00 | 22.50 | |
| M7 somun (2.40) | 22.50 | **24.90** | somun yığını toplam 2.90 mm |
| Burcun çıplak diş ucu | 24.90 | **25.50** | plaka üstünde 3.50 mm diş |
| **Knob alt yüzü** | **23.00** | — | `knob_gap = 1.00` |

Düz altlı bir düğme Z = 23.00'da somunun **1.90 mm içinde** kalırdı: düğme
somunun üstüne biner, mile tam geçmez ve plakaya sürterek dönerdi. Bu yüzden
`knob.scad` düğmenin altına bir **somun havşası** açar:

```
   knob_nut_d      = 13.00 mm   // havsa capi  (M7 somunun kose capi ~11.5)
   knob_nut_dep    =  3.20 mm   // havsa derinligi, knob alt yuzunden

   Havsa tavani = 23.00 + 3.20 = 26.20 mm

   Somun ustune kalan hava   = 26.20 - 24.90 = 1.30 mm   OK
   Dis ucune kalan hava      = 26.20 - 25.50 = 0.70 mm   OK
   Knob cidar eti            = (17.00 - 13.00) / 2 = 2.00 mm   OK
   Mil yuvasi ile ortusme    = 12.00 - 3.20 = 8.80 mm gecme boyu  OK
```

**Doğrulama kuralı:** `knob_nut_dep` ≥ `somun+rondela (2.90)` −
`knob_gap (1.00)` + 0.50 hava = **2.40 mm**. Seçilen 3.20 mm, burcun çıplak
diş ucunu da içine aldığı için bu alt sınırın üzerindedir.

**Havşasız alternatif:** Düğmeyi düz altlı yapmak isterseniz `knob_gap`
değerini **en az 3.40 mm** (2.90 somun + 0.50 hava) yapmanız gerekir. Bu
durumda knob alt yüzü Z = 25.40'a, üst yüzü Z = 40.40'a çıkar; yani
"keycap üstü = knob üstü = 38.00" hizası bozulur ve bölüm 1.2'deki Z yığını
ile bölüm 3.2'deki knob satırları yeniden hesaplanmalıdır. Bu tasarım
**havşalı çözümü** kullanır.

#### 5.3.2 Mil boyu kontrolü

Mil yuvasının tavanı Z = 23.00 + `knob_shaft_dep` (12.00) = **35.00**'tir.
EC11 milinin ucu bu kotun altında kalmalıdır, yani **plaka üstünden en fazla
13.00 mm** çıkmalıdır. Daha uzun milli bir varyant kullanırsanız ya mili
kısaltın ya da `knob_shaft_dep` değerini artırın (tavan eti
`knob_h − knob_shaft_dep` = 3.00 mm'nin altına düşmesin).

**7 mm burçlu EC11 varyantı** kullanılırsa plaka üstünde 5.50 mm diş kalır;
somun yığını yine 2.90 mm'dir ama çıplak diş ucu Z = 27.50'ye çıkar ve
3.20 mm'lik havşayı (tavan 26.20) **1.30 mm aşar**. Bu varyantta üç seçenek
vardır: (a) `knob_nut_dep` değerini 4.50'ye çıkar, (b) `knob_gap` değerini
1.00'den 2.50'ye çıkar, (c) burç üzerine 2 mm'lik ara pul veya ikinci bir
somun ekleyip fazla dişi doldur.

### 5.4 Enkoder pim delikleri — dar nokta

Burç deliği yarıçapı 3.60, pim deliği yarıçapı 0.75, merkezler arası 5.00
→ aradaki et **5.00 − 3.60 − 0.75 = 0.650 mm**.

| Üretim | Değerlendirme |
|---|---|
| Alüminyum / FR4 1.5 mm | ✅ Sorun yok |
| Lazer akrilik 1.5 mm | ⚠️ Kerf 0.10–0.20 mm bu eti 0.45'e düşürür; kırılabilir |
| FDM PETG | ⚠️ 0.65 mm ≈ 1.5 çevrim; `uretim_telafi = 0.15` ile 0.50'ye iner |

**Öneri:** Akrilikte veya FDM'de pim deliklerini **açma**. EC11 zaten M7 somunla
sıkıldığında dönmez; pimler yalnızca ekstra güvence içindir. Kapatmak için
`parameters.scad` içinde `enc_pin_d = 0.01;` yeterlidir (delik pratikte yok olur),
ya da `plate.scad`'de `enkoder_delik_2d` içindeki `for (s = [-1, 1])` döngüsünü
yorum satırına al. Alüminyum plakada ise **mutlaka aç** — dönme engelleyici
görev görür ve montajda enkoderi hizalar.

### 5.5 Genel tolerans özeti

| Öğe | Nominal | Kabul bandı | Kritiklik |
|---|---:|---|---|
| MX deliği | 14.00 | 13.95 – 14.05 | 🔴 Kritik |
| Plaka kalınlığı | 1.50 | 1.40 – 1.60 | 🔴 Kritik |
| Enkoder deliği | ⌀7.20 | ⌀7.10 – ⌀7.40 | 🟡 Orta |
| Tuş adımı | 19.05 | ±0.10 (kümülatif ±0.20) | 🟡 Orta (keycap çakışması) |
| LED penceresi | ⌀3.00 | ⌀2.90 – ⌀3.40 | 🟢 Düşük |
| M3 geçme deliği | ⌀3.20 | ⌀3.20 – ⌀3.50 | 🟢 Düşük |
| Dış kontur | 88.20 × 69.15 | ±0.30 | 🟢 Düşük |
| İç yükseklik | 18.00 | −0.00 / +1.00 | 🟡 Orta (DevKit sığması) |

---

## 6. Montaj Sırası Özeti

> Tam adım adım anlatım, kablo renkleri ve lehim detayları:
> **`docs/07-MONTAJ-KILAVUZU.md`**. Pin ataması: **SPEC 3.1** (değiştirilemez).

| # | Adım | Dikkat |
|:--:|---|---|
| 1 | **Insert'leri göm.** 4 köşe kulesine M3×5 pirinç insert'i 230–250 °C havya ucuyla dik bastır. | Kule üst yüzüyle aynı hizada dursun; eğik girerse vida tutmaz. |
| 2 | **Anahtarları plakaya tak.** 11 adet MX Blue'yu plakanın **üstünden** bastır, klipslerin oturduğunu **gözle ve elle** doğrula. | Anahtar pinleri arkaya (+Y) bakacak şekilde aynı yöne hizala — lehim çok kolaylaşır. ⚠️ **Clicky anahtarda "klik sesi geldi" ölçüt DEĞİLDİR** — anahtar oturmadan da tık sesi çıkar (10.3 / ADIM 4.2). 5 pinliyse önce plastik ayakları kes. |
| 3 | **Enkoderi tak.** EC11'i alttan geçir, pimleri deliklere otur, üstten rondela + M7 somunla sık. | Aşırı sıkma — 1.50 mm plaka bükülür. |
| 4 | **Ortak GND hattını ör.** Tüm 11 anahtarın bir bacağını + EC11'in ortak ucunu tek telle papatya dizimi yap. | Tek kalın (0.5 mm²) tel; uçları makaronla. |
| 5 | **Sinyal tellerini lehimle.** SPEC 3.1'e göre: K1→GPIO4, K2→GPIO5, K3→GPIO6, K4→GPIO7, K5→GPIO15, K6→GPIO16, K7→GPIO17, K8→GPIO18, K9→GPIO8, K10→GPIO9, K11→GPIO10, ENC_A→GPIO11, ENC_B→GPIO12, ENC_SW→GPIO13. | Her teli lehimledikten sonra **süreklilik ölç**. Sonradan bulmak çok zor. |
| 6 | **LED şeridini hazırla.** 3 × WS2812B'yi 8.00 mm aralıkla dizip plakanın alt yüzüne, LED pencerelerinin altına yapıştır. Veri girişine 330 Ω, besleme ucuna 1000 µF, +5 V hattına **1N4148 diyot** (SPEC 3.3). | Diyot **zorunludur** — 3.3 V veri seviyesi aksi hâlde sınırda kalır. |
| 7 | **Enkoder RC filtresini kur** (SPEC 3.4): A ve B kanalları için 10 kΩ pull-up + 100 nF. | Yazılım debounce tek başına yetmez. |
| 8 | **DevKitC-1'i yatağına oturt.** Kaburgaların arasına bastır, USB-C soketi sağ duvardaki açıklığa hizalansın. Çift taraflı bantla sabitle. | Kart altına iletken bir şey kalmasın. |
| 9 | **USB kablosunu tak ve firmware yükle.** Kasayı kapatmadan önce tüm tuşları ve enkoderi test et. | Kapattıktan sonra hata bulmak = baştan sökmek. |
| 9b | **Süngeri yerleştir.** 3 mm poron/EVA'yı 10.4'teki üç parça hâlinde kes, taban **iç** yüzeyine yapıştır. | DevKit yatağını ve tel koridorunu **boş bırak**; sünger anahtar gövdesine/lehimlere değmesin (10.4). |
| 10 | **Plakayı kasaya oturt, 4 × M3×12 vidayı sık.** Çapraz sırayla ve elle sık. | Tork verme; insert PETG'den sıyrılır. |
| 11 | **Silikon ayakları ayak çukurlarına yapıştır.** Eğim isteniyorsa arka ayaklar yüksek olacak (Bölüm 7). | |
| 12 | **Keycap'leri ve knob'u tak.** Knob'u mile bastırırken D düzlüğünü hizala; düğmenin altındaki havşa M7 somununun üzerine oturur. | Knob sıkı geliyorsa `knob_shaft_d` değerini 0.05 artırıp yeniden bas. Knob plakadan yüksek duruyor veya sürtüyorsa somun havşası yetersizdir — bkz. 5.3.1. |

**Mekanik malzeme listesi**

| Parça | Adet | Not |
|---|:--:|---|
| **Cherry MX Blue** (`MX1A-E1NN`), clicky, **3 pinli plate-mount** | 11 | 50 g tetikleme · 2.2 mm ön hareket · 4.0 mm toplam hareket. **5 pinli aldıysan 2 plastik ayağı kes** — bkz. 10.3. Uyumlu alternatifler: Gateron Blue, Kailh Box White, Outemu Blue (10.1). |
| **Poron / EVA sünger, 3 mm** (veya kesilmiş kaymaz dolap altlığı) | ~1 dm² | Kasa tabanının **iç** yüzeyine; boş kovuğun rezonansını keser. Kesim ölçüleri ve nereye değmeyeceği: **10.4**. |
| Keycap 1u (MX çapraz sap) | 11 | |
| EC11 döner enkoder (M7 burç, 6 mm D-shaft) | 1 | 20 tık/tur, butonlu |
| Enkoder düğmesi (knob) | 1 | `knob.scad` veya hazır ⌀17. **Hazır knob alırsan altında M7 somununu içine alan bir boşluk olmalı** (bkz. 5.3.1) |
| M3 × 12 silindir başlı vida | 4 | Sandviç yapıda M3 × 25 |
| M3 × 5 pirinç heat-set insert (⌀4.20) | 4 | Yalnızca FDM/CNC gövdede |
| ⌀8 × 2 mm silikon ayak | 4 | Eğim için arka ikisi daha yüksek |
| M7 somun + rondela | 1 | Genelde enkoderle gelir |

---

## 7. Klavye Eğimi (Typing Angle)

Varsayılan tasarım **düz (0°)** çalışır. Eğim iki şekilde eklenir.

### 7.1 Basit yol — farklı yükseklikte ayaklar (önerilen)

Ön ve arka ayak merkezleri arası mesafe: `69.15 − 2 × 10.00 = **49.15 mm**`.
Gereken arka yükselme: `49.15 × tan(açı)`.

| Açı | Arka yükselme | Ön ayak | Arka ayak | Yorum |
|:--:|---:|---:|---:|---|
| 0° | 0.000 mm | 2.0 mm | 2.0 mm | Düz (varsayılan) |
| 3° | 2.576 mm | 2.0 mm | ~4.6 mm | Çok hafif |
| **5°** | **4.300 mm** | 2.0 mm | **~6.3 mm** | **Klasik klavye eğimi** |
| **6°** | **5.166 mm** | 2.0 mm | **~7.2 mm** | Bu tasarımın varsayılan `tilt_angle` değeri |
| 7° | 6.035 mm | 2.0 mm | ~8.0 mm | Belirgin |
| 8° | 6.908 mm | 2.0 mm | ~8.9 mm | Yüksek |
| 10° | 8.666 mm | 2.0 mm | ~10.7 mm | Bilek desteği ister |

**Uygulama:** öne ⌀8 × 2 mm, arkaya ⌀8 × 6 mm silikon ayak yapıştır (5°'ye çok yakın).
Hazır ayak yükseklikleri sınırlıysa arka ayakların altına 2–3 mm keçe/silikon pul ekle.

### 7.2 Parametrik yol — eğim kaması (`egim_kamasi`)

`parameters.scad` içinde:

```openscad
tilt_enable = true;    // kama parçasını üret
tilt_angle  = 6.00;    // istediğin açı (derece)
tilt_front  = 2.50;    // kamanın ön kenar kalınlığı
```

Türetilen değerler otomatik hesaplanır:

```
tilt_span = plate_d − 2 × foot_inset            = 49.15 mm
tilt_rise = tilt_span × tan(tilt_angle)         = 5.166 mm   (6°)
tilt_rear = tilt_front + tilt_rise              = 7.666 mm
```

Sonra:

```bash
openscad -o egim_kamasi.stl mechanical/case.scad   # tilt_enable = true iken
```

`case.scad` tek başına açıldığında kama, gövdenin arkasında ayrı bir parça
olarak görünür; `assembly.scad` da onu montajın önüne serer.

Kama, gövdeyle **aynı dış kontura** (88.20 × 69.15) sahiptir: alt yüzü düz
(masaya oturur), üst yüzü `tilt_angle` kadar eğimlidir. Gövdenin düz tabanı
bu eğimli düzleme tam oturur — temas **düzlem–düzlem**'dir, nokta teması yoktur.
Kamanın alt yüzünde de aynı 4 konumda ⌀8.00 × 1.00 ayak çukuru bulunur.

### 7.3 Gövdeyi doğrudan eğimli basmak (3. yol — önerilmez)

Tabanı eğimli bir gövde tek parça basılabilir ama:

- İç boşluğun tabanı da eğilir → DevKit yatağı ve pedler yeniden hizalanmalı,
- 6°'de arka duvar 20.50 + 5.17 = **25.67 mm** olur, malzeme ~%25 artar,
- Baskı süresi uzar, destek gerekebilir,
- Eğimi sonradan değiştiremezsin.

Ayrı kama veya farklı ayak yüksekliği **her zaman daha iyi** çözümdür:
tek bir parçayı yeniden basarak açıyı istediğin zaman değiştirebilirsin.

---

## 8. SPEC Dışı Varsayımlar

Aşağıdakiler `docs/00-CEKIRDEK-SPEC.md`'de **belirtilmemiştir**; bu tasarımda
en makul değerler seçilmiş ve `parameters.scad`'de tek noktadan
değiştirilebilir hâlde bırakılmıştır. Hiçbiri spec'teki bir ölçüyle çelişmez.

| # | Varsayım | Seçilen değer | Gerekçe |
|:--:|---|---|---|
| 1 | LED pencerelerinin **Y koordinatı** | 63.40 | Spec yalnızca "üst bezelde, ⌀3.00, aralık 8.00" diyor. MX üst kenarı (60.625) ile iç arka duvar (66.15) arasındaki bandın **gerçek ortası 63.3875**'tir; 63.40 buna en yakın yuvarlak değerdir (0.0125 mm sapma). Et payları bu yüzden tam eşit değildir: MX tarafında **1.275 mm**, duvar tarafında **1.250 mm** — üretimde etkisizdir. |
| 2 | Vida merkezinin kenardan içeri mesafesi | 4.50 | Görev tanımından. 2.90 mm kenar eti bırakır, köşe kulesi duvarla kaynar. |
| 3 | Enkoder dönme engelleyici pim delikleri | 2 × ⌀1.50 @ ±5.00 (X ekseni) | Görev tanımından. Eksen yönü (X) seçildi: Y ekseninde olsalardı K10 karesine 1.3 mm daha yaklaşırlardı. |
| 4 | USB-C açıklığının **duvarı ve konumu** | Sağ duvar, Y = 42.75, Z = 9.70 | DevKitC-1 63.00 × 25.50 mm'dir ve USB soketleri **kısa kenardadır**. İç derinlik 63.15 mm olduğu için kart Y ekseninde duramaz (0.15 mm pay) → uzun kenarı X'e paralel yerleşti → soketler yan duvara baktı. |
| 5 | USB soket merkez yüksekliği | 7.20 mm (iç tabandan) | 4.00 ped + 1.60 kart + 1.63 (USB-C soket yarı yüksekliği 3.26/2) = 7.23 → 7.20 |
| 6 | Köşe kulesi ve insert ölçüleri | kule ⌀7.60, yuva ⌀4.20 × 6.00, boşluk ⌀3.40 × 8.00 | M3×5 pirinç insert'in yaygın dış çapı 4.0–4.2 mm. 1.70 mm et yeterli. |
| 7 | Ayak çukurları | ⌀8.00 × 1.00, kenardan 10.00 | Yaygın ⌀8 silikon tampon. 2.50 mm tabanda 1.50 mm et bırakır. |
| 8 | DevKitC-1 yatağı | pedler ⌀6.00 × 4.00 + 3 yönlü ⌀1.20 kaburga | DevKitC-1'de **montaj deliği yoktur**; kart kaburgalar arasına oturur, çift taraflı bantla sabitlenir. |
| 9 | Knob ölçüleri | ⌀17.00 × 15.00, yuva ⌀6.15 / düzlük 4.65 / derinlik 12.00 | 19.05 adıma 2.05 mm pay; 6 mm D-shaft nominal düzlüğü 4.50 + 0.15 baskı payı. |
| 9b | Knob **somun havşası** ve plaka boşluğu | ⌀13.00 × 3.20 havşa, `knob_gap = 1.00` | Spec knob'dan hiç bahsetmiyor. M7 somun + rondela plaka üstünde 2.90 mm yer kaplar; havşa bunu düğmenin içine alır ve "keycap üstü = knob üstü = 38.00" hizasını korur. Havşasız çözümde `knob_gap ≥ 3.40` gerekir (bkz. 5.3.1). |
| 10 | `uretim_telafi` parametresi | Varsayılan **0.00** | Spec ölçülerini hiç değiştirmez; yalnızca FDM kullanıcısı 0.15 yaparak telafi uygular. |
| 11 | Klavye eğimi parametreleri | `tilt_enable = false`, `tilt_angle = 6.00` | Spec eğimden bahsetmiyor; varsayılan kapalı (düz gövde spec'e birebir uyar). |
| 12 | Keycap ölçüleri | alt 18.00, üst 14.00, h 10.00 | **Yalnızca `assembly.scad` görselinde** temsilîdir; üretilen bir parça değildir. |
| 13 | EC11 gövde/burç ölçüleri | gövde 13.2 × 12.4, burç dişi 5.00 mm | En yaygın EC11 varyantı. 7 mm burçlu varyant için Bölüm 5.3'teki not geçerlidir. |
| 14 | Plaka dış konturu **keskin köşeli** | Köşe yarıçapı yok | DXF'te kontur tam **4 LINE** olarak istendiği için yuvarlatma yapılmadı. Kesim sonrası kenarlar elle hafifçe kırılmalıdır. |

---

## 9. Doğrulama

`mechanical/gen_dxf.py` çalıştırıldığında üretilen `plate.dxf` **kendi kendini
doğrular** ve entity sayısını raporlar:

```
KONTUR    :   4      ← dış dikdörtgen
MX_DELIK  :  44      ← 11 anahtar × 4 kenar
ENKODER   :   1      ← ⌀7.20
ENK_PIM   :   2      ← ⌀1.50
LED       :   3      ← ⌀3.00
VIDA      :   4      ← ⌀3.20
------------------------------------
LINE   :  48   (4 + 44)
CIRCLE :  10   (1 + 2 + 3 + 4)
SONUÇ  : DOĞRULANDI
```

Entity sayısı beklenenden farklıysa betik **çıkış kodu 1** döndürür — CI'da
doğrudan kullanılabilir.

---

## 10. Anahtar Seçimi — Cherry MX Blue (clicky)

Bu projede **Cherry MX Blue** kullanılır. Bu bölüm, seçimin mekanik tasarıma
ne yaptığını (ve **ne yapmadığını**) tek yerde toplar.

### 10.1 Teknik veriler

| Öğe | Değer |
|---|---|
| Parça numarası | **`MX1A-E1NN`** (Cherry MX Blue) |
| Tip | **Clicky (tıklı)** — sesli ve taktil |
| Mekanizma | **İki parçalı slider**: gövde içinde stemden ayrı bir **click jacket** (tık ceketi) vardır. Tık sesini ve taktil basamağı üreten parça budur. |
| Tetikleme kuvveti | **50 g (0.50 N)** |
| Tık / taktil tepe kuvveti | ~60 g |
| Dibe vurma (bottom-out) | ~60 g |
| Ön hareket (pretravel, tetikleme noktası) | **2.2 mm** |
| Toplam hareket | **4.0 mm** |
| Sıfırlama (reset) noktası | ~1.7 mm → **~0.5 mm histerezis** |
| Kontak sıçraması | Cherry MX ailesi veri sayfası değeri **≤ 5 ms**. Clicky varyantlarda click jacket **bırakış tarafında ek sıçrama** üretir; eskimiş anahtarlarda 10 ms'ye yaklaşabilir. |

**Uyumlu alternatifler** (hepsi boyutsal olarak aynıdır, plaka değişmez):

| Alternatif | Notu |
|---|---|
| **Gateron Blue** | Daha ucuz (~28 TL), daha pürüzsüz his, tık sesi biraz daha yumuşak. |
| **Kailh Box White** | Tık'ı **click bar** ile üretir (jacket değil). Kutulu gövde sayesinde toza/suya daha dayanıklı. |
| **Outemu Blue** | En ucuzu; kalite partiden partiye değişir, birkaç yedek al. |

> **Firmware etkisi:** Click jacket'in bırakıştaki ek sıçraması yüzünden tuş
> debounce'u **8 ms**'dir (`firmware/src/config.h` → `EK_KEY_DEBOUNCE_MS`).
> Enkoder butonu debounce'u **5 ms** kalır (`EK_ENC_SW_DEBOUNCE_MS`) — EC11'in
> kubbe kontağında click jacket yoktur. Gerekçenin tamamı:
> `docs/06-ONEMLI-NOTLAR.md` madde **22a**.

> **Histerezis (0.5 mm) ne demek:** Anahtar 2.2 mm'de tetiklenir ama ancak
> 1.7 mm'ye kadar **yukarı bırakıldığında** sıfırlanır. Yani parmağını 2.0 mm
> civarında "titretirsen" ikinci basış hiç görülmez. Bir makro klavyede bu
> pratikte sorun değildir (aynı tuşa saniyede 8 kez basılmaz), ama tuşu yarım
> bırakıp tekrar basma alışkanlığın varsa ikinci tetikleme kaybolur — çözüm
> tuşu **tam bırakmaktır**, debounce'u düşürmek değil.

### 10.2 Boyutsal etki: **HİÇBİR ÖLÇÜ DEĞİŞMEDİ**

Bu, bölümün en önemli cümlesidir:

> **MX Blue, MX Brown / Red / Black / Silent ile boyutsal olarak birebir
> aynıdır. Plaka, kasa, knob, DXF ve `parameters.scad` içindeki hiçbir değer
> değişmemiştir. `mechanical/plate.dxf` dosyasını yeniden üretmene gerek
> YOKTUR.**

Sebebi basit: Cherry MX ailesinde anahtar tipini belirleyen şey gövdenin
**içi**dir (slider profili, click jacket, yay). Dış gövde — plakaya oturan
14 mm boyun, yaylı klipsler, 15.6 mm flanş, çapraz keycap sapı — tüm
varyantlarda **aynı kalıptan** çıkar.

Değişmeyenlerin listesi (hepsi Bölüm 3.1 ve 3.2'de olduğu gibi kalır):

| Ölçü | Değer | MX Blue ile durumu |
|---|---:|---|
| MX plaka deliği | 14.00 × 14.00 | **Aynı** (tolerans 13.95 – 14.05) |
| Tuş adımı | 19.05 | **Aynı** |
| Plaka kalınlığı | 1.50 | **Aynı** (klips hâlâ 1.5 mm'ye göre) |
| Plaka dış ölçü | 88.20 × 69.15 | **Aynı** |
| İç boşluk / iç yükseklik | 82.20 × 63.15 / 18.00 | **Aynı** |
| Enkoder, LED, vida delikleri | — | **Aynı** |
| `plate.dxf` entity sayısı | 48 LINE + 10 CIRCLE | **Aynı** |

Değişen tek "sayı" **kuvvettir**: BOM ve README tablolarında anahtar artık
**50 g** olarak yazılır (eski "herhangi bir ağırlık" ifadesi kaldırıldı).
Bu, plaka veya kasa açısından hiçbir şey ifade etmez; yalnızca doğru parçayı
sipariş edebilmek içindir.

### 10.3 3 pinli mi, 5 pinli mi? (plate-mount vs PCB-mount)

**Bu proje PCB'siz'dir**: anahtarlar plakaya klipslenir ve bacaklarına **elle**
tel lehimlenir. Bu yüzden **3 pinli (plate-mount) versiyon alınmalıdır.**

**Fark nedir?**

| | 3 pinli (plate-mount) | 5 pinli (PCB-mount) |
|---|---|---|
| Gövde altındaki merkez direk | ⌀4 mm plastik direk (var) | ⌀4 mm plastik direk (var) |
| **Metal kontak pini** | **2 adet** | **2 adet** |
| **Plastik konumlandırma ayağı** | **yok** | **2 adet**, merkezin iki yanında (tipik ⌀1.6–1.7 mm, merkezden yaklaşık ±5.1 mm, boyu ~3 mm — *tipik değerlerdir, kendi anahtarını kumpasla ölç*) |
| Amaç | Plakaya klipslenir, teller elle çekilir | PCB'deki karşılık deliklerine oturur, kart üstünde dönmez |

**Düz 1.5 mm plakada 5 pinli anahtarın üç somut sorunu:**

1. **Plaka altı yükseklik bütçesi şişer.** MX gövdesinin plaka altında kalan
   kısmı ~6.6 mm'dir; lehim ve tel bükümüyle birlikte plaka altı yığın
   **~9 mm**'ye çıkar (bkz. `06-ONEMLI-NOTLAR.md` madde 58). 5 pinlinin
   plastik ayakları bunun **altına ~3 mm daha** ekler → plaka altı ~12 mm.
   18.00 mm'lik iç yükseklikte bu, sünger ve kablo için kalan payı yer
   (Bölüm 10.4'teki sünger kalınlığı hesabını bozar).
2. **Eğrilik kontrolü yapılamaz.** Montaj kılavuzu ADIM 4.3, plakayı
   anahtarlar aşağı bakacak şekilde düz bir masaya koyup "hepsi masaya
   değiyor mu" diye baktırır. 5 pinlide plaka **plastik ayakların üstünde**
   durur, anahtar gövdeleri masaya hiç değmez ve eğri duran anahtarı
   göremezsin.
3. **Lehimleme sırasında anahtarı eğriltir.** Plakayı yüz üstü tezgâha
   yaslayıp lehim yaptığında anahtar bu iki plastik ayak üzerinde **tahterevalli
   gibi sallanır**; havyanın bastırdığı yönde yamulur ve klips tek taraftan
   boşalır. Keycap takıldığında eğrilik görünür hâle gelir ve düzeltmek için
   anahtarı sökmen gerekir.

**Çözüm — elindeki 5 pinliyse:**

1. Anahtarı ters çevir. Ortada büyük **⌀4 mm plastik merkez direği**,
   onun etrafında **2 adet parlak metal kontak pini**, ve merkezin sağ/sol
   yanında **2 adet ince plastik ayak** göreceksin.
2. **Yan keskiyle sadece bu 2 plastik ayağı**, gövde yüzeyine **dibinden**
   kes. Kalan çıkıntıyı maket bıçağıyla düzle.
3. Kesikten sonra anahtarı düz bir cam/masa üstüne bastır; **gövdenin alt
   yüzü tam düz oturmalı**, hiç sallanmamalı.

> 🔴 **METAL PİNLERİ SAKIN KESME.** Kesmen gereken şey **mat/beyaz plastik**
> ayaklardır. **Parlak metal olan 2 pin anahtarın elektrik kontağıdır** —
> kesersen anahtar çöp olur, geri dönüşü yoktur. Şüpheye düşersen kesme:
> plastik ayak elastiktir ve tırnakla bastırılınca hafifçe verir; metal pin
> serttir ve keskiyle kesilirken "çıt" diye kopar.

> **Merkez direği kesme.** ⌀4 mm plastik merkez direği hem 3 hem 5 pinlide
> vardır, bu tasarımda boşta kalır ve hiçbir zarar vermez. Kesmeye çalışırsan
> gövdenin alt kapağını çatlatırsın.

### 10.4 Akustik — MX Blue ve 18 mm'lik boş kovuk

**Sorun.** MX Blue **yüksek sesli** bir anahtardır ve bu tasarımda plakanın
hemen altında **82.20 × 63.15 × 18.00 mm ≈ 93 cm³** boş hava vardır. Boş,
sert duvarlı, paralel yüzeyli bir hacim **rezonans odası** gibi davranır:
tık sesi ve yayın "ping"i bu odada büyür, tuş sesi **çınlamalı / boşluklu
(hollow, pingy)** çıkar. Aynı anahtar ağzına kadar dolu bir gövdede çok daha
"tok" duyulur — fark anahtardan değil, kovuktan gelir.

**Çözüm: kovuğun tabanına sünger.**

**Malzeme (biri yeterli):**

| Malzeme | Kalınlık | Not |
|---|---|---|
| **Poron / PORON benzeri poliüretan** | **3 mm** | En iyi sonuç, kendinden yapışkanlı bulunur. |
| **EVA köpük** (mat / taban altlığı) | **3 mm** | Ucuz, makasla kesilir, iş görür. |
| **Kaymaz mutfak dolabı altlığı** (PVC/EVA ağ köpük) | ~2–3 mm | En ucuz yol; makasla kesilir, çift taraflı ince bantla yapıştırılır. |

**Nereye yapıştırılır:** kasanın **taban iç yüzeyine** (Z = 2.50 düzlemi),
yani plakaya değil. Yapıştırmadan önce tabanı izopropil alkolle sil.

**Ne kadar alan doldurulabilir — hesap:**

```
  İç boşluk taban alanı      82.20 × 63.15 = 5190.9 mm²  (51.9 cm²)
  − DevKit yatağı            63.00 × 25.50 = 1606.5 mm²  (16.1 cm²)
  ────────────────────────────────────────────────────────────────
  = Sünger için kalan alan                   3584.4 mm²  (35.8 cm²)
  − 4 köşe vida kulesinin kovuğa taşan kısmı  ≈ 120 mm²
  ────────────────────────────────────────────────────────────────
  ≈ 3460 mm²  ≈  34 cm²   kullanılabilir taban
```

Bu 34 cm² tek parça değildir; DevKit yatağı (X 22.20–85.20, Y 30.00–55.50)
kovuğu **üç ayrı şeride** böler:

| Bölge | Sınırlar (plaka orijinine göre) | Ölçü | Alan |
|---|---|---:|---:|
| **Ön şerit** (kullanıcıya yakın) | X 3.00–85.20, Y 3.00–30.00 | 82.20 × 27.00 | 22.2 cm² |
| **Arka şerit** | X 3.00–85.20, Y 55.50–66.15 | 82.20 × 10.65 | 8.8 cm² |
| **Sol şerit** (DevKit'in solu) | X 3.00–22.20, Y 30.00–55.50 | 19.20 × 25.50 | 4.9 cm² |

**Pratik kesim ölçüleri** (her kenardan ~1 mm pay bırakılmıştır):

| Parça | Kes | Not |
|---|---|---|
| Ön parça | **80 × 25 mm** | İki ön köşesinden **8 × 8 mm** kare çentik kes — vida kuleleri (⌀7.60) oraya gelir. |
| Arka parça | **80 × 9 mm** | Aynı şekilde iki köşesinden 8 × 8 mm çentik. |
| Sol parça | **18 × 24 mm** | Çentik gerekmez. |

Toplam kaplanan alan ≈ 2000 + 720 + 432 − 256 (çentikler) ≈ **2900 mm²
≈ 29 cm²**, yani kullanılabilir tabanın **~%85'i**. Bu, çınlamayı kesmek
için fazlasıyla yeterlidir; kalan %15'i doldurmaya çalışıp kabloyu sıkıştırma.

**Yükseklik bütçesi — sünger neye DEĞMEMELİ:**

```
   İç yükseklik (plaka altı → taban içi)                18.00 mm
   − Anahtar gövdesinin plaka altında kalan kısmı       ~6.60 mm  (tipik)
   − Lehim topu + tel bükümü                            ~2.40 mm  (tipik)
   ──────────────────────────────────────────────────────────────
   = Anahtarın/lehimin altında kalan serbest yükseklik   ~9.00 mm

   3 mm sünger konursa:  9.00 − 3.00 = 6.00 mm hava kalır   ✔ rahat
   6 mm sünger konursa:  9.00 − 6.00 = 3.00 mm hava kalır   ⚠ üst sınır
```

> 🔴 **Sünger anahtarın gövdesine ve lehim uçlarına DEĞMEMELİDİR.** Değerse
> üç şey olur: (a) plaka yukarı doğru itilir ve vidalar sıkıldığında ortadan
> kabarır, (b) sünger lehim uçlarına sürtüp izolasyonu zamanla aşındırır,
> (c) anahtarın alt kapağı sürekli bastırıldığı için his değişir.
> **Önerilen kalınlık 3 mm'dir; 6 mm'yi hiçbir yerde geçme.**

> **DevKit ve kablo güzergâhı boş kalır.** DevKit yatağının (X 22.20–85.20,
> Y 30.00–55.50) altına **sünger koyma** — kart 4.00 mm'lik pedlerin üstünde
> durur ve alt yüzü Z = 6.50'dedir; altına sünger girerse kart yükselir ve
> USB-C soketi kasadaki açıklıkla hizasını kaybeder (bkz. madde 55).
> Aynı şekilde tel demetinin geçtiği koridoru da açık bırak; sünger telin
> üstüne bindirilirse kapak kapanmaz.

**Ek önlemler (gerekiyorsa, sırayla dene):**

1. **Yan duvarlara 2 mm keçe.** Ön ve arka iç duvarlara ince kendinden
   yapışkanlı keçe şerit yapıştır. Paralel duvarlar arası yansımayı kırar.
   Sol/sağ duvarlara gerek yok (oralarda zaten kule ve DevKit var).
2. **Silikon ayaklar zorunludur.** ⌀8 × 2–3 mm silikon ayak, gövdenin
   titreşimini masaya iletmeyi keser — sesin "masadan gelen" kalın kısmını
   büyük oranda yok eder. Sert plastik ayak veya çıplak taban bunun tam
   tersini yapar: masa rezonans tablası olur.
3. **Vidaları eşit sık.** Bir köşesi boşta kalan plaka her basışta hafifçe
   oynar ve metalik bir "tık-tak" ekler (bkz. ADIM 14.3, çapraz sıkma).

> **Beklenti yönetimi:** Bunların hiçbiri MX Blue'yu **sessiz** yapmaz —
> tık sesi anahtarın **içindeki** click jacket'ten gelir ve kasadan
> bağımsızdır. Sünger, sesin **çınlamalı/boşluklu** kısmını alır; geriye
> temiz ve tok bir "tık" kalır. Sessizlik istiyorsan çözüm sünger değil,
> farklı bir anahtardır.

---

*ExtraKeyboard MK1 · HW_REV = MK1 · Bu doküman `docs/00-CEKIRDEK-SPEC.md` v3.0.0 ile uyumludur.*
