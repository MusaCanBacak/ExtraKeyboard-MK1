# Basit Yapım Kılavuzu — 3D Baskı Gövde + Plaka, Doğrudan Kablolama

> Yapmak için bu dosya yeter. PCB tasarımı yok, çizim de gerekmez: baskı dosyaları
> hazır, [`mechanical/stl/`](../mechanical/stl/) klasöründe.
> Diğer `docs/` dosyaları derinlik/referans içindir. Bazıları projenin ilk tasarımını
> (11 tuş, WS2812B LED) anlatır; çelişkide bu dosya ve
> [`PIN-HARITASI.md`](../PIN-HARITASI.md) geçerlidir.
> **Montaj sırasında hızlı bakış: [EK A — Bağlantı Haritası](#ek-a--bağlantı-haritası-hızlı-başvuru)** (en altta).

---

## 1. Tasarım: eğimli gövde + üst plaka

İki baskı parçası var: **gövde** (önden arkaya yükselen bir kama) ve onun üstüne
oturan **üst plaka**. Anahtarlar plakaya takılır. ESP32 DevKit, gövdenin arka-sağ
köşesindeki **cebe** oturur. Delikli kart katmanı yoktur; teller doğrudan DevKit'e
gider. Plaka gövdeye **4 köşe vidasıyla** tutturulur.

Aynı gövdeye iki plaka takılabilir:

| Plaka | Tuş | Enkoder | LED | Baskı dosyası |
|---|---|---|---|---|
| **Klavye** | 12 (4 × 3) | 1 (arka şeritte) | 3 | `ust-plaka-klavye.stl` |
| **Numpad** | 16 (4 × 4) | — | 2 | `ust-plaka-numpad.stl` |

**Üstten** (klavye, kullanıcı aşağıda):

```
            ▲ ARKA — yüksek kenar (33 mm)
   ┌──────────────────────────────────────────┐
   │     ●      ●      ●           ◎          │  ← arka şerit: LED'ler + enkoder
   │   LED1   LED2   LED3         ENC         │     (altında ESP32 cebi, sağda)
   │                                          │
   │    [Tuş9 ]  [Tuş10]   [COMBO]  [ OS  ]   │
   │    [Tuş5 ]  [Tuş6 ]   [Tuş7 ]  [Tuş8 ]   │  ← 4 × 3 tuş, adım 19.05 mm
   │    [Tuş1 ]  [Tuş2 ]   [Tuş3 ]  [Tuş4 ]   │
   └──────────────────────────────────────────┘
            ▼ ÖN — alçak kenar (19 mm)
     plaka 87.85 × 99.77 mm · gövde dışı 94.20 × 105.15 mm
```

**Yandan** (ön solda):

```
                                              ARKA 33 mm
                                    ╱▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔╗
   ÜST PLAKA 3 mm, 8° ─────╱▔▔▔▔▔▔▔                 ║
              ╱▔▔▔▔▔▔▔ ┃   ┃   ┃            ◎ ●    ║  ← enkoder + LED'ler arka şeritte
   ╔════▔▔▔ anahtar gövdeleri          ┌─────────┐  ║
   ║                                   │  ESP32  │  ║  ← ESP32 cebi (8 mm duvar)
   ╚═══════════════════════════════════╧═════════╧══╝
   ÖN 19 mm      ▲ taban düz (2.5 mm), masaya oturur ▲
   └──────────────── gövde dış derinliği 105.15 ──────┘
```

**Neden bu yapı:**
- Anahtarlar plakada, böylece tuş adımı **19.05 mm standart** kalır ve tuş başlıkları normal görünür.
- **Bacak bükmek, delikli kart, header yok.** Teller anahtardan doğrudan DevKit pinine gider.
- LED'ler ve enkoder, ESP32'nin hemen üstündeki arka şeritte. Teller kısa kalır.
- Plaka 4 vidayla sökülebilir; kablolamaya her zaman geri dönülebilir.

---

## 2. Neden anahtarlar delikli karta oturmuyor

MX anahtarının iki lehim bacağı arası **X'te 6.35 mm = 2.5 delik**:

```
        bacak 1              bacak 2
           ●─────── 6.35 mm ────●
   delik   ●    ●    ●    ●    ●     ← 2.54 mm grid
           ✔                    ✘    (iki deliğin ortasına düşer)
```

Biri deliğe denk gelirse diğeri her zaman ortada kalır. Ayrıca tuş adımı
**19.05 mm = 7.5 delik**, o da grid'e oturmaz. İkisini birden çözmenin tek yolu
adımı 20.32 mm'ye (8 delik) çıkarıp **her anahtarın bir bacağını bükmek** olurdu.
Bu yüzden anahtarlar plakaya takılır ve her anahtarın teli doğrudan DevKit'e çekilir.

---

## 3. Ölçüler ve baskı dosyaları

| Dosya | Parça |
|---|---|
| [`govde.stl`](../mechanical/stl/govde.stl) | Gövde — klavye ve numpad için aynı |
| [`ust-plaka-klavye.stl`](../mechanical/stl/ust-plaka-klavye.stl) | Klavye üst plakası: 12 tuş + enkoder + 3 LED |
| [`ust-plaka-numpad.stl`](../mechanical/stl/ust-plaka-numpad.stl) | Numpad üst plakası: 16 tuş + 2 LED |
| [`enkoder-dugmesi.stl`](../mechanical/stl/enkoder-dugmesi.stl) | Enkoder düğmesi |

Tuş başlığı (keycap) dosyası yoktur: MX uyumlu **herhangi bir** tuş başlığı olur.
Aşağıdaki ölçüler bu modellerden okunmuştur; kendin çizeceksen buradan al.
(`mechanical/` klasöründeki `.scad` dosyaları ve `plate.dxf`, ilk 11 tuşlu tasarıma aittir.)

### 3.1 Üst plaka

| Ölçü | Değer |
|---|---|
| Dış ölçü | **87.85 × 99.77 mm**, köşeler keskin |
| Kalınlık | **3.00 mm** |
| Eğim (takılıyken) | **8°**, gövdenin üst kenarıyla aynı |
| Anahtar deliği | **14.15 × 14.15 mm** kare (14.00 + FDM payı). Klavyede 12, numpadde 16 |
| Tuş adımı | **19.05 mm** |
| LED penceresi | **⌀3.20 mm** (3 mm LED). Klavyede 3, numpadde 2 |
| Enkoder deliği (klavye) | **⌀7.20 mm**. İç yüzde, deliğin çevresinde **11.90 × 12.50 mm, 1.57 mm derin** cep var; EC11 gövdesi buna oturur |
| Işık bölmesi | İç yüzde, LED pencerelerinin çevresinde **5.00 mm** yüksek ince duvarlar. Her LED yalnızca kendi penceresinden görünür |
| Vida deliği | **⌀2.00 mm, 4 adet**, köşelerde, kenarlardan 3.00 mm |

Plakanın **dış yüzü düzdür**. Işık bölmeleri ve enkoder cebi iç yüzdedir (gövdeye bakan taraf).

**Delik merkezleri (klavye)** — orijin **arka-sol köşe** (üstten bakınca), X sağa,
Y öne doğru, plaka yüzeyi boyunca (mm):

| | Sütun 1 | Sütun 2 | Sütun 3 | Sütun 4 |
|---|---|---|---|---|
| **Arka sıra** | Tuş 9 `15.35, 45.84` | Tuş 10 `34.40, 45.84` | COMBO `53.45, 45.84` | OS `72.50, 45.84` |
| **Orta sıra** | Tuş 5 `15.35, 64.89` | Tuş 6 `34.40, 64.89` | Tuş 7 `53.45, 64.89` | Tuş 8 `72.50, 64.89` |
| **Ön sıra** | Tuş 1 `15.35, 83.94` | Tuş 2 `34.40, 83.94` | Tuş 3 `53.45, 83.94` | Tuş 4 `72.50, 83.94` |

- LED1 / LED2 / LED3 (soldan): `9.82, 10.31` · `24.82, 10.31` · `39.82, 10.31` (aralık 15.00)
- Enkoder: `65.00, 16.00`
- Vida delikleri: `3.00, 3.00` · `84.85, 3.00` · `3.00, 96.77` · `84.85, 96.77`

**Numpad plakası:** dış ölçü, kalınlık, sütunlar ve vida delikleri aynıdır. 4 sıra
vardır; sıra merkezleri Y = `26.79` · `45.84` · `64.89` · `83.94`. LED'ler:
`14.00, 9.00` · `29.00, 9.00`. Enkoder yoktur. Tuş düzeni (arka sıradan öne):
`7 8 9 /` · `4 5 6 *` · `1 2 3 −` · `0 . ⏎ +`.

### 3.2 Gövde — eğimli kama

| Ölçü | Değer |
|---|---|
| Dış ölçü (üstten) | **105.15 (derinlik) × 94.20 (genişlik) mm**, dikey köşeler R2 |
| **Ön duvar yüksekliği** | **19.00 mm** |
| **Arka duvar yüksekliği** | **33.00 mm** |
| **Üst kenar eğimi** | **≈ 8°** (`atan(14 / 99.15) = 8.04°`), plaka eğimiyle aynı |
| Taban | **Düz**, masaya tam oturur |
| Duvar / taban kalınlığı | **3.00 / 2.50 mm** |
| İç açıklık | **99.15 × 88.20 mm** |
| Plaka basamağı | İç çevre boyunca **1.50 mm** genişlik, duvar üst kenarının **3.00 mm** altında. Plaka buna oturur ve üst yüzü duvarla **aynı hizada** kalır |
| Köşe takozu ×4 | **⌀2.00 mm** pilot delik, ~5 mm derin, plakaya dik (8° eğik). İç duvarlardan 3.00 mm içeride, plakanın vida delikleriyle aynı eksende |
| ESP32 cebi | Arka-sağ köşede, tabandan **8.00 mm** yükselen duvarlarla çevrili. İç ölçü **28.30 mm** (derinlik yönünde) × **57.65 mm** (sağ iç duvardan sola doğru). Sol ucunda **18.60 × 6.15 mm** uzantı. Cebin ön iç kenarı arka dış yüzden **31.30 mm** içeride |
| USB açıklığı | **Sağ yan duvarda**, **14.47 × 9.00 mm** oval (yarım daire uçlu). Merkezi dış tabandan **13.80**, arka dış yüzden **23.58 mm**. Kenarlar: yatay 16.34↔30.81, dikey 9.30↔18.30 |

Plakanın altındaki serbest yükseklik ön kenarda **≈ 13.5 mm**, arka kenarda
**≈ 27.5 mm**. Öndeki boşluk, plakanın altına sarkan anahtar gövdeleri, bacakları ve
teller için yeter. Arkadaki yüksek bölge ESP32, enkoder ve LED'ler içindir.

### 3.3 Enkoder düğmesi

| Ölçü | Değer |
|---|---|
| Kütük | **⌀20.00 × 7.50 mm**; üst kapak 1.50, etek duvarı 1.50 (iç ⌀17.00) |
| Mil deliği | **⌀6.19 mm**, yuvarlak (D düzlüğü yok), **5.30 mm** derin; ⌀10.00 göbekte. Göbek etek kenarından 0.70 mm içeride biter |

Hazır bir 6 mm enkoder düğmesi de olur.

### 3.4 3D baskı notları

- **PETG önerilir**; sıcakta deforme olmaz. PLA da olur.
- **Gövdeyi tabanı tablaya gelecek şekilde bas.**
- **Plakayı düz dış yüzü tablaya gelecek şekilde bas.** Işık bölmeleri ve enkoder
  cebi yukarıda kalır.
- Anahtar delikleri modelde zaten **14.15 mm**: FDM'de delikler ~0.15 mm küçük çıkar.
  **Önce tek delikli bir test parçası bas** ve anahtarı dene. 10 dakika, 12 delikli
  hatalı baskıdan kurtarır.
- ⌀2.00 deliklerde: M2 vida gövdedeki pilot deliğe doğrudan diş açar. Plakadaki delik
  dar gelirse **2.2–2.4 mm matkapla** genişlet.

---

## 4. Malzeme

| Parça | Klavye | Numpad | Not |
|---|---|---|---|
| ESP32-S3-DevKitC-1 | 1 | 1 | **N16R8 önerilir**; N8R2 (8 MB flash + 2 MB PSRAM) da olur. Native "USB" soketi şart |
| MX uyumlu anahtar (ör. Cherry MX Blue) | 12 | 16 | 3 pinli plate-mount |
| Tuş başlığı (keycap) 1U | 12 | 16 | MX uyumlu herhangi biri |
| EC11 enkoder | 1 | — | Butonlu, M7 burç, 6 mm mil |
| Düz LED 3 mm (tek renk) | 3 | 2 | Renk serbest |
| Direnç 330 Ω | 3 | 2 | Her LED'e bir tane |
| Direnç 10 kΩ | 2 | — | Enkoder RC filtresi |
| Kondansatör 100 nF | 2 | — | Enkoder RC filtresi |
| Küçük delikli kart (~20 × 30 mm) | 1 | — | RC filtresini taşır (önerilir) |
| M2 vida, 6–8 mm | 4 | 4 | Plakayı köşe takozlarına tutar |
| Tel 26 AWG | ~2 m | ~2 m | **Çok damarlı**; tek damarlı tel anahtar dibinde kırılır |
| Isıyla daralan makaron | biraz | biraz | LED dirençleri ve tel eklerini yalıtmak için |
| Silikon ayak ⌀8 mm | 4 | 4 | |
| Sünger (poron/EVA) 3 mm | 1 | 1 | Önerilir. Blue anahtarın boş kovukta çınlamasını azaltır |
| USB **veri** kablosu | 1 | 1 | Şarj-only kablo çalışmaz |
| Baskı | gövde, klavye plakası, düğme | gövde, numpad plakası | [`mechanical/stl/`](../mechanical/stl/) |

Fiyatlı liste: [`hardware/BOM.csv`](../hardware/BOM.csv).

---

## 5. Kablolama

Klavyede toplam **18 sinyal teli** (12 tuş + enkoder 3 + LED 3), **1 ortak GND
zinciri** ve enkoder filtresi için bir **3V3** teli var. Hepsi bu.

### 5.1 Anahtarlar

Her anahtarın **bir bacağı ortak GND**, **diğeri kendi GPIO'suna**. Matris ve diyot yok.

| Konum (üstten) | Sütun 1 | Sütun 2 | Sütun 3 | Sütun 4 |
|---|---|---|---|---|
| **Arka sıra** | Tuş 9 → **GPIO10** | Tuş 10 → **GPIO9** | COMBO → **GPIO8** | OS → **GPIO21** |
| **Orta sıra** | Tuş 5 → **GPIO15** | Tuş 6 → **GPIO16** | Tuş 7 → **GPIO17** | Tuş 8 → **GPIO18** |
| **Ön sıra** | Tuş 1 → **GPIO4** | Tuş 2 → **GPIO5** | Tuş 3 → **GPIO6** | Tuş 4 → **GPIO7** |

Bu eşleme hazır firmware imajlarının (varsayılan derleme) eşlemesidir. Üst sıra
karışık çıkarsa kabloyu sökme: rol sırası `firmware/src/keys.cpp` içindeki
`KEY_PINS` dizisiyle değişir ([PIN-HARITASI.md](../PIN-HARITASI.md) bölüm 3).

**GND papatya dizimi:** Tek bir teli kes, izolesini 12 noktada (numpadde 16) ortadan
sıyır, her anahtarın GND bacağına sırayla lehimle, ucunu DevKit'in GND pinine götür.
Enkoderin C ve SW-2 bacakları ile LED katotları da bu zincire bağlanır.

**Numpad** (16 tuş, enkoder yok) — GPIO → tuş, arka sıradan öne:

```
   arka : 7 → GPIO11   8 → GPIO12   9 → GPIO13   / → GPIO14
          4 → GPIO8    5 → GPIO9    6 → GPIO10   * → GPIO21
          1 → GPIO15   2 → GPIO16   3 → GPIO17   − → GPIO18
   ön   : 0 → GPIO4    . → GPIO5    ⏎ → GPIO6    + → GPIO7
```

Numpad LED'leri: GPIO42 Windows, GPIO41 macOS. Ayrıntı:
[`firmware-numpad/NUMPAD-NOTLAR.md`](../firmware-numpad/NUMPAD-NOTLAR.md).

### 5.2 Enkoder (EC11)

| EC11 pini | Nereye |
|---|---|
| A | GPIO11 (+ RC filtresi) |
| C (orta) | GND |
| B | GPIO12 (+ RC filtresi) |
| SW bacak 1 | GPIO13 |
| SW bacak 2 | GND |

**RC filtresi**, A ve B için ayrı ayrı, küçük delikli kart üzerinde:

```
   3V3 ──[10 kΩ]──┬── GPIO11 (veya 12)
                  ├── EC11 A (veya B)
                 ═╪═ 100 nF
                 GND
```

> **Zorunlu.** Enkoderde yazılım debounce yetmez; iki kanalın faz ilişkisi
> bozulunca sayaç ileri geri zıplar ve ses kontrolü kullanılamaz olur.

### 5.3 LED'ler

3 adet **düz (tek renk) LED**, her biri kendi pininde ve kendi direnciyle:

```
   GPIO14 ──[330 Ω]──► LED1 anot (uzun bacak) ── katot ──┐   Windows
   GPIO42 ──[330 Ω]──► LED2 anot              ── katot ──┤   macOS
   GPIO41 ──[330 Ω]──► LED3 anot              ── katot ──┘   COMBO
                                                         GND
```

> Uzun bacak (anot) dirence, kısa bacak (katot) GND'ye. Ters takılan LED
> yanmaz ama zarar da görmez; çevirip tekrar dene. Direnci LED bacağına lehimleyip
> makaronla kapatmak yeterlidir.
>
> Projenin ilk sürümü 3 × WS2812B kullanıyordu (diyot + 1000 µF gerektiriyordu).
> Güncel firmware düz LED sürer; o devre artık kullanılmaz.

---

## 6. Yapım sırası

1. **Parçaları bas** (§3.4). Önce tek delikli test parçasıyla anahtarın oturuşunu dene.
2. **Anahtarları plakaya tak** (dış yüzden bastırarak). Hepsinin dik olduğunu kontrol et.
   ⚠️ Blue anahtar **tam oturmadan da tık sesi çıkarır**. Sesle değil, yandan
   bakarak kontrol et.
3. **Enkoderi** plakanın iç yüzünden cebine oturt, burcunu delikten geçir, dış yüzden
   somunla sık.
4. **LED'leri** iç yüzden, ışık bölmelerinin içinden pencerelere yerleştir (LED1
   soldaki pencere). Yerinde tutmak için bir damla sıcak silikon yeter.
