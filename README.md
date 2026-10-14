# ExtraKeyboard MK1

**11 tuşlu, 3 LED'li, döner enkoderli, USB'den çalışan harici makro klavye.**

`Sürüm 3.0.0` · `Donanım MK1` · `ESP32-S3` · `Windows + macOS` · `Türkçe arayüz`

---

## Bu nedir?

ExtraKeyboard, ana klavyenizin yanında duran ve sık yaptığınız işleri tek tuşa
indiren bir yardımcı cihazdır. Uygulama açın, klasör açın, kısayol gönderin,
metin yazın, kabuk komutu çalıştırın, sesi ayarlayın — hepsi parmağınızın altında.

Projenin temel kararı şudur: **mantık cihazda değil bilgisayardadır.**
Cihaz yalnızca *"hangi tuşa basıldı"* bilgisini gönderir; *"ne yapılacağına"*
bilgisayardaki Python uygulaması karar verir. Böylece bir eylemi değiştirmek için
firmware yüklemek gerekmez, tek bir ayar penceresi yeterlidir.

| Öğe | Adet | Görevi |
|---|---|---|
| İşlev tuşu `K1..K9` | 9 | Doğrudan atanabilir eylem |
| Combo tuşu `K10` | 1 | Basılı tutulurken K1..K9'dan **2 tanesi** ile kombinasyon |
| OS tuşu `K11` | 1 | Windows ⇄ macOS profili arasında geçiş |
| Enkoder `ENC` | 1 | Döndür = ses aç/kıs, bas = sessize al |
| Durum LED'i `LED1..LED3` | 3 | OS modu / Combo durumu / Bağlantı durumu |

**Toplam atanabilir eylem:** 9 tuş + **36 combo** + 4 enkoder hareketi = **49 slot**,
üstelik Windows ve macOS için **ayrı ayrı**.

---

## Öne çıkan özellikler

- **Sürücü gerektirmez.** ESP32-S3'ün yerleşik USB'si sayesinde cihaz standart
  bir HID klavye + seri port olarak görünür. Tak ve çalıştır.
- **36 kombinasyon.** `K10`'a bir kez basın (bas-çek), sonra iki tuşa dokunun; combo tetiklenince mod kendiliğinden kapanır. Sıra önemsizdir:
  `2+5` ile `5+2` aynı komutu çalıştırır.
- **10 farklı eylem tipi:** uygulama, URL, kısayol, metin, kabuk komutu, dosya,
  klasör, medya tuşu, makro ve "hiçbir şey".
- **Ayrı Windows / macOS profilleri.** Yollar ve kısayollar iki sistemde farklıdır;
  cihazdaki OS tuşuyla anında geçilir.
- **Uygulama kapalıyken de çalışır.** HID yedek modunda tuşlar `F13–F22`
  gönderir, enkoder sesi doğrudan kontrol eder.
- **Gerçek iki yönlü protokol.** Cihaz ile uygulama, satır tabanlı ASCII bir CDC
  protokolüyle konuşur; LED renkleri, parlaklık ve OS modu uygulamadan yönetilir.
- **Üç durum LED'i.** Hangi profildesiniz, combo modu açık mı, uygulama bağlı mı —
  ekrana bakmadan görürsünüz.
- **Baştan sona Türkçe.** Arayüz, dokümanlar ve hata mesajları Türkçedir.

---

## Fiziksel yerleşim

