# Dokümantasyon Haritası

**ExtraKeyboard MK1 · v3.0.0** — Bu dosya, aradığın bilgiyi hangi dokümanda
bulacağını söyler. Doğrudan cevap vermez; **seni doğru dosyaya yönlendirir**.

> **Altın kural:** [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) tek doğruluk
> kaynağıdır. Herhangi bir doküman ile spec çelişirse **spec kazanır**.
> Pin numaraları, protokol mesajları, slot isimleri, JSON şeması, renkler,
> ölçüler ve modül API imzaları yalnızca orada tanımlanır.

---

## 1. "Ne yapmak istiyorsun?" → "Şu dosyayı oku"

### Projeyi tanımak

| İstediğin | Oku |
|---|---|
| Bu proje nedir, ne işe yarar? | [`../README.md`](../README.md) |
| Hangi dosya nerede, ne işe yarıyor? | **Bu dosya** + [`../README.md`](../README.md) → *Dosya düzeni* |
| v2'den v3'e ne değişti? | [`../README.md`](../README.md) → *Sürüm notları* |
| Kesin ölçü / pin / protokol nedir? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) |
| Sırada ne var, neler planlanıyor? | [`08-YOL-HARITASI.md`](08-YOL-HARITASI.md) |

### Cihazı yapmak

| İstediğin | Oku |
|---|---|
| Ne satın almalıyım? (malzeme listesi) | [`01-DONANIM.md`](01-DONANIM.md) · [`../README.md`](../README.md) → *Gereksinimler* |
| Hangi tel hangi pine gidiyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §3.1 · [`01-DONANIM.md`](01-DONANIM.md) |
| Hangi pinleri kullanmamalıyım? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §3.2 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. 3–6 |
| LED devresi neden diyot istiyor? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **7** |
| Enkoder RC filtresi neden zorunlu? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §3.4 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **12** |
| Lehimleme sırası ne olmalı? | [`05-MONTAJ.md`](05-MONTAJ.md) |
| Güç vermeden önce neyi ölçmeliyim? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **17** + kontrol listesi |

### Kasayı basmak / kestirmek

| İstediğin | Oku |
|---|---|
| Kasa ve plaka ölçüleri nedir? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §2.1 · [`02-MEKANIK.md`](02-MEKANIK.md) |
| OpenSCAD / DXF dosyalarını nasıl üretirim? | [`02-MEKANIK.md`](02-MEKANIK.md) |
| Hangi filament, hangi baskı ayarları? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **49, 59** |
| Delikler küçük çıkıyor, ne yapmalıyım? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **50, 51** |
| Heat-set insert nasıl takılır? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **54** |
| Enkoder somunu tutmuyor / gövde dönüyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **52, 53** |
| USB deliği nereye gelecek? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **2, 55** |

### Firmware yazmak / yüklemek

| İstediğin | Oku |
|---|---|
| Firmware'i nasıl derleyip yüklerim? | [`03-FIRMWARE.md`](03-FIRMWARE.md) · [`../README.md`](../README.md) → *Hızlı başlangıç* |
| `ARDUINO_USB_MODE` neden 0 olmalı? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **1** |
| Combo durum makinesi nasıl çalışıyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.2 · [`03-FIRMWARE.md`](03-FIRMWARE.md) |
| Hangi mesajı ne zaman göndermeliyim? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §5.1 / §5.2 |
| HID yedek modu ne kadarını kapsıyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §5.3 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **65** |
| Enkoder tık başına birden fazla olay üretiyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **13** |
| Enkoder ters yönde çalışıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **14** |
| Zamanlama / `millis()` / debounce tuzakları | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **20, 21, 22** |
| Ayarları nereye kaydetmeliyim? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §5.2 (`CMD SAVE`) · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **27** |

### PC uygulamasını geliştirmek

| İstediğin | Oku |
|---|---|
| Modüller birbirini nasıl çağırıyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §8 (API sözleşmesi) |
| `config.json` şeması nedir? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7 |
| Slot isimleri nasıl yazılır? (`K1`, `C_2_5`, `cw`) | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7.1 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **24** |
| 10 eylem tipi ne yapıyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7.2 · [`04-PC-UYGULAMASI.md`](04-PC-UYGULAMASI.md) |
| Arayüz sekmeleri ve tema | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §8 · [`04-PC-UYGULAMASI.md`](04-PC-UYGULAMASI.md) |
| Seri thread'den arayüze nasıl veri taşırım? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **34** |
| Config'i nasıl güvenli kaydederim? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **41** |
| Portu nasıl bulmalıyım? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **43, 44** |
| İki kopya çalışmasını nasıl engellerim? | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **45** |
| v2 config'i nasıl taşınıyor? | [`04-PC-UYGULAMASI.md`](04-PC-UYGULAMASI.md) · `tools/migrate_v2_config.py` |

