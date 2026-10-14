# ExtraKeyboard MK1 — Firmware

ESP32-S3 (ESP32-S3-DevKitC-1, WROOM-1 **N16R8**) için PlatformIO + Arduino
framework ile yazılmış cihaz yazılımı.

Tüm pinler, protokol mesajları, renkler ve süreler
[`../docs/00-CEKIRDEK-SPEC.md`](../docs/00-CEKIRDEK-SPEC.md) dosyasından alınmıştır.
Bir çelişki görürsen o dosya kazanır.

---

## 1. Gereksinimler

| Araç | Sürüm |
|---|---|
| PlatformIO Core (CLI) | 6.1 veya üzeri |
| `espressif32` platformu | `^6.5.0` (ilk derlemede otomatik iner) |
| Adafruit NeoPixel | `^1.12.0` (otomatik iner) |

PlatformIO kurulu değilse:

```bash
python3 -m pip install --user platformio
```

VS Code kullanıyorsan "PlatformIO IDE" eklentisi de yeterlidir.

---

## 2. Derleme

```bash
cd firmware
pio run
```

İlk derleme araç zincirini indirdiği için birkaç dakika sürebilir.

---

## 3. Yükleme

Kartı USB-C ile bağla. macOS'ta port genellikle `/dev/cu.usbmodem*`,
Linux'ta `/dev/ttyACM*`, Windows'ta `COMx` olur.

```bash
pio run --target upload
```

Port otomatik bulunamazsa elle ver:

```bash
pio run --target upload --upload-port /dev/cu.usbmodem101
```

**Kart yükleme moduna girmiyorsa:** `BOOT` düğmesini basılı tut, `RESET`'e
bir kez bas, `BOOT`'u bırak ve komutu tekrar çalıştır.

İlk yüklemeden sonra cihaz kendi USB kimliğiyle
(`VID 0x303A` / `PID 0x82E1` / `ExtraKeyboard MK1`) yeniden numaralandırılır;
bu yüzden port adı değişebilir.

---

## 4. Seri izleme (hata ayıklama)

```bash
pio device monitor
```

Cihaz saniyede bir `HB <uptime_ms>` yollar. Elle komut denemek için:

```
CMD ID
CMD PING
CMD OS MAC
CMD LED 1 1E90FF
CMD LED BRIGHT 90
CMD LED 1 AUTO
CMD ENC MODE HOST
CMD HIDFB OFF
CMD SAVE
```

> **Not:** Cihaz "uygulama bağlı" sayılmak için hem CDC DTR sinyalinin yüksek
> olmasını hem de **son 3 saniye içinde** PC'den bir satır almış olmayı ister.
> PC uygulaması bu yüzden en az 3 saniyede bir `CMD PING` göndermelidir.
> Aksi hâlde cihaz HID yedek moduna düşer (LED3 kırmızı olur).

---

## 5. En kritik ayar

`platformio.ini` içindeki şu iki bayrak **asla değiştirilmemelidir**:

```ini
-D ARDUINO_USB_MODE=0
-D ARDUINO_USB_CDC_ON_BOOT=1
```

`ARDUINO_USB_MODE=1` yapılırsa TinyUSB yığını devre dışı kalır; cihaz sadece
seri port olarak görünür ve **USB HID (F13–F22, ses tuşları) hiç çalışmaz.**

N16R8 modülü için bellek ayarları da zorunludur:

```ini
board_build.arduino.memory_type = qio_opi   ; Quad flash + Octal PSRAM
board_build.partitions          = default_16MB.csv
board_upload.flash_size         = 16MB
```

Bunlar yanlış olursa kart açılışta sürekli yeniden başlar.

---

## 6. Kaynak dosyaları

| Dosya | Görevi |
|---|---|
| `src/config.h` | Pinler, süreler, renkler, sürümler, USB kimliği |
| `src/keys.h/.cpp` | 11 tuş okuma, 5 ms debounce, combo durum makinesi |
| `src/encoder.h/.cpp` | EC11 quadrature durum tablosu çözücüsü + buton |
| `src/leds.h/.cpp` | 3× WS2812B durum LED'i, bloklamayan flaşlar |
| `src/protocol.h/.cpp` | CDC satır tabanlı olay gönderme / komut ayrıştırma |
| `src/hid.h/.cpp` | USB HID klavye (F13–F22) ve ses tuşları |
| `src/storage.h/.cpp` | NVS: OS modu, HID yedek, enkoder modu, LED ayarları |
| `src/main.cpp` | USB kurulumu, olay döngüsü, bağlantı takibi |

---

## 7. Pin özeti (spec bölüm 3.1)

| İşlev | GPIO | | İşlev | GPIO |
|---|---|---|---|---|
| K1 | 4 | | K8 | 18 |
| K2 | 5 | | K9 | 8 |
| K3 | 6 | | K10 (COMBO) | 9 |
| K4 | 7 | | K11 (OS) | 10 |
| K5 | 15 | | ENC_A | 11 |
| K6 | 16 | | ENC_B | 12 |
| K7 | 17 | | ENC_SW | 13 |
| | | | LED_DATA | 14 |

Tüm anahtarlar aktif-LOW, `INPUT_PULLUP`, matris yok, diyot yok.

---

## 8. Cihaz üzerindeki kısayollar

| Hareket | Sonuç |
|---|---|
| `K11` kısa basış (< 800 ms) | Windows ⇄ macOS geçişi, NVS'e kaydedilir, LED1 rengi değişir |
| `K11` uzun basış (≥ 3 s) | HID yedek modu açılır/kapanır, LED3 üç kez beyaz yanar |
| `K10` basılı tutma | Combo modu (LED2 turuncu); K1..K9'dan iki tanesi combo üretir |
| Enkoder çevirme | Ses artır / azalt |
| Enkoder kısa basış | Sessize al |
| Enkoder uzun basış (≥ 800 ms) | `EV ENC LONG` (eylemini PC belirler) |

---

## 9. LED anlamları (spec bölüm 6.4)

| LED | Durum | Renk |
|---|---|---|
| LED1 | Windows | `#1E90FF` mavi |
| LED1 | macOS | `#FFFFFF` beyaz |
| LED2 | Combo kapalı | sönük |
| LED2 | Combo modu açık | `#FF9500` turuncu |
| LED2 | Combo tetiklendi (150 ms) | `#2CC985` yeşil |
| LED3 | Uygulama bağlı | `#2CC985` yeşil |
| LED3 | Uygulama yok / HID yedek | `#E04F5F` kırmızı |
| LED3 | Tuş aktivitesi (80 ms) | `#3B8ED0` mavi |

Varsayılan parlaklık `60/255`.

---

## 10. Sık karşılaşılan sorunlar

| Belirti | Çözüm |
|---|---|
| Cihaz HID göndermiyor | `ARDUINO_USB_MODE=0` olduğunu doğrula, tam temizlik yap: `pio run -t fullclean` |
| Kart sürekli yeniden başlıyor | `memory_type = qio_opi` ve `BOARD_HAS_PSRAM` ayarlarını kontrol et |
| LED'ler hiç yanmıyor / rastgele | +5 V hattına 1N4148 diyot, veri hattına 330 Ω, besleme uçlarına 1000 µF eklendiğini doğrula |
| Enkoder çift sayıyor | Her iki kanalda 10 kΩ + 100 nF RC filtresinin takılı olduğunu doğrula |
| Port görünmüyor | `BOOT` + `RESET` ile yükleme moduna al ve yeniden yükle |
