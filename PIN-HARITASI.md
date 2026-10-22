# ExtraKeyboard MK1 — Pin Haritası

ESP32-S3-DevKitC-1 tabanlı. Kaynak: `firmware/src/config.h` (tam klavye) ve
`firmware-numpad/src/config.h` (numpad varyantı).

**Genel kurallar (her iki varyant):**
- Tüm anahtarlar **aktif-LOW + `INPUT_PULLUP`**: tuşun bir bacağı GPIO'ya, diğer
  bacağı **ortak GND**'ye gider. Basılınca GPIO GND'ye çekilir (LOW = basılı).
- **Matris YOK, diyot YOK** — her tuş kendi GPIO'suna doğrudan bağlı.
- LED devresi: **GPIO → 330 Ω → LED anot (uzun bacak); katot (kısa bacak) → GND.**
- Bağlantı: cihazın **native USB** portu (kart üstünde "USB" yazan konnektör),
  D-/D+ = GPIO19/GPIO20 (dahili, harici bağlantı yok).

---

## 1) TAM KLAVYE (MK1) — 12 tuş + 1 enkoder + 3 LED

| GPIO | Bağlandığı | İşlev | Not |
|-----:|-----------|-------|-----|
| 4  | K1  | İşlev tuşu 1 | anahtar → GND |
| 5  | K2  | İşlev tuşu 2 | anahtar → GND |
| 6  | K3  | İşlev tuşu 3 | anahtar → GND |
| 7  | K4  | İşlev tuşu 4 | anahtar → GND |
| 15 | K5  | İşlev tuşu 5 | anahtar → GND |
| 16 | K6  | İşlev tuşu 6 | anahtar → GND |
| 17 | K7  | İşlev tuşu 7 | anahtar → GND |
| 18 | K8  | İşlev tuşu 8 | anahtar → GND |
| 10 | K11 | **Tuş 9** (işlev) | üst sıra · rol varsayılan derlemeye göre (bkz. bölüm 3) |
| 9  | K10 | **Tuş 10** (işlev) | üst sıra · 〃 |
| 8  | K9  | **COMBO** tuşu | üst sıra · combo modunu açar/kapatır |
| 21 | K12 | **OS** tuşu | üst sıra · J3-18 · kısa: Win/Mac · uzun (3 sn): HID yedek |
| 11 | ENC_A | Enkoder A kanalı | EC11 + RC donanım debounce |
| 12 | ENC_B | Enkoder B kanalı | EC11 + RC donanım debounce |
| 13 | ENC_SW | Enkoder butonu | basınca GND |
| 14 | LED1 (Windows) | Durum LED'i | J1-20 · Windows modunda yanar |
| 42 | LED2 (macOS) | Durum LED'i | J3-6 · macOS modunda yanar |
| 41 | LED3 (COMBO) | Durum LED'i | J3-7 · combo modunda yanar |

---

## 2) NUMPAD VARYANTI — 16 tuş + 2 LED (enkoder YOK)

Enkoder ve LED_WIN pinleri (11/12/13/14) burada **tuş** olur.

| GPIO | Bağlandığı | Fiziksel konum | Yazdığı (keypad) |
|-----:|-----------|----------------|------------------|
| 4  | K1  | alt sıra 1 | KP0 (0) |
| 5  | K2  | alt sıra 2 | KP. (.) |
| 6  | K3  | alt sıra 3 | KPEnter (⏎) |
| 7  | K4  | alt sıra 4 | KP+ (+) |
| 15 | K5  | 3. sıra 1  | KP1 (1) |
| 16 | K6  | 3. sıra 2  | KP2 (2) |
| 17 | K7  | 3. sıra 3  | KP3 (3) |
| 18 | K8  | 3. sıra 4  | KP- (−) |
| 8  | K9  | 2. sıra 1  | KP4 (4) |
| 9  | K10 | 2. sıra 2  | KP5 (5) |
| 10 | K11 | 2. sıra 3  | KP6 (6) |
| 21 | K12 | 2. sıra 4  | KP* (*) |
| 11 | K13 | üst sıra 1 | KP7 (7) |
| 12 | K14 | üst sıra 2 | KP8 (8) |
| 13 | K15 | üst sıra 3 | KP9 (9) |
| 14 | K16 | üst sıra 4 | KP/ (/) |
| 42 | LED0 | — | Windows modu göstergesi (yanık=Win) |
| 41 | LED1 | — | macOS modu göstergesi (yanık=Mac) |

Fiziksel düzen (üstten alta):
```
7 8 9 /     (Tuş 13-16, GPIO 11,12,13,14)
4 5 6 *     (Tuş  9-12, GPIO 8,9,10,21)
1 2 3 −     (Tuş  5-8,  GPIO 15,16,17,18)
0 . ⏎ +     (Tuş  1-4,  GPIO 4,5,6,7)
```
Mod değişimi: **0 (GPIO4) basılı tut + Enter (GPIO6)** → Windows/macOS geçişi.