5. **GND zincirini** lehimle: tek tel, 12 anahtar + enkoder C ve SW-2 + 3 LED katodu.
6. **RC filtresini** küçük delikli karta kur (§5.2), **LED dirençlerini** anot
   bacaklarına lehimleyip makaronla kapat.
7. **Sinyal tellerini** anahtarlardan, enkoderden ve LED dirençlerinden DevKit
   pinlerine çek (EK A.2). Renk kodu kullan; plakanın açılıp kapanabilmesi için
   telleri biraz uzun bırak.
8. **DevKit'i cebine yerleştir**: kartın **"USB"** yazan soketi sağ duvardaki
   açıklığa, açıklığın ortasına gelsin ("UART" yazan değil).
9. **GÜÇ VERMEDEN ÖNCE:** multimetreyle 5V ↔ GND ve 3V3 ↔ GND arasında kısa devre
   olmadığını kontrol et. Kısa varsa USB portunu yakarsın.
10. **Firmware'i yükle** — hazır imaj ve yükleyiciyle: kurulum paketinde
    `2-FIRMWARE/`, depoda [README → 4. Firmware](../README.md#4-firmware).
    Yükleyici modülü kendisi tanır. Kaynaktan derlemek için:
    [04-FIRMWARE-KURULUM.md](04-FIRMWARE-KURULUM.md); en kritik ayar
    `ARDUINO_USB_MODE=0`, yoksa HID hiç çalışmaz.
11. **Test et:** 12 tuş, enkoder iki yön + basış, 3 LED, combo, OS geçişi. (Numpad:
    16 tuş; Windows/macOS geçişi "0" basılıyken Enter.)
12. **Kapat:** süngeri tabana koy (DevKit'e ve tellere baskı yapmasın), plakayı
    basamağa oturt, **4 köşeden M2 vidalarla** sabitle, ayakları yapıştır.

---

## 7. Test ederken

| Belirti | Sebep | Çözüm |
|---|---|---|
| Tek basışta eylem **iki kez** çalışıyor | Anahtar sıçraması | `firmware/src/config.h` → `EK_KEY_DEBOUNCE_MS` 8 → 12 |
| Bir tuş hiç çalışmıyor | Lehim veya yanlış GPIO | Multimetre ile anahtar bacağı ↔ DevKit pini süreklilik |
| Üst sıra tuşları yer değiştirmiş | Kablolama varsayılandan farklı | `keys.cpp` → `KEY_PINS` sırası ([PIN-HARITASI.md](../PIN-HARITASI.md) bölüm 3) |
| Enkoder ileri geri zıplıyor | RC filtresi yok/yanlış | 10 kΩ + 100 nF kontrol |
| Enkoder ters yönde | A/B ters | A ve B tellerini yer değiştir |
| LED yanmıyor | Ters takılı ya da yanlış GPIO | LED'i çevir; GPIO14 / 42 / 41 kontrol |
| İki LED birlikte parlıyor | Işık komşu pencereden sızıyor | LED'i ışık bölmesinin içine tam oturt |
| Cihaz USB'de görünmüyor | Kablo "UART" soketinde ya da şarj-only kablo | "USB" soketi ve veri kablosu kullan |
| Plaka basamağa tam oturmuyor | Teller veya LED bacakları sıkışıyor | Telleri kenarlara topla, LED bacaklarını kısalt |
| Vida plakadan geçmiyor | FDM deliği küçük basmış | Plakadaki deliği 2.2–2.4 mm matkapla aç |
| Cihaz masada kayıyor | Ayak yok | 4 silikon ayağı düz tabana yapıştır |
| Ses çok "boşluklu" çınlıyor | Boş kovuk rezonansı | Tabana sünger |

Daha uzun liste: [08-SORUN-GIDERME.md](08-SORUN-GIDERME.md)

---

## 8. Sonra

En kolayı: Finder'da **`ExtraKeyboard-Baslat.command`** dosyasına çift tıkla
(ilk seferde sağ tık → Aç). Terminalden istersen:

```bash
cd ~/ExtraKeyboard-MK1 && .venv/bin/python run_app.py
```

Cihazsız her şeyin yerinde olduğunu doğrulamak için:

```bash
.venv/bin/python tools/selfcheck.py --ui
```

Kullanım: [05-UYGULAMA-KULLANIMI.md](05-UYGULAMA-KULLANIMI.md) ·
Dikkat edilecekler: [06-ONEMLI-NOTLAR.md](06-ONEMLI-NOTLAR.md)

---

## EK A — Bağlantı Haritası (hızlı başvuru)

> Anlatım yok. Montajda ve baskı öncesinde açık duracak sayfa bu.
>
> ### 📏 TÜM ÖLÇÜLER MİLİMETRE (mm) — cm DEĞİL
> `87.85 × 99.77` = 8.8 × 10 cm demektir. Açılar derece (°),
> elektronik değerler kendi birimiyle (Ω, nF) yazılıdır.

### A.1 Mekanik — parçalar

**Zihninde canlandır:** bardak altlığından biraz büyük bir taban (dıştan 94 × 105 mm),
öne doğru alçalan bir kama: arka duvar 33, ön duvar 19 mm, sırt eğimi 8°. Üstte düz
bir plaka: önde 4 × 3 tuş, arkadaki şeritte 3 LED ve enkoder.

| Parça | Ana ölçüler (mm) |
|---|---|
| Gövde `govde.stl` | Dış **94.20 × 105.15**, ön **19.00** → arka **33.00**, duvar 3.00, taban 2.50. Plaka basamağı 1.50 genişlik, üst kenardan 3.00 aşağıda. 4 köşe takozu ⌀2.00 pilot delik. Arka-sağda ESP32 cebi (8.00 yüksek duvar). Sağ duvarda USB açıklığı **14.47 × 9.00**, merkez tabandan 13.80, arka dış yüzden 23.58 |
| Klavye plakası `ust-plaka-klavye.stl` | **87.85 × 99.77 × 3.00**, 12 × **14.15** kare delik, adım **19.05**. İlk tuş `15.35, 45.84` (arka-sol köşeden). Enkoder ⌀7.20 `65.00, 16.00` + iç yüzde 11.90 × 12.50 × 1.57 cep. LED ⌀3.20 × 3, Y = 10.31, X = 9.82 / 24.82 / 39.82. İç yüzde 5.00 yüksek ışık bölmesi. Vida deliği ⌀2.00 × 4, kenarlardan 3.00 |
| Numpad plakası `ust-plaka-numpad.stl` | Klavye plakasıyla aynı dış ölçü ve vida delikleri. 16 delik (4 × 4), ilk tuş `15.35, 26.79`. LED ⌀3.20 × 2: `14.00, 9.00` ve `29.00, 9.00` |
| Enkoder düğmesi `enkoder-dugmesi.stl` | **⌀20.00 × 7.50**, mil deliği ⌀6.19 yuvarlak, 5.30 derin |

### A.2 Elektronik — bağlantılar (klavye)

Anahtar bacakları yönsüzdür: biri GPIO'ya, diğeri GND zincirine; hangisi olduğu fark
etmez. EC11'in 3'lü tarafı **A–C–B** (C ortada), 2'li tarafı SW.

| Nereden | Nereye |
|---|---|
| Tuş 1 / Tuş 2 / Tuş 3 / Tuş 4 (ön sıra) | **GPIO4 / GPIO5 / GPIO6 / GPIO7** |
| Tuş 5 / Tuş 6 / Tuş 7 / Tuş 8 (orta sıra) | **GPIO15 / GPIO16 / GPIO17 / GPIO18** |
| Tuş 9 / Tuş 10 / COMBO / OS (arka sıra) | **GPIO10 / GPIO9 / GPIO8 / GPIO21** |
| Her anahtarın 2. bacağı | **GND zinciri** (tek ortak tel) → DevKit GND |
| ENC A | **RC-A düğümü** → **GPIO11** |
| ENC B | **RC-B düğümü** → **GPIO12** |
| ENC C (orta) | GND zinciri |
| ENC SW 1. pin | **GPIO13** |
| ENC SW 2. pin | GND zinciri |
| **GPIO14** | → 330 Ω → **LED1** anot (Windows, soldaki pencere) |
| **GPIO42** | → 330 Ω → **LED2** anot (macOS, ortadaki pencere) |
| **GPIO41** | → 330 Ω → **LED3** anot (COMBO, sağdaki pencere) |
| LED1·2·3 katot | GND zinciri |
| DevKit **3V3** | 10 kΩ'ların üst ucu (RC filtresi) |
| DevKit'in **"USB" serigrafili soketi** (native) | Sağ duvardaki açıklıktan dışarı. "UART" yazan sokete TAKMA, klavye çalışmaz. Fiş tipi karta göre USB-C (klon) veya Micro-B (resmî Espressif) |

Numpad bağlantıları: §5.1 ve [PIN-HARITASI.md](../PIN-HARITASI.md) bölüm 2.

### A.3 Elektronik — küçük parçalar

| Parça | Değer / tip | Bağlantısı |
|---|---|---|
| Direnç ×2 | **10 kΩ** | 3V3 → RC-A ve RC-B düğümleri |
| Kondansatör ×2 | **100 nF** | RC-A ve RC-B düğümleri → GND |
| RC düğümü (×2) | — | Düğümde üç uç birleşir: 10 kΩ alt ucu + ENC teli + GPIO (11 veya 12) |
| Direnç ×3 | **330 Ω** | GPIO14 / 42 / 41 ile LED anotları arasında, LED bacağına lehimli + makaron |

> DevKit üzerindeki pin adları karta basılıdır; GPIO numarasını **yazısından**
> doğrula, konumundan sayma.
