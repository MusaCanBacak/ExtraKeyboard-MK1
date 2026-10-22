# 04 — Firmware Kurulum ve Yükleme Kılavuzu

> **Bağlayıcı kaynak:** [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) bölüm 3
> (pin şeması), bölüm 4 (USB kimliği) ve bölüm 10 (sürüm).
> Protokol ayrıntıları için [`03-PROTOKOL.md`](03-PROTOKOL.md).
>
> Hedef donanım: **ESP32-S3-DevKitC-1 (ESP32-S3-WROOM-1, N16R8)**
> Firmware sürümü: **3.0.0** · Donanım revizyonu: **MK1**

---

## İçindekiler

0. [Hızlı başlangıç](#0-hızlı-başlangıç)
1. [Gerekli araçlar ve kurulumu](#1-gerekli-araçlar-ve-kurulumu)
2. [Depoyu açma ve firmware klasörüne girme](#2-depoyu-açma-ve-firmware-klasörüne-girme)
3. [platformio.ini — satır satır açıklama](#3-platformioini--satır-satır-açıklama)
4. [İlk yükleme](#4-i̇lk-yükleme)
5. [Yükleme sonrası: yeniden numaralandırma](#5-yükleme-sonrası-yeniden-numaralandırma)
6. [Seri monitör ile doğrulama](#6-seri-monitör-ile-doğrulama)
7. [Arduino IDE 2.x ile alternatif yol](#7-arduino-ide-2x-ile-alternatif-yol)
8. [Sık karşılaşılan yükleme hataları](#8-sık-karşılaşılan-yükleme-hataları)
9. [Sıfırlama ve fabrika ayarlarına dönme](#9-sıfırlama-ve-fabrika-ayarlarına-dönme)
10. [Spec dışı varsayımlar](#10-spec-dışı-varsayımlar)

---

## 0. Hızlı başlangıç

Ortamı zaten kurmuş olanlar için özet:

```bash
cd ~/ExtraKeyboard-MK1/firmware

pio device list                 # portları listele
pio run                         # sadece derle
pio run -t upload               # derle ve yükle
pio device monitor              # HB akışını izle  (çıkış: Ctrl + C)
pio run -t erase                # flash'ı tamamen sil (NVS dahil)
```

**Kartı bootloader moduna alma:** `BOOT` tuşunu basılı tut → `RST` tuşuna bas ve
bırak → `BOOT` tuşunu bırak.

> **⚠️ Bu projenin kartlarında `pio run -t upload` KULLANMAYIN.** PlatformIO
> imajı QIO / 80 MHz olarak yazar; bu kartlardaki Boya flash çipleri bu ayarla
> ROM tarafından okunamaz ve kart **boot döngüsüne** girer (seri çıktıda
> `ets_loader.c 78`). Ayrıca modüller arasında bellek tipi farklıdır
> (`[env:quad]` / `[env:n16r8]`). Doğru yazma yordamı — `--flash_mode dio
> --flash_freq 40m`, birim ortamları ve kutusuz güncelleme — için kök dizindeki
> **README.md → Firmware** bölümüne bakın.

---

## 1. Gerekli araçlar ve kurulumu

Üç yol vardır. **A yolu önerilir**; B otomasyon/CI için, C ise PlatformIO
kurmak istemeyenler içindir.

| Yol | Araç | Kime uygun |
|---|---|---|
| **A — Önerilen** | VS Code + PlatformIO IDE eklentisi | Herkes. Ayarlar `platformio.ini`'den okunur, elle bir şey seçmek gerekmez. |
| **B** | PlatformIO CLI (`pio`) | Terminal alışkanlığı olanlar, betikle çalışanlar, CI |
| **C — Alternatif** | Arduino IDE 2.x | PlatformIO istemeyenler. **Menüden 15 ayarı elle doğru seçmek zorundasınız** (bölüm 7). |

### 1.0 Donanım: DevKitC-1'in İKİ USB portu

Devam etmeden önce bu ayrımı netleştirin, bölüm 8'deki hataların yarısı bundan
kaynaklanır:

```
                ESP32-S3-DevKitC-1  (üstten görünüm, USB portları sola bakar)
          ┌──────────────────────────────────────────────────────┐
          │  [RST]                                      [BOOT]   │
   ┌──────┤                                                      │
   │ UART │ ← USB-to-UART köprüsü (CP2102N)                      │
   └──────┤   • esptool buraya bağlanır                          │
          │   • firmware'in Serial protokolü BURADA GÖRÜNMEZ     │
   ┌──────┤                                                      │
   │ USB  │ ← ESP32-S3'ün yerleşik USB OTG'si (GPIO19 / GPIO20)  │
   └──────┤   • HID Keyboard + Consumer Control + CDC-ACM        │
          │   • ExtraKeyboard MK1 olarak numaralandırılan port    │
          │   • KUTUDAN DIŞARI ÇIKARILACAK port budur            │
          └──────────────────────────────────────────────────────┘
```

| Port etiketi | Ne işe yarar | Ne zaman kullanılır |
|---|---|---|
| **UART** | CP2102N USB-seri köprüsü. Otomatik reset devresi buradadır. | **İlk yükleme** ve sorun giderme. En güvenilir yükleme yolu. |
| **USB** | ESP32-S3 yerleşik USB OTG. Composite HID + CDC burada belirir. | **Normal kullanım.** Protokolü izlemek, uygulamayı çalıştırmak, bitmiş ürün. |

> **Not:** İkisi aynı anda takılı olabilir; hatta önerilir. UART portundan
> yükleyip USB portundan izlemek en rahat geliştirme düzenidir. Bitmiş üründe
> mahfazadan **yalnızca `USB` portu** dışarı çıkar — çünkü spesifikasyon bölüm 4
> composite HID + CDC istiyor ve bunu yalnızca yerleşik USB OTG sağlayabilir.

---

### 1.1 A yolu — VS Code + PlatformIO IDE

#### macOS

**1. VS Code kurun**

```bash
brew install --cask visual-studio-code
```

Homebrew yoksa <https://code.visualstudio.com> adresinden `.zip` indirin,
açın ve `Visual Studio Code.app` dosyasını `/Applications` klasörüne taşıyın.

**2. Python 3 olduğunu doğrulayın**

PlatformIO Core, Python 3.6+ ister. macOS'ta genelde vardır:

```bash
python3 --version
```

Yoksa: `brew install python@3.12`

**3. PlatformIO IDE eklentisini kurun**

- VS Code'u açın.
- Sol çubukta **Extensions** (`Cmd + Shift + X`).
- Arama kutusuna `PlatformIO IDE` yazın.
- Yayıncısı **PlatformIO** olan eklentiyi seçin → **Install**.
- Eklenti ilk açılışta PlatformIO Core'u `~/.platformio` altına indirir.
  Bu 2–5 dakika sürer; alt çubuktaki ilerleme çubuğunu bekleyin.
- Bittiğinde VS Code yeniden başlatmanızı isteyecektir.

**4. Kurulumu doğrulayın**

VS Code alt çubuğunda bir karınca yuvası (🏠), onay (✓), ok (→), fiş (🔌) ve
çöp kutusu simgesi belirmelidir. Ayrıca `Cmd + Shift + P` → `PlatformIO: Home`
komutu çalışmalıdır.

**5. UART portu için sürücü (yalnızca gerekirse)**

macOS 11 (Big Sur) ve sonrası CP2102N'yi yerleşik olarak tanır. `ls /dev/cu.*`
komutunda `/dev/cu.usbserial-*` görmüyorsanız Silicon Labs CP210x VCP
sürücüsünü kurun: <https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers>
Kurulumdan sonra **System Settings → Privacy & Security** altında sistem
uzantısına izin verip yeniden başlatmanız gerekir.

`USB` (yerleşik) portu için **hiçbir sürücü gerekmez.**

---

#### Windows

**1. VS Code kurun**

<https://code.visualstudio.com> → *Download for Windows* → kurulum sihirbazı.
*Add to PATH* seçeneğini işaretli bırakın.

**2. Python 3 kurun**

<https://www.python.org/downloads/windows/> → en güncel 3.x sürümü.
Kurulum ekranının **altındaki "Add python.exe to PATH" kutusunu mutlaka
işaretleyin.** Doğrulama:

```bat
py --version
```

**3. PlatformIO IDE eklentisini kurun**

- VS Code → **Extensions** (`Ctrl + Shift + X`)
- `PlatformIO IDE` → **Install**
- Core indirmesi bitene kadar bekleyin, VS Code'u yeniden başlatın.

> Windows Defender veya kurumsal antivirüs `~\.platformio\penv` altındaki
> Python ortamını karantinaya alabilir. Kurulum takılırsa bu klasörü istisna
> listesine ekleyin.

**4. UART portu için CP210x sürücüsü**

Windows 10/11 çoğu zaman otomatik indirir. Aygıt Yöneticisi'nde sarı ünlem
işaretli bir aygıt görürseniz sürücüyü elle kurun:
<https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers>
(`CP210x Universal Windows Driver` → zip'i açın → `.inf` dosyasına sağ tık →
**Yükle**.)

`USB` (yerleşik) portu için Windows 10 ve 11'de yerleşik `usbser.sys` yeterlidir;
**sürücü kurmayın.**

---

### 1.2 B yolu — PlatformIO CLI

> **Uyarı:** PlatformIO'yu projenin `.venv` klasörüne **kurmayın.** O sanal ortam
> PC uygulaması içindir (`customtkinter`, `pyserial`, `pystray`) ve PlatformIO'nun
> kendi bağımlılıkları oradaki sürümlerle çakışabilir. Ayrı bir ortam kullanın.

#### macOS

```bash
# Ayrı, izole bir sanal ortam
python3 -m venv ~/.pio-venv
~/.pio-venv/bin/pip install --upgrade pip
~/.pio-venv/bin/pip install platformio

# Kolay erişim için PATH'e ekleyin (zsh)
echo 'export PATH="$HOME/.pio-venv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

pio --version           # PlatformIO Core, version 6.x.x
```

Alternatif (Homebrew):

```bash
brew install platformio
```

#### Windows

```bat
py -m venv %USERPROFILE%\.pio-venv
%USERPROFILE%\.pio-venv\Scripts\python.exe -m pip install --upgrade pip
%USERPROFILE%\.pio-venv\Scripts\python.exe -m pip install platformio
```

PATH'e eklemek için (PowerShell, kalıcı):

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";$env:USERPROFILE\.pio-venv\Scripts",
    "User")
```

Yeni bir terminal açıp doğrulayın:

```bat
pio --version
```

#### VS Code eklentisiyle gelen `pio`'yu kullanma

A yolunu zaten kurduysanız CLI de vardır, sadece PATH'te değildir:

| Platform | Yol |
|---|---|
| macOS / Linux | `~/.platformio/penv/bin/pio` |
| Windows | `%USERPROFILE%\.platformio\penv\Scripts\pio.exe` |

macOS'ta kısayol:

```bash
echo 'export PATH="$HOME/.platformio/penv/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### 1.3 C yolu — Arduino IDE 2.x

Ayrıntılı ayar tablosu **bölüm 7**'dedir. Kurulum özeti:

#### macOS

1. <https://www.arduino.cc/en/software> → *Arduino IDE 2.x* macOS sürümü.
2. `.dmg` dosyasını açın, `Arduino IDE.app` uygulamasını `/Applications`'a taşıyın.
3. İlk açılışta macOS "geliştirici doğrulanamıyor" diyebilir →
   **System Settings → Privacy & Security → Yine de Aç**.
4. **Arduino IDE → Settings** (`Cmd + ,`) → *Additional boards manager URLs*
   alanına:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
5. **Tools → Board → Boards Manager** → `esp32` arayın →
   **esp32 by Espressif Systems** → sürüm **2.0.14 veya üzeri** → *Install*.
   (İndirme ~1 GB'dır, sabırlı olun.)

#### Windows

1. <https://www.arduino.cc/en/software> → *Arduino IDE 2.x* Windows kurulumu.
2. Kurulum sırasında sunulan **USB sürücülerini kabul edin**.
3. **File → Preferences** (`Ctrl + ,`) → *Additional boards manager URLs*:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
4. **Tools → Board → Boards Manager** → `esp32` → **esp32 by Espressif Systems**
   → sürüm **2.0.14 veya üzeri** → *Install*.

---

## 2. Depoyu açma ve firmware klasörüne girme

### 2.1 Klasör düzeni

```
ExtraKeyboard/
├── docs/
│   ├── 00-CEKIRDEK-SPEC.md
│   ├── 03-PROTOKOL.md
│   └── 04-FIRMWARE-KURULUM.md   ← bu dosya
├── firmware/                     ← PlatformIO projesinin KÖKÜ
│   ├── platformio.ini
│   └── src/
│       └── main.cpp
├── app/
├── hardware/
├── mechanical/
└── tools/
```

> **KRİTİK:** PlatformIO projesinin kökü `ExtraKeyboard/` değil,
> **`ExtraKeyboard/firmware/`** klasörüdür — `platformio.ini` orada yaşar.
> VS Code'da yanlış klasörü açarsanız PlatformIO araç çubuğu görünmez.

### 2.2 VS Code ile açma (A yolu)

1. VS Code → **File → Open Folder…**
2. `~/ExtraKeyboard-MK1/firmware` klasörünü seçin.
3. VS Code "Do you trust the authors of the files in this folder?" derse
   **Yes, I trust the authors**.
4. PlatformIO `platformio.ini` dosyasını görünce projeyi otomatik tanır ve
   ilk açılışta araç zincirini indirir:
   - `toolchain-riscv32-esp` / `toolchain-xtensa-esp32s3` (~400 MB)
   - `framework-arduinoespressif32` (~800 MB)
   - `tool-esptoolpy`

   Bu **tek seferliktir** ve internete bağlı olarak 5–20 dakika sürer.
   Alt çubukta *"Configuring project…"* yazısı kaybolana kadar bekleyin.

5. Hazır olduğunda alt çubukta şu simgeler kullanılabilir:

| Simge | Kısayol | İşlev | CLI karşılığı |
|---|---|---|---|
| ✓ | `Cmd/Ctrl + Alt + B` | Build (derle) | `pio run` |
| → | `Cmd/Ctrl + Alt + U` | Upload (yükle) | `pio run -t upload` |
| 🔌 | — | Serial Monitor | `pio device monitor` |
| 🗑 | — | Clean | `pio run -t clean` |

### 2.3 Terminalden açma (B yolu)

```bash
cd ~/ExtraKeyboard-MK1/firmware
ls -la
# platformio.ini ve src/ görmelisiniz

pio project data          # proje ayarlarını doğrula
pio run                   # ilk derleme (araç zinciri burada iner)
```

Windows:

```bat
cd /d C:\...\ExtraKeyboard\firmware
dir
pio run
```

---

## 3. `platformio.ini` — satır satır açıklama

Aşağıda `firmware/platformio.ini` dosyasının **referans içeriği** ve her
satırın ne yaptığı verilmiştir. Firmware kaynağını yazan taraf lib seçimini
değiştirebilir, ancak **"ZORUNLU" işaretli satırlar aynen korunmalıdır** —
onlar spesifikasyonun doğrudan karşılığıdır.

```ini
; ============================================================================
;  ExtraKeyboard MK1 — PlatformIO proje yapılandırması
;  Kart : ESP32-S3-DevKitC-1  (ESP32-S3-WROOM-1, N16R8)
;  FW   : 3.0.0   ·   HW: MK1   ·   BlueDevelopment
; ============================================================================

[platformio]
src_dir      = src
default_envs = extrakeyboard

[env:extrakeyboard]
platform  = espressif32@6.5.0
board     = esp32-s3-devkitc-1
framework = arduino

; ---- Yonga / bellek yerleşimi -------------------------------------------
board_build.mcu                 = esp32s3
board_build.f_cpu               = 240000000L
board_build.flash_mode          = qio
board_build.arduino.memory_type = qio_opi
board_build.partitions          = default_16MB.csv
board_upload.flash_size         = 16MB

; ---- Yükleme ve izleme ---------------------------------------------------
upload_speed    = 921600
monitor_speed   = 115200
monitor_dtr     = 1
monitor_rts     = 0
monitor_filters = time, esp32_exception_decoder

; ---- Derleme bayrakları --------------------------------------------------
build_flags =
    -D ARDUINO_USB_MODE=0
    -D ARDUINO_USB_CDC_ON_BOOT=1
    -D BOARD_HAS_PSRAM
    -D USB_VID=0x303A
    -D USB_PID=0x82E1
    -D USB_MANUFACTURER="\"BlueDevelopment\""
    -D USB_PRODUCT="\"ExtraKeyboard MK1\""
    -D FW_VERSION="\"3.0.0\""
    -D HW_REV="\"MK1\""
    -D CORE_DEBUG_LEVEL=0

; ---- Kütüphaneler --------------------------------------------------------
lib_deps =
    adafruit/Adafruit NeoPixel@^1.12.0
```

### 3.1 `[platformio]` bölümü

| Satır | Anlamı |
|---|---|
| `src_dir = src` | Kaynak dosyaların `firmware/src/` altında olduğunu söyler. PlatformIO'nun varsayılanı zaten budur; açıkça yazmak yanlış anlaşılmayı önler. |
| `default_envs = extrakeyboard` | `pio run` komutu ortam adı verilmeden çalıştırıldığında hangi `[env:...]` bloğunun kullanılacağı. İleride bir hata ayıklama ortamı eklenirse varsayılan bozulmaz. |

### 3.2 Platform ve kart

| Satır | Anlamı | Neden bu değer |
|---|---|---|
| `platform = espressif32@6.5.0` | Espressif 32 geliştirme platformu, **sürüm sabitlenmiş**. | Sürüm sabitlemek zorunludur: `espressif32` sürümü Arduino core sürümünü belirler, Arduino core sürümü de TinyUSB davranışını. Sabitlenmezse bir gün derleyen proje ertesi gün USB'yi numaralandıramayabilir. `6.5.0`, Arduino core 2.0.14 getirir. |
| `board = esp32-s3-devkitc-1` | Kart tanımı. Varsayılan pin eşlemesi, bellek düzeni, flash hızı buradan gelir. | Spec bölüm 3'te MCU olarak bu kart belirtilmiştir. |
| `framework = arduino` | Arduino-ESP32 çatısı (ESP-IDF üzerine kurulu). | `USBHIDKeyboard`, `USBHIDConsumerControl`, `USBCDC` sınıfları ve `Preferences` (NVS) API'si buradan gelir. Saf ESP-IDF ile de yazılabilirdi ama Arduino katmanı TinyUSB tanımlayıcılarını hazır sunar. |

### 3.3 Yonga ve bellek yerleşimi

| Satır | Anlamı | Neden bu değer |
|---|---|---|
| `board_build.mcu = esp32s3` | Hedef yonga ailesi. | Kart tanımından da gelir; açık yazmak yanlış kart seçimini erken yakalar. |
| `board_build.f_cpu = 240000000L` | CPU saati 240 MHz. | Enkoder tarama döngüsü ve WS2812B zamanlaması için en yüksek saat tercih edilir. |
| `board_build.flash_mode = qio` | SPI flash 4 hatlı Quad I/O modunda. | N16R8 varyantındaki flash QIO destekler; DIO'ya göre iki kat hızlı okuma. |
| `board_build.arduino.memory_type = qio_opi` | **Flash = QIO, PSRAM = OPI (Octal)**. | `N16R8`'in `R8`'i 8 MB **Octal** PSRAM demektir. Bu satır yanlışsa (`qio_qspi` gibi) kart açılışta panik verip sürekli yeniden başlar. |
| `board_build.partitions = default_16MB.csv` | Bölüm (partition) tablosu. | 16 MB flash'a uygun standart tablo. **İçinde `nvs` bölümü vardır** — LED renkleri, parlaklık, OS modu ve HID yedek ayarı oraya yazılır (spec §6.3, §5.2 `CMD SAVE`). NVS'siz bir tablo seçilirse ayarlar kalıcı olmaz. |
| `board_upload.flash_size = 16MB` | esptool'a flash boyutunu bildirir. | `N16` = 16 MB. Yanlış değer verilirse bölüm tablosu flash sınırını aşar ve yükleme başarısız olur. |

### 3.4 Yükleme ve izleme

| Satır | Anlamı | Not |
|---|---|---|
| `upload_speed = 921600` | esptool'un UART köprüsüyle konuşma hızı. | Uzun/kalitesiz kabloda hata verirse `115200`'e düşürün (bölüm 8.2). |
| `monitor_speed = 115200` | Seri monitörün açacağı baud. | Native USB CDC'de baud fiilen anlamsızdır, ama spec §5 uygulamanın `115200` açtığını söyler; monitörü de aynı tutmak tutarlılık sağlar. |
| `monitor_dtr = 1` | Monitör portu açarken **DTR sinyalini yükseltir**. | **Önemli:** Firmware `DTR` düşükken HID yedek moduna düşer (spec §5.3). `monitor_dtr = 1` sayesinde `pio device monitor`, cihaza "uygulama bağlandı" der; `LED3` yeşile döner ve normal protokol akışını izlersiniz. `0` bırakılırsa cihazı yedek modda gözlemlersiniz. |
| `monitor_rts = 0` | RTS sinyali düşük tutulur. | ESP32 kartlarında RTS otomatik-reset devresine bağlıdır. `1` yapılırsa monitör her açılışta kartı resetleyebilir. |
| `monitor_filters = time, esp32_exception_decoder` | `time`: her satırın başına zaman damgası koyar — `HB` periyodunu göz ile doğrulamak için birebir.<br>`esp32_exception_decoder`: çökme durumunda ham adresleri dosya/satır numarasına çevirir. | — |

### 3.5 Derleme bayrakları — en kritik bölüm

#### `-D ARDUINO_USB_MODE=0` — **ZORUNLU, PROJENİN HAYATİ NOKTASI**

ESP32-S3'te **iki ayrı ve birbirinden bağımsız USB çevre birimi** vardır:

| Çevre birimi | Yetenek | Arduino karşılığı |
|---|---|---|
| **USB Serial/JTAG Controller** | Sabit işlevli. **Yalnızca** bir CDC seri portu ve JTAG hata ayıklayıcı sunar. Tanımlayıcıları donanıma gömülüdür: değiştirilemez, HID eklenemez. | `ARDUINO_USB_MODE=1` |
| **USB OTG (full-speed)** | Genel amaçlı. TinyUSB yığını üzerinden **istenen her USB sınıfı** tanımlanabilir; composite cihaz kurulabilir; VID/PID/üretici/ürün dizeleri yazılımdan belirlenir. | `ARDUINO_USB_MODE=0` |

Spesifikasyon bölüm 4 şunu istiyor:

> Cihaz **composite**: `HID Keyboard` + `HID Consumer Control` + `CDC-ACM`
> VID `0x303A`, PID `0x82E1`, Product `ExtraKeyboard MK1`

Bunların **hiçbiri** USB Serial/JTAG denetleyicisiyle mümkün değildir.
Dolayısıyla:

```
ARDUINO_USB_MODE = 0   →  TinyUSB / USB-OTG  →  HID + CDC composite  ✅ ÇALIŞIR
ARDUINO_USB_MODE = 1   →  USB Serial/JTAG    →  yalnızca düz seri     ❌ ÇALIŞMAZ
```

**Yanlış değer verilirse ne olur:**

| Belirti | Açıklama |
|---|---|
| `USBHIDKeyboard.h: No such file or directory` | Mod 1'de HID sınıfları hiç derlenmez. |
| Derlense bile cihaz "USB JTAG/serial debug unit" olarak görünür | VID/PID `303A:1001` çıkar, `0x82E1` değil. Uygulama `find_ports()` ile cihazı **bulamaz**. |
| Tuşlara basınca hiçbir HID kodu gitmez | Klavye arayüzü hiç numaralandırılmamıştır. |
| `USB.VID()` / `USB.productName()` çağrıları etkisiz kalır | Tanımlayıcılar donanımda sabittir. |

> **Bu tek satır yanlışsa proje çalışmaz.** Herhangi bir sorun giderme
> oturumunda ilk bakılacak yer burasıdır.

#### `-D ARDUINO_USB_CDC_ON_BOOT=1` — **ZORUNLU**

Global `Serial` nesnesinin hangi donanıma bağlanacağını belirler:

| Değer | `Serial` nesnesi nereye gider | Sonuç |
|---|---|---|
| `1` | `USBCDC` — yerleşik USB'nin CDC-ACM arayüzü | ✅ `Serial.printf("HB %lu\n", ms)` çıktısı **USB portundan** gelir. Protokol çalışır. |
| `0` | `HardwareSerial` UART0 — GPIO43 (TX) / GPIO44 (RX) | ❌ Çıktı fiziksel UART pinlerine gider. USB portunu dinleyen uygulama hiçbir şey görmez. |

`0` seçilirse CDC'ye `USBSerial` adlı ayrı bir nesne üzerinden erişilir ve tüm
firmware kodunun `Serial` yerine `USBSerial` yazması gerekir. Karışıklığı
önlemek için `1` kullanılır.

#### `-D BOARD_HAS_PSRAM` — **ZORUNLU**

`N16R8`'deki 8 MB Octal PSRAM'in başlatılmasını ve heap'e eklenmesini sağlar.
`board_build.arduino.memory_type = qio_opi` ile birlikte çalışır; ikisinden
biri eksikse kart açılışta

```
E (xxx) psram: PSRAM ID read error
```

verip yeniden başlama döngüsüne girebilir. Bu projede PSRAM fiilen gerekli
değildir (RAM kullanımı çok düşüktür) ama **modül üzerinde takılı olduğu için
doğru yapılandırılmak zorundadır.**

#### USB kimlik bayrakları — **ZORUNLU (spec bölüm 4)**

| Bayrak | Spec karşılığı |
|---|---|
| `-D USB_VID=0x303A` | VID = `0x303A` (Espressif) |
| `-D USB_PID=0x82E1` | PID = `0x82E1` |
| `-D USB_MANUFACTURER="\"BlueDevelopment\""` | Manufacturer = `BlueDevelopment` |
| `-D USB_PRODUCT="\"ExtraKeyboard MK1\""` | Product = `ExtraKeyboard MK1` |

**Tırnak kaçışına dikkat:** `"\"BlueDevelopment\""` yazımı gereklidir. Dış tırnaklar
`platformio.ini` içindir, kaçışlı iç tırnaklar C dizesi içindir. Kaçış
unutulursa derleyici `BlueDevelopment` sembolünü bulamayıp hata verir.

Seri numarası (`EK1-<MAC son 6 hane>`) derleme zamanında bilinemez; firmware
onu çalışma anında MAC adresinden üretir ve `USB.serialNumber()` ile ayarlar
(`USB.begin()` çağrısından **önce**).

> **Not:** Bu bayraklar TinyUSB tanımlayıcılarının **varsayılanlarını** ayarlar.
> Firmware ayrıca `setup()` içinde `USB.VID(0x303A)`, `USB.PID(0x82E1)`,
> `USB.manufacturerName(...)`, `USB.productName(...)` çağırarak aynı değerleri
> açıkça yazabilir — Arduino IDE ile derlendiğinde tek yol budur (bölüm 7.3).

#### Sürüm bayrakları

| Bayrak | Kullanım yeri |
|---|---|
| `-D FW_VERSION="\"3.0.0\""` | `ID <fw> ...` yanıtının ilk alanı (spec §5.1, §10) |
| `-D HW_REV="\"MK1\""` | `ID ... <hw> ...` yanıtının ikinci alanı |

Bu değerlerin kaynak kodda değil `platformio.ini`'de tutulması, sürüm
yükseltmesinde tek bir dosya değiştirmeyi sağlar.

#### `-D CORE_DEBUG_LEVEL=0`

Arduino-ESP32 çekirdeğinin kendi hata ayıklama çıktılarını kapatır.
**Kritik:** `Serial` nesnesi CDC'ye bağlı olduğu için bu çıktılar da CDC'den
akar ve `EV`/`HB` satırlarının arasına karışır. Uygulama bu satırları bilinmeyen
sayıp atar (protokol bozulmaz), ancak elle test sırasında ekranı kirletir ve
yüksek seviyelerde zamanlamayı bozar. Geliştirme sırasında geçici olarak
`3` (Info) veya `4` (Debug) yapılabilir; **teslim edilen firmware'de `0`
olmalıdır.**

### 3.6 `lib_deps`

```ini
lib_deps =
    adafruit/Adafruit NeoPixel@^1.12.0
```

3 adet WS2812B LED'i sürmek için kullanılan kütüphane. Sürüm aralığı `^1.12.0`
(uyumlu minör güncellemelere izin verir). Bu seçim spesifikasyonda belirtilmemiştir
(bkz. bölüm 10); firmware kaynağını yazan taraf `FastLED` gibi bir alternatifi
tercih edebilir — **LED renkleri ve parlaklık davranışı spec §6.4'e uyduğu
sürece** kütüphane seçimi serbesttir.

### 3.7 Yapılandırma bütünlük denetimi

Yükleme öncesi bu dört satırı gözle doğrulayın:

```ini
-D ARDUINO_USB_MODE=0            ← composite HID+CDC için hayati
-D ARDUINO_USB_CDC_ON_BOOT=1     ← Serial'in USB'ye gitmesi için hayati
board_build.arduino.memory_type = qio_opi   ← N16R8 için hayati
board_build.partitions = default_16MB.csv   ← NVS için hayati
```

---

## 4. İlk yükleme

### 4.1 Kabloyu takma

1. **UART** etiketli USB-C portunu bilgisayara bağlayın. (İlk yükleme için en
   güvenilir yol budur — otomatik reset devresi oradadır.)
2. İsterseniz **USB** portunu da ikinci bir kabloyla bağlayın; yükleme sonrası
   izleme için kullanışlıdır.

### 4.2 Portu doğrulama

```bash
pio device list
```

Örnek çıktı (macOS, boş bir DevKit):

```
/dev/cu.usbserial-0001
----------------------
Hardware ID: USB VID:PID=10C4:EA60 SER=0001 LOCATION=1-1
Description: CP2102N USB to UART Bridge Controller
```

| Gördüğünüz | Anlamı |
|---|---|
| `VID:PID=10C4:EA60`, `CP210x` | **UART portu.** Yükleme için bunu kullanın. |
| `VID:PID=303A:1001`, `USB JTAG/serial debug unit` | Kartta ExtraKeyboard firmware'i **yok** ya da `ARDUINO_USB_MODE=1` ile derlenmiş. |
| `VID:PID=303A:82E1`, `ExtraKeyboard MK1` | **Doğru firmware yüklü**, yerleşik USB portu. |

Windows'ta port adları `COM3`, `COM7` gibidir; açıklama satırı aynıdır.

### 4.3 Bootloader moduna alma

ESP32-S3 çoğu zaman otomatik reset devresi sayesinde kendiliğinden bootloader'a
girer. Girmezse (bölüm 8.2'deki `Failed to connect` hatası) **elle** alın:

```
1.  BOOT tuşunu basılı TUT           ┌─────┐
                                     │BOOT │ ← basılı tut
2.  BOOT basılıyken RST tuşuna       └─────┘
    bas ve BIRAK                     ┌─────┐
                                     │ RST │ ← bas–bırak
3.  BOOT tuşunu BIRAK                └─────┘

4.  Kart artık indirme (download) modundadır.
    LED'ler sönük kalır, hiçbir şey çalışmaz — bu normaldir.
```

Anımsatıcı: **"BOOT'u tut, RST'ye dokun, BOOT'u bırak."**

> Kartı bootloader'a aldıktan sonra port adı **değişebilir** (özellikle `USB`
> portundan yüklüyorsanız). Yüklemeden hemen önce `pio device list` ile tekrar
> bakın.

### 4.4 Derleme

Önce sadece derleyip hataları görün:

```bash
cd ~/ExtraKeyboard-MK1/firmware
pio run
```

Başarılı çıktının sonu şuna benzer:

```
RAM:   [=         ]   9.4% (used 30820 bytes from 327680 bytes)
Flash: [==        ]  22.1% (used 695000 bytes from 3145728 bytes)
========================= [SUCCESS] Took 41.22 seconds =========================
```

VS Code'da: alt çubuktaki **✓ (Build)** simgesi veya `Cmd/Ctrl + Alt + B`.

### 4.5 Yükleme

**Port otomatik seçilsin:**

```bash
pio run -t upload
```

**Portu elle belirtin** (birden fazla seri cihaz varsa önerilir):

```bash
# macOS
pio run -t upload --upload-port /dev/cu.usbserial-0001

# Windows
pio run -t upload --upload-port COM7
```

Portu kalıcı sabitlemek isterseniz `platformio.ini` içine ekleyin:

```ini
upload_port   = /dev/cu.usbserial-0001
monitor_port  = /dev/cu.usbmodem101
```

VS Code'da: alt çubuktaki **→ (Upload)** simgesi veya `Cmd/Ctrl + Alt + U`.

**Beklenen çıktı:**

```
Configuring upload protocol...
AVAILABLE: esp-builtin, esp-bridge, espota, esptool
CURRENT: upload_protocol = esptool
Looking for upload port...
Auto-detected: /dev/cu.usbserial-0001
Uploading .pio/build/extrakeyboard/firmware.bin
esptool.py v4.5.1
Serial port /dev/cu.usbserial-0001
Connecting....
Chip is ESP32-S3 (revision v0.1)
Features: WiFi, BLE
Crystal is 40MHz
MAC: a4:c1:38:xx:xx:xx
Uploading stub...
Running stub...
Stub running...
Changing baud rate to 921600
Changed.
Configuring flash size...
Flash will be erased from 0x00000000 to 0x00004fff...
Flash will be erased from 0x00008000 to 0x00008fff...
Flash will be erased from 0x00010000 to 0x000bafff...
Compressed 20304 bytes to 13137...
Writing at 0x00000000... (100 %)
...
Hash of data verified.

Leaving...
Hard resetting via RTS pin...
========================= [SUCCESS] Took 28.05 seconds =========================
```

> **`MAC: a4:c1:38:xx:xx:xx` satırını not edin.** Son üç bayt (`xx:xx:xx`)
> cihazın seri numarasını belirler: `EK1-<son 6 hane>`. `ID` yanıtında bu
> değeri göreceksiniz (spec §4).

**Yükleme sırasında seri monitör AÇIK OLMAMALIDIR.** Port tekildir; açık monitör
`Permission denied` / `Access is denied` hatası verdirir.

---

## 5. Yükleme sonrası: yeniden numaralandırma

Yükleme bittikten sonra kart yeniden başlar ve firmware çalışmaya başlar.
Bu anda **USB portunda yeni bir cihaz belirir** — buna *yeniden numaralandırma*
(re-enumeration) denir.

### 5.1 Ne olur

```
Yükleme öncesi:
    /dev/cu.usbserial-0001    → CP2102N köprüsü (UART portu)
    (USB portunda cihaz yok, ya da boş bir JTAG/serial birimi)

Yükleme sonrası, ~1 saniye içinde:
    /dev/cu.usbserial-0001    → CP2102N köprüsü, DEĞİŞMEZ
    /dev/cu.usbmodem101       → YENİ: ExtraKeyboard MK1  ← protokol burada
```

Bu iki port **farklı fiziksel arayüzlerdir ve karıştırılmamalıdır**:

| | UART portu | USB portu |
|---|---|---|
| macOS adı | `/dev/cu.usbserial-XXXX` | `/dev/cu.usbmodemXXX` |
| Windows adı | `COMx` (CP210x) | `COMy` (USB Seri Aygıt) |
| VID:PID | `10C4:EA60` | `303A:82E1` |
| Açıklama | `CP2102N USB to UART Bridge` | `ExtraKeyboard MK1` |
| Ne için | Firmware yüklemek | **Protokol + HID** |

### 5.2 Doğrulama

```bash
pio device list
```

Beklenen:

```
/dev/cu.usbmodem101
-------------------
Hardware ID: USB VID:PID=303A:82E1 SER=EK1-A4C138 LOCATION=1-1
Description: ExtraKeyboard MK1
```

`SER=EK1-A4C138` alanı spec bölüm 4'teki `EK1-<MAC son 6 hane>` biçimidir.
`Description` alanı da tam olarak `ExtraKeyboard MK1` olmalıdır — PC uygulaması
VID/PID'i bulamazsa bu dizeye düşer (spec §4).

### 5.3 Neden port adı değişir

- Cihaz her açılışta USB yığınına **yeniden kaydolur**; işletim sistemi ona o
  anda boş olan bir sıra numarası verir. macOS'ta `usbmodem101`, `usbmodem1101`,
  `usbmodem2101` gibi adlar aynı cihaz için farklı zamanlarda görülebilir.
- Windows'ta COM numarası genelde sabit kalır (kayıt defterinde seri numarasına
  bağlanır) ama farklı bir USB yuvasına takılırsa değişebilir.

**Bu yüzden PC uygulaması port adına asla güvenmez**, her seferinde
`find_ports()` ile VID/PID araması yapar (spec §4, `03-PROTOKOL.md` §4.a).

### 5.4 Yeniden numaralandırma olmuyorsa

`303A:82E1` cihazı hiç belirmiyorsa:

1. **USB** portuna kablo takılı mı? (UART portu ExtraKeyboard'u göstermez.)
2. Kablo veri taşıyor mu? Yalnız-şarj kabloları D+/D− hatlarını taşımaz.
3. `ARDUINO_USB_MODE=0` mu? (bölüm 3.5 ve 8.3)
4. Firmware `setup()` içinde `USB.begin()` çağırıyor mu?
5. Bölüm 8.3 ve 8.5'e bakın.

---

## 6. Seri monitör ile doğrulama

### 6.1 Monitörü açma

```bash
cd ~/ExtraKeyboard-MK1/firmware
pio device monitor
```

Birden fazla port varsa **doğru olanı** açtığınızdan emin olun:

```bash
# macOS
pio device monitor --port /dev/cu.usbmodem101 --baud 115200

# Windows
pio device monitor --port COM8 --baud 115200
```

Kalıcı hâle getirmek için `platformio.ini`:

```ini
monitor_port = /dev/cu.usbmodem101
```

VS Code'da: alt çubuktaki **🔌 (Serial Monitor)** simgesi.

| Tuş | İşlev |
|---|---|
| `Ctrl + C` | Monitörden çık |
| `Ctrl + T` sonra `Ctrl + H` | Yardım |
| `Ctrl + T` sonra `Ctrl + D` | DTR sinyalini aç/kapat |

### 6.2 Beklenen çıktı

`monitor_filters = time` etkin olduğu için her satırın başında zaman damgası
vardır:

```
--- Terminal on /dev/cu.usbmodem101 | 115200 8-N-1
--- Available filters and text transformations: colorize, debug, default, direct,
--- esp32_exception_decoder, hexlify, log2file, nocontrol, printable, send_on_enter, time
--- More details at https://bit.ly/pio-monitor-filters
--- Quit: Ctrl+C | Menu: Ctrl+T | Help: Ctrl+T followed by Ctrl+H
14:32:07.104 > HB 1000
14:32:08.106 > HB 2000
14:32:09.105 > HB 3000
14:32:10.104 > HB 4000
14:32:11.106 > HB 5000
```

**Doğrulama ölçütleri:**

| Ölçüt | Beklenen |
|---|---|
| `HB` satırları geliyor mu | Evet, kesintisiz |
| Aralık | Zaman damgaları arası **≈ 1000 ms** (spec §5.1) |
| `uptime_ms` değeri | Her satırda 1000 artıyor, geri gitmiyor |
| Biçim | `HB` + tek boşluk + sayı. Başka karakter yok. |
| Gürültü | Arada `[E][...]` gibi çekirdek günlüğü **olmamalı** (`CORE_DEBUG_LEVEL=0`) |
| LED3 | **Yeşil** — çünkü `monitor_dtr = 1` cihaza "uygulama bağlandı" dedi |

### 6.3 Etkileşimli doğrulama

`pio device monitor` varsayılan olarak yazdığınızı **anında** gönderir ve
Enter'da `\r\n` yollar. Komut göndermek için `send_on_enter` süzgecini ekleyin:

```bash
pio device monitor --filter send_on_enter --echo
```

Ardından yazın:

```
CMD ID
```

Beklenen yanıt:

```
14:32:44.201 > ID 3.0.0 MK1 EK1-A4C138 WIN
```

> Komut göndermek için `pio device monitor` yerine
> **`miniterm --eol LF`** kullanmak daha güvenilirdir; ayrıntılı elle test
> yordamı ve komut örnekleri için [`03-PROTOKOL.md` bölüm 7](03-PROTOKOL.md#7-protokolü-elle-test-etme).

### 6.4 Tuş ve enkoder doğrulaması

Monitör açıkken cihazdaki tuşlara basın. Beklenen (spec §5.1):

```
14:33:01.512 > EV KEY 1 DOWN
14:33:01.640 > EV KEY 1 UP
14:33:02.118 > EV MODE COMBO_ON
14:33:02.702 > EV COMBO 2 5
14:33:03.310 > EV MODE COMBO_OFF
14:33:04.021 > EV OS MAC
14:33:05.440 > EV ENC CW
14:33:05.612 > EV ENC CW
14:33:06.008 > EV ENC CCW
14:33:06.755 > EV ENC PRESS
14:33:07.104 > HB 61000
```

Tam sınama kontrol listesi: [`03-PROTOKOL.md` bölüm 7.6](03-PROTOKOL.md#76-sınama-kontrol-listesi).

### 6.5 Pin doğrulaması

Tuş numaraları yanlış geliyorsa (örneğin K1'e basınca `EV KEY 3 DOWN` çıkıyorsa)
sorun kabloda ya da firmware pin dizisindedir. Spec bölüm 3.1'deki tablo
**değiştirilemez**:

| Tuş | GPIO | | Tuş | GPIO |
|---|---|---|---|---|
| K1 | 4 | | K9 | 8 |
| K2 | 5 | | K10 (COMBO) | 9 |
| K3 | 6 | | K11 (OS) | 10 |
| K4 | 7 | | ENC_A | 11 |
| K5 | 15 | | ENC_B | 12 |
| K6 | 16 | | ENC_SW | 13 |
| K7 | 17 | | LED_DATA | 14 |
| K8 | 18 | | | |

Enkoder ters yönde sayıyorsa `ENC_A` ve `ENC_B` kabloları yer değiştirmiştir —
**pin numaralarını değiştirmeyin**, kabloyu düzeltin veya firmware'de yön
işaretini ters çevirin.

---

## 7. Arduino IDE 2.x ile alternatif yol

PlatformIO kurmak istemiyorsanız Arduino IDE ile de derleyebilirsiniz. Ancak
`platformio.ini`'nin otomatik yaptığı her ayarı **Tools menüsünden elle**
seçmek zorundasınız. Tek bir yanlış seçim cihazın hiç görünmemesine yol açar.

### 7.1 Sketch klasörü düzeni

Arduino IDE, sketch dosyasının adının klasör adıyla **aynı** olmasını ister:

```
ExtraKeyboard_MK1/
└── ExtraKeyboard_MK1.ino     ← firmware/src/main.cpp içeriği
```

`firmware/src/main.cpp` dosyasını bu klasöre `ExtraKeyboard_MK1.ino` adıyla
kopyalayın. `#include <Arduino.h>` satırı Arduino IDE'de gereksizdir ama zararı
yoktur.

### 7.2 Kart seçimi

**Tools → Board → esp32 → ESP32S3 Dev Module**

> `ESP32S3 Dev Module` seçin. `ESP32-S3-DevKitC-1` adında ayrı bir girdi de
> olabilir; o girdi bazı ayar menülerini gizler. `ESP32S3 Dev Module` tüm
> seçenekleri açar ve aşağıdaki tabloyu uygulayabilmenizi sağlar.

### 7.3 Tools menüsü ayar tablosu — TAMAMI

Aşağıdaki tablodaki her satırı **birebir** uygulayın.

| # | Tools menüsü ayarı | Seçilecek değer | Ne işe yarar / neden bu değer |
|---|---|---|---|
| 1 | **Board** | `ESP32S3 Dev Module` | Hedef yonga ve varsayılan pin haritası. |
| 2 | **USB Mode** | `USB-OTG (TinyUSB)` | **EN KRİTİK AYAR.** `ARDUINO_USB_MODE=0` karşılığı. TinyUSB yığınını açar; HID Keyboard + Consumer Control + CDC composite yalnızca bu modda mümkündür (bölüm 3.5). `Hardware CDC and JTAG` seçilirse cihaz düz seri port olarak görünür, HID hiç çalışmaz ve VID/PID `303A:82E1` olmaz. |
| 3 | **USB CDC On Boot** | `Enabled` | `ARDUINO_USB_CDC_ON_BOOT=1` karşılığı. `Serial` nesnesini USB CDC'ye bağlar. `Disabled` olursa `Serial.print` çıktısı GPIO43/44 UART pinlerine gider ve protokol USB'den akmaz. |
| 4 | **Flash Size** | `16MB (128Mb)` | Modül `N16R8`'dir: 16 MB flash. Küçük seçilirse bölüm tablosu sığmaz, yükleme başarısız olur. |
| 5 | **PSRAM** | `OPI PSRAM` | `R8` = 8 MB **Octal** PSRAM. `QSPI PSRAM` veya `Disabled` seçilirse kart açılışta PSRAM hatası verip sürekli yeniden başlayabilir. `board_build.arduino.memory_type = qio_opi` karşılığı. |
| 6 | **Partition Scheme** | `16M Flash (3MB APP/9.9MB FATFS)` | 16 MB flash'a uygun ve **`nvs` bölümü içeren** tablo. NVS olmadan LED renkleri, parlaklık, OS modu ve HID yedek ayarı kalıcı olmaz (`CMD SAVE` çalışmaz). |
| 7 | **Flash Mode** | `QIO 80MHz` | 4 hatlı Quad I/O, 80 MHz. `board_build.flash_mode = qio` karşılığı. |
| 8 | **CPU Frequency** | `240MHz (WiFi)` | En yüksek saat. Enkoder taraması ve WS2812B zamanlaması için tercih edilir. |
| 9 | **Core Debug Level** | `None` | `CORE_DEBUG_LEVEL=0` karşılığı. Çekirdek günlükleri de CDC'den aktığı için protokol akışını kirletir. |
| 10 | **Arduino Runs On** | `Core 1` | `loop()` 1. çekirdekte çalışır, USB/sistem görevleri 0. çekirdekte kalır. Tuş tarama gecikmesini düşük tutar. |
| 11 | **Events Run On** | `Core 1` | Arduino olay kuyruğu da aynı çekirdekte; çekirdekler arası senkronizasyon derdi olmaz. |
| 12 | **USB Firmware MSC On Boot** | `Disabled` | Açık olursa cihaz ayrıca bir USB **disk** olarak da görünür. Spec bölüm 4'te böyle bir arayüz yoktur; composite tanımlayıcıyı gereksiz büyütür. |
| 13 | **USB DFU On Boot** | `Disabled` | Açık olursa bir DFU arayüzü daha eklenir. Yine spec dışıdır; bazı Windows sürümlerinde composite aygıtın tanınmasını zorlaştırır. |
| 14 | **JTAG Adapter** | `Disabled` | Yerleşik JTAG kapalı kalsın; GPIO39–42 serbest kalır ve USB Serial/JTAG denetleyicisi devreye girip USB-OTG ile çakışmaz. |
| 15 | **Erase All Flash Before Sketch Upload** | `Disabled` | Normal geliştirmede `Disabled` — böylece NVS'teki kullanıcı ayarları korunur. **Fabrika ayarlarına dönmek için geçici olarak `Enabled` yapın** (bölüm 9). |
| 16 | **Upload Mode** | `UART0 / Hardware CDC` | Yüklemenin **UART portu** üzerinden yapılacağını söyler. `USB-OTG CDC (TinyUSB)` seçilirse yükleme yerleşik USB portundan denenir; bu, cihaz her yüklemeden sonra yeniden numaralandığı için kırılgandır. |
| 17 | **Upload Speed** | `921600` | Hızlı yükleme. Bağlantı hatası verirse `115200`'e düşürün. |
| 18 | **Port** | UART portu (`/dev/cu.usbserial-*` veya `COMx`) | Yükleme portu. `ExtraKeyboard MK1` yazan portu **seçmeyin** — o çıktı portudur. |

### 7.4 USB kimliğini koda yazma

Arduino IDE'de VID/PID/üretici/ürün dizeleri için **menü yoktur.** Bu değerler
`setup()` içinde, `USB.begin()` çağrısından **önce** kodla ayarlanmalıdır
(spec bölüm 4):

```cpp
#include "USB.h"

void setup() {
    USB.VID(0x303A);
    USB.PID(0x82E1);
    USB.manufacturerName("BlueDevelopment");
    USB.productName("ExtraKeyboard MK1");
    USB.serialNumber(seriNumarasiUret());   // "EK1-A4C138"
    USB.begin();                            // en son çağrılır

    // Buradan sonra firmware'in geri kalan kurulumu gelir:
    // GPIO pinlerini INPUT_PULLUP yapma, WS2812B başlatma,
    // NVS'ten OS modu ve LED ayarlarını okuma, HB zamanlayıcısı.
}
```

PlatformIO'daki `-D USB_VID=...` bayrakları yalnızca **varsayılanı** değiştirir;
yukarıdaki çağrılar her iki ortamda da doğru sonucu garanti eder. Bu nedenle
firmware kaynağında bu çağrıların bulunması **önerilir**.

### 7.5 Derleme ve yükleme

1. **Sketch → Verify/Compile** (`Cmd/Ctrl + R`) — önce sadece derleyin.
2. Kartı bootloader moduna alın (bölüm 4.3) — Arduino IDE otomatik reset'i
   çoğu zaman halleder, gerekirse elle yapın.
3. **Sketch → Upload** (`Cmd/Ctrl + U`).
4. Yükleme bitince **Tools → Port** menüsünü yeniden açın: artık listede
   `ExtraKeyboard MK1` yazan **yeni bir port** görmelisiniz (bölüm 5).
5. O portu seçip **Tools → Serial Monitor** (`Cmd/Ctrl + Shift + M`) açın.
   Sağ alttaki baud seçicisini `115200`, satır sonu seçicisini
   **`New Line`** (yalnız LF) yapın.

> **Arduino IDE Serial Monitor uyarısı:** Satır sonu seçicisi varsayılan olarak
> `Both NL & CR` gelir; bu `\r\n` gönderir. Firmware `\r` karakterlerini yok
> saydığı için komutlar yine çalışır, ancak **`New Line`** seçmek protokole
> birebir uygundur (spec §5: satır sonu `\n`).

### 7.6 PlatformIO ↔ Arduino IDE karşılık tablosu

| `platformio.ini` | Arduino IDE Tools ayarı |
|---|---|
| `-D ARDUINO_USB_MODE=0` | **USB Mode** = `USB-OTG (TinyUSB)` |
| `-D ARDUINO_USB_CDC_ON_BOOT=1` | **USB CDC On Boot** = `Enabled` |
| `-D BOARD_HAS_PSRAM` | **PSRAM** = `OPI PSRAM` |
| `board_build.arduino.memory_type = qio_opi` | **Flash Mode** = `QIO 80MHz` + **PSRAM** = `OPI PSRAM` |
| `board_upload.flash_size = 16MB` | **Flash Size** = `16MB (128Mb)` |
| `board_build.partitions = default_16MB.csv` | **Partition Scheme** = `16M Flash (3MB APP/9.9MB FATFS)` |
| `board_build.f_cpu = 240000000L` | **CPU Frequency** = `240MHz (WiFi)` |
| `-D CORE_DEBUG_LEVEL=0` | **Core Debug Level** = `None` |
| `upload_speed = 921600` | **Upload Speed** = `921600` |
| `-D USB_VID` / `USB_PID` / `USB_PRODUCT` | *(menü yok — kodla, bölüm 7.4)* |
| `pio run -t erase` | **Erase All Flash Before Sketch Upload** = `Enabled` |

---

## 8. Sık karşılaşılan yükleme hataları

### 8.1 Port hiç görünmüyor

**Belirti:** `pio device list` boş ya da beklenen cihaz yok. Arduino IDE'de
**Tools → Port** menüsü gri.

#### macOS — `cu.` ile `tty.` farkı

macOS her seri cihazı **iki düğümle** açar:

| Düğüm | Davranış | Kullanım |
|---|---|---|
| `/dev/tty.usbmodem101` | *call-in*. Açarken **DCD (Data Carrier Detect)** sinyalini bekler. USB CDC cihazlarında bu sinyal gelmeyebilir → **açılış sonsuza kadar kilitlenir.** | ❌ Kullanmayın |
| `/dev/cu.usbmodem101` | *call-out*. DCD beklemez, hemen açılır. | ✅ **Daima bunu kullanın** |

```bash
ls -l /dev/cu.*        # doğru liste
ls -l /dev/tty.*       # aynı cihazlar, kullanmayın
```

PlatformIO ve pyserial otomatik seçimde `cu.` tercih eder; elle port yazarken
`tty.` yazmayın.

#### macOS — diğer kontroller

| Kontrol | Komut / işlem |
|---|---|
| Sistem cihazı görüyor mu | **Apple menü → Bu Mac Hakkında → Ek Bilgi → Sistem Raporu → USB** |
| Kablo veri taşıyor mu | Yalnız-şarj USB-C kablolarında D+/D− yoktur. Bilinen bir veri kablosuyla deneyin. |
| Hub sorunu | Doğrudan bilgisayara takın, hub/dock kullanmayın. |
| CP210x sürücüsü | UART portu için gerekebilir (bölüm 1.1). Kurulumdan sonra **System Settings → Privacy & Security** altında sistem uzantısına izin verip yeniden başlatın. |

#### Windows — sürücü ve Aygıt Yöneticisi

1. `Win + X` → **Aygıt Yöneticisi**.
2. **Görünüm → Gizli aygıtları göster** işaretleyin.
3. Bakılacak yerler:

| Nerede göründüğü | Anlamı | Çözüm |
|---|---|---|
| *Bağlantı Noktaları (COM ve LPT)* → `Silicon Labs CP210x (COMx)` | UART portu tamam | — |
| *Bağlantı Noktaları* → `USB Seri Aygıt (COMy)` | Yerleşik USB CDC tamam | — |
| *Diğer aygıtlar* → sarı ünlemli `CP2102N` | CP210x sürücüsü yok | Silicon Labs VCP sürücüsünü kurun (bölüm 1.1) |
| *Evrensel Seri Veri Yolu denetleyicileri* → `Bilinmeyen USB Aygıtı` | Tanımlayıcı hatası | Bölüm 8.5 |

4. Sürücü kurduktan sonra kabloyu **çıkarıp takın**; Windows yeni COM numarası
   atayabilir.

#### Kartta firmware var ama görünmüyor

`303A:82E1` yerine `303A:1001` (`USB JTAG/serial debug unit`) görüyorsanız
firmware yanlış modda derlenmiştir → bölüm 8.3.

---

### 8.2 `A fatal error occurred: Failed to connect to ESP32-S3`

**Tam hata metni** genelde şöyledir:

```
A fatal error occurred: Failed to connect to ESP32-S3:
No serial data received.
For troubleshooting steps visit:
https://docs.espressif.com/projects/esptool/en/latest/troubleshooting.html
```

veya

```
A fatal error occurred: Failed to connect to ESP32-S3:
Wrong boot mode detected (0x13)! The chip needs to be in download mode.
```

**Anlamı:** esptool porta bağlandı ama yonga bootloader'da değil ya da hiç
yanıt vermiyor.

**Çözümler, sırayla:**

1. **Kartı elle bootloader moduna alın** (bölüm 4.3):
   `BOOT` basılı tut → `RST` bas–bırak → `BOOT` bırak.
   Sonra hemen `pio run -t upload` çalıştırın.

2. **Doğru portu seçtiğinizden emin olun.** UART portundan yüklüyorsanız
   `/dev/cu.usbserial-*` veya CP210x'in COM numarası olmalı:
   ```bash
   pio run -t upload --upload-port /dev/cu.usbserial-0001
   ```

3. **Yükleme hızını düşürün.** `platformio.ini`:
   ```ini
   upload_speed = 115200
   ```
   Uzun, kalitesiz veya uzatmalı kablolarda 921600 çalışmaz.

4. **Portu kimse kullanmıyor mu?** Açık bir seri monitör, `screen` oturumu,
   Arduino IDE Serial Monitor veya çalışan ExtraKeyboard uygulaması portu
   kilitler. Hepsini kapatın.
   ```bash
   # macOS: portu kimin tuttuğunu bul
   lsof | grep cu.usbserial
   ```

5. **Kabloyu ve yuvayı değiştirin.** Hub yerine doğrudan bilgisayar,
   USB 3.x yerine USB 2.0 yuvası deneyin.

6. **Kartın beslemesi yeterli mi?** WS2812B LED'ler tam parlaklıkta akım
   çekiyorsa yükleme sırasında gerilim düşebilir. LED besleme kablosunu
   geçici olarak sökün.

7. **GPIO0 / GPIO46 kontrolü.** Spec bölüm 3.2 bu pinleri **yasaklar** çünkü
   açılışta LOW olurlarsa kart bootloader'a düşer. Prototipte yanlışlıkla bir
   anahtar bağlandıysa kart normal çalışmaya hiç geçmez. Kabloyu kontrol edin.

---

### 8.3 Yükleme başarılı ama cihaz görünmüyor

**Belirti:** `SUCCESS` yazdı, kart resetlendi, ama `USB` portunda
`ExtraKeyboard MK1` beliren yok. LED'ler de yanmıyor olabilir.

**Neden 1 — `ARDUINO_USB_MODE` yanlış (en sık neden)**

```bash
grep ARDUINO_USB_MODE ~/ExtraKeyboard-MK1/firmware/platformio.ini
```

`-D ARDUINO_USB_MODE=0` görmelisiniz. `1` ise cihaz USB Serial/JTAG denetleyicisi
üzerinden `303A:1001` olarak numaralandırılır; HID hiç yoktur, PID istenen
`0x82E1` değildir ve uygulama cihazı bulamaz (bölüm 3.5).

Arduino IDE kullanıyorsanız: **Tools → USB Mode = `USB-OTG (TinyUSB)`**.

Düzelttikten sonra **temiz derleme** yapın — eski nesne dosyaları eski bayrakla
derlenmiş olabilir:

```bash
pio run -t clean
pio run -t upload
```

**Neden 2 — `ARDUINO_USB_CDC_ON_BOOT` yanlış**

`0` ise `Serial` UART0'a bağlıdır; USB portunda CDC arayüzü belirse bile hiçbir
veri akmaz. `1` olmalı (Arduino IDE: **USB CDC On Boot = `Enabled`**).

**Neden 3 — `USB.begin()` çağrılmamış**

TinyUSB modunda USB yığını **elle başlatılır**. Firmware `setup()` içinde
`USB.begin()` çağırmıyorsa hiçbir arayüz numaralandırılmaz. HID nesneleri
(`USBHIDKeyboard`, `USBHIDConsumerControl`) `USB.begin()`'den **önce**
`begin()` edilmelidir ki tanımlayıcıya eklensinler.

**Neden 4 — yanlış porta bakıyorsunuz**

`UART` portu ExtraKeyboard'u **asla** göstermez. `USB` etiketli porta kablo
takın (bölüm 1.0).

**Neden 5 — kablo veri taşımıyor**

Yalnız-şarj kabloları. Bilinen bir veri kablosuyla deneyin.

**Neden 6 — firmware açılışta çöküyor**

UART portundan bağlanıp çekirdek günlüklerini okuyun (`ARDUINO_USB_MODE=0`
iken çekirdek panikleri yine de UART0'a düşer):

```bash
pio device monitor --port /dev/cu.usbserial-0001 --baud 115200
```

Sürekli tekrarlayan `Guru Meditation Error` veya
`rst:0x3 (RTC_SW_SYS_RST)` görüyorsanız firmware'de bir çökme vardır.
`esp32_exception_decoder` süzgeci yığın izini kaynak satırına çevirir.

---

### 8.4 macOS: "… açılamıyor çünkü geliştirici doğrulanamıyor"

**Belirti:**

> **"esptool" açılamıyor çünkü Apple, kötü amaçlı yazılım içerip içermediğini
> denetleyemiyor.**

veya PlatformIO çıktısında:

```
Error: ... cannot be opened because the developer cannot be verified
```

**Neden:** macOS Gatekeeper, internetten indirilen ve Apple tarafından noter
onaylı (notarized) olmayan çalıştırılabilir dosyaları karantinaya alır.
PlatformIO'nun `~/.platformio/packages/` altına indirdiği `esptool`, `openocd`,
`xtensa-esp32s3-elf-gcc` gibi araçlar bu duruma düşebilir.

**Çözüm A — tek dosya için izin (en güvenli)**

1. Uyarı penceresini kapatın.
2. **Sistem Ayarları → Gizlilik ve Güvenlik**.
3. Sayfayı aşağı kaydırın; *"…engellendi çünkü tanımlı bir geliştiriciden
   değil"* satırının yanındaki **Yine de İzin Ver** düğmesine basın.
4. İşlemi tekrar deneyin; bu kez **Aç** seçeneği sunulur.
5. **Her araç için ayrı ayrı** tekrarlamanız gerekebilir (esptool, openocd, gcc…).

**Çözüm B — PlatformIO paket klasöründen karantina bayrağını kaldırma**

Çok sayıda araç engelleniyorsa toplu çözüm:

```bash
xattr -dr com.apple.quarantine ~/.platformio/packages
xattr -dr com.apple.quarantine ~/.platformio/penv
```

Arduino IDE için:

```bash
xattr -dr com.apple.quarantine ~/Library/Arduino15/packages/esp32
```

> Bu komut karantina bayrağını **yalnızca belirtilen klasörde** siler.
> Sistem genelinde Gatekeeper'ı kapatmayın (`spctl --master-disable`) —
> gereksiz ve riskli.

**Çözüm C — Arduino IDE uygulamasının kendisi engellenirse**

`Arduino IDE.app` ilk açılışta engellenirse: **Finder → Uygulamalar →
`Arduino IDE.app` üzerine sağ tık (veya Control + tık) → Aç → Aç**.
Sağ tıkla açmak Gatekeeper'a tek seferlik izin verir.

---

### 8.5 Windows: cihaz "Bilinmeyen USB Aygıtı" görünüyor

**Belirti (Aygıt Yöneticisi → Evrensel Seri Veri Yolu denetleyicileri):**

> **Bilinmeyen USB Aygıtı (Aygıt Tanımlayıcı İsteği Başarısız Oldu)**
> *Unknown USB Device (Device Descriptor Request Failed)* — Kod 43

**Anlamı:** Windows cihazı elektriksel olarak gördü ama USB tanımlayıcılarını
okuyamadı. Bu bir **sürücü sorunu değildir**; cihaz kendini tanıtamıyordur.

**Çözümler, sırayla:**

1. **`ARDUINO_USB_MODE=0` kontrolü.** Mod 1'de TinyUSB hiç başlamaz ve
   composite tanımlayıcı üretilmez (bölüm 8.3).

2. **`USB.begin()` çağrılıyor mu?** Çağrılmazsa USB-OTG çevre birimi hiç
   uyanmaz; Windows boş bir aygıt görür. HID sınıflarının `begin()` çağrıları
   `USB.begin()`'den önce olmalıdır.

3. **Firmware açılışta çöküyor olabilir.** Numaralandırma tamamlanmadan kart
   resetlenirse bu hata çıkar. UART portundan seri monitör açıp
   `Guru Meditation Error` arayın (bölüm 8.3, Neden 6).

4. **Hayalet aygıt kaydını temizleyin:**
   - `Win + X` → **Aygıt Yöneticisi**
   - **Görünüm → Gizli aygıtları göster**
   - `Bilinmeyen USB Aygıtı` üzerine sağ tık → **Aygıtı kaldır**
     (*"Bu aygıtın sürücü yazılımını sil"* varsa işaretleyin)
   - Aynı işlemi gri görünen tüm `ExtraKeyboard MK1` / `USB Seri Aygıt`
     girdileri için tekrarlayın
   - Kabloyu çıkarıp takın; Windows aygıtı sıfırdan tanır

5. **Farklı USB yuvası deneyin.** Özellikle **USB 2.0** yuvası; bazı USB 3.x
   denetleyicileri full-speed composite aygıtlarda sorun çıkarır. Hub ve
   dock kullanmayın.

6. **USB Selective Suspend'i kapatın:**
   **Denetim Masası → Güç Seçenekleri → Plan ayarlarını değiştir →
   Gelişmiş güç ayarlarını değiştir → USB ayarları →
   USB seçmeli askıya alma ayarı → Devre Dışı**

7. **Kablo.** Yalnız-şarj kablosu D+/D− taşımaz; veri kablosu kullanın.

8. **Son çare — flash'ı silip yeniden yükleyin** (bölüm 9). Bozuk bir NVS
   içeriği açılışta çökmeye ve numaralandırmanın yarım kalmasına yol açabilir.

---

### 8.6 `Permission denied` / `Access is denied` / port meşgul

**macOS / Linux:**

```
serial.serialutil.SerialException: [Errno 13] could not open port
/dev/cu.usbmodem101: [Errno 16] Resource busy
```

**Windows:**

```
could not open port 'COM7': PermissionError(13, 'Erişim reddedildi.')
```

**Neden:** Seri port aynı anda **tek bir program** tarafından açılabilir.

**Çözüm:**

1. Açık seri monitörleri kapatın (`pio device monitor` → `Ctrl + C`,
   Arduino IDE Serial Monitor, PuTTY, `screen`).
2. Çalışan ExtraKeyboard uygulamasını **tepsi simgesinden Çıkış** ile kapatın —
   pencereyi kapatmak yetmez, tepside çalışmaya devam eder.
3. Takılı kalan `screen` oturumlarını temizleyin:
   ```bash
   screen -ls
   screen -X -S <oturum_adi> quit
   ```
4. Portu kimin tuttuğunu bulun:
   ```bash
   # macOS
   lsof | grep usbmodem
   ```

---

### 8.7 Derleme hataları

| Hata | Neden | Çözüm |
|---|---|---|
| `USBHIDKeyboard.h: No such file or directory` | `ARDUINO_USB_MODE=1` | `0` yapın, `pio run -t clean` sonra tekrar derleyin |
| `'USB' was not declared in this scope` | `#include "USB.h"` eksik veya USB modu yanlış | Include ekleyin, `ARDUINO_USB_MODE=0` doğrulayın |
| `'BlueDevelopment' was not declared in this scope` | `build_flags` içinde tırnak kaçışı unutulmuş | `-D USB_MANUFACTURER="\"BlueDevelopment\""` biçimini kullanın |
| `region 'iram0_0_seg' overflowed` | Kod IRAM'a sığmadı | `CORE_DEBUG_LEVEL=0` yapın, gereksiz `IRAM_ATTR` işaretlerini kaldırın |
| `Error: Partition table does not fit` | `flash_size` ile `partitions` uyuşmuyor | `board_upload.flash_size = 16MB` + `default_16MB.csv` |
| `Please specify `upload_port`` | Birden çok seri cihaz var, otomatik seçim yapamıyor | `--upload-port` ile açıkça belirtin |
| `PlatformIO: Can not find working Python` | Python 3 PATH'te değil | Bölüm 1.1 adım 2 |

---

### 8.8 Firmware çalışıyor ama davranış yanlış

| Belirti | Olası neden | Kontrol |
|---|---|---|
| `HB` geliyor ama tuşlar hiç event üretmiyor | Anahtar kablosu GND'ye gitmiyor, ya da `INPUT_PULLUP` ayarlanmamış | Spec §3.1: tüm anahtarlar **aktif-LOW**, anahtar → GND |
| Yanlış tuş numarası geliyor | Kablo veya firmware pin dizisi yanlış | Spec §3.1 pin tablosu (bölüm 6.5) |
| Enkoder ters sayıyor | `ENC_A` ↔ `ENC_B` yer değiştirmiş | Kabloyu düzeltin; pin numaralarını **değiştirmeyin** |
| Enkoder bir tıkta 2–4 event üretiyor | RC debounce devresi takılı değil | Spec §3.4: her kanala 10 kΩ + 100 nF **zorunlu** |
| LED'ler hiç yanmıyor veya rastgele renkler | WS2812B veri hattı 3.3 V eşiğinin altında kalıyor | Spec §3.3: +5 V hattına seri **1N4148** diyot (VDD ≈ 4.3 V) + veri hattına 330 Ω |
| LED'ler ilk açılışta titriyor | Besleme kondansatörü yok | Spec §3.3: **1000 µF / 10 V** elektrolitik |
| Tuşa bir kez basınca 2 event | Yazılım debounce yok/yetersiz | Spec §6.1: **5 ms** yazılım debounce, tuş başına ayrı durum makinesi |
| Kart rastgele yeniden başlıyor | Yasak GPIO kullanılmış veya besleme yetersiz | Spec §3.2 yasak pin listesi; toplam çekim < 150 mA olmalı |
| `LED3` hep kırmızı, uygulama açık | CDC `DTR` yükselmiyor | `monitor_dtr = 1`; uygulama tarafında `ser.dtr = True` |

---

## 9. Sıfırlama ve fabrika ayarlarına dönme

Cihaz şu ayarları **NVS**'te (flash üzerindeki kalıcı anahtar-değer deposu)
saklar:

| Ayar | Nereden yazılır |
|---|---|
| OS modu (`WIN` / `MAC`) | K11 kısa basış (spec §6.3) veya `CMD OS ...` |
| LED renkleri (LED1–LED3) | `CMD LED <i> <RRGGBB>` + `CMD SAVE` |
| Genel parlaklık | `CMD LED BRIGHT <0-255>` + `CMD SAVE` |
| Enkoder modu (`HID` / `HOST`) | `CMD ENC MODE ...` + `CMD SAVE` |
| HID yedek modu (`ON` / `OFF`) | `CMD HIDFB ...` veya K11 3 sn basış |

### 9.1 Tam silme — `pio run -t erase`

**En kesin yöntem.** Flash'ın **tamamını** siler: uygulama, bölüm tablosu,
bootloader ve **NVS dahil** her şey.

```bash
cd ~/ExtraKeyboard-MK1/firmware

# 1. Kartı bootloader moduna al (bölüm 4.3)
# 2. Flash'ı tamamen sil
pio run -t erase

# 3. Firmware'i yeniden yükle (kart artık BOŞ)
pio run -t upload
```

Beklenen çıktı:

```
esptool.py v4.5.1
Serial port /dev/cu.usbserial-0001
Connecting....
Chip is ESP32-S3 (revision v0.1)
Erasing flash (this may take a while)...
Chip erase completed successfully in 18.3s
Hard resetting via RTS pin...
========================= [SUCCESS] Took 24.11 seconds =========================
```

> **UYARI:** `erase` sonrası kartta **hiçbir firmware kalmaz.** Cihaz USB
> portunda görünmez, LED'ler yanmaz — bu normaldir. Mutlaka arkasından
> `pio run -t upload` çalıştırın.
>
> Silme işleminden sonra kart bootloader modundan çıkmış olabilir; yükleme
> hata verirse bölüm 4.3'ü tekrar uygulayın.

### 9.2 Yalnızca NVS'i silme

Firmware'i korurken sadece kullanıcı ayarlarını sıfırlamak isterseniz NVS
bölümünü hedefleyebilirsiniz. `default_16MB.csv` tablosunda NVS `0x9000`
adresinde ve `0x5000` (20 KB) boyutundadır:

```bash
# PlatformIO'nun kendi esptool'unu kullanın
~/.platformio/packages/tool-esptoolpy/esptool.py \
    --chip esp32s3 \
    --port /dev/cu.usbserial-0001 \
    erase_region 0x9000 0x5000
```

Windows:

```bat
%USERPROFILE%\.platformio\packages\tool-esptoolpy\esptool.py ^
    --chip esp32s3 --port COM7 erase_region 0x9000 0x5000
```

Bölüm adreslerini doğrulamak için:

```bash
pio run -t envdump | grep -i partition
```

veya derleme çıktısındaki `partitions.bin` yerleşimine bakın.

> Bu yöntem daha hızlıdır ama adresi yanlış girerseniz uygulama bölümünü bozarsınız.
> Emin değilseniz **9.1'i kullanın.**

### 9.3 Arduino IDE ile silme

**Tools → Erase All Flash Before Sketch Upload → `Enabled`** yapın, sketch'i
yükleyin. Yükleme öncesi tüm flash silinir; NVS de gider.

> Yükleme bittikten sonra bu ayarı **`Disabled`** durumuna geri alın. Aksi hâlde
> her yüklemede kullanıcının LED ve OS ayarları silinir ve yükleme gereksiz yere
> uzar.

### 9.4 Cihaz üzerinden yumuşak sıfırlama

Spesifikasyonda cihaz üzerinden tam fabrika ayarına dönüş için bir tuş
kombinasyonu **tanımlanmamıştır** (bkz. bölüm 10). Elle geri alınabilecekler:

| Ayar | Cihaz üzerinden nasıl varsayılana döner |
|---|---|
| OS modu | K11'e kısa basarak `WIN` konumuna getirin |
| HID yedek modu | K11'e 3 sn basarak `ON` konumuna getirin (LED3 üç kez beyaz flaş) |
| LED renkleri / parlaklık | **Cihazdan geri alınamaz** — `CMD LED ...` + `CMD SAVE` gönderin ya da 9.1'i uygulayın |

Varsayılan değerlere elle dönüş (spec §6.4 ve §7):

```
CMD LED BRIGHT 60
CMD LED 1 1E90FF
CMD LED 2 FF9500
CMD LED 3 2CC985
CMD ENC MODE HID
CMD HIDFB ON
CMD OS WIN
CMD SAVE
```

Bu satırları [`03-PROTOKOL.md` bölüm 7.2](03-PROTOKOL.md#72-miniterm-ile--önerilen-yöntem)
yordamıyla `miniterm` üzerinden gönderebilirsiniz.

### 9.5 PC uygulaması yapılandırmasını sıfırlama

Cihaz NVS'i ile PC uygulamasının `config.json` dosyası **ayrı** şeylerdir.
Tuş ve combo atamalarını sıfırlamak için:

```bash
# Yedek al
mv ~/ExtraKeyboard-MK1/config.json \
   ~/ExtraKeyboard-MK1/config.json.yedek
```

Uygulama bir sonraki açılışta varsayılan şema 3 yapılandırmasını yeniden üretir
(spec §7, `ConfigManager.load()`).

### 9.6 PlatformIO derleme önbelleğini temizleme

Derleme hataları mantıksızsa (bayrak değiştirdiğiniz hâlde eski davranış
sürüyorsa) önbelleği temizleyin:

```bash
cd ~/ExtraKeyboard-MK1/firmware
pio run -t clean          # yalnızca derleme çıktıları
rm -rf .pio               # tam temizlik (araç zinciri korunur)
pio run
```

Araç zincirini de yeniden indirmek isterseniz (nadiren gerekir):

```bash
rm -rf ~/.platformio/packages
pio run                   # yeniden indirir
```

---

## 10. Spec dışı varsayımlar

`00-CEKIRDEK-SPEC.md` aşağıdaki noktaları tanımlamadığı için en makul seçenek
seçilmiş ve burada açıkça işaretlenmiştir.

| # | Konu | Varsayım | Gerekçe |
|---|---|---|---|
| 1 | `platformio.ini` içeriği | Bölüm 3'teki referans dosya | Spec bölüm 9 yalnızca `firmware/ platformio.ini + src/` der, içerik vermez. "ZORUNLU" işaretli satırlar spec §3, §4 ve §10'un doğrudan karşılığıdır; gerisi (platform sürümü, `f_cpu`, `monitor_filters`) makul varsayılanlardır. |
| 2 | PlatformIO platform sürümü | `espressif32@6.5.0` (Arduino core 2.0.14) | Sürüm sabitlemek zorunlu; sabitlenmezse TinyUSB davranışı sürümler arası değişip USB numaralandırmasını bozabilir. Spec sürüm belirtmez. |
| 3 | Bölüm tablosu | `default_16MB.csv` | Spec NVS kullanımını ima eder (`CMD SAVE`, §6.3 OS modunun NVS'e yazılması) ama tabloyu adlandırmaz. Bu tablo 16 MB flash'a uyar ve `nvs` bölümü içerir. |
| 4 | LED kütüphanesi | `adafruit/Adafruit NeoPixel@^1.12.0` | Spec WS2812B'yi donanım olarak belirtir, kütüphane seçmez. Firmware kaynağını yazan taraf `FastLED` gibi bir alternatifi seçebilir; **§6.4'teki renk ve parlaklık davranışı korunduğu sürece** fark etmez. |
| 5 | `CORE_DEBUG_LEVEL=0` | Teslim edilen firmware'de sıfır | Çekirdek günlükleri de CDC'den aktığı için `EV`/`HB` akışını kirletir. Spec §5 protokolün temiz olmasını gerektirir; bu bayrak onun pratik sonucudur. |
| 6 | `upload_speed = 921600` | Varsayılan yükleme hızı | Spec yükleme hızından söz etmez. Kalitesiz kabloda `115200`'e düşürme yönergesi bölüm 8.2'de verilmiştir. |
| 7 | `monitor_dtr = 1` | Seri monitör DTR'yi yükseltir | Spec §5.3 HID yedek modunun ölçütünü DTR olarak verir. Monitörün DTR'yi yükseltmesi, geliştiricinin cihazı "uygulama bağlı" durumunda gözlemlemesini sağlar. |
| 8 | Yükleme portu | İlk yükleme **UART** portundan | Spec DevKit'in iki portundan söz etmez. UART portu otomatik reset devresine sahip olduğu için en güvenilir yükleme yoludur; bitmiş üründe mahfazadan **USB** portu çıkar (spec §4 composite HID+CDC gereksinimi bunu zorunlu kılar). |
| 9 | Arduino IDE ayar tablosu | Bölüm 7.3'teki 18 satır | Spec Arduino IDE'den söz etmez. Tablodaki her satır `platformio.ini`'deki bir ayarın birebir karşılığıdır (bölüm 7.6 eşleştirme tablosu). |
| 10 | Arduino IDE partition şeması | `16M Flash (3MB APP/9.9MB FATFS)` | `default_16MB.csv` ile en yakın eşleşen menü girdisi; `nvs` bölümü içerir. |
| 11 | Cihaz üzerinden fabrika sıfırlama | **Yoktur** | Spec §6.3 K11 için yalnızca iki işlev tanımlar (kısa = OS geçişi, uzun = HID yedek). Üçüncü bir sıfırlama kombinasyonu uydurmak spec'e aykırı olurdu; bunun yerine `pio run -t erase` ve elle `CMD` dizisi (bölüm 9.4) belgelenmiştir. |
| 12 | NVS bölüm adresi | `0x9000`, uzunluk `0x5000` | `default_16MB.csv`'nin standart yerleşimi. Bölüm 9.2'de adresi doğrulama komutu da verilmiştir. |
| 13 | `USB.begin()` çağrı sırası | HID sınıflarının `begin()` çağrıları `USB.begin()`'den **önce** | TinyUSB tanımlayıcısı `USB.begin()` anında dondurulur; sonradan eklenen arayüzler numaralandırılmaz. Spec §4 composite yapıyı ister, sırayı belirtmez. |
| 14 | PlatformIO kurulum yeri | Projenin `.venv` klasörüne **kurulmaz**, ayrı ortam | `.venv` PC uygulaması içindir (`pyserial 3.5`, Python 3.13.7 kurulu). PlatformIO'nun bağımlılıkları oradaki sürümlerle çakışabilir. |

---

*ExtraKeyboard MK1 · Firmware Kurulum Kılavuzu · v3.0.0 · BlueDevelopment*