---

## 3) Uygulamadaki "Tuş N" ↔ GPIO eşlemesi (tam klavye)

Uygulama tuşları `keys.cpp` içindeki `KEY_PINS[]` dizisinin SIRASINA göre
numaralanır. Tuş 1–8 her birimde aynıdır (GPIO 4, 5, 6, 7, 15, 16, 17, 18).
**Üst sıranın dört tuşu birime göre farklı kablolanmıştır** ve rolü derleme
ortamı seçer (`platformio.ini`):

| Rol | `[env:quad]` / `[env:n16r8]` — **varsayılan, yeni yapımlar** | `[env:e74610]` |
|-----|----------------|----------------|
| Tuş 9  | GPIO10 | GPIO21 |
| Tuş 10 | GPIO9  | GPIO8  |
| COMBO  | GPIO8  | GPIO9  |
| OS     | GPIO21 | GPIO10 |

> **Yeni yapımda** üst sırayı soldaki sütuna göre kablola. Tuşlar yine karışık
> çıkarsa kabloyu sökmek gerekmez: `keys.cpp`'deki `KEY_PINS` sırasını değiştir
> (ya da `EK_KEYMAP_SWAPPED` gibi bir bayrakla kendi ortamını aç). Hangi tuşun
> hangi olayı ürettiğini uygulamanın **LED & Cihaz → Canlı Olay Logu** gösterir.
> GPIO↔pin etiketi (K1..K12) `config.h`'de sabittir; değişen yalnızca hangi
> fiziksel tuşun hangi rolü aldığıdır. (Eski not "bu eşleme 5 klavyede geçerli"
> diyordu — YANLIŞTI: takas yalnızca E74610'da var.)

---

## 4) ESP32-S3 AYRILMIŞ / KRİTİK PİNLER — bunlara tuş/LED BAĞLANMAZ

Bu proje aşağıdaki pinlerin hiçbirini tuş/LED için kullanmaz (doğru tercih):

| Pin(ler) | Ne için ayrılmış | Bağlanırsa ne olur |
|---------|------------------|--------------------|
| **19, 20** | Native USB D-/D+ | USB tamamen bozulur |
| 26–32 | Dahili SPI flash | Kart açılmaz/çöker |
| 33–37 | Octal PSRAM (N16R8) | PSRAM'li kartta çöker |
| **0** | Boot strapping (BOOT düğmesi) | Boot moduna takılır |
| 3, 45, 46 | Strapping | Boot/besleme sorunları |
| 43, 44 | UART0 konsol | (native USB kullanıldığı için boş) |
| 38, 48 | Dahili RGB LED (bazı kartlar) | Firmware GPIO48'i söndürür |
| 39, 40, 41, 42 | Pin-JTAG (MTCK/MTDO/MTDI/MTMS) | 41/42 LED olarak kullanılıyor* |

\* **GPIO41/42 (LED2/LED3):** Bunlar pin-JTAG hatları, ama proje **native
USB-JTAG** kullandığı için bu pinleri LED çıkışı yapmak güvenlidir; USB'yi
etkilemez.

**Sonuç:** Pin şeması temiz — hiçbir tuş/LED USB, flash, PSRAM veya strapping
pinine düşmez. Yani bağlantı kopmaları pin çakışmasından değildir.

---

## 5) Boş / genişleme için uygun GPIO'lar

Tam klavyede kullanılmayan, yeni tuş eklemek için uygun pinler: **1, 2, 39, 40,
47**. (38 ve 48 bazı kartlarda dahili RGB LED'dir — kullanma.)

---

## 6) Bellek / flash yapılandırması (pin değil ama kritik)

ESP32-S3 modülleri aynı görünse de **bellek tipi farklı olabilir** ve yanlış
ayar kartı hiç açılmaz hâle getirir (boot döngüsü, log'da `ets_loader.c 78`).
Yüklemeden önce `esptool.py --chip esp32s3 flash_id` ile oku:

| `flash_id` çıktısı | Ortam | memory_type | flash |
|---|---|---|---|
| `Embedded PSRAM 2MB` (Quad) + 8 MB flash | `[env:quad]` | `qio_qspi` | 8 MB |
| `Embedded PSRAM 8MB` (Octal) + 16 MB flash — **N16R8** | `[env:n16r8]` | `qio_opi` | 16 MB |

**Flash'a yazarken DIO + 40 MHz şart:** `--flash_mode dio --flash_freq 40m`.
Bu kartlardaki Boya (`Manufacturer: 68`) flash çipleri QIO/80 MHz ile ROM
tarafından okunamıyor. Derleme qio/80m kalır (hazır `dio_40m` bootloader
yoktur), başlığı esptool yazarken değiştirir. Bu yüzden düz
`pio run -t upload` **kullanılmaz**; yordam için README'nin Firmware bölümü.
