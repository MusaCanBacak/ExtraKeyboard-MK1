# ExtraKeyboard MK1 — Çekirdek Spesifikasyon (v3.0.0)

> ⚠️ **Güncel donanım farklıdır.** Bu şartnamenin donanım bölümleri (tuş sayısı ve
> pinleri, LED devresi, mekanik ölçüler) projenin ilk tasarımına aittir: 11 tuş,
> 3 × WS2812B LED, düz kutu gövde. Güncel donanım için
> [`PIN-HARITASI.md`](../PIN-HARITASI.md) ve [`BASIT-YAPIM.md`](BASIT-YAPIM.md)
> geçerlidir.

> **BU DOSYA TEK DOĞRULUK KAYNAĞIDIR (Single Source of Truth).**
> Firmware, PC uygulaması, mekanik ve tüm dokümantasyon bu dosyadaki
> pin numaralarına, protokol mesajlarına, isimlendirmeye ve JSON şemasına
> **birebir** uymak zorundadır. Bir çelişki görürsen bu dosya kazanır.

---

## 1. Ürün Tanımı

11 tuşlu, 3 LED'li, 1 döner enkoderli harici makro klavye.
**Mantık cihazda değil PC'dedir**: cihaz sadece "hangi tuşa basıldı" bilgisini
gönderir, "ne yapılacağına" PC uygulaması karar verir.

| Öğe | Adet | Görev |
|---|---|---|
| İşlev tuşu `K1..K9` | 9 | Doğrudan atanabilir eylem (uygulama/URL/kısayol/…) |
| Combo tuşu `K10` | 1 | **Bas-çek (latch):** bir kez basılır, ardından K1..K9'dan seçilen **2 tuş** comboyu oluşturur |
| OS tuşu `K11` | 1 | Windows ⇄ macOS modu arasında geçiş |
| Enkoder `ENC` | 1 | Döndür = ses aç/kıs, bas = sessize al |
| Durum LED'i `LED1..LED3` | 3 | OS modu / Combo durumu / Bağlantı durumu |

**Kombinasyon sayısı:** C(9,2) = **36** benzersiz combo.

### 1.1 Anahtarlar

**Anahtarlar: Cherry MX Blue (clicky), 3 pinli plate-mount.** 11 adet (K1..K11).

| Özellik | Değer |
|---|---|
| Parça no | `MX1A-E1NN` (Cherry MX Blue) |
| Tip | Clicky (tıklı) — **iki parçalı slider**, gövde içinde ayrı **click jacket** (tık ceketi) tık sesini ve taktil hissi üretir |
| Tetikleme kuvveti | **50 g** (0.50 N) |
| Tık / taktil tepe kuvveti | ~60 g |
| Dibe vurma kuvveti | ~60 g |
| Ön hareket (tetikleme noktası) | **2.2 mm** |
| Toplam hareket | **4.0 mm** |
| Sıfırlama (reset) noktası | ~1.7 mm → **~0.5 mm histerezis** |
| Kontak sıçraması | Veri sayfası ≤ 5 ms; clicky'de bırakışta **ek sıçrama** (bkz. 6.1) |
| Montaj | **3 pinli (plate-mount)** — bkz. aşağıdaki zorunluluk |

> **ZORUNLU — 3 pinli alın.** Bu projede PCB yoktur, anahtarlar plakaya elle
> kablolanır. 5 pinli (PCB-mount) versiyonda gövde altında **2 adet ekstra
> plastik konumlandırma ayağı** vardır; düz 1.50 mm plakada bu ayaklar için
> delik olmadığından anahtar plakaya tam oturmaz, eğri durur.
> Zorunda kalırsanız 5 pinliyi alıp **yalnızca 2 plastik ayağı** yan keskiyle
> kesin — **metal kontak pinlerini KESMEYİN**.

> **Histerezis notu.** Tetikleme 2.2 mm, sıfırlama ~1.7 mm olduğundan tuşun
> tekrar tetiklenebilmesi için basıldığı noktadan ~0.5 mm daha yukarı
> bırakılması gerekir. Makro klavyede sorun değildir (hızlı tekrarlı basış
> senaryosu yoktur), yalnızca bilinmesi gerekir.