4 sütun × 3 satır ızgara, **19.05 mm** (0.75") standart tuş adımı.

```
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

  Üst bezelde soldan sağa:  (LED1)   (LED2)   (LED3)
```

Tuş numaralandırması **sol üstten sağa** okunur: `K1` sol üst, `K9` sağ alt.
Uygulama arayüzü de tuşları tam olarak bu düzende gösterir.

**LED anlamları**

| LED | Durum | Renk |
|---|---|---|
| **LED1** | Windows profili | Mavi `#1E90FF` |
| | macOS profili | Beyaz `#FFFFFF` |
| **LED2** | Combo modu açık (K10 basılı) | Turuncu `#FF9500` |
| | Combo tetiklendi (150 ms flaş) | Yeşil `#2CC985` |
| **LED3** | Uygulama bağlı | Yeşil `#2CC985` |
| | Uygulama yok / HID yedek modu | Kırmızı `#E04F5F` |

---

## Nasıl çalışır

```
   ┌──────────────────────┐         USB-C          ┌──────────────────────────┐
   │  ExtraKeyboard MK1   │◄──────────────────────►│      Bilgisayar          │
   │  (ESP32-S3)          │                        │                          │
   │                      │   HID Keyboard         │  ┌────────────────────┐  │
   │  11 tuş ──┐          ├───────────────────────►│  │ İşletim sistemi    │  │
   │  enkoder ─┤ firmware │   HID Consumer         │  │ (F13–F22, ses)     │  │
   │  3 LED ◄──┘          ├───────────────────────►│  └────────────────────┘  │
   │                      │                        │                          │
   │                      │   CDC-ACM (seri)       │  ┌────────────────────┐  │
   │   "EV KEY 3 UP"      ├───────────────────────►│  │ ExtraKeyboard      │  │
   │   "EV COMBO 2 5"     │                        │  │ uygulaması         │  │
   │                      │◄───────────────────────┤  │  → config.json     │  │
   │                      │   "CMD LED 1 1E90FF"   │  │  → eylemi çalıştır │  │
   └──────────────────────┘                        │  └────────────────────┘  │
                                                   └──────────────────────────┘
```

1. Tuşa basılır, cihaz `EV KEY 3 UP` satırını seri porttan gönderir.
2. Uygulama bu satırı okur, aktif profildeki `K3` slotuna bakar.
3. Slottaki eylem (uygulama aç / kısayol gönder / metin yaz …) çalıştırılır.
4. Uygulama kapalıysa cihaz devreye girer ve doğrudan `F15` tuşunu gönderir.

---

## Teknik özet

| Konu | Değer |
|---|---|
| MCU | ESP32-S3-WROOM-1 (N16R8), ESP32-S3-DevKitC-1 kartı |
| Bağlantı | USB-C, **HID Keyboard + HID Consumer Control + CDC-ACM** composite |
| USB kimliği | VID `0x303A` · PID `0x82E1` · `BlueDevelopment` / `ExtraKeyboard MK1` |
| Protokol | Satır tabanlı ASCII, `\n` sonlu, 115200 (CDC'de hız önemsiz) |
| Tuş sayısı | 11 (9 işlev + combo + OS), matris **yok**, diyot **yok** |
| Kombinasyon | C(9,2) = **36** |
| Enkoder | EC11, RC donanım debounce + 4 adımlı durum tablosu |
| LED | 3 × WS2812B, varsayılan parlaklık 60/255 |
| Debounce | Tuşlar 5 ms yazılım; enkoder 10 kΩ + 100 nF (τ = 1 ms) |
| Güç | USB 5 V, toplam çekim < 150 mA |
| Gövde | 88.20 × 69.15 × 22.00 mm, plaka 1.50 mm, tuş adımı 19.05 mm |
| Firmware | Arduino / PlatformIO, `ARDUINO_USB_MODE=0` (TinyUSB) |
| Uygulama | Python 3.10+, CustomTkinter, pyserial, pyautogui, pystray |
| Yapılandırma | `config.json`, şema sürümü **3**, atomik yazma |

---

## Hızlı başlangıç

> ### 🔧 Cihazı yapacaksan buradan başla → **[docs/BASIT-YAPIM.md](docs/BASIT-YAPIM.md)**
>
> Tek dosyada tüm yapım yolu: 3 katmanlı yapı (plaka / delikli kart / gövde),
> 3D baskı için hazır delik koordinatları, dikey katman yığını, kablolama ve
> montaj sırası. PCB tasarımı yok, karmaşık CAD yok.
>
> Aşağıdaki bölümler ve `docs/01`–`docs/08` daha derin referanstır.

### 1. Donanım

Anahtarları, enkoderi ve LED'leri şu pinlere bağlayın. **Tüm anahtarlar
aktif-LOW**: bir bacak GPIO'ya, diğer bacak GND'ye.

| İşlev | GPIO | | İşlev | GPIO |
|---|---|---|---|---|
| K1 | 4 | | K9 | 8 |
| K2 | 5 | | K10 (COMBO) | 9 |
| K3 | 6 | | K11 (OS) | 10 |
| K4 | 7 | | ENC_A | 11 |
| K5 | 15 | | ENC_B | 12 |
| K6 | 16 | | ENC_SW | 13 |
| K7 | 17 | | LED_DATA | 14 (330 Ω üzerinden) |
| K8 | 18 | | | |

Üç zorunlu ek bileşen: LED besleme hattına **1N4148 diyot**, LED uçlarına
**1000 µF** kondansatör, enkoderin A ve B kanallarına **10 kΩ + 100 nF** RC filtresi.
Gerekçeleri ve hesapları için → [`docs/06-ONEMLI-NOTLAR.md`](docs/06-ONEMLI-NOTLAR.md)
maddeler 7, 8, 12.

> **GPIO 0, 3, 19, 20, 26–37, 43–46 kullanılmaz.** Gerekçeler için
> [`docs/00-CEKIRDEK-SPEC.md`](docs/00-CEKIRDEK-SPEC.md) bölüm 3.2.

### 2. Firmware

```bash
cd firmware
pio run --target upload
```

`platformio.ini` içinde şu iki bayrak **zorunludur**; olmadan cihaz HID
klavye olarak hiç görünmez:

```ini
build_flags =
    -D ARDUINO_USB_MODE=0
    -D ARDUINO_USB_CDC_ON_BOOT=1
```

Kabloyu DevKit üzerindeki **"USB"** yazan sokete takın (**"UART"** yazana değil).

### 3. Uygulama

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_app.py
```

macOS'ta ilk çalıştırmada **Sistem Ayarları → Gizlilik ve Güvenlik →
Erişilebilirlik** ve **Girdi İzleme** izinlerini verin, ardından uygulamayı
**kapatıp yeniden açın**. Bu adım atlanırsa kısayol ve metin eylemleri sessizce
hiçbir şey yapmaz.

---

## Dosya düzeni

```
ExtraKeyboard/
├── README.md                    # bu dosya
├── run_app.py                   # v3 giriş noktası
├── config.json                  # v3 yapılandırma (ilk çalıştırmada üretilir)
├── Main.py                      # ESKİ v2 — dokunulmadı, referans olarak duruyor
├── macro_config.json            # ESKİ v2 yapılandırma — otomatik migrate edilir
│
├── docs/                        # dokümantasyon (00–08)
│   ├── 00-CEKIRDEK-SPEC.md      # TEK DOĞRULUK KAYNAĞI
│   ├── 01-DONANIM.md
│   ├── 02-MEKANIK.md
│   ├── 03-FIRMWARE.md
│   ├── 04-PC-UYGULAMASI.md
│   ├── 05-MONTAJ.md
│   ├── 06-ONEMLI-NOTLAR.md      # incelikler ve tuzaklar (70 madde)
│   ├── 07-SORUN-GIDERME.md
│   ├── 08-YOL-HARITASI.md
│   └── INDEX.md                 # doküman haritası
│
├── firmware/
│   ├── platformio.ini
│   └── src/                     # main.cpp, keys, encoder, leds, protocol, storage
│
├── hardware/                    # şematik, BOM, kablolama tablosu
├── mechanical/                  # OpenSCAD kaynakları + DXF üretici
│
├── app/
│   ├── main.py                  # tekil örnek kontrolü + kurulum
│   ├── core/
│   │   ├── config.py            # ConfigManager, slot isimleri, şema
│   │   ├── device.py            # DeviceLink — seri thread, otomatik bağlanma
│   │   └── actions.py           # ActionRunner — 10 eylem tipi
│   └── ui/
│       ├── main_window.py       # sekmeler: Tuşlar / Combolar / Enkoder / LED / Ayarlar
│       ├── key_grid.py          # 4×3 fiziksel yerleşim
│       ├── combo_matrix.py      # 9×9 üst üçgen (36 hücre)
│       ├── action_editor.py     # tip + değer + gözat diyaloğu
│       └── tray.py              # sistem tepsisi simgesi
│
└── tools/
    └── migrate_v2_config.py     # macro_config.json → config.json
```

---

## Dokümantasyon haritası

Hepsi `docs/` altındadır. Ayrıntılı yönlendirme için
[`docs/INDEX.md`](docs/INDEX.md) dosyasına bakın.

| Doküman | İçerik |
|---|---|
| [`00-CEKIRDEK-SPEC.md`](docs/00-CEKIRDEK-SPEC.md) | **Tek doğruluk kaynağı.** Pin şeması, protokol, JSON şeması, ölçüler, modül API'leri. Bir çelişki görürsen bu dosya kazanır. |
| [`01-DONANIM.md`](docs/01-DONANIM.md) | Elektronik şema, malzeme listesi (BOM), kablolama tablosu, LED ve enkoder devreleri. |
| [`02-MEKANIK.md`](docs/02-MEKANIK.md) | Kasa ve plaka ölçüleri, OpenSCAD parametreleri, DXF üretimi, 3D baskı ayarları. |
| [`03-FIRMWARE.md`](docs/03-FIRMWARE.md) | ESP32-S3 firmware mimarisi, durum makineleri, protokol gerçeklemesi, derleme ve yükleme. |
| [`04-PC-UYGULAMASI.md`](docs/04-PC-UYGULAMASI.md) | Python uygulamasının modül yapısı, `core/` ve `ui/` sözleşmeleri, eylem tipleri, tema. |
| [`05-MONTAJ.md`](docs/05-MONTAJ.md) | Adım adım montaj: lehimleme sırası, ölçüm kontrolleri, ilk çalıştırma, izinler. |
| [`06-ONEMLI-NOTLAR.md`](docs/06-ONEMLI-NOTLAR.md) | **70 maddelik incelik listesi.** Her madde: risk, neden, çözüm, belirti. Bir şey çalışmıyorsa önce buraya bak. |
| [`07-SORUN-GIDERME.md`](docs/07-SORUN-GIDERME.md) | Belirtiden teşhise giden akış: cihaz görünmüyor, LED yanmıyor, eylem çalışmıyor… |
| [`08-YOL-HARITASI.md`](docs/08-YOL-HARITASI.md) | Sürüm geçmişi, planlanan özellikler, bilinen sınırlamalar. |

---

## Gereksinimler

### Donanım

| Parça | Adet | Not |
|---|---|---|
| ESP32-S3-DevKitC-1 (N16R8) | 1 | Yerleşik USB OTG şart |
| MX uyumlu mekanik anahtar | 11 | Herhangi bir ağırlık |
| Keycap (1u) | 11 | Düşük profil önerilir (XDA / DSA / Cherry) |
| EC11 döner enkoder (butonlu) | 1 | M7 × 0.75 dişli burç |
| Enkoder knob | 1 | **En fazla 20 mm çap** |
| WS2812B LED modülü | 3 | 5 V, tekil modül |
| 1N4148 diyot | 1 | LED besleme hattında |
| 1000 µF / 10 V elektrolitik kondansatör | 1 | LED uçlarında |
| 330 Ω direnç | 1 | LED veri hattında |
| 10 kΩ direnç | 2 | Enkoder RC filtresi |
| 100 nF kondansatör | 2 | Enkoder RC filtresi |
| ~~Vida / insert~~ | 0 | Gövde **geçmeli** (snap-fit), donanım gerekmez |
| Silikon ayak | 4 | ⌀8 mm (taban çukuru `foot_d = 8.00`) |
| 26 AWG çok telli silikon tel | 7 renk × 2 m | Net tüketim ≈ 1.90 m |
| USB-C **veri** kablosu | 1 | Şarj kablosu iş görmez |

### Yazılım

- **Firmware:** PlatformIO (veya Arduino IDE 2.x) + `espressif32` platformu,
  `Adafruit NeoPixel` (ya da `FastLED`), `Adafruit TinyUSB`.
- **Uygulama:** Python **3.10+**, `customtkinter`, `pyserial`, `pyautogui`,
  `pyperclip`, `pystray`, `Pillow`.
- **İşletim sistemi:** Windows 10/11 veya macOS 12+.

---

## Sık sorulanlar

**Uygulamayı kurmadan da çalışır mı?**
Kısmen. Uygulama kapalıyken cihaz HID yedek moduna geçer: K1–K9 sırasıyla
`F13`–`F21`, K11 `F22` gönderir ve enkoder sesi doğrudan kontrol eder.
**Combo bu modda devre dışıdır** ve LED3 kırmızı yanıp söner.

**Combo nasıl yapılır?**
`K10`'a **bir kez basın** (basılı tutmak gerekmez — LED2 turuncu yanıp mod kilitlenir), ardından K1–K9 arasından iki tuşa dokunun; combo tetiklenir ve mod kendiliğinden kapanır. Vazgeçerseniz K10'a tekrar basın; 10 sn işlem yapılmazsa mod kendiliğinden kapanır. Sıra önemsizdir.
`K10` basılıyken tuşların normal eylemleri **çalışmaz**.

**Neden 36 combo?**
9 tuştan sırasız 2 tanesini seçmek: C(9,2) = (9 × 8) / 2 = 36.

**Windows ve macOS ayarları neden ayrı?**
Uygulama yolları (`C:\...\chrome.exe` ⇄ `/Applications/Chrome.app`) ve kısayollar
(`ctrl+c` ⇄ `command+c`) iki sistemde farklıdır. `K11` tuşuyla profil anında
değişir, LED1 rengi hangisinde olduğunuzu gösterir.

**macOS'ta kısayollar çalışmıyor.**
Erişilebilirlik ve Girdi İzleme izinlerini verip uygulamayı **kapatıp yeniden
açın**. İzin, çalışan bir sürece geriye dönük uygulanmaz.
→ [`06-ONEMLI-NOTLAR.md`](docs/06-ONEMLI-NOTLAR.md) madde 35–36.

**Cihaz seri port olarak görünüyor ama klavye olarak görünmüyor.**
`ARDUINO_USB_MODE=0` bayrağı eksik ya da kablo DevKit'in "UART" soketinde.
→ [`06-ONEMLI-NOTLAR.md`](docs/06-ONEMLI-NOTLAR.md) madde 1–2.

**Uygulama cihaza bağlanamıyor.**
Arduino IDE Seri Monitörü veya PlatformIO monitörü açık olabilir; seri port aynı
anda tek uygulama tarafından açılabilir. → madde 42.

**Türkçe karakterler yazılmıyor.**
`text` eylemi ASCII dışı karakterleri pano üzerinden yapıştırır. Hedef uygulama
yapıştırmayı desteklemiyorsa çalışmayabilir. → madde 37.

**Enkoder ters yönde çalışıyor.**
A ve B tellerini (GPIO11 ⇄ GPIO12) yer değiştirin ya da firmware'deki
`ENC_REVERSED` sabitini değiştirin. → madde 14.

**Ses bir tıkta iki kademe değişiyor.**
Hem cihaz HID gönderiyor hem uygulama medya eylemi çalıştırıyor. Enkoder modu
`hid` iken uygulama eylem çalıştırmamalıdır. → madde 60.

**v2 ayarlarım ne olacak?**
`macro_config.json` ilk çalıştırmada otomatik olarak `config.json`'a taşınır
(`tools/migrate_v2_config.py`). Eski dosyaya dokunulmaz.

**Kasa 3D yazıcı olmadan yapılabilir mi?**
Plakayı 1.5 mm alüminyum, pirinç veya FR4'ten lazer/CNC kestirebilirsiniz;
`mechanical/` altındaki DXF üretici bunun için vardır. Gövde için hazır bir
proje kutusu da kullanılabilir.

---

## Sürüm notları

### v3.0.0 — bu sürüm

Sıfırdan yeniden tasarlandı. v2'den taşınan tek şey `macro_config.json` içindeki
kullanıcı ayarlarıdır.

| Konu | v2 | **v3** |
|---|---|---|
| Tuş sayısı | 8 | **11** (9 işlev + combo + OS) |
| Kombinasyon | C(8,2) = 28 | **C(9,2) = 36** |
| Durum LED'i | yok | **3 × WS2812B** (OS / combo / bağlantı) |
| Enkoder | yok | **EC11** (çevir / bas / uzun bas) |
| Cihaz → PC yolu | Global klavye dinleyicisi; cihaz `Ctrl+Shift+Alt+F13..F20` gönderirdi | **Gerçek CDC seri protokol** (`EV KEY 3 UP`, `EV COMBO 2 5`) |
| PC → cihaz yolu | yok | **Komutlar** (`CMD LED`, `CMD OS`, `CMD ENC MODE`, `CMD SAVE`) |
| Profiller | Tek liste, OS ayrımı sadece kısayolda | **Ayrı `windows` / `mac` profilleri**, çoklu profil desteği |
| Eylem tipleri | 4 (`none`, `app`, `url`, `shortcut`) | **10** (+ `text`, `command`, `file`, `folder`, `media`, `macro`) |
| Yapılandırma | `macro_config.json`, şemasız | `config.json`, **şema 3**, atomik yazma, migrate desteği |
| Uygulama kapalıyken | Hiçbir şey çalışmaz | **HID yedek modu** (F13–F22 + ses) |
| Mimari | Tek dosya (`Main.py`, ~1000 satır) | `app/core` + `app/ui` ayrımı, sözleşmeli modül API'si |

**Neden `Ctrl+Shift+Alt+F13` hilesi bırakıldı?**
v2'de cihaz, normal bir klavye gibi F13–F20 gönderiyordu; uygulama da global bir
klavye dinleyicisiyle bunları yakalıyordu. Bu yaklaşımın üç sorunu vardı:
(1) tuş kombinasyonu her uygulamaya sızıyordu, (2) global dinleyici işletim
sisteminden özel izin gerektiriyordu ve bazı pencerelerde hiç çalışmıyordu,
(3) cihazdan bilgisayara **veri** göndermek (combo durumu, enkoder yönü) mümkün
değildi. v3'te ayrı bir CDC seri kanalı kullanılır: veri girdi akışına hiç
karışmaz, iki yönlüdür ve genişletilebilir.

### Bilinen sınırlamalar

- Combo, HID yedek modunda (uygulama kapalıyken) çalışmaz.
- Windows'ta yönetici yetkili pencerelere kısayol gönderilemez (UIPI).
- macOS'ta `media` eylemlerinin oynat/duraklat kısmı uygulamaya bağımlıdır.
- BLE desteği yoktur; bu bilinçli bir tasarım kararıdır
  (→ [`06-ONEMLI-NOTLAR.md`](docs/06-ONEMLI-NOTLAR.md) madde 63).

---

## Lisans

Bu depoda ayrı bir lisans dosyası bulunmamaktadır; tüm hakları saklıdır.
Kişisel ve eğitim amaçlı kullanım, çoğaltma ve değiştirme serbesttir.
Ticari kullanım için **BlueDevelopment** ile iletişime geçin.

Üçüncü taraf bileşenler kendi lisanslarına tabidir (Arduino-ESP32, Adafruit
TinyUSB, Adafruit NeoPixel / FastLED, CustomTkinter, pyserial, pyautogui,
pystray, Pillow).

---

<sub>ExtraKeyboard MK1 · Firmware 3.0.0 · Uygulama 3.0.0 · Donanım MK1 · BlueDevelopment</sub>