### Kullanmak

| İstediğin | Oku |
|---|---|
| İlk kurulum ve izinler | [`05-MONTAJ.md`](05-MONTAJ.md) · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **35, 36** |
| Combo nasıl yapılır? | [`../README.md`](../README.md) → *Sık sorulanlar* · [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.2 |
| LED renkleri ne anlama geliyor? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.4 · [`../README.md`](../README.md) |
| Windows/macOS profili nasıl değişir? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.3 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **66** |
| Kısayolları nasıl yazmalıyım? | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7.2 · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **67** |
| Uygulamayı otomatik başlatmak | [`04-PC-UYGULAMASI.md`](04-PC-UYGULAMASI.md) · [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **46** |

### Bir şey çalışmıyor

| Belirti | Önce buraya bak |
|---|---|
| Cihaz bilgisayarda hiç görünmüyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **1, 2, 19** → [`07-SORUN-GIDERME.md`](07-SORUN-GIDERME.md) |
| Seri port var ama klavye yok | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **1, 2** |
| Cihaz hiç açılmıyor / sürekli resetleniyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **4, 5, 16, 33** |
| LED'ler yanmıyor veya rastgele renkler | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **7, 8, 9, 10** |
| Tek basışta eylem iki kez çalışıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **22, 26, 45** |
| Uygulama bağlanamıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **42, 43, 44** |
| Uygulama donuyor / sessizce çöküyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **34, 47, 48** |
| Eylem çalışıyor görünüyor ama bir şey olmuyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **35, 39, 40** |
| Türkçe karakterler yazılmıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **37** |
| Ses iki kademe değişiyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **60** |
| Combo çalışmıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **23, 24, 65** |
| Yanlış tuşun eylemi çalışıyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **70** |
| Ayarlar kayboldu | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **41, 46** |
| Firmware yüklenemiyor | [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) md. **69** |
| Yukarıdakilerin hiçbiri değil | [`07-SORUN-GIDERME.md`](07-SORUN-GIDERME.md) |

---

## 2. Tüm dosyalar — tek satırlık özetler

### Dokümanlar (`docs/`)

| Dosya | Tek satırda |
|---|---|
| [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) | **Tek doğruluk kaynağı**: pin tablosu, USB kimliği, CDC protokolü, cihaz içi mantık, `config.json` şeması, modül API imzaları, dosya düzeni. |
| [`01-DONANIM.md`](01-DONANIM.md) | Elektronik şema, malzeme listesi, kablolama tablosu, LED ve enkoder yardımcı devreleri, güç bütçesi. |
| [`02-MEKANIK.md`](02-MEKANIK.md) | Kasa/plaka geometrisi, OpenSCAD parametreleri, DXF üretimi, 3D baskı ve kesim seçenekleri. |
| [`03-FIRMWARE.md`](03-FIRMWARE.md) | ESP32-S3 firmware mimarisi, tuş/enkoder/combo durum makineleri, protokol gerçeklemesi, derleme ve yükleme adımları. |
| [`04-PC-UYGULAMASI.md`](04-PC-UYGULAMASI.md) | Python uygulamasının `core/` + `ui/` yapısı, eylem çalıştırma, tema, tepsi, otomatik başlatma, v2 taşıma. |
| [`05-MONTAJ.md`](05-MONTAJ.md) | Kutudan çalışır cihaza: lehimleme sırası, ölçüm kontrolleri, mekanik montaj, ilk çalıştırma ve izinler. |
| [`06-ONEMLI-NOTLAR.md`](06-ONEMLI-NOTLAR.md) | **70 maddelik incelik ve tuzak listesi** (risk / neden / çözüm / belirti) + spec dışı varsayımlar + 5 dakikalık kontrol listesi. |
| [`07-SORUN-GIDERME.md`](07-SORUN-GIDERME.md) | Belirtiden teşhise giden akış şemaları ve hızlı testler. |
| [`08-YOL-HARITASI.md`](08-YOL-HARITASI.md) | Sürüm geçmişi, bilinen sınırlamalar, planlanan özellikler. |
| [`INDEX.md`](INDEX.md) | **Bu dosya** — hangi soruya hangi doküman cevap veriyor. |

### Kök dizin

| Dosya | Tek satırda |
|---|---|
| [`../README.md`](../README.md) | Proje tanıtımı, yerleşim şeması, teknik özet, 3 adımlık hızlı başlangıç, SSS, sürüm notları. |
| `../run_app.py` | v3 uygulamasının giriş noktası; `app/main.py`'yi çağırır. |
| `../config.json` | v3 yapılandırması (şema 3). İlk çalıştırmada üretilir; elle düzenlenebilir. |
| `../Main.py` | **Eski v2** uygulaması, tek dosya. Dokunulmadı, yalnızca referans. |
| `../macro_config.json` | **Eski v2** yapılandırması. `config.json`'a otomatik taşınır, silinmez. |

### Kaynak dizinleri

| Dizin | Tek satırda |
|---|---|
| `../firmware/` | PlatformIO projesi: `platformio.ini` + `src/` (tuşlar, enkoder, LED'ler, protokol, NVS). |
| `../hardware/` | Şematik, malzeme listesi ve kablolama tablosunun kaynak dosyaları. |
| `../mechanical/` | OpenSCAD kaynakları ve DXF üretici; kasa, plaka ve taban. |
| `../app/core/` | `config.py` (ConfigManager), `device.py` (DeviceLink), `actions.py` (ActionRunner). |
| `../app/ui/` | `main_window.py`, `key_grid.py`, `combo_matrix.py`, `action_editor.py`, `tray.py`. |
| `../tools/` | `migrate_v2_config.py` — v2 ayarlarını v3 şemasına taşır. |

---

## 3. Hızlı başvuru — nerede ne tanımlı

Bir değeri değiştirmen gerekiyorsa, **kaynağı** burada:

| Bilgi | Tanımlandığı yer |
|---|---|
| GPIO pin numaraları | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §3.1 |
| Yasak pinler | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §3.2 |
| VID / PID / cihaz isimleri | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §4 |
| Protokol mesajları (`EV`, `CMD`, `HB`, `ID`, `ACK`, `ERR`) | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §5.1, §5.2 |
| HID yedek modu eşlemesi (F13–F22) | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §5.3 |
| Combo durum makinesi | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.2 |
| LED renkleri ve anlamları | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §6.4 |
| `config.json` şeması ve slot isimleri | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7, §7.1 |
| Eylem tipleri ve değer biçimleri | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §7.2 |
| Modül API imzaları | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §8 |
| Mekanik ölçüler | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §2.1 |
| Sürüm numaraları | [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md) §10 |

---

## 4. Okuma sırası önerileri

**Cihazı sıfırdan yapacaksan**
`README.md` → `00-CEKIRDEK-SPEC.md` → `01-DONANIM.md` → `02-MEKANIK.md` →
**`06-ONEMLI-NOTLAR.md` (A ve G bölümleri)** → `05-MONTAJ.md` → `03-FIRMWARE.md`

**Sadece yazılıma katkı vereceksen**
`00-CEKIRDEK-SPEC.md` §5, §7, §8 → `04-PC-UYGULAMASI.md` →
**`06-ONEMLI-NOTLAR.md` (F bölümü)**

**Sadece firmware'e katkı vereceksen**
`00-CEKIRDEK-SPEC.md` §3, §5, §6 → `03-FIRMWARE.md` →
**`06-ONEMLI-NOTLAR.md` (A, B, C, E bölümleri)**

**Cihazı sadece kullanacaksan**
`README.md` → `05-MONTAJ.md` → takıldığın yerde `07-SORUN-GIDERME.md`

**Bir hata avlıyorsan**
Yukarıdaki *"Bir şey çalışmıyor"* tablosu → `06-ONEMLI-NOTLAR.md` ilgili madde →
`07-SORUN-GIDERME.md`

---

<sub>ExtraKeyboard MK1 · v3.0.0 · Bu dosya `docs/` altındaki tüm dokümanların haritasıdır.</sub>

- [09-GENISLETME.md](09-GENISLETME.md) — Tuş sayısını artırma rehberi
