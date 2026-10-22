# ExtraKeyboard MK1 — NUMPAD Varyantı

16 tuşlu + 2 LED'li **tak-çalıştır numpad**. Eş PC uygulamasına gerek yoktur;
tuşlar doğrudan gerçek keypad HID kodları gönderir (hem Windows hem macOS
otomatik tanır, sürücü/uygulama gerekmez).

> Bu varyant `firmware/` (12 tuş + enkoder + 3 LED, uygulama tabanlı) temel
> alınarak türetildi. Enkoder yoktur; 3 LED yerine 2 LED vardır; tuşlar
> uygulamaya EV KEY bildirmek yerine doğrudan keypad HID kodu yazar.

## Donanım
- Kart: **ESP32-S3-DevKitC-1** — modüle göre iki ortam (yanlış ortam boot-loop yapar):

| Ortam | Modül | `platformio.ini` |
|---|---|---|
| `extrakeyboard` | N8R2 — 8 MB flash + 2 MB Quad PSRAM (ör. birim 6F0568) | `qio_qspi`, `default_8MB.csv`, 8MB |
| `numpad_n16r8` | N16R8 — 16 MB flash + 8 MB Octal PSRAM | `qio_opi`, `default_16MB.csv`, 16MB |

## Pin dizilimi (4×4 tuş)
Tuş numarası = `keys.cpp` içindeki `KEY_PINS[]` sırası. Tüm tuşlar aktif-LOW,
`INPUT_PULLUP`, matris YOK — her tuşun bir bacağı GPIO'ya, diğeri ortak GND'ye.

| Tuş | GPIO | | Tuş | GPIO | | Tuş | GPIO | | Tuş | GPIO |
|----|----|-|----|----|-|----|----|-|----|----|
| 1  | 4  | | 2  | 5  | | 3  | 6  | | 4  | 7  |
| 5  | 15 | | 6  | 16 | | 7  | 17 | | 8  | 18 |
| 9  | 8  | | 10 | 9  | | 11 | 10 | | 12 | 21 |
| 13 | 11 | | 14 | 12 | | 15 | 13 | | 16 | 14 |

## LED'ler (2 adet, düz tek-renk, GPIO→330Ω→anot, katot→GND)
- **GPIO42** yanık = **Windows** modu
- **GPIO41** yanık = **macOS** modu
- Her an yalnızca biri yanar (aktif OS belli). Tuş basışında flaş YOK.
- Mod değişiminde ikisi birlikte 3 kez yanıp söner.

## Tuş haritası (fiziksel görünüm, üstten alta — "ters satır")
`hid.cpp` içindeki `NUMPAD_HID[]` tablosu. Tuş 1-4 fiziksel EN ALT sırayı,
Tuş 13-16 EN ÜST sırayı sürer → standart numpad düzeni:

```
üst  : 7 8 9 /     (Tuş 13 14 15 16)
       4 5 6 *     (Tuş  9 10 11 12)
       1 2 3 -     (Tuş  5  6  7  8)
alt  : 0 . ⏎ +     (Tuş  1  2  3  4)
```

HID usage kodları (sayfa 0x07, keypad): KP7=0x5F … KP0=0x62, KP.=0x63,
KP/=0x54, KP*=0x55, KP-=0x56, KP+=0x57, KPEnter=0x58. `pressRaw/releaseRaw`.

## Mod değiştirme kombosu: **"0"ı basılı tut + Enter'a bas**
- Ayrı OS tuşu olmadığından Windows/macOS geçişi bu kombodadır.
- **"0"ı basılı tut, Enter'a bas** → mod değişir; ne "0" ne Enter yazılır
  (sızıntısız), iki LED birlikte yanıp söner. NVS'e yazılır (kalıcı).
- "0"a tek başına bas-bırak → normal "0" (bırakışta yazılır; "0" basılıyken
  yazmaz çünkü Enter bekler — otomatik tekrar etmez).
- Enter'a "0" basılı değilken bas → normal Enter (anında).
- Kod: `main.cpp` `onKeyEvent()` + `doModeSwitch()`.

## Windows'ta NumLock notu
Windows'ta keypad rakam tuşları **yalnızca NumLock AÇIKken** rakam yazar
(kapalıyken yön/Home/End olurlar). `/ * - +` ve Enter her durumda çalışır.
macOS'ta bu sorun yoktur. Numpad'de NumLock tuşu yoktur; gerekirse ana
klavyeden aç. (İstenirse firmware'e NumLock kombosu/otomatiği eklenebilir.)

## Derleme ve yükleme
**Hazır imaj (önerilen):** [Sürümler](https://github.com/MusaCanBacak/ExtraKeyboard-MK1/releases/latest)
sayfasındaki `ExtraKeyboard-Firmware.zip` → yükleyiciyi çalıştırın → **Numpad**
seçin. Yükleyici modülü kendisi tanır, kutuyu açmadan yazar ve ayarları korur.

**Kaynaktan:**
```bash
cd firmware-numpad
~/.platformio/penv/bin/pio run -e extrakeyboard     # N8R2
~/.platformio/penv/bin/pio run -e numpad_n16r8      # N16R8
```
Yazma **DIO / 40 MHz** ile yapılmalıdır; `pio run -t upload` QIO / 80 MHz yazar
ve kart açılmaz (bkz. kök README → Firmware). Genel imajları üretmek için
`python3 tools/imaj-olustur.py`, bu projedeki birimleri güncellemek için
`python tools/yukle-kutusuz.py`.

Kart firmware çalıştırmıyorsa (boş kart) indirme moduna elle alın:
**BOOT tut → RST bas-bırak → BOOT'u bırak.** Not: bu kartlarda esptool'un RTS ile
attığı reset, ancak USB-JTAG reset dizisinden (`--before usb_reset`) sonra açılışı
tetikler; yükleyici bunu kendisi yapar.

## Doğrulama
Açılışta CDC'den `ID 3.0.0 MK1 EK1-xxxxxx WIN|MAC` gelir; her 1 sn `HB` atar.
Tuşlar bir metin alanında gerçek rakam/işaret yazmalı.
