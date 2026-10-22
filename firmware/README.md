# ExtraKeyboard MK1 — Firmware (klavye)

ESP32-S3-DevKitC-1 (ESP32-S3-WROOM-1) için PlatformIO + Arduino çekirdeği
(arduino-esp32 2.0.17) ile yazılmış cihaz yazılımı. Numpad varyantı:
[`../firmware-numpad/`](../firmware-numpad/).

| Konu | Kaynak |
|---|---|
| Kablolama ve pinler (birim farkları dahil) | [`../PIN-HARITASI.md`](../PIN-HARITASI.md) |
| Yapım ve yükleme | [`../README.md`](../README.md#4-firmware) |
| Protokol (`EV …` / `CMD …`) | [`../docs/03-PROTOKOL.md`](../docs/03-PROTOKOL.md) |
| Sabitler: pinler, süreler, USB kimliği | [`src/config.h`](src/config.h) |

---

## 1. Hazır imaj

Derlemeden yüklemek için
[Sürümler](https://github.com/MusaCanBacak/ExtraKeyboard-MK1/releases/latest)
sayfasındaki `ExtraKeyboard-Firmware.zip`'i kullanın. Yükleyici kartı kutusunu
açmadan günceller ve modülü kendisi tanır.

## 2. Ortamlar

Kartlar aynı görünse de bellek tipleri farklıdır ve **yanlış ortam kartı boot
döngüsüne sokar** (kart hiç açılmaz).

| Ortam | Modül | Bellek ayarı | Üst sıra tuşları |
|---|---|---|---|
| `n16r8` | WROOM-1 N16R8 — 16 MB flash + 8 MB Octal PSRAM | `qio_opi`, `default_16MB.csv` | orijinal |
| `quad` | WROOM-1 N8R2 — 8 MB flash + 2 MB Quad PSRAM | `qio_qspi`, `default_8MB.csv` | orijinal |
| `e74610` | N16R8 — yalnızca E74610 birimi | `qio_opi` | takaslı (`EK_KEYMAP_SWAPPED`) |

Modülü öğrenmek için kart indirme modundayken `esptool --chip esp32s3 flash-id`
çalıştırın: `Embedded PSRAM 8MB` → N16R8, `Embedded PSRAM 2MB` → N8R2.

## 3. Derleme

```bash
cd firmware
pio run -e n16r8          # ya da: pio run -e quad
```

Dört genel imajı (klavye + numpad, N16R8 + N8R2) derleyip birleştirmek ve
doğrulamak için kök dizinde `python3 tools/imaj-olustur.py` kullanın.

## 4. Yükleme

> **⚠️ `pio run -t upload` kullanmayın.** PlatformIO imajı QIO / 80 MHz başlığıyla
> yazar; bu kartlardaki Boya flash çipleri o ayarla okunamaz ve kart açılmaz (seri
> çıktıda `ets_loader.c 78`). Derleme `qio` / 80 MHz kalır, çünkü hazır bootloader
> ELF'leri yalnızca öyle gelir. Başlık **yazarken** DIO / 40 MHz yapılır.

Önerilen yol, kendi birleştirdiğiniz imajı yükleyiciyle yazmaktır. Yükleyici kartı
kutuyu açmadan indirme moduna alır, cihaz ayarlarını korur ve sonucu doğrular:

```bash
python3 dagitim/ExtraKeyboard-Firmware/yukle.py --imaj <birlesik-imaj.bin>
```

Parça parça elle yazmak için kart indirme modundayken (esptool 4.x sözdizimi):

```bash
esptool.py --chip esp32s3 --port <PORT> write_flash \
  --flash_mode dio --flash_freq 40m --flash_size 16MB \
  0x0     .pio/build/n16r8/bootloader.bin \
  0x8000  .pio/build/n16r8/partitions.bin \
  0xe000  ~/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin \
  0x10000 .pio/build/n16r8/firmware.bin
```

`quad` için `--flash_size 8MB` ve `.pio/build/quad/` kullanın. Kart
`CMD BOOTLOADER CONFIRM` ile indirme moduna alındıysa, yazmadan sonra
`FORCE_DOWNLOAD_BOOT` bayrağı kurulu kalır. Kart yeniden indirme moduna açılırsa
USB kablosunu çıkarıp takın; yükleyici bu bayrağı kendisi temizler.

## 5. Seri izleme

```bash
pio device monitor -e n16r8
```

Cihaz saniyede bir `HB <uptime_ms>` gönderir. Elle denenebilecek komutlar:
`CMD ID`, `CMD PING`, `CMD OS MAC`, `CMD LED BRIGHT 90`, `CMD ENC MODE HOST`,
`CMD HIDFB OFF`, `CMD SAVE`. Tam liste için protokol belgesine bakın.

> Cihaz kendini "uygulama bağlı" saymak için hem CDC DTR hattının yüksek olmasını
> hem de son 3 saniyede PC'den bir satır almış olmayı ister. Aksi hâlde HID yedek
> moduna düşer ve tuşlar `F13`–`F22` gönderir.

## 6. Değiştirilmemesi gereken ayarlar

```ini
-D ARDUINO_USB_MODE=0          ; TinyUSB: HID + CDC birlikte. 1 olursa HID hiç çalışmaz.
-D ARDUINO_USB_CDC_ON_BOOT=1   ; Serial = USB CDC (uygulamanın konuştuğu port)
```

USB kimliği de derleme bayrağıdır (üretici `BlueDevelopment`, ürün
`ExtraKeyboard MK1`), çünkü TinyUSB `setup()`'tan önce başlar.

## 7. Kaynak dosyaları

| Dosya | Görevi |
|---|---|
| `src/config.h` | Pinler, süreler, sürüm, USB kimliği, bekçi süreleri |
| `src/keys.h/.cpp` | 12 tuş okuma (8 ms debounce), `KEY_PINS` sırası, combo durum makinesi |
| `src/encoder.h/.cpp` | EC11 durum tablosu çözücüsü + buton |
| `src/leds.h/.cpp` | 3 düz LED (Windows / macOS / COMBO), bloklamayan yanıp sönmeler |
| `src/protocol.h/.cpp` | CDC satır protokolü, `CMD BOOTLOADER CONFIRM`, gönderim tıkanma bekçisi |
| `src/hid.h/.cpp` | USB HID klavye (`F13`–`F22`) ve ses tuşları |
| `src/storage.h/.cpp` | NVS: OS modu, HID yedek, enkoder modu, LED ayarları |
| `src/main.cpp` | USB kurulumu, döngü bekçisi, olay döngüsü, bağlantı takibi |
