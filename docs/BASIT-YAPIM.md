# Basit Yapım Kılavuzu — 3 Katmanlı, Delikli Kart + 3D Baskı

> Yapmak için bu dosya yeter. PCB tasarımı yok, karmaşık CAD yok.
> Diğer `docs/` dosyaları derinlik/referans içindir.
> **Montaj sırasında hızlı bakış: [EK A — Bağlantı Haritası](#ek-a--bağlantı-haritası-hızlı-başvuru)** (en altta).

---

## 1. Tasarım: 3 katman, tek kutu

Anahtarlar delikli karta oturmadığı için (sebebi §2) yapı **katmanlı** olur:
üstte anahtarları tutan plaka, altta elektroniğin olduğu kart, hepsi tek kutuda.
Gövde **önden arkaya yükselen bir kama** (7.6° eğim) ve tuş alanının **arkasında
30 mm'lik bir elektronik bölmesi** var — ESP32 oraya giriyor.

**Üstten** (kullanıcı aşağıda):

```
   ┌──────────────────────────────┐  ▲ ARKA — yüksek kenar (29 mm)
   │  ● ● ●   ELEKTRONİK BÖLMESİ  │  30.00   ← anahtar YOK, ESP32 burada
   ├──────────────────────────────┤
   │   K1   K2   K3   ⊙ENC        │
   │   K4   K5   K6    K10        │  69.15   ← tuş alanı
   │   K7   K8   K9    K11        │
   └──────────────────────────────┘  ▼ ÖN — alçak kenar (15 mm)
     plaka 88.20 mm · gövde dışı 94.20 mm
```

**Yandan** (ön solda):

```
                                              ARKA 29 mm
                                    ╱▔▔▔▔▔▔▔▔▔▔▔╗
   ÜST PLAKA ────╱▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔            ║
       ╱▔▔▔▔▔▔▔▔ │   │   │   │                  ║
   ╔══▔ ▼   ▼    ▼   ▼   ▼   ▼    ┌────────────┐║
   ║  anahtar gövdeleri (9 mm)    │[ESP32]     │║  ← BÖLME
   ║        ┌─────────────────────┴────────────┤║     tam yükseklik
   ║        │  delikli kart 80 × 45            │║
   ╚════════╧══════════════════════════════════╝╝
   ÖN 15 mm      ▲ taban düz, masaya oturur ▲
   └── plaka 99.15 · gövde dış derinliği 105.15 ──┘
```

**Neden bu yapı doğru:**
- Anahtarlar plakada → tuş adımı **19.05 mm standart** kalır, keycap'ler normal görünür
- **Bacak bükmek yok**, delik hizalama derdi yok
- **Bölme sayesinde ESP32 sıkışmıyor**: anahtar altında yalnızca 9.2 mm var,
  DevKit ise 11.9 mm istiyor — bölmede 20.6–24.6 mm bulunca sorun kalmıyor
- Kartın öne uzanan kısmı yatık dirençleri taşır, boşa gitmez
- Delikli kart mekanik yük almaz, DevKit sökülebilir kalır

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
Katmanlı yapı bu işin tamamını gereksiz kılıyor.

---

## 3. Ölçüler (çizimi kendin yapacaksın)

### 3.1 Üst plaka

| Ölçü | Değer |
|---|---|
| Dış ölçü | **88.20 × 99.15 mm** |
| — tuş alanı (ön) | 69.15 mm |
| — elektronik bölmesi (arka) | **30.00 mm**, üstünde anahtar yok |
| Kalınlık | **1.50 mm** ← MX klipsinin tutması için pazarlıksız |
| Anahtar deliği | **14.00 × 14.00 mm** kare, 11 adet |
| Enkoder deliği | **⌀7.20 mm** + 2 pim deliği ⌀1.50 |
| LED penceresi | **⌀3.00 mm**, 3 adet |
| Kanca çentiği | **9.0 × 1.2 mm**, kenarlarda **8 adet** — vida YOK, plaka çıtlayarak oturur |

**Delik merkezleri** — orijin **sol üst (arka) köşe**, X sağa, Y öne doğru (mm):

| | Sütun 1 | Sütun 2 | Sütun 3 | Sütun 4 |
|---|---|---|---|---|
| **Satır 1** | K1 `15.53, 45.53` | K2 `34.58, 45.53` | K3 `53.63, 45.53` | **ENC** `72.68, 45.53` |
| **Satır 2** | K4 `15.53, 64.58` | K5 `34.58, 64.58` | K6 `53.63, 64.58` | **K10** `72.68, 64.58` |
| **Satır 3** | K7 `15.53, 83.63` | K8 `34.58, 83.63` | K9 `53.63, 83.63` | **K11** `72.68, 83.63` |

- LED'ler (bölme şeridinde): `36.10, 10.00` · `44.10, 10.00` · `52.10, 10.00`
- Kanca çentikleri (kenar ortası konumları): arka kenarda x = `22` ve `66` · ön kenarda x = `22` ve `66` · sol kenarda y = `25` ve `70` · sağ kenarda y = `32` ve `70` (sağda üstteki kanca USB açıklığıyla çakışmasın diye kaydırıldı). Her çentik kenardan içeri 1.2 mm, genişlik 9.0 mm.

### 3.2 Gövde — eğimli kama

**Yandan profil bir yamuk.** Çizmesi kolay: iki yükseklik ver, açı kendiliğinden çıkar.

| Ölçü | Değer |
|---|---|
| Dış ölçü (üstten) | **94.20 × 105.15 mm** = plaka + 2×3 duvar (duvarlar plakanın DIŞINA eklenir) |
| İç açıklık (plaka yuvası) | **88.60 × 99.55 mm** = plaka 88.20×99.15 + kenar başına 0.2 pay |
| **Ön duvar yüksekliği** | **15.00 mm** |
| **Arka duvar yüksekliği** | **29.00 mm** |
| **Eğim açısı** | **≈ 7.6°** (`atan(14 / 105.15) = 7.58°` — klavye standardı 6–9°) |
| Taban | **Düz**, masaya tam oturur |
| Keycap dahil yükseklik | ön kenarda ~32, en yüksek tuş tepesinde ~40, arka sırtta 29 (tuşsuz şerit) |
| Duvar kalınlığı | 3.00 mm |
| Taban kalınlığı | 2.50 mm |
| USB açıklığı (Type-C) | **13 × 8 mm** (köşe R2), **sağ yan duvarda**; merkez dış tabandan **12.80**, arka dış köşeden **21.0** (kenarlar: yatay 14.5↔27.5, dikey 8.8↔16.8) |

#### Neden arkada bölme var

Anahtar gövdesi plakanın altında **9.0 mm** yer kaplar. ESP32 yığını ise
**11.94 mm** ister — ikisi üst üste 21.94 mm eder ve bu, tuş alanının altına
sığmaz (öne doğru tavan alçalır). Çözüm: **tuş alanının arkasına 30 mm'lik,
üstünde anahtar olmayan bir bölme** koymak. Orada tam iç yükseklik ESP32'nindir.

| Ön dış kenardan | İç boşluk | Anahtar altı serbest | Orada ne var |
|---|---|---|---|
| 3 mm (iç ön duvar) | 11.40 mm | 2.40 mm | sadece anahtarlar + tel |
| 18.7 mm | 13.49 mm | 4.49 mm | en öndeki anahtar sırası |
| 57 mm (kart ön kenarı) | 18.61 mm | **9.61 mm** | yatık dirençler, küçük kondansatörler |
| 72 mm (bölme sınırı) | 20.58 mm | — | **anahtar biter, bölme başlar** |
| 102 mm (iç arka duvar) | **24.60 mm** | — | **ESP32 DevKit + yüksek kondansatör** |

#### Bölmedeki dikey yığın (kasa iç tabanından yukarı)

| Z (mm) | Ne var |
|---|---|
| 0 → 3.0 | Standoff + kablo geçişi |
| 3.0 → 4.6 | Delikli kart (1.6 mm) |
| 4.6 → 7.1 | DevKit header plastiği (2.54 mm) |
| 7.1 → 8.7 | DevKit PCB (1.6 mm) |
| 8.7 → 11.9 | USB-C konnektörü / WROOM modülü (3.2 mm) |

Gereken **12.94 mm** (yığın + 1 mm pay), bölmede mevcut **20.58–24.60 mm** → bol pay.

#### Geçmeli bağlantı (vida yok)

Plaka gövdeye **çıtlayarak** oturur; vida ve heat-set insert kullanılmaz.

```
   duvar kesiti:                ┌── plaka (kenarı 45° pahlı)
                                ▼
   ██ ← duvar üst kenarı   ═════════╗
   ██┐                          ▲   ██
   ██│← kanca dişi 1.0 mm   çentik  ██
   ██┘                              ██
   ██ ← omuz 1.5 mm — tuş basış     ██
   ██    yükünü vida değil BU taşır ██
```

- **Omuz (ledge):** iç çevre boyunca, duvar üst kenarından 1.50 mm aşağıda,
  1.5 mm genişlik. Plaka buna oturur ve üst yüzeyi duvarla **aynı hizada** kalır.
- **8 kanca:** duvara iki dik yarık (1.5 × 12 mm) açıp esneyen dil oluştur;
  dilin ucunda içeri bakan **1.0 mm diş**, girişte 45°, çıkışta 30° pah
  (takması kolay, sökmesi mümkün). Konumlar çentik konumlarıyla aynı.
- **Kanırtma yuvası ×2:** ön duvar üst kenarında, x = `8` ve `80` konumlarında
  8 × 2.5 mm — düz tornavidayla kapağı açmak için.
- **Tolerans:** dişi ilk baskıda **0.8 mm** bas, tek kancalı test parçasıyla dene;
  gevşekse 1.0–1.2'ye çıkar. FDM toleransı baskıdan baskıya değişir.
- Delikli kart için tabana **4 adet 3 mm post** bas (veya çift taraflı bant yeterli).
- Taban düz olduğu için **4 adet düz silikon ayak** yeterli, kama ayak gerekmez.

> **Yerleştirme kuralı:** Yüksek parçalar (ESP32, 1000 µF kondansatör) **bölmeye**;
> yatık dirençler ve küçük kondansatörler kartın öne uzanan kısmına. Anahtarların
> altında yalnızca **9.6 mm** var, 1000 µF oraya sığmaz.

### 3.3 3D baskı notları

- **PETG kullan.** 1.50 mm PLA plaka, klips kuvvetinde çatlar.
- FDM'de delikler ~0.15 mm küçük çıkar → anahtar deliğini **14.15 mm** çiz.
- **Önce tek delikli test parçası bas**, anahtarı dene. 10 dakika, 11 delikli hatalı baskıdan kurtarır.
- **Kama gövdeyi düz tabanı tablaya bakacak şekilde bas.** Duvarlar dikey yükselip
  farklı yüksekliklerde bittiği için **çıkıntı (overhang) yok, destek gerekmez**.
  Eğimli yüzeyi tablaya yatırırsan hem destek gerekir hem üst kenarlar bozulur.

---

## 4. Malzeme

| Parça | Adet | Not |
|---|---|---|
| ESP32-S3-DevKitC-1 | 1 | Native USB şart |
| Cherry MX Blue anahtar | 11 | Elindekiler |
| Keycap 1U | 11 | |
| EC11 enkoder + düğme | 1 | |
| WS2812B LED | 3 | Tek veri hattı |
| Delikli kart | 1 | 7×9 cm alıp **80 × 45 mm**'ye kes, **arka duvara dayalı** monte et |
| Dişi header 2×22 | 1 takım | DevKit sökülebilir kalsın |
| 1N4148 diyot | 1 | **Atlanamaz** (§5.3) |
| Direnç 10 kΩ | 2 | Enkoder filtresi |
| Direnç 330 Ω | 1 | LED veri hattı |
| Kondansatör 100 nF | 2 | Enkoder filtresi |
| Kondansatör 1000 µF | 1 | LED beslemesi |
| Tel 26 AWG | ~2 m | **Çok damarlı** — tek damarlı anahtar dibinde kırılır |
| Silikon ayak ⌀8 mm | 4 | |
| Sünger (poron/EVA) 3 mm | 1 | Blue gürültülü, boş kovuk çınlar |

---

## 5. Kablolama

Toplam **11 sinyal teli + 1 ortak GND zinciri**. Hepsi bu.

### 5.1 Anahtarlar

Her anahtarın **bir bacağı ortak GND**, **diğeri kendi GPIO'suna**:

| Tuş | GPIO | | Tuş | GPIO |
|---|---|---|---|---|
| K1 | 4 | | K7 | 17 |
| K2 | 5 | | K8 | 18 |
| K3 | 6 | | K9 | 8 |
| K4 | 7 | | K10 (COMBO) | 9 |
| K5 | 15 | | K11 (OS) | 10 |
| K6 | 16 | | | |

**GND papatya dizimi:** Tek bir teli kes, izolesini 11 noktada ortadan sıyır,
her anahtarın GND bacağına sırayla lehimle, ucunu karttaki GND'ye götür.
11 ayrı tel çekme — 1 tel yeter.

### 5.2 Enkoder (EC11)

| EC11 pini | Nereye |
|---|---|
| A | GPIO11 (+ RC filtresi) |
| C (orta) | GND |
| B | GPIO12 (+ RC filtresi) |
| SW bacak 1 | GPIO13 |
| SW bacak 2 | GND |

**RC filtresi** — A ve B için ayrı ayrı, delikli kart üzerinde:

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
> yanmaz ama zarar da görmez — çevirip tekrar dene.
>
> **Not:** Projenin ilk sürümü 3 × WS2812B (adreslenebilir RGB) kullanıyordu;
> o devre 1N4148 diyot ve 1000 µF kondansatör gerektiriyordu. Güncel firmware
> düz LED sürer, WS2812B devresi artık kullanılmaz.

---

## 6. Yapım sırası

1. **Plakayı bas ve test et** — önce tek delikli test parçası, anahtar tam oturuyor mu?
2. **Gövdeyi bas.** Önce tek kancalı test parçasıyla diş toleransını doğrula (§3.2).
3. **Delikli kartı hazırla (KATMAN 2):** 80 × 45 mm'ye kes, dişi header'ı lehimle,
   RC filtresini, LED besleme diyodunu ve kondansatörü yerleştir.
   **DevKit'i kartın arka kenarına yakın koy** — kasanın en yüksek yeri orası.
   > DevKit'i takmadan önce iki header sırası arasındaki delik sayısını say —
   > **9 delik (22.86 mm)** olmalı, o zaman karta düz oturur.
4. **Anahtarları plakaya klipsle (KATMAN 1).** Hepsinin dik olduğunu gözle kontrol et.
   ⚠️ Blue anahtar **tam oturmadan da tık sesi çıkarır** — sesle değil,
   plakaya bastırıp yandan bakarak kontrol et.
5. **Enkoderi** plakaya somunla tak.
6. **GND papatya zincirini** lehimle (tek tel, 11 nokta).
7. **11 sinyal telini** anahtarlardan karta çek. Renk kodu kullan, telleri
   katmanlar arası mesafeye göre biraz uzun bırak (~60 mm).
8. **LED'leri** bezel arkasına yerleştir, zinciri lehimle. **DIN/DOUT yönüne dikkat.**
9. **GÜÇ VERMEDEN ÖNCE:** multimetre ile 5V ↔ GND arası kısa devre kontrolü.
   Kısa varsa USB portunu yakarsın.
10. **Firmware'i yükle** — hazır imaj ve yükleyiciyle: kurulum paketinde
    `2-FIRMWARE/`, depoda [README → 4. Firmware](../README.md#4-firmware).
    Yükleyici modülü kendisi tanır. Kaynaktan derlemek için:
    [04-FIRMWARE-KURULUM.md](04-FIRMWARE-KURULUM.md); en kritik ayar
    `ARDUINO_USB_MODE=0`, yoksa HID hiç çalışmaz.
11. **Test et:** 11 tuş, enkoder iki yön + basış, 3 LED, combo, OS geçişi.
12. **Süngeri** taban içine yapıştır (anahtar altına ve bölmedeki ESP32'ye değmesin).
    ⚠️ **Kablolama ve test tamamen bitmeden kapağı çıtlatma** — her açma-kapama
    kancaları yorar (PETG'de ~20–50 çevrim ömür). Her şey çalışınca plakayı
    hizala, çevresine sırayla bastırarak 8 kancayı çıtlat, ayakları yapıştır.
    Açman gerekirse ön köşedeki kanırtma yuvalarından düz tornavidayla kaldır.

---

## 7. Test ederken

| Belirti | Sebep | Çözüm |
|---|---|---|
| Tek basışta eylem **iki kez** çalışıyor | Anahtar sıçraması | `firmware/src/config.h` → `EK_KEY_DEBOUNCE_MS` 8 → 12 |
| Bir tuş hiç çalışmıyor | Lehim veya yanlış GPIO | Multimetre ile anahtar bacağı ↔ DevKit pini süreklilik |
| Enkoder ileri geri zıplıyor | RC filtresi yok/yanlış | 10 kΩ + 100 nF kontrol |
| Enkoder ters yönde | A/B ters | A ve B tellerini yer değiştir |
| LED yanmıyor / titriyor | 1N4148 yok veya DIN/DOUT ters | Diyodu ve zincir yönünü kontrol et |
| Cihaz USB'de görünmüyor | `ARDUINO_USB_MODE=1` | `platformio.ini`'de `0` yap, yeniden yükle |
| Kapak kapanmıyor | Teller sıkışmış **veya** kart fazla önde | Telleri kenarlara topla; kartı arka duvara daya (önde sadece 3.5 mm boşluk var) |
| Cihaz masada öne kayıyor | Ayak yok / eğim iterek çalışıyor | 4 silikon ayağı düz tabana yapıştır |
| Ses çok "boşluklu" çınlıyor | Boş kovuk rezonansı | Tabana sünger |
| Plaka gevşek / takırdıyor | Kanca dişi ince basılmış | Dişi 1.0–1.2 mm ile yeniden bas; omuza 1 mm sünger şerit de yapışır |
| Keycap sökerken plaka kalkıyor | Çekme kuvveti kancalara biniyor | Keycap çekerken plakaya parmakla bastır |
| Kanca kırıldı | Çevrim ömrü doldu / PLA kullanıldı | Gövdeyi PETG ile yeniden bas; kalan 7 kanca geçici olarak tutar |

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

> Anlatım yok. Solda **çizeceğin parçaların ölçüleri**, sağda **elektronik
> bağlantılar ve parçalar**. Montajda ve CAD çizerken açık duracak alan bu.
>
> ### 📏 TÜM ÖLÇÜLER MİLİMETRE (mm) — cm DEĞİL
> `88.20 × 99.15` = 8.8 × 9.9 cm demektir. Açılar derece (°),
> elektronik değerler kendi birimiyle (Ω, µF, nF) yazılıdır.

### A.1 Mekanik — çizilecek parçalar, ölçü ölçü

**Zihninde canlandır:** bardak altlığından biraz büyük bir taban (dıştan 94 × 105 mm),
öne doğru alçalan kama — arka duvar iki parmak (29), ön duvar yarısı (15),
sırt eğimi 7.6°. Üstte düz bir kapak plakası; arka 30 mm'lik şeridi tuşsuz,
kalanı 3×3 numpad + sağ sütun. Keycap'lerle en yüksek nokta ~40 mm.

#### Parça 1 — Gövde (tek parça baskı)

| Öğe | Ölçü (mm) |
|---|---|
| Dış kütük | **94.20 × 105.15** (= plaka + 2×3 duvar), ön duvar **15.00** → arka **29.00**, üst yüz eğik (**7.6°**) |
| Duvar / taban | 3.00 / 2.50 → iç açıklık **88.60 × 99.55** (plaka + 0.2 pay/kenar), iç yükseklik 11.40 → 24.60 |
| İç omuz (plaka rafı) | Çepeçevre, duvar üst kenarından **1.50 aşağıda**, **1.5 genişlik** çıkıntı |
| Kanca dili ×8 | Duvarda iki dik yarık **1.5 × 12** arasında **9.0 genişlik** dil; ucunda içeri **1.0 diş** (giriş 45°, çıkış 30° pah) |
| Kanca konumları | Plaka koordinatında: ön/arka x = **22**, **66** · sol y = **25**, **70** · sağ y = **32**, **70** — gövdenin dış kenarından ölçüyorsan **+3 ekle** |
| Kanırtma yuvası ×2 | Ön duvar üst kenarında **8 × 2.5**; plaka koordinatında x = 8 ve 80 → **dış kenardan 11 ve 83** |
| USB açıklığı (Type-C) | **Sağ duvar**: **13 × 8**, köşe R2; merkez dış tabandan **12.80**, arka dış köşeden **21.0** → kenarlar yatay 14.5↔27.5, dikey 8.8↔16.8. 12.8 = taban 2.5 + standoff 3.0 + kart 1.6 + header 2.54 + PCB 1.6 + soket ortası 1.6. Kartı deliğe hizala: **"USB" portu** deliğin ortasına, soket burnu iç duvara **DAYALI** (boşluk yok — ağzı dış yüzeyden yalnızca 3 mm içeride kalır) |
| Kart postu ×4 | Tabandan **⌀5.0 × 3.0** yükseklik; 80 × 45 kartın köşe deliklerine denk (kart arka duvara dayalı) |
| Ayak çukuru ×4 (isteğe bağlı) | Taban altında **⌀8.0 × 1.0**, köşelerden 10 içeride |

#### Parça 2 — Üst plaka (tek parça baskı)

| Öğe | Ölçü (mm) |
|---|---|
| Kütük | **88.20 × 99.15 × 1.50** |
| Anahtar deliği ×11 | **14.00 × 14.00** kare (FDM'de **14.15** çiz) |
| Enkoder deliği | **⌀7.20** merkez `72.68, 45.53` + iki pim deliği **⌀1.50** merkezleri `67.68, 45.53` ve `77.68, 45.53` (üst-sol köşeden) |
| LED penceresi ×3 | **⌀3.00**; arka kenardan **10.00**, aralık **8.00**, orta pencere plaka ortasında |
| Kanca çentiği ×8 | Kenardan içeri **1.2**, genişlik **9.0** — konumlar gövdedeki kancalarla aynı |
| Alt kenar pahı | Çepeçevre **1.0 × 45°** (kancaya giriş kolaylığı) |
| Delik merkezleri | İlk tuş **15.53, 45.53** · adım **19.05** — tam tablo §3.1'de |

#### Parça 3 — Enkoder düğmesi (istersen hazır al: 6 mm D-mil düğmesi)

| Öğe | Ölçü (mm) |
|---|---|
| Kütük | **⌀17 × 16** silindir |
| Mil yuvası | Alt yüzden **⌀6.15**, D-düz kısımlı, **12.0 derin** |
| Somun havşası | Alt yüzden **⌀13.0 × 3.2** (M7 somunun üstüne oturmasın diye) |

#### Parça 4 — Delikli kart (kesim)

| Öğe | Ölçü (mm) |
|---|---|
| Kesim | 7×9 **cm** karttan **80 × 45 mm** kesilir |
| Köşe delikleri | Postlara denk **⌀3.2**, köşelerden ~4 içeride |
| ESP32 header sıraları | Kartın **arka-sağ şeridinde**, sıralar arası **9 delik = 22.86 mm** |
| Kartın kutudaki yeri | Arka iç duvara dayalı, **sağa yaslanmış** (sağ iç duvara ~0.5); DevKit'in USB soket burnu sağ iç duvara **dayalı**, "USB" portu delik ortasında (arkadan 21) |

### A.2 Elektronik — bağlantılar

Anahtar bacakları yönsüzdür: biri GPIO'ya, diğeri GND zincirine — hangisi
olduğu fark etmez. EC11'in 3'lü tarafı **A–C–B** (C ortada), 2'li tarafı SW.
WS2812B pad'leri: 5V · GND · DIN · DOUT (zincir yönü DOUT → sonraki DIN).

| Nereden | Nereye |
|---|---|
| K1 bacak | **GPIO4** |
| K2 bacak | **GPIO5** |
| K3 bacak | **GPIO6** |
| K4 bacak | **GPIO7** |
| K5 bacak | **GPIO15** |
| K6 bacak | **GPIO16** |
| K7 bacak | **GPIO17** |
| K8 bacak | **GPIO18** |
| K9 bacak | **GPIO8** |
| K10 bacak | **GPIO9** |
| K11 bacak | **GPIO10** |
| Her anahtarın 2. bacağı | **GND zinciri** (tek ortak tel) → kart GND |
| ENC A | Kart **RC-A düğümü** → **GPIO11** |
| ENC B | Kart **RC-B düğümü** → **GPIO12** |
| ENC C (orta) | GND zinciri |
| ENC SW 1. pin | **GPIO13** |
| ENC SW 2. pin | GND zinciri |
| **GPIO14** | → 330 Ω → **LED1 DIN** |
| DevKit **5V** | → 1N4148 → **LED1·2·3 5V** hattı |
| DevKit **GND** | **LED1·2·3 GND** hattı |
| LED1 **DOUT** | LED2 **DIN** |
| LED2 **DOUT** | LED3 **DIN** |
| DevKit'in **"USB" serigrafili portu** (native) | Sağ duvardaki açıklıktan dışarı — "UART" yazan porta TAKMA, klavye çalışmaz. Fiş tipi karta göre USB-C (klon) veya Micro-B (resmî Espressif) |

### A.3 Elektronik — parçalar (kart üstünde lehimli)

| Parça | Değer / tip | Bağlantısı |
|---|---|---|
| Dişi header ×2 sıra | 1×22 pin | ESP32 buraya takılır (sökülebilir) |
| Diyot | **1N4148** | DevKit 5V → LED 5V hattı; **çizgili uç LED tarafında** |
| Kondansatör | **1000 µF / ≥10 V** | LED 5V hattı ↔ GND; **uzun bacak 5V'ta** |
| Direnç | **330 Ω** | GPIO14 ile LED1 DIN arasında |
| Direnç ×2 | **10 kΩ** | 3V3 → RC-A ve RC-B düğümleri |
| Kondansatör ×2 | **100 nF** | RC-A ve RC-B düğümleri → GND |
| RC düğümü (×2) | — | Düğümde üç uç birleşir: 10 kΩ alt ucu + ENC teli + GPIO (11 veya 12) |

> DevKit üzerindeki pin adları karta basılıdır; GPIO numarasını **yazısından**
> doğrula, konumundan sayma.