**Uyumlu alternatifler** (hepsi boyutsal olarak aynı, 3 pinli alın):
Gateron Blue (daha ucuz, ~28 TL/adet), Kailh Box White (click bar mekanizması,
toza/suya daha dayanıklı), Outemu Blue (en ucuz, kalite değişken).

---

## 2. Fiziksel Yerleşim

4 sütun × 3 satır ızgara, **19.05 mm** (0.75") standart tuş adımı.
9 tuş sol tarafta numpad şeklinde 3×3, kalan 2 tuş sağ sütunda altlı üstlü,
enkoder sağ sütunun en üstünde.

```
      +-----------------------------------------------+  ▲ ARKA (yüksek, 29.00)
      |   (LED1)      (LED2)      (LED3)              |
      |          ELEKTRONİK BÖLMESİ  —  30.00 mm      |  ← anahtar YOK
      |          (delikli kart + ESP32 altta)         |     ESP32 buraya girer
      +===============================================+
        SÜTUN 1     SÜTUN 2     SÜTUN 3     SÜTUN 4
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |    ( )    |
  1   |    K1     |    K2     |    K3     |    ENC    |   ← Enkoder (ses)
      |           |           |           |   knob    |
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |           |
  2   |    K4     |    K5     |    K6     |    K10    |   ← COMBO
      |           |           |           |  [COMBO]  |
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |           |
  3   |    K7     |    K8     |    K9     |    K11    |   ← OS SWITCH
      |           |           |           |  [WIN/MAC]|
      +-----------+-----------+-----------+-----------+
      |<--------- 3×3 NUMPAD ----------->|<-- ek -->|
                                                        ▼ ÖN (alçak, 15.00)
```

**Tuş numaralandırması sol-üstten sağa doğru okunur** (K1 sol üst, K9 sağ alt).
Uygulama arayüzü de tuşları bu düzende gösterir.

### 2.1 Ana Ölçüler (mm)

| Ölçü | Değer | Not |
|---|---|---|
| Tuş adımı (pitch) | 19.05 | X ve Y aynı |
| Tuş alanı (Genişlik × Derinlik) | 76.20 × 57.15 | 4×19.05 ve 3×19.05 |
| Bezel (her kenar) | 6.00 | |
| Tuş alanı bölümü | 69.15 | 57.15 + 2×6 |
| Elektronik bölmesi (arka) | **30.00** | üstünde anahtar yok — ESP32 buraya |
| Plaka dış ölçü | **88.20 × 99.15** | 69.15 tuş alanı + 30.00 bölme |
| Gövde dış ölçü | **94.20 × 105.15** | plaka + 2×3 duvar; duvarlar plakanın **dışına** eklenir |
| Duvar kalınlığı | 3.00 | |
| İç açıklık (plaka yuvası) | 88.60 × 99.55 | plaka + 0.2 pay/kenar — plaka içine düşer, omuza oturur |
| Plaka kalınlığı | 1.50 | MX klips tutması için ZORUNLU |
| Gövde ön duvar yüksekliği | **15.00** | Eğimli kama — bkz. aşağıdaki not |
| Gövde arka duvar yüksekliği | **29.00** | |
| Eğim açısı | **≈ 7.6°** | `atan(14 / 105.15) = 7.58°` |
| İç boşluk (ön → arka) | **11.40 → 24.60** | Bölmede DevKit için 12.94 gerekir |
| Taban kalınlığı | 2.50 | |
| Toplam gövde yüksekliği | **15.00 → 29.00** | Önden arkaya yükselir |
| MX anahtar plaka deliği | 14.00 × 14.00 | tolerans 13.95–14.05 |
| Enkoder plaka deliği | ⌀7.20 | EC11 M7 burç |
| LED penceresi | ⌀3.00 × 3 adet | **bölme şeridinde** (arka kenardan 10.00), aralık 8.00 |
| Bağlantı | **Geçmeli (snap-fit)** | 8 kanca + çevre omuzu; vida ve insert YOK — bkz. BASIT-YAPIM §3.2 |

> **Not — neden arkada 30.00 mm'lik elektronik bölmesi var.**
> Yapı **katmanlıdır**: anahtarlar üst plakada, delikli kart ve DevKit onların
> altında. Anahtar gövdesi + pinler + lehim plakanın altında **9.0 mm** yer kaplar.
> DevKit yığını ise standoff (3.0) + delikli kart (1.6) + header plastiği (2.54)
> + DevKit PCB (1.6) + USB-C konnektörü (3.2) = **11.94 mm** ister.
> İkisi üst üste **21.94 mm** eder ve bu, tuş alanının altına sığmaz — üstelik
> eğim yüzünden tavan öne doğru alçaldığı için durum daha da kötüleşir.
>
> Çözüm: **tuş alanının arkasına, üstünde anahtar olmayan 30.00 mm'lik bir bölme.**
> Orada 9.0 mm'lik anahtar payı hiç harcanmaz, tam iç yükseklik (20.58–24.60 mm)
> DevKit'e kalır. Delikli kart (80 × 45) arka duvara dayanır ve öne doğru
> tuş alanının altına uzanarak yatık dirençleri taşır.
>
> Eğim (7.58°) **ergonomi içindir** — klavyelerdeki standart yazma açısı 6–9°'dir.
> Hacim sorununu çözen şey eğim değil, bölmedir.
>
> Ayrıntı, eğim boyunca boşluk tablosu, montaj yığını ve tüm delik
> koordinatları: [BASIT-YAPIM.md](BASIT-YAPIM.md) §3.
>
> ⚠️ `mechanical/*.scad` dosyaları bu geometriden **öncesine** aittir (düz kutu,
> bölmesiz). Kendi çizimini yapıyorsan BASIT-YAPIM.md §3'ü kullan;
> bkz. [mechanical/OKU-ONCE.md](../mechanical/OKU-ONCE.md).

> **Not — anahtar tipi ölçüleri etkilemez.** Cherry MX Blue, **boyutsal olarak
> diğer tüm MX anahtarlarıyla birebir aynıdır**: plaka deliği 14.00 mm kare,
> adım 19.05 mm, gövde flanşı 15.6 mm. Brown → Blue geçişinde **plaka ve tuş
> yerleşimi değişmez**.

> **Not — akustik.** MX Blue yüksek sesli bir anahtardır ve plaka altındaki boş
> kovuk rezonans odası gibi çalışıp sese "çınlamalı/boşluklu" (hollow, pingy) bir
> karakter verir. Bu bir ölçü değişikliği değil, **dolgu** meselesidir:
> - Tabanın iç yüzeyine **2–3 mm poron/EVA sünger** yapıştırın; tabandan yansıyan
>   sesi bu keser.
> - Kalan boşluğa gevşekçe sünger doldurun — DevKit'i, delikli kartı ve kabloları
>   **sıkıştırmadan**.
> - Sünger **anahtar gövdelerine değmemeli** (tuş alanının altında yalnızca
>   2.4–9.2 mm boşluk var) ve bölmedeki DevKit'in üstünü kapatmamalı.
> - Silikon ayaklar gövde–masa temasını keser, masaya iletilen gümbürtüyü azaltır.

---

## 3. Elektronik — Pin Şeması (DEĞİŞTİRİLEMEZ)

**MCU: ESP32-S3-DevKitC-1 (ESP32-S3-WROOM-1, N16R8)**
Seçim gerekçesi: yerleşik USB OTG → sürücüsüz **USB HID + CDC composite**;
BLE gerekmez, eşleştirme derdi yok; GPIO bolluğu var.

### 3.1 Pin Tablosu

| İşlev | GPIO | Yön / Mod | Bağlantı |
|---|---|---|---|
| K1 | **GPIO4** | INPUT_PULLUP | Anahtar → GND |
| K2 | **GPIO5** | INPUT_PULLUP | Anahtar → GND |
| K3 | **GPIO6** | INPUT_PULLUP | Anahtar → GND |
| K4 | **GPIO7** | INPUT_PULLUP | Anahtar → GND |
| K5 | **GPIO15** | INPUT_PULLUP | Anahtar → GND |
| K6 | **GPIO16** | INPUT_PULLUP | Anahtar → GND |
| K7 | **GPIO17** | INPUT_PULLUP | Anahtar → GND |
| K8 | **GPIO18** | INPUT_PULLUP | Anahtar → GND |
| K9 | **GPIO8** | INPUT_PULLUP | Anahtar → GND |
| K10 (COMBO) | **GPIO9** | INPUT_PULLUP | Anahtar → GND |
| K11 (OS) | **GPIO10** | INPUT_PULLUP | Anahtar → GND |
| ENC_A | **GPIO11** | INPUT_PULLUP | EC11 A (+ RC debounce) |
| ENC_B | **GPIO12** | INPUT_PULLUP | EC11 B (+ RC debounce) |
| ENC_SW | **GPIO13** | INPUT_PULLUP | EC11 buton → GND |
| LED_DATA | **GPIO14** | OUTPUT | 330 Ω → WS2812B DIN |

**Tüm anahtarlar aktif-LOW.** Matris YOK, diyot YOK — her tuş doğrudan
kendi GPIO'suna bağlı. Bu sayede combo (3 tuş aynı anda) hayalet tuş
(ghosting) sorunu olmadan çalışır.

### 3.2 KULLANILMAYACAK Pinler (gerekçeleriyle)

| GPIO | Neden yasak |
|---|---|
| 0, 46 | Boot strapping — açılışta LOW olursa cihaz bootloader'a düşer |
| 3 | JTAG kaynak seçimi strapping |
| 19, 20 | **Yerleşik USB D− / D+** — dokunulamaz |
| 26–32 | SPI Flash (SPICS1/HD/WP/CLK/Q/D) |
| 33–37 | Octal PSRAM (N16R8 varyantında kullanılır) |
| 43, 44 | U0TXD / U0RXD — seri konsol |
| 45 | VDD_SPI strapping |
| 48 | DevKitC-1 üzerindeki dahili RGB LED (isteğe bağlı kullanılabilir) |

> **Not (GPIO15/16):** Bu pinler yalnızca harici 32.768 kHz kristal
> takılırsa XTAL_32K_P/N olur. Bu projede kristal yok, normal GPIO'durlar.

### 3.3 Güç ve LED

- Besleme: USB 5 V (VBUS); konnektör karta göre **USB-C (klonlar)** veya **Micro-B (resmî DevKitC-1)**. Toplam çekim < 150 mA.
- Kartta iki port vardır: **"USB" (native — HID buradan çalışır)** ve "UART" (yalnız seri/yükleme). Cihaz "USB" portundan bağlanır.
- WS2812B **5 V** ile beslenir, veri hattı ESP32'den **3.3 V**'tur.
  WS2812B'nin V_IH değeri 0.7 × VDD = 3.5 V olduğundan 3.3 V **sınırdadır**.
  **Çözüm (zorunlu):** LED'lerin +5 V hattına seri **1N4148** diyot koy →
  VDD ≈ 4.3 V olur, V_IH ≈ 3.0 V'a düşer, 3.3 V veri güvenle tanınır.
  *(Alternatif: 74AHCT125 seviye çevirici veya 3.3 V uyumlu SK6812.)*
- WS2812B besleme uçlarına **1000 µF / 10 V** elektrolitik kondansatör.
- Veri hattına MCU çıkışına yakın **330 Ω** seri direnç.

### 3.4 Enkoder RC Debounce (zorunlu)

EC11 mekanik enkoderin kontak sıçraması yazılımla tam bastırılamaz.
Her iki kanal için:

```
3V3 ──[10 kΩ]──┬── ENC_A (GPIO11)
               │
               ├── EC11 pin A
               │
              === 100 nF
               │
              GND ── EC11 pin C (ortak uç)
```

**Düğüm okunuşu:** 10 kΩ direncin alt ucu, 100 nF'nin üst ucu, `ENC_A` (GPIO11)
ve **EC11 pin A** tek bir düğümdür. 100 nF'nin alt ucu GND'ye gider ve
**EC11 pin C (ortak uç)** de GND'dedir. Enkoderin iç kontağı kapandığında
A ile C birleşir, düğüm GND'ye çekilir; kontak açıkken direnç düğümü 3V3'e
çeker. `EC11 pin A` GND'ye **doğrudan bağlanmaz** — aksi hâlde hat kalıcı
olarak LOW kalır ve kondansatör hiç iş görmez.

`ENC_B` (GPIO12) için aynısı (R2 = 10 kΩ, C2 = 100 nF, EC11 pin B; ortak uç
yine aynı `EC11 pin C`). `ENC_SW` sadece dahili pull-up + yazılım
debounce ile yeterlidir.

---

## 4. USB Kimliği

| Alan | Değer |
|---|---|
| VID | `0x303A` (Espressif) |
| PID | `0x82E1` |
| Manufacturer | `BlueDevelopment` |
| Product | `ExtraKeyboard MK1` |
| Serial | `EK1-<MAC son 6 hane>` |

Cihaz **composite**: `HID Keyboard` + `HID Consumer Control` + `CDC-ACM`.
PC uygulaması portu önce VID/PID, bulamazsa Product string ile bulur.

---

## 5. Haberleşme Protokolü (CDC Seri, satır tabanlı ASCII)

- Satır sonu: `\n` (LF). Büyük harf komutlar. Alanlar tek boşlukla ayrılır.
- Baud hızı önemsizdir (native USB CDC), uygulama yine de `115200` açar.
- Bilinmeyen satırlar **sessizce yok sayılır** (ileri uyumluluk).

### 5.1 Cihaz → PC (Event)

| Mesaj | Anlamı |
|---|---|
| `EV KEY <n> DOWN` | `n` = 1..9, tuş basıldı |
| `EV KEY <n> UP` | `n` = 1..9, tuş bırakıldı — **eylem UP'ta tetiklenir** |
| `EV COMBO <a> <b>` | `a < b`, ikisi de 1..9. Combo tetiklendi |
| `EV MODE COMBO_ON` | K10'a basıldı (bas-çek), combo modu kilitlendi |
| `EV MODE COMBO_OFF` | Combo modu kapandı: combo tetiklendi, K10 ile iptal edildi veya 10 sn zaman aşımı |
| `EV OS WIN` / `EV OS MAC` | Cihaz OS modu değişti (K11 ile) |
| `EV ENC CW` / `EV ENC CCW` | Enkoder bir tık döndü |
| `EV ENC PRESS` | Enkoder butonuna basıldı |
| `EV ENC LONG` | Enkoder butonu 800 ms basılı tutuldu |
| `HB <uptime_ms>` | Her 1000 ms'de bir kalp atışı |
| `ID <fw> <hw> <serial> <os>` | Kimlik yanıtı, örn. `ID 3.0.0 MK1 EK1-A4C138 WIN` |
| `ACK <komut>` | Komut kabul edildi |
| `ERR <sebep>` | Komut reddedildi |

### 5.2 PC → Cihaz (Command)

| Komut | Anlamı |
|---|---|
| `CMD ID` | Kimlik iste → `ID ...` |
| `CMD PING` | → `ACK PING` |
| `CMD OS WIN` / `CMD OS MAC` | OS modunu PC'den zorla |
| `CMD LED <i> <RRGGBB>` | `i` = 1..3, örn. `CMD LED 1 1E90FF`. LED'in **temel rengini** değiştirir; durum mantığı (flaşlar) üzerine çalışmaya devam eder, LED sabitlenmez |
| `CMD LED <i> AUTO` | İlgili LED'i bölüm 6.4'teki varsayılan rengine döndürür |
| `CMD LED BRIGHT <0-255>` | Genel parlaklık |
| `CMD ENC MODE HID` / `HOST` | Enkoder: cihaz HID ses gönderir / PC karar verir |
| `CMD HIDFB ON` / `OFF` | HID yedek modu (app yokken F13–F21) |
| `CMD SAVE` | Ayarları NVS'e yaz |

### 5.3 HID Yedek Modu (uygulama kapalıyken)

PC uygulaması bağlı değilken (CDC DTR düşük) cihaz **HID yedek moduna** düşer:

| Tuş | Gönderilen HID kodu |
|---|---|
| K1..K9 | `F13` … `F21` |
| K11 | `F22` |
| K10 (combo) | *(devre dışı — LED3 kırmızı yanıp söner)* |
| Enkoder | Consumer Control: Volume Up / Down / Mute |

**Enkoder HID modu her zaman aktiftir** — uygulama olmadan da ses çalışır.

---

## 6. Cihaz İçi Mantık

### 6.1 Debounce

| Girdi | Süre | Sabit (`firmware/src/config.h`) |
|---|---|---|
| Tuşlar `K1..K11` | **8 ms** | `EK_KEY_DEBOUNCE_MS` |
| Enkoder butonu `ENC_SW` | **5 ms** | `EK_ENC_SW_DEBOUNCE_MS` |

- Tuşlar: **8 ms** yazılım debounce, tuş başına ayrı durum makinesi.
  **Gerekçe:** Cherry MX Blue clicky'dir; gövde içindeki ayrı **click jacket**
  tuş **bırakılırken** stemden ayrılıp geri çarpar ve veri sayfasındaki ≤ 5 ms'lik
  sıçramanın üstüne bırakış tarafında **ek kontak sıçraması** bindirir (yıpranmış
  anahtarda 10 ms'ye yaklaşabilir). 5 ms'de kalınırsa tek basış **iki kez** eylem
  tetikleyebilir — makro klavyede bu, atanan uygulamanın iki kez açılması demektir.
  8 ms bu riski kapatır ve cihazda hissedilmez (hızlı yazı yazılmıyor).
- Enkoder butonu: **5 ms** — bilinçli olarak tuşlardan farklıdır. EC11'in gömülü
  butonu tek parçalı kubbe/kontak mekanizmasıdır, click jacket yoktur, bırakışta
  ek sıçrama üretmez.
- Süreler **yalnızca `config.h`'den** ayarlanır; başka dosyada sabit sayı yazılmaz.
  Lineer/taktil anahtara geçilirse tuş değeri 5 ms'e düşürülebilir; çift tetikleme
  görülürse 12 ms'e çıkarılır.
- Enkoder kanalları: RC donanım filtresi + 4-adımlı durum tablosu (state table)
  çözücü. EC11 tıklama başına tam bir quadrature çevrimi üretir → 1 tık = 1 event.

### 6.2 Combo Durum Makinesi — BAS-ÇEK (latch)

K10 **basılı tutulmaz**: bir kez basılır, mod kilitlenir, cihaz sıradaki iki
tuş basışını bekler. Combo tetiklenince mod **kendiliğinden kapanır**
(tek seferlik). Geçişler K10 ve tuşların **DOWN kenarında** olur; bırakışlar
işlevsizdir — bu yüzden tuşların basılı tutulmasına gerek yoktur.

```
IDLE ──(K10 basıldı)──► ARMED        [EV MODE COMBO_ON, LED2 turuncu]
ARMED ──(1. tuş basıldı)──► ONE_HELD (ilk tuş SEÇİLİR; bırakılabilir,
                                      normal eylemi BASTIRILIR)
ONE_HELD ──(2. farklı tuş)──► combo  [EV COMBO a b, a<b normalize,
                                      LED2 yeşil flaş] ──► IDLE
                                     [EV MODE COMBO_OFF — tek seferlik]
ARMED/ONE_HELD ──(K10 tekrar basıldı)──► IDLE  [COMBO_OFF — iptal]
ARMED/ONE_HELD ──(10 sn işlem yok)──► IDLE     [COMBO_OFF — zaman aşımı,
                                     `EK_COMBO_LATCH_TIMEOUT_MS`, 0=kapalı]
```

**Kritik kurallar:**
- Mod açıkken K1..K9'un normal `EV KEY` eventleri ve HID kodları
  **gönderilmez**; combo'ya katılan tuşların UP'ları da yutulur.
- Aynı tuşa ikinci kez basmak yok sayılır (`3+3` yoktur).
- Combo sırası önemsizdir (`2+5` = `5+2` → `C_2_5`).
- Eski alışkanlık da çalışır: K10 basılı tutulup iki tuşa basılırsa aynı
  akış işler (mod DOWN'da açıldığı için).

### 6.3 OS Tuşu (K11)
- **Kısa basış (<800 ms):** Windows ⇄ Mac geçişi, NVS'e kaydet,
  LED1 rengini değiştir, `EV OS <WIN|MAC>` gönder.
- **Uzun basış (≥3 s):** HID yedek modunu aç/kapat (`CMD HIDFB` eşdeğeri),
  LED3 üç kez beyaz yanıp söner.

### 6.4 LED Anlamları

| LED | Durum | Renk |
|---|---|---|
| **LED1** | OS = Windows | Mavi `#1E90FF` |
| | OS = macOS | Beyaz `#FFFFFF` |
| **LED2** | Combo kapalı | Sönük |
| | Combo modu açık (K10 basılı) | Turuncu `#FF9500` |
| | Combo tetiklendi (150 ms flaş) | Yeşil `#2CC985` |
| **LED3** | PC uygulaması bağlı | Yeşil `#2CC985` |
| | Uygulama yok / HID yedek | Kırmızı `#E04F5F` |
| | Tuş aktivitesi (80 ms flaş) | Mavi `#3B8ED0` |

Varsayılan parlaklık: **60/255** (gözü yormaması için).

---

## 7. Yapılandırma Şeması (`config.json`, schema 3)

**Windows ve macOS profilleri AYRI tutulur** — uygulama yolları farklıdır.

```json
{
  "schema": 3,
  "app_version": "3.0.0",
  "device": {
    "port": "auto", "vid": "0x303A", "pid": "0x82E1",
    "product": "ExtraKeyboard MK1", "baud": 115200
  },
  "active_profile": "Varsayilan",
  "profiles": {
    "Varsayilan": {
      "windows": {
        "keys":   { "K1": {"type":"none","value":"","name":"Tuş 1"}, "...K9": {} },
        "combos": { "C_1_2": {"type":"none","value":"","name":"Combo 1+2"}, "...C_8_9": {} },
        "encoder":{ "mode":"hid",
                    "cw":    {"type":"media","value":"volume_up","name":"Ses +"},
                    "ccw":   {"type":"media","value":"volume_down","name":"Ses −"},
                    "press": {"type":"media","value":"mute","name":"Sessiz"},
                    "long":  {"type":"none","value":"","name":"Uzun basış"} }
      },
      "mac": { "…aynı yapı…" }
    }
  },
  "leds": {
    "brightness": 60,
    "os_win": "#1E90FF", "os_mac": "#FFFFFF",
    "combo": "#FF9500", "link_ok": "#2CC985", "link_err": "#E04F5F"
  },
  "ui": { "theme":"Dark", "minimize_to_tray": true, "start_minimized": false },
  "autostart": false
}
```

### 7.1 Anahtar İsimlendirme (ZORUNLU)
- Tuşlar: `K1` … `K9`
- Combolar: `C_<a>_<b>` — **daima `a < b`**, örn. `C_1_2`, `C_2_5`, `C_8_9` (36 adet)
- Enkoder: `cw`, `ccw`, `press`, `long`

### 7.2 Eylem Tipleri

| `type` | `value` örneği | Davranış |
|---|---|---|
| `none` | `""` | Hiçbir şey yapma |
| `app` | `/Applications/Safari.app` · `C:\...\notepad.exe` | Uygulama başlat |
| `url` | `bluedevelopment.com` | Varsayılan tarayıcıda aç (şema yoksa `https://` ekle) |
| `shortcut` | `command+c` · `ctrl+shift+esc` | Tuş kombinasyonu bas |
| `text` | `merhaba dünya` | Metni yaz |
| `command` | `say merhaba` | Kabuk komutu çalıştır |
| `file` | `~/notlar.txt` | Dosyayı varsayılan uygulamada aç |
| `folder` | `~/Downloads` | Klasörü Finder/Explorer'da aç |
| `media` | `volume_up`, `volume_down`, `mute`, `play_pause`, `next`, `prev` | Medya tuşu |
| `macro` | `ctrl+c|500|ctrl+v` | `|` ile ayrılmış adımlar; sayı = ms bekleme |

**Kısayol normalizasyonu:** Windows profilinde `command`/`cmd` → `ctrl`,
macOS profilinde `ctrl` **olduğu gibi kalır** (macOS'ta Control ayrı bir tuştur;
kullanıcı `command` yazmalıdır). Uygulama arayüzü aktif profile göre ipucu gösterir.

---

## 8. PC Uygulaması — Modül API Sözleşmesi

Dosya düzeni ve **birbirini çağıran modüllerin imzaları** aşağıdaki gibidir.
`core/` ve `ui/` ayrı yazılır, bu yüzden bu API kesindir.

### `app/core/config.py`
```python
SCHEMA_VERSION = 3
KEY_IDS: list[str]          # ["K1".."K9"]
COMBO_IDS: list[str]        # 36 adet "C_a_b", a<b
ENCODER_IDS: list[str]      # ["cw","ccw","press","long"]
ACTION_TYPES: list[str]     # ["none","app","url","shortcut","text",
                            #  "command","file","folder","media","macro"]
MEDIA_VALUES: list[str]

def combo_id(a: int, b: int) -> str            # (2,5)->"C_2_5"; a>b ise takas eder
def parse_combo_id(cid: str) -> tuple[int,int]

class ConfigManager:
    path: str
    data: dict
    def __init__(self, path: str | None = None) -> None
    def load(self) -> dict                      # yoksa varsayılan üretir, v2'yi migrate eder
    def save(self) -> None                      # atomik yazma (.tmp + os.replace)
    def profile(self, os_key: str) -> dict      # os_key: "windows" | "mac"
    def get_action(self, os_key: str, slot: str) -> dict
    def set_action(self, os_key: str, slot: str, type_: str, value: str, name: str|None=None) -> None
    def led_settings(self) -> dict
    def list_profiles(self) -> list[str]
    def add_profile(self, name: str) -> None
    def delete_profile(self, name: str) -> None
    def set_active_profile(self, name: str) -> None
    def export_to(self, path: str) -> None
    def import_from(self, path: str) -> None
```

### `app/core/device.py`
```python
class DeviceEvent:            # basit veri sınıfı
    kind: str                 # "key" | "combo" | "mode" | "os" | "enc" | "hb" | "id" | "ack" | "err" | "link"
    slot: str | None          # "K3", "C_2_5", "cw", ...
    raw: str
    payload: dict

class DeviceLink:
    """Arka plan thread'inde seri portu yönetir; otomatik bulur ve yeniden bağlanır."""
    def __init__(self, cfg: ConfigManager, on_event: Callable[[DeviceEvent], None]) -> None
    def start(self) -> None
    def stop(self) -> None
    @property
    def connected(self) -> bool
    @property
    def port_name(self) -> str | None
    def send(self, line: str) -> bool                      # "CMD PING"
    def set_led(self, index: int, hex_color: str) -> bool  # index 1..3
    def set_brightness(self, value: int) -> bool
    def set_os(self, os_key: str) -> bool                  # "windows"|"mac"
    def set_encoder_mode(self, mode: str) -> bool          # "hid"|"host"
    @staticmethod
    def find_ports(cfg: ConfigManager) -> list[str]
```
`on_event` **arka plan thread'inden** çağrılır. UI, `self.after(0, ...)` ile
ana thread'e aktarmak zorundadır.

### `app/core/actions.py`
```python
class ActionRunner:
    def __init__(self, cfg: ConfigManager) -> None
    def current_os_key(self) -> str                        # "windows" | "mac"
    def set_os_key(self, os_key: str) -> None
    def run(self, slot: str) -> tuple[bool, str]           # (başarı, mesaj)
    def run_action(self, action: dict) -> tuple[bool, str]
```

### `app/ui/` ve `app/main.py`
- `main.py` → tekil örnek kontrolü (port 64210), `ConfigManager`, `DeviceLink`,
  `ActionRunner` kurar, `MainWindow`'u açar.
- `ui/main_window.py` → `MainWindow(ctk.CTk)`; sekmeler:
  **Tuşlar**, **Combolar**, **Enkoder**, **LED & Cihaz**, **Ayarlar**.
- `ui/key_grid.py` → 4×3 fiziksel yerleşimi birebir yansıtan ızgara.
- `ui/combo_matrix.py` → 9×9 üst üçgen matris (36 hücre).
- `ui/action_editor.py` → tip + değer + gözat diyaloğu (tüm slotlar için ortak).
- `ui/tray.py` → pystray simgesi (Windows + macOS).

**Tema:** mevcut v2 ile aynı — CustomTkinter, koyu tema,
renkler `#1a1a2e` / `#16213e` / `#1e1e2e`, vurgular `#3B8ED0` `#2CC985` `#FF9500` `#E04F5F`.

---

## 9. Dosya Düzeni

```
ExtraKeyboard/
├── README.md
├── Main.py                     # ESKİ v2 — dokunulmadı, referans
├── macro_config.json           # ESKİ v2 config — migrate edilir
├── config.json                 # YENİ v3 config (ilk çalıştırmada üretilir)
├── run_app.py                  # v3 giriş noktası
├── docs/   00..08 dokümanlar
├── firmware/  platformio.ini + src/
├── hardware/  şematik, BOM, kablolama
├── mechanical/ OpenSCAD + DXF üretici
├── app/    core/ + ui/ + main.py
└── tools/  migrate_v2_config.py
```

---

## 10. Sürüm

`FW_VERSION = "3.0.0"` · `APP_VERSION = "3.0.0"` · `HW_REV = "MK1"`
