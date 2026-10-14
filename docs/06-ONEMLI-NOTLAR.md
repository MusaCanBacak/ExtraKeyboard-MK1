# 06 — Önemli Notlar / İncelikler ve Tuzaklar

> **Bu dosya projenin en kritik dokümanıdır.**
> Aşağıdaki **70 ana madde + 4 ek madde (`22a`, `51a`, `58a`, `70a`)**, yani
> toplam **74 maddenin** her biri, gerçekte insanların ayağını kaydıran bir
> ayrıntıyı anlatır. Bir şey çalışmıyorsa önce buraya bak.
> *(Harfli maddeler, anahtar tipinin **Cherry MX Blue (clicky)** olarak
> kesinleşmesiyle eklendi; mevcut 1–70 numaralandırması korunsun diye ana
> numaraların arasına harfle yerleştirildiler.)*
> Tek doğruluk kaynağı [`00-CEKIRDEK-SPEC.md`](00-CEKIRDEK-SPEC.md)'tir;
> burada yazan hiçbir şey spec'i geçersiz kılmaz, sadece açıklar.

**Her madde şu formattadır:**

- **Risk:** ne ters gidebilir
- **Neden:** teknik gerekçe
- **Çözüm:** somut olarak ne yapılacak
- **Belirti:** yanlış yaparsan ne görürsün

**İçindekiler**

| Bölüm | Maddeler | Konu |
|---|---|---|
| [A](#a-donanım--ölümcül-olanlar) | 1–6 | Donanım — ölümcül olanlar (pin/USB seçimi) |
| [B](#b-donanım--ws2812b-led-zinciri) | 7–11 | Donanım — WS2812B LED zinciri |
| [C](#c-donanım--enkoder-tuşlar-ve-kablolama) | 12–17 | Donanım — enkoder, tuşlar, kablolama |
| [D](#d-donanım--güç) | 18–19 | Donanım — güç bütçesi |
| [E](#e-firmware) | 20–33 **(+ 22a)** | Firmware |
| [F](#f-pc-uygulaması) | 34–48 | PC uygulaması |
| [G](#g-mekanik) | 49–59 **(+ 51a, 58a)** | Mekanik / 3D baskı |
| [H](#h-kullanım-ve-tasarım-kararları) | 60–70 **(+ 70a)** | Kullanım ve tasarım kararları |

**Cherry MX Blue (clicky) ile gelen maddeler — hepsi bir arada:**

| Madde | Konu |
|---|---|
| **22a** | Click jacket bırakış sıçraması → 5 ms debounce'ta **çift tetikleme** |
| **51a** | **5 pinli** anahtarın plastik ayakları → plakada eğri oturma |
| **58a** | **Boş kovuk rezonansı** → çınlamalı/boşluklu tuş sesi ve sünger çözümü |
| **70a** | **0.5 mm histerezis** → tuşu yeterince bırakmayınca ikinci basış kaybolur |

---

## A. DONANIM — ÖLÜMCÜL OLANLAR

Bu altı madde yanlışsa cihaz **hiç** çalışmaz. Lehim kalitesi, kod kalitesi,
kasa kalitesi hiçbir şey ifade etmez.

### 1. `ARDUINO_USB_MODE=0` olmadan HID hiç çalışmaz

**Risk:** Cihaz seri port olarak görünür, `HB` mesajları akar, her şey yolunda
sanırsın — ama bilgisayar onu **klavye olarak hiç görmez**. HID yedek modu
(F13–F21) tamamen ölüdür, `Consumer Control` ses tuşları çalışmaz.

**Neden:** ESP32-S3'te iki ayrı USB yığını var.
`ARDUINO_USB_MODE=1` → çipin içindeki *USB Serial/JTAG* çevre birimi kullanılır.
Bu birim donanım seviyesinde **sadece CDC-ACM + JTAG** yapabilir; HID sınıfı
tanımlamak fiziksel olarak mümkün değildir.
`ARDUINO_USB_MODE=0` → *USB-OTG* çevre birimi + **TinyUSB** yığını devreye girer.
Composite cihaz (HID Keyboard + HID Consumer Control + CDC-ACM) ancak budur.
Spec bölüm 4 tam olarak bu composite yapıyı şart koşar.

**Çözüm:** `firmware/platformio.ini` içinde build bayrakları **zorunlu**:

```ini
build_flags =
    -D ARDUINO_USB_MODE=0
    -D ARDUINO_USB_CDC_ON_BOOT=1
```

Arduino IDE kullanılıyorsa: **Tools → USB Mode → "USB-OTG (TinyUSB)"** ve
**Tools → USB CDC On Boot → "Enabled"**. Bu iki ayar ayrı ayrı seçilmelidir;
birini unutmak yeter.
Doğrulama: Windows'ta Aygıt Yöneticisi'nde hem *Klavyeler* hem *Bağlantı
Noktaları (COM & LPT)* altında girdi olmalı. macOS'ta
`system_profiler SPUSBDataType | grep -A6 ExtraKeyboard` çıktısında HID arayüzü
görünmeli.

**Belirti:** Seri porttan `EV KEY 1 UP` satırları düzgün geliyor ama uygulama
kapalıyken hiçbir tuş bir şey yapmıyor; enkoderi çevirince ses değişmiyor;
Aygıt Yöneticisi'nde "Klavyeler" altında yeni bir aygıt yok.

---

### 2. DevKitC-1'in iki USB portu var — yanlışına takarsan HID yok

**Risk:** Kart takılı, kod yükleniyor, seri monitör çalışıyor, ama cihaz
klavye olarak görünmüyor. Saatlerce firmware'de hata aranıyor. Hata firmware'de
değil, **kabloyu taktığın soket**te.

**Neden:** ESP32-S3-DevKitC-1 üzerinde iki adet USB-C soketi vardır:
- **UART** yazılı olan: kart üstündeki USB-seri köprü çipine gider. Sadece
  program yükleme ve klasik seri iletişim yapar. HID **imkânsız**.
- **USB** yazılı olan: doğrudan ESP32-S3'ün GPIO19/GPIO20'sine, yani yerleşik
  USB OTG çevre birimine bağlıdır. HID + CDC composite **yalnızca buradan** çıkar.

**Çözüm:** Nihai kullanımda kablo **her zaman "USB" yazan sokete** takılır.
Kasadaki USB açıklığı da bu sokete göre konumlandırılır (madde 55). Firmware'i
"UART" portundan yükleyip sonra kabloyu "USB" portuna almak kabul edilebilir bir
akıştır; ama `ARDUINO_USB_CDC_ON_BOOT=1` sayesinde "USB" portundan da yükleme
yapılabilir.

**Belirti:** Seri monitör açılıyor, `HB 12345` satırları geliyor, fakat işletim
sistemi hiçbir klavye görmüyor. Kabloyu diğer sokete alınca aygıt listesinde
iki yeni cihaz birden beliriyor.

---

### 3. GPIO19 ve GPIO20 yerleşik USB'dir — kullanırsan cihaz kaybolur

**Risk:** Bu iki pine bir şey bağlarsan ya da kodda `pinMode()` ile ele alırsan
USB veri hattı bozulur; cihaz bilgisayardan **tamamen kaybolur**. Seri port da
gider, HID de gider, yeniden program yüklemek için karta manuel BOOT+RESET
yapman gerekir.

**Neden:** ESP32-S3'te USB D− = GPIO19, D+ = GPIO20 sabittir, alternatifi yoktur.
DevKitC-1'de "USB" soketi doğrudan bu pinlere bağlıdır. Pin başlıklarında da
dışarı çıkarılmışlardır, bu yüzden yanlışlıkla kullanmak çok kolaydır.

**Çözüm:** Spec bölüm 3.1'deki pin tablosunda GPIO19/20 zaten yok. Kablolama
sırasında bu iki pini **boş bırak**, üzerlerine hiçbir tel lehimleme, kod içinde
adlarını hiç geçirme. Pin başlığında yanlışlıkla temas etmesin diye komşu
pinlere lehim yaparken dikkat et.

**Belirti:** Kart güç alıyor (kırmızı LED yanıyor) ama bilgisayarda hiçbir aygıt
belirmiyor; `ls /dev/cu.*` çıktısında yeni bir şey yok; Windows "USB aygıtı
tanınmadı" diyor.

---

### 4. GPIO26–32 flash, GPIO33–37 octal PSRAM — cihaz hiç boot etmez

**Risk:** Bu pinlerden birine tuş bağlarsan ve tuş basılıyken (yani pin GND'ye
çekiliyken) güç verirsen, çip flash'ı okuyamaz. Cihaz boot etmez, sonsuz reset
döngüsüne girer ya da tamamen ölü kalır.

**Neden:** ESP32-S3-WROOM-1 **N16R8** modülünde:
- GPIO26–32 → SPI Flash hatları (SPICS1, SPIHD, SPIWP, SPICLK, SPIQ, SPID).
- GPIO33–37 → **octal** PSRAM hatları. `N16R8`'in "R8" kısmı 8 MB octal PSRAM
  demektir; quad PSRAM'li modüllerde 33–37 serbesttir ama **bizim modülde değil**.

Bu hatlar çip her komut çektiğinde saniyede milyonlarca kez kullanılır. Dışarıdan
bir tuşla GND'ye çekmek, çalışan bir işlemcinin adres yolunu kısa devre etmekle
aynı şeydir.

**Çözüm:** Spec bölüm 3.2'deki yasak listesine harfiyen uy. Kullanılan tüm
GPIO'lar 4–18 aralığındadır (4,5,6,7,8,9,10,11,12,13,14,15,16,17,18). Bir pin
eklemen gerekirse önce 21, 38, 39, 40, 41, 42, 47 gibi gerçekten serbest
pinlere bak.

**Belirti:** Karta güç verince hiçbir şey olmuyor; ya da seri konsolda sürekli
tekrar eden `rst:0x7 (TG0WDT_SYS_RST)` / `invalid header` / `flash read err`
satırları akıyor. Tuşu bırakıp resetleyince açılıyorsa teşhis kesindir.

---

### 5. Strapping pinleri (GPIO0, 3, 45, 46) — açılışta bootloader'a düşme

**Risk:** Bu pinlerden birine tuş bağlarsan, cihaz **takılırken o tuşa basılı
olması** hâlinde normal firmware yerine bootloader'a düşer veya yanlış flash
voltajıyla açılır. Kullanıcı sebebini asla anlayamaz; "bazen açılmıyor" der.

**Neden:** ESP32-S3 reset anında dört pinin seviyesini okuyup çalışma modunu
belirler:
- **GPIO0** → LOW ise indirme (bootloader) modu.
- **GPIO46** → boot modu seçiminde GPIO0 ile birlikte okunur.
- **GPIO45** → VDD_SPI voltajı (1.8 V / 3.3 V) seçimi. Yanlışsa flash okunamaz.
- **GPIO3** → JTAG sinyal kaynağı seçimi.

Bizim tüm tuşlarımız `INPUT_PULLUP` + anahtar → GND, yani **basılıyken LOW**.
Yani strapping pinine bağlı bir tuş, tam da bootloader'a düşüren durumu üretir.

**Çözüm:** Bu dört pini kullanma. Spec'teki pin tablosunda zaten yoklar.
Kartın üstündeki **BOOT** düğmesi GPIO0'a bağlıdır; kasayı kapatırken bu düğmeye
bir şeyin (vida kulesi, kablo demeti, sünger) sürekli baskı yapmadığından emin ol.

**Belirti:** Cihaz bazen açılıyor bazen açılmıyor; açılmadığında bilgisayarda
"ESP32-S3 in download mode" benzeri bir seri aygıt beliriyor ama HID yok.

---

### 6. GPIO48 dahili RGB LED ve DevKitC-1 v1.0/v1.1 farkı

**Risk:** "Kartın üstünde zaten RGB LED var, onu kullanayım" deyip GPIO48'e
kod yazıyorsun, hiçbir şey yanmıyor. Ya da harici WS2812B zincirini GPIO48'e
bağlıyorsun, kart üstündeki LED zincirin başına giriyor ve renkler bir kayıyor.

**Neden:** DevKitC-1'in donanım revizyonları arasında dahili RGB LED pini
değişti: **v1.0 → GPIO48**, **v1.1 → GPIO38**. (Espressif'in resmî revizyon
değişikliği bu yöndedir; `docs/01-DONANIM-PIN-SEMASI.md` bölüm 4.1 aynı şeyi
söyler.) Ayrıca bazı kartlarda bu LED'i besleyen `RGB` lehim köprüsü
fabrikada **açık** gelir.
Spec bölüm 3.2 GPIO48'i "isteğe bağlı kullanılabilir" olarak işaretler,
**zorunlu değil**.

**Çözüm:** Projenin LED_DATA pini **GPIO14**'tür ve harici 3 LED'lik zincir
oraya bağlanır. Dahili LED'i sadece geliştirme sırasında "canlılık işareti"
olarak kullan; kabul testlerinde ona güvenme. Kullanacaksan önce kartının
şemasından pin numarasını doğrula.

**Belirti:** GPIO48'e yazdığın renk kartta görünmüyor; ya da harici LED1
beklediğin rengi değil bir öncekinin rengini gösteriyor (zincirde fazladan bir
LED var demektir).

---

## B. DONANIM — WS2812B LED ZİNCİRİ

### 7. WS2812B 5 V'ta beslenirken 3.3 V veri seviyesi sınırdadır — 1N4148 matematiği

**Risk:** LED'ler hiç yanmaz, ya da rastgele renkler çakar, ya da bugün çalışır
yarın çalışmaz. En sinsi hâli: masada çalışır, kasaya girip kablolar uzayınca
bozulur.

**Neden:** WS2812B veri girişi için mantıksal yüksek eşiği
**V_IH = 0.7 × VDD**'dir.

| Besleme (VDD) | Gereken V_IH | ESP32-S3 çıkışı (V_OH ≈ 3.3 V) | Sonuç |
|---|---|---|---|
| 5.0 V | 0.7 × 5.0 = **3.50 V** | 3.3 V | ✗ 0.2 V **eksik** |
| 4.3 V | 0.7 × 4.3 = **3.01 V** | 3.3 V | ✓ 0.29 V pay |

Yani doğrudan 5 V beslemede sinyal eşiğin **altında** kalır. Bazen çalışması
şansa bağlıdır (üretim toleransı) ve bu yüzden hata çok geç fark edilir.

**Çözüm (spec 3.3'te zorunlu):** LED'lerin +5 V hattına **seri 1N4148 diyot**
koy. Silisyum diyotun ileri gerilim düşümü ≈ 0.65–0.7 V olduğundan LED besleme
gerilimi 4.3 V'a iner, eşik 3.01 V'a düşer, 3.3 V rahatça tanınır.

```
VBUS 5V ──►|──┬── WS2812B VCC (≈4.3 V)
          1N4148 │
                === 1000 µF / 10 V
                 │
GND ─────────────┴── WS2812B GND
```

Diyot **yönü** kritik: bant (katot) LED tarafına bakar. Ters takarsan LED'ler
hiç güç almaz.
Akım kontrolü: 1N4148'in sürekli ileri akımı ~200 mA'dir. 3 LED'in tam beyaz
teorik tepe akımı 3 × 60 mA = 180 mA — sınıra çok yakın. Varsayılan parlaklık
60/255 olduğu için gerçek çekim 180 × 60/255 ≈ **43 mA**'dir, sorun yok.
Parlaklığı 255'e çıkarıp uzun süre beyaz yakacaksan diyodu **1N4001** (1 A) ile
değiştir; gerilim düşümü benzerdir.
*Alternatifler:* 74AHCT125 seviye çevirici (en temiz çözüm) veya 3.3 V veri ile
çalışan **SK6812**.

**Belirti:** İlk LED yanıyor diğerleri yanmıyor; renkler titriyor; kabloyu
elinle tutunca düzeliyor; parlaklığı düşürünce daha kararlı çalışıyor.

---

### 8. 1000 µF kondansatör yoksa ilk LED ölür

**Risk:** Cihazı ilk kez takarken zincirin **ilk LED'i** anında ölür. Sonra
"lehim hatası mı acaba" diye saatlerce zincir sökülür.

**Neden:** WS2812B'ler açılış anında dahili kontrolcülerini beslemek için ani
bir akım darbesi çeker. USB hattı üzerinden gelen bu darbe, kablo endüktansıyla
birlikte **gerilim aşımı (overshoot)** üretir. Zincirin ilk elemanı bu darbeyi
tam göğüsler ve mutlak maksimum gerilimini (VDD + 0.3 V) aşan bir tepe görür.

**Çözüm:** LED zincirinin besleme uçlarına, **LED'lere olabildiğince yakın**,
**1000 µF / 10 V** elektrolitik kondansatör bağla. Polarite kritiktir:
kondansatörün üzerindeki beyaz bant/eksi işareti **GND** tarafına gelir.
Kondansatör 1N4148'in **LED tarafına** takılır (4.3 V hattına), 5 V tarafına
değil — böylece darbeyi doğrudan LED'lerin gördüğü noktada bastırır.

**Belirti:** İlk takışta bir "cik" sesi/kıvılcım; sonrasında LED1 hiç yanmaz
veya sabit beyaz kalır ve LED2–LED3 hiç veri almaz (çünkü LED1'in DOUT'u ölü).

---

### 9. 330 Ω seri direnç veri hattını ve ilk LED'i korur

**Risk:** Direnç yoksa ilk LED'in DIN girişi zamanla ya da anında bozulur;
zincir "bazen" veri alır.

**Neden:** MCU çıkışı ile LED girişi arasındaki kablo bir iletim hattı gibi
davranır. WS2812B'nin ~400 ns'lik hızlı kenarlarında uyumsuz empedans **çınlama
(ringing)** üretir; tepe değerler besleme gerilimini aşıp giriş koruma
diyotlarını sürekli iletime sokar. 330 Ω seri direnç bu kenarları yumuşatır ve
koruma diyotlarından geçen akımı sınırlar; ayrıca ESD için bir tampon oluşturur.

**Çözüm:** 330 Ω direnci **MCU pinine (GPIO14) yakın** koy, LED tarafına değil.
Yakınlık önemlidir: dirençten sonraki kablo uzunluğu ne kadar fazlaysa koruma o
kadar iyi çalışır.

**Belirti:** Uzun kabloda LED'ler bozuluyor, kısa kabloda düzeliyor; ilk LED
zamanla renk kaçırmaya başlıyor.

---

### 10. WS2812B DIN/DOUT yönü — ters lehimlersen hiçbir şey yanmaz

**Risk:** Zincir tamamen sessiz kalır. Kod doğru, besleme doğru, ama veri LED'e
girmiyor çünkü LED'in **çıkışına** bağlanmış.

**Neden:** WS2812B tek yönlü bir shift register zinciridir: veri **DIN**'den
girer, LED kendi 24 bitini alıkoyar, kalanı **DOUT**'tan bir sonrakine yollar.
DOUT bir **çıkıştır**, oraya sinyal sürmek hiçbir işe yaramaz. Tek tek LED
modüllerinde ok işaretleri küçüktür ve kasa içinde LED ters çevrildiğinde
görünmez hâle gelir.

**Çözüm:** Lehimden **önce** her modülün üstündeki ok yönünü kalemle işaretle.
Zincir sırası: `GPIO14 → 330 Ω → LED1.DIN`, `LED1.DOUT → LED2.DIN`,
`LED2.DOUT → LED3.DIN`. LED3.DOUT boşta kalır.
Spec bölüm 6.4'e göre LED1 = OS, LED2 = Combo, LED3 = Bağlantı; yani **zincirin
sırası aynı zamanda anlam sırasıdır** — LED'leri sırayla dizmezsen semboller
karışır.

**Belirti:** Hiçbir LED yanmıyor (ters), ya da LED1 yerine LED3 mavi yanıyor
(sıra ters dizilmiş).

---

### 11. Güç sırası: veri varken besleme yoksa LED yanar (bileşen olarak ölür)

**Risk:** Test sırasında ESP32'yi USB'den beslerken LED'lerin 5 V ucunu ayrı
tutup sadece veri kablosunu takılı bırakmak, LED'leri kalıcı olarak öldürür.

**Neden:** VDD yokken DIN pinine 3.3 V uygulanınca akım, girişin ESD koruma
diyodu üzerinden çipin besleme rayına akar. Bu diyot birkaç mA için tasarlanmıştır;
"hayalet besleme" onu ve arkasındaki devreyi yakar.

**Çözüm:** Prensip: **önce GND, sonra VCC, en son DATA** bağla; sökerken tersi.
Kalıcı montajda LED besleme ve veri aynı konektörde olsun ki ikisi birlikte
gitsin/gelsin. Ölçüm yaparken LED zincirini komple sök, tek tek uç kaldırma.

**Belirti:** Test sırasında ısınan bir LED; sonradan o LED'in artık hiç
yanmaması ve zincirin ondan sonrasının ölmesi.

---

## C. DONANIM — ENKODER, TUŞLAR VE KABLOLAMA

### 12. EC11 kontak sıçraması — sadece yazılım debounce yetmez

**Risk:** Enkoderi bir tık çevirirsin, ses 3 kademe artar. Ya da bir tık sağa
çevirirsin, bir sola bir sağa gider. Kullanıcı deneyimi çöp olur.

**Neden:** Tuş sıçraması ile enkoder sıçraması **farklı problemlerdir**:
- Tuşta sıçrama "aynı yönde tekrar"dır; 5 ms yok saymak yeter.
- Enkoderde A ve B kanalları **birbirine göre faz farkı** taşır. Bir kanal
  sıçrarken diğeri sabitken durum makinesi **yanlış yönde** geçerli bir geçiş
  görür. Yani gürültü, "geçersiz veri" değil "geçerli ama yanlış veri" üretir.
  Yazılımda bunu ayırt etmenin güvenilir yolu yoktur.
- Ayrıca sıçrama darbeleri mikrosaniye mertebesindedir; `loop()` içinde
  yakalanmayabilir ama kesme (interrupt) ile yakalanır ve her biri bir olay sayılır.

**Çözüm (spec 3.4'te zorunlu):** Her iki kanala **RC alçak geçiren filtre**:
3V3 → 10 kΩ → pin, pinden GND'ye 100 nF.
Zaman sabiti τ = 10 kΩ × 100 nF = **1 ms**. Bu, mikrosaniyelik sıçramaları
tamamen yutar ama insan elinin en hızlı çevirmesini (tık başına ~5–10 ms)
geçirir. RC filtresinin üzerine **4 adımlı durum tablosu** çözücü gelir; ikisi
birlikte gürültüyü sıfırlar.
`ENC_SW` (GPIO13) için RC gerekmez; dahili pull-up + 5 ms yazılım debounce yeterlidir.

**Belirti:** Tek tık çevirmede ses 2–3 kademe atlıyor; yavaş çevirirken bazen
ters yöne gidiyor; hızlı çevirince adım kaçırıyor.

---

### 13. EC11 varyantı tık başına 1, 2 veya 4 geçiş üretir

**Risk:** Firmware'i bir enkoderle ayarlarsın, başka bir EC11 alırsın, aynı kod
bu sefer tık başına 4 olay üretir. "Aynı parça, aynı kod, farklı davranış" —
sinir bozucu bir durumdur.

**Neden:** EC11 gövdesindeki detent (tık) mekanizması ile quadrature çevrimin
hizası üretici ve model bazında değişir:
- **1 çevrim/detent (en yaygın):** Her tıkta A ve B tam bir 4 durumlu çevrim
  yapar, tık aralarında her iki kanal da HIGH'ta dinlenir. Spec bölüm 6.1'in
  varsaydığı varyant budur → **1 tık = 1 event**.
- **2 çevrim/detent:** Yarım çevrimde durur; her tıkta 2 event çıkar.
- **4 geçiş sayarsan:** Durum tablosunu "her geçerli geçişte olay üret" şeklinde
  yazmışsandır; tık başına 4 event alırsın.

**Çözüm:** Firmware'de bir **bölme sabiti** tut, sihirli sayı yayma:

```cpp
// Enkoder varyantına göre ayarlanır: 1 çevrim/detent → 4
static const int8_t ENC_STEPS_PER_DETENT = 4;   // ham quadrature geçişi / tık
```

Kalibrasyon yöntemi: geçici olarak her ham geçişte seri porta bir satır bastır,
enkoderi **tam 10 tık** çevir, çıkan satırı say. 40 çıktıysa sabit 4, 20 çıktıysa
2, 10 çıktıysa 1'dir. Ayrıca sadece "her iki kanal da HIGH" dinlenme noktasında
olay üretmek (detent hizalı çözücü) varyant farkını büyük ölçüde otomatik kapatır.

**Belirti:** Bir tıkta ses 4 kademe değişiyor (bölme yok) ya da 4 tık çevirince
ses 1 kademe değişiyor (fazla bölünmüş).

---

### 14. Enkoder yön tersliği — sağa çevirince ses kısılıyor

**Risk:** Kullanıcı sağa (saat yönü) çeviriyor, ses azalıyor. Küçük ama her
kullanımda rahatsız eden bir hata.

**Neden:** A ve B kanallarının hangisinin GPIO11 hangisinin GPIO12'ye gittiği
tamamen lehimleme sırasına bağlıdır. EC11'in üç bacaklı yüzünde orta bacak
**ortak (C)** uçtur; kenardaki iki bacak A ve B'dir ve **üzerlerinde etiket
yoktur**. %50 ihtimalle ters lehimlenir.

**Çözüm:** İki yol var, ikisi de meşru:
1. **Donanım:** A ve B tellerini yer değiştir (GPIO11 ↔ GPIO12). En hızlısı.
2. **Yazılım:** Firmware'de tek bir sabitle çevir — protokolü değiştirmeden:

```cpp
// Enkoder yönü ters lehimlendiyse true yap; EV ENC CW/CCW anlamı düzelir
static const bool ENC_REVERSED = false;
```

Hangisini seçersen seç **protokol sabittir**: saat yönü daima `EV ENC CW`
üretmek zorundadır (spec 5.1). Düzeltmeyi PC uygulamasında yapma — cihaz doğru
olayı göndermelidir, yoksa HID yedek modunda (uygulama yokken) ses yine ters
çalışır.

**Belirti:** `CMD ENC MODE HOST` iken uygulamanın kayıt ekranında sağa
çevirince `ccw` görünüyor.

---

### 15. Matris yok — bu bilinçli bir karardır, diyot arama

**Risk:** "Klavye yapıyoruz, matris ve 1N4148 diyot lazım" diye 11 diyot lehimlemek
ve boşuna karmaşa üretmek. Ya da tersi: matrise geçip combo'yu bozmak.

**Neden:** Combo işlevi, spec bölüm 6.2'ye göre **aynı anda 3 tuş** ister
(K10 + iki işlev tuşu). Satır/sütun matrisinde aynı anda üç tuş basılıysa ve
üçü bir dikdörtgenin köşelerine denk geliyorsa, elektriksel olarak **dördüncü
bir tuş da basılmış gibi görünür** (ghosting). Bunu engellemenin tek yolu her
anahtara seri diyot koymaktır (blocking diode) — 11 anahtar için 11 diyot,
22 ek lehim noktası, 22 ek hata ihtimali.

ESP32-S3'te 11 serbest GPIO fazlasıyla vardır. Spec bölüm 3.1: **her tuş
doğrudan kendi GPIO'suna**. Böylece:
- Ghosting fiziksel olarak imkânsızdır (her tuşun kendi okuma yolu var).
- N-key rollover bedavaya gelir.
- Tarama (scan) döngüsü yok → gecikme yok, `loop()` daha basit.
- Diyot yok → 22 lehim eksik.

**Çözüm:** Her anahtarın bir bacağı kendi GPIO'suna, diğer bacağı **ortak GND**'ye.
Anahtar polaritesi yoktur (MX anahtarının iki kontak bacağı simetriktir), ters
takma diye bir şey olmaz. Diyot alma, lehimleme, arama.

**Belirti:** (Yanlış yaparsan) matriste K10+K3+K7 basınca uygulamada K1 de
basılmış görünür ve combo yanlış hesaplanır.

---

### 16. Ortak GND: tuşlarda papatya dizimi tamam, LED'de asla

**Risk:** LED'ler yanıp sönerken tuşlar hayalet basış üretir; ya da parlak
beyazda cihaz kendini resetler.

**Neden:** İki farklı akım rejimi var:
- **Tuşlar** neredeyse sıfır akım çeker (sadece dahili pull-up'ın ~50 µA'i).
  Bu yüzden 11 anahtarın GND'sini tek bir telle papatya dizimi (daisy chain)
  şeklinde birbirine bağlayıp tek uçtan ESP32 GND'sine götürmek tamamen doğrudur
  ve el kablolamasında standart pratiktir.
- **LED'ler** ise ani ve büyük akım darbeleri çeker (43–180 mA, hem de yüksek
  frekanslı). Bu akım tuşların ince ortak GND teli üzerinden dönerse, telin
  direnci ve endüktansı üzerinde bir **gerilim düşümü** oluşur. Örnek: 0.2 Ω'luk
  bir dönüş yolunda 180 mA → 36 mV; darbe kenarlarında endüktif tepe bunun çok
  üstüne çıkar. Bu, tüm tuşların "GND referansını" oynatır ve eşik civarındaki
  okumaları bozar; kötü durumda çipin brownout dedektörünü tetikler.

**Çözüm:**
- Tuş GND'si: papatya dizimi, tek uçtan ESP32'nin **bir** GND pinine.
- LED GND'si ve 1000 µF kondansatörün GND'si: **ayrı ve kalın** bir telle,
  ESP32'nin **başka bir** GND pinine, doğrudan (yıldız topraklama).
- İki GND yolu sadece kartın üstünde buluşsun, kasa içinde hiçbir yerde ortak
  bir ince tel paylaşmasın.
- LED besleme teli için 24 AWG veya kalını, tuş telleri için 26–28 AWG yeterli.

**Belirti:** LED2 yeşil flaş yaparken seri porta sahte `EV KEY` satırları
düşüyor; parlaklığı 255 yapınca cihaz resetleniyor (`Brownout detector was
triggered` mesajı).

---

### 17. Lehim köprüsü ve kısa devre — güç vermeden önce multimetre

**Risk:** Tek bir lehim köprüsü USB portunu, ESP32'yi ya da anakartın USB
denetleyicisini yakabilir. 5 dakikalık kontrol, 300 TL'lik kartı kurtarır.

**Neden:** El kablolamasında en sık iki hata: (a) komşu GPIO pinleri arasında
lehim köprüsü, (b) 5 V ile GND'nin kondansatör veya LED bacağında birleşmesi.
İkisi de görsel olarak fark edilmesi zor, elektriksel olarak ölümcüldür.

**Çözüm — güç vermeden önce, sırayla:**
1. Multimetreyi **süreklilik (continuity/diyot)** moduna al.
2. **5 V ↔ GND** arası ölç. Kısa devre (0 Ω / bip) **olmamalı**. 1000 µF
   kondansatör yüzünden ölçüm birkaç saniye düşük başlayıp yükselir — bu
   normaldir, sabit 0 Ω olmamalıdır.
3. **3V3 ↔ GND** arası ölç. Kısa devre olmamalı.
4. Her tuş için: ilgili **GPIO ↔ GND**. Tuş bırakılmışken açık devre,
   basılıyken kısa devre olmalı. 11 tuşun 11'ini de tek tek dene — bu aynı
   zamanda pin haritasını doğrular.
5. **Komşu GPIO'lar arası** (örn. GPIO4 ↔ GPIO5) açık devre olmalı.
6. Lehimleri **büyüteç veya telefon kamerasıyla** yakınlaştırarak incele;
   çıplak gözle görülmeyen köprüler ekranda belli olur.
7. İlk güç verişi mümkünse **USB hub üzerinden** yap; anakartın portunu değil
   ucuz hub'ı riske at.

**Belirti:** Takar takmaz USB portu kapanıyor ("USB aygıtı çok fazla güç
çekiyor" / port ölüyor); kart ısınıyor; hiç LED yanmıyor.

---

## D. DONANIM — GÜÇ

### 18. USB 500 mA limiti ve LED parlaklığının güç bütçesine etkisi

**Risk:** Parlaklığı 255 yapıp üç LED'i de beyaz yakınca cihaz resetleniyor,
ya da bilgisayar portu kapatıyor.

**Neden — sayılarla:** USB 2.0 bir cihaza numaralandırmadan (enumeration) önce
**100 mA**, konfigürasyondan sonra istediği kadar (bizim descriptor'da 500 mA'e
kadar) verir.

| Yük | Akım |
|---|---|
| ESP32-S3, WiFi/BT kapalı, 240 MHz | ~40–60 mA |
| WS2812B başına bekleme (LED sönük, çip açık) | ~1 mA × 3 = 3 mA |
| WS2812B başına tam beyaz (3 kanal × 20 mA) | 60 mA |
| 3 LED tam beyaz, parlaklık **255** | 180 mA |
| 3 LED tam beyaz, parlaklık **60** (varsayılan) | 180 × 60/255 ≈ **43 mA** |

Varsayılan senaryo: 60 + 3 + 43 ≈ **106 mA** → spec bölüm 3.3'ün "< 150 mA"
hedefiyle uyumlu, USB limitinin çok altında.
Parlaklık 255 senaryosu: 60 + 180 = **240 mA** → hâlâ 500 mA'in altında ama
1N4148 diyodu (madde 7) zorlar ve ince kablolarda gerilim düşümü yapar.

**Çözüm:**
- Varsayılan parlaklığı **60/255**'te tut (spec 6.4). Kullanıcı arayüzünde
  parlaklık kaydırıcısını 0–160 aralığında sınırlamak makul bir korumadır.
- Firmware **açılışta LED'leri sönük başlatsın**, numaralandırma bittikten
  (CDC/HID hazır) sonra hedef parlaklığa yükselsin. Böylece 100 mA'lik
  numaralandırma öncesi bütçe aşılmaz.
- Üç LED'i aynı anda tam beyaz yakan bir animasyon yazma; spec'teki flaşlar
  zaten tek LED ve 80–150 ms'liktir.

**Belirti:** Parlaklığı artırınca cihaz kendini resetliyor; laptop'ın klavye
arka aydınlatması kısılıyor; "USB Aygıtı Güç Aşımı" uyarısı.

---

### 19. Şarj kablosu ile veri kablosu farkı

**Risk:** Her şey doğru, cihaz güç alıyor (LED'ler yanıyor) ama bilgisayarda
hiç görünmüyor. Saatler firmware'de aranıyor; sorun 20 TL'lik kabloda.

**Neden:** Piyasadaki USB-C kablolarının önemli bir kısmı **sadece güç** taşır;
D+/D− telleri fiziksel olarak yoktur (özellikle powerbank/şarj cihazlarıyla
gelen kısa kablolar). Ayrıca bazı USB-C↔USB-C kabloları USB 2.0 veri hatlarını
taşımaz.

**Çözüm:** Bilinen çalışan bir veri kablosu kullan; test için başka bir cihazı
(telefon, Arduino) aynı kabloyla bilgisayara bağlayıp veri geçiyor mu bak.
Kutuya/dokümana "veri kablosu gereklidir" notunu yaz. Kabloyu 1 m altında tut
(uzun kablo + ince tel = gerilim düşümü).

**Belirti:** LED'ler yanıyor, kart üstündeki güç LED'i yanıyor, ama
`ls /dev/cu.*` veya Aygıt Yöneticisi'nde hiçbir yeni aygıt yok. Kabloyu
değiştirince anında düzeliyor.

---

## E. FIRMWARE

### 20. `loop()` içinde `delay()` kullanmak enkoder tıklarını kaçırır

**Risk:** Enkoderi hızlı çevirince adımlar kayboluyor; tuşlar geç tepki veriyor;
LED flaşı sırasında basılan tuş hiç görülmüyor.

**Neden:** Bu firmware **kooperatif** çalışır: tek bir `loop()` içinde tuş
okuma, enkoder çözme, LED güncelleme ve seri işleme sırayla yapılır.
`delay(150)` çağırdığın 150 ms boyunca **hiçbir şey okunmaz**. İnsan eli
enkoderi saniyede 20 tıka kadar çevirebilir → tık başına 50 ms. 150 ms'lik bir
`delay()` üç tık birden yutar. Combo LED flaşı (150 ms) ve tuş flaşı (80 ms)
tam da bu tuzağa davetiye çıkarır.

**Çözüm:** Bloklamayan zamanlama kullan. Her zamanlı iş için bir `unsigned long`
zaman damgası ve bir durum bayrağı tut:

```cpp
static uint32_t led2_flash_until = 0;

void comboFired() {
    led2_flash_until = millis() + 150;   // "şimdiden 150 ms sonrası"
    led_set(2, COLOR_COMBO_FIRE);
}

void ledTask() {
    if (led2_flash_until && (int32_t)(millis() - led2_flash_until) >= 0) {
        led2_flash_until = 0;
        led_set(2, comboActive ? COLOR_COMBO_ON : COLOR_OFF);
    }
}
```

`loop()` içinde **tek bir `delay()` bile bulunmamalıdır**. `delayMicroseconds()`
yalnızca WS2812B kütüphanesinin içinde (bit zamanlaması için) kabul edilebilir.
Tuş okumayı ayrıca bir zamanlayıcıya bağlama; `loop()` zaten µs mertebesinde
döner, her turda hepsini oku.

**Belirti:** Enkoderi yavaş çevirince tam çalışıyor, hızlı çevirince adım
kaçırıyor; combo yaptıktan hemen sonraki tuş basışı kayboluyor.

---

### 21. `millis()` taşması (49.7 gün) ve doğru karşılaştırma yöntemi

**Risk:** Cihaz 49–50 gün kesintisiz açık kaldıktan sonra tuşlar kilitlenir,
debounce sonsuza kadar "henüz süre dolmadı" der, kalp atışı durur. Test
sırasında **asla** yakalayamazsın; kullanıcıda 7 hafta sonra çıkar.

**Neden:** `millis()` 32 bit işaretsizdir. 2³² ms = 4 294 967 296 ms =
**49.71 gün** sonra 0'a döner. Yanlış yazım:

```cpp
if (millis() >= son_zaman + 5) { ... }   // ✗ HATALI
```

`son_zaman = 4294967293` iken `son_zaman + 5` taşıp `2` olur; `millis()` hâlâ
~4.29 milyar olduğu için koşul **her turda** doğru olur → debounce tamamen
devre dışı kalır. Simetrik hata da mümkündür: taşmadan hemen sonra
`millis()` küçük, `son_zaman` büyük → koşul 49 gün boyunca yanlış kalır.

**Çözüm:** **Daima fark al**, toplama yapma. İşaretsiz aritmetikte çıkarma
taşmada da doğru sonucu verir (modüler aritmetik):

```cpp
if (millis() - son_zaman >= 5) { ... }   // ✓ DOĞRU, taşmada da çalışır
```

`son_zaman` mutlaka `uint32_t` (veya `unsigned long`) olmalı; `int` ya da
`long` yaparsan taşma davranışı tanımsızlaşır. Aynı kural `HB` üretimi
(1000 ms), enkoder uzun basış (800 ms), K11 uzun basış (3000 ms) ve tüm LED
flaşları için geçerlidir.
Kanıtlamak için test derlemesinde `millis()`'i `(millis() + 4294960000UL)`
döndüren bir sarmalayıcıyla değiştir; cihaz ~7 saniye sonra taşmaya girer ve
hatayı anında görürsün.

**Belirti:** 7 hafta çalışan cihaz aniden tuşlara tepki vermiyor ama `HB`
gönderiyor (ya da tam tersi); yeniden takınca düzeliyor.

---

### 22. Debounce süresi: çok kısa da çok uzun da hatalıdır

**Risk:** Kısa tutarsan tek basışta iki `EV KEY ... UP` gider ve eylem iki kez
çalışır (iki Safari penceresi, iki kez yapıştırma). Uzun tutarsan tuş "ağır"
hissettirir ve hızlı ardışık basışlar yutulur.

**Neden:** Mekanik kontak kapanırken/açılırken mikro sıçramalar yapar:
- Cherry MX ailesi veri sayfası değeri: **≤ 5 ms**.
- Ucuz klon anahtarlar ve eskimiş kontaklar: **10 ms**'ye kadar.
- **Clicky varyantlar (bu projedeki MX Blue) bırakış tarafında ek sıçrama
  üretir** — bkz. madde **22a**. Bu yüzden bu projede tuş debounce'u
  **5 ms değil 8 ms**'dir.
- İnsan eli aynı tuşa en fazla saniyede ~8 kez basabilir → basışlar arası
  ~125 ms, tuşun basılı kalma süresi ~50–60 ms.

Yani güvenli pencere yaklaşık **5–20 ms**'dir. Spec bölüm 6.1'in **5 ms**'i
lineer/taktil (jacket'siz) anahtarlar için doğru değerdir; **clicky MX Blue
için proje değeri 8 ms**'ye çıkarılmıştır (madde 22a). Enkoder butonu
(`ENC_SW`) **5 ms**'de kalır — orada click jacket yoktur.

**Çözüm:** Tuş başına ayrı durum makinesi, ayrı zaman damgası (tek bir global
`last_change` **yanlıştır**; combo'da üç tuş aynı anda değişir):

```cpp
struct KeyState {
    uint8_t  pin;
    bool     stable;        // debounce edilmiş son durum (true = basılı)
    bool     raw_last;      // ham okuma
    uint32_t t_change;      // ham okumanın son değiştiği an
};
// Tek adres: firmware/src/config.h
//   #define EK_KEY_DEBOUNCE_MS    8   // tuşlar   (MX Blue clicky)
//   #define EK_ENC_SW_DEBOUNCE_MS 5   // enkoder butonu (EC11 kubbe)
```

Ham okuma değiştiğinde `t_change` güncellenir;
`millis() - t_change >= EK_KEY_DEBOUNCE_MS` olduğunda `stable` güncellenir ve
olay üretilir. **Sayıyı `config.h` dışında hiçbir dosyaya yazma** — iki yerde
duran bir debounce değeri er geç ayrışır. Hâlâ çift tetikleme görüyorsan
8 → 12 ms yap; 20 ms'yi geçme.

**Belirti:** Çok kısa → tek basışta uygulama iki kez açılıyor.
20 ms'den uzun → tuş "gecikmeli" hissettiriyor, hızlı çift basış tek sayılıyor.

---

### 22a. MX Blue'nun click jacket'i bırakışta EK sıçrama üretir — 5 ms yetmez

**Risk:** Tuşa **bir kez** basarsın, atadığın uygulama **iki kez** açılır. Ya da
metin eylemi iki kez yapışır, ya da bir kısayol iki kez gider. Klasik "5 ms
debounce yeterlidir" varsayımı **clicky bir anahtarda geçerli değildir**;
bu, MX Brown/Red ile hiç görmediğin bir hatadır ve MX Blue'ya geçer geçmez
ortaya çıkar.

**Neden:** MX Blue'nun sliderı **iki parçalıdır**. Gövdenin içinde stemden ayrı,
serbest hareket edebilen bir **click jacket** (tık ceketi) vardır:

- **Basarken:** stem aşağı iner, jacket bir noktada takılır, sonra kurtulup
  aşağı çarpar → *tık*. Kontak bu sırada zaten kapanmıştır.
- **Bırakırken:** stem yukarı çıkarken jacket'ten **ayrılır** ve jacket gövde
  içinde yukarı doğru geri çarpar. Bu mekanik darbe, tam da kontağın açıldığı
  ana **ikinci bir titreşim** bindirir.

Yani veri sayfasındaki **≤ 5 ms**'lik tipik sıçrama değeri **basış** tarafı
içindir; clicky bir anahtarda asıl sorun **bırakış (release)** tarafındadır.
Eskimiş, tozlanmış bir mavi anahtarda bu ek sıçrama **10 ms**'ye yaklaşabilir.

Bu proje için özellikle can sıkıcıdır çünkü **eylem `UP` anında tetiklenir**
(madde 25). Yani sıçramanın bindiği kenar, tam da eylemi çalıştıran kenardır:
5 ms'lik pencere kapanmadan gelen ikinci `UP`, **ikinci bir eylem** demektir.
Bir makro klavyede bu, "Chrome'u aç" tuşuna basınca **iki Chrome penceresi**
açılması demektir.

**Çözüm:** Tuş debounce'u **8 ms**. Tek adres `firmware/src/config.h`:

```c
#define EK_KEY_DEBOUNCE_MS        8     // tuş yazılım debounce (MX Blue clicky)
#define EK_ENC_SW_DEBOUNCE_MS     5     // enkoder butonu debounce (EC11 kubbe)
```

Neden 8 ms güvenli:

| Soru | Cevap |
|---|---|
| Sıçramayı kapatıyor mu? | Evet — veri sayfası ≤ 5 ms, jacket'in eklediği pay ile birlikte 8 ms tipik durumları kapatır. |
| Hissedilir mi? | **Hayır.** Bu bir makro klavyedir; hızlı yazı yazılmaz. Aynı tuşa saniyede en fazla birkaç kez basılır (basışlar arası ~125 ms). 8 ms bunun **%6**'sıdır. |
| Neden 20 ms değil? | 15–20 ms üzeri gecikme *fark edilmeye başlar* ve hızlı çift basış tek sayılır (madde 22). |

**Enkoder butonu neden 5 ms kalıyor:** `ENC_SW`, EC11'in gövdesine gömülü basit
**tek parçalı kubbe/kontak** mekanizmasıdır. İçinde click jacket yoktur,
dolayısıyla bırakış tarafında ek sıçrama üretmez. Farklı mekanizma → farklı
sabit. İkisini tek sayıya bağlamak, enkoder butonunu boşuna yavaşlatır.

> **Anahtar tipini değiştirirsen:** Lineer (MX Red/Black) veya taktil
> (MX Brown) anahtara geçersen click jacket ortadan kalkar,
> `EK_KEY_DEBOUNCE_MS` değerini **5**'e indirebilirsin. Kailh **Box White**
> tık'ı jacket yerine **click bar** ile üretir; onda da 8 ms uygun bir
> başlangıçtır.

**Belirti:** Tek basışta uygulama iki kez açılıyor / metin iki kez yapışıyor.
Seri konsolda (`pio device monitor -b 115200`) tek fiziksel basış için
**iki `EV KEY <n> UP`** satırı görünüyor — özellikle **bırakırken**, basarken
değil. Yeni anahtarda seyrek, birkaç aylık kullanımdan sonra sıklaşıyor.

---

### 23. Combo modunda normal tuş eventlerinin bastırılması ZORUNLUDUR

**Risk:** Kullanıcı K10 + K2 + K5 yapıyor; PC hem `C_2_5` combosunu hem K2 ve K5
tuşlarının normal eylemlerini çalıştırıyor. Üç uygulama birden açılıyor.

**Neden:** Spec bölüm 6.2 açıkça der: *"K10 basılıyken K1..K9'un normal `EV KEY`
eventleri ve HID kodları gönderilmez."* Bastırma **cihazda** yapılmak
zorundadır, PC'de değil — çünkü:
- HID yedek modunda (uygulama kapalı) PC tarafında filtreleyecek kimse yoktur;
  F14 ve F17 doğrudan işletim sistemine gider.
- PC'de filtrelemek zamanlama yarışı yaratır: `EV KEY 2 UP` ile `EV COMBO 2 5`
  arasında hangisinin önce geleceği garanti edilemez.

**Çözüm:** Combo durum makinesi `ARMED` durumuna girer girmez bir bayrak yükselt
ve `EV KEY`/HID üretim yollarının **ikisini birden** kapat:

```cpp
if (comboState != COMBO_IDLE) {
    // EV KEY gönderme YOK, HID keyboard report gönderme YOK.
    // Sadece combo durum makinesini besle.
}
```

Combo yalnızca `EV COMBO <a> <b>` üretir; `EV MODE COMBO_ON/OFF` sınır
işaretleridir. Spec 5.3'e göre HID yedek modunda combo tamamen devre dışıdır ve
LED3 kırmızı yanıp söner — yani bastırma orada da uygulanır.

**Belirti:** Bir combo tetiklediğinde PC uygulamasının günlüğünde combo
eyleminin yanı sıra iki ayrı tuş eylemi de görünüyor; HID yedek modunda combo
denerken metin kutusuna F-tuşu karakterleri düşüyor.

---

### 24. Combo normalize edilmezse 36 yerine 72 slot oluşur

**Risk:** Kullanıcı `2+5` combosuna bir eylem atıyor, sonra tuşlara `5+2`
sırasıyla basıyor ve hiçbir şey olmuyor. Ya da config dosyasında `C_5_2` gibi
şemada olmayan anahtarlar birikiyor, uygulama `KeyError` veriyor.

**Neden — sayı:** 9 tuştan 2'sini **sırasız** seçmek:
C(9,2) = 9!/(2!·7!) = (9×8)/2 = **36**.
**Sıralı** seçmek (permütasyon): P(9,2) = 9 × 8 = **72**.
Yani normalize etmezsen slot uzayı tam iki katına çıkar, kullanıcının ayarladığı
combo'nun ancak yarısı çalışır ve hangi yarısının çalışacağı basma sırasına bağlı
olur.

**Çözüm:** Normalizasyon **iki yerde birden** yapılır (savunmalı programlama):
1. **Firmware:** `EV COMBO <a> <b>` gönderilmeden hemen önce `a > b` ise takas et.
   Spec 5.1: *"`a < b`, ikisi de 1..9"*. Sıra önemsizdir (spec 6.2).
2. **PC:** `app/core/config.py` içindeki `combo_id(a, b)` fonksiyonu spec 8'e göre
   *"a>b ise takas eder"*. Uygulama gelen ham sayılara asla güvenmez, daima bu
   fonksiyondan geçirir.

```python
def combo_id(a: int, b: int) -> str:
    if a > b:
        a, b = b, a
    return f"C_{a}_{b}"
```

Config üretilirken de 36 anahtar `for a in 1..8: for b in a+1..9` döngüsüyle
üretilir; asla elle yazılmaz.

**Belirti:** `config.json` içinde `C_5_2` gibi bir anahtar görüyorsun; combo
ayarı bazen çalışıyor bazen çalışmıyor; combo sekmesindeki matriste 36 yerine
farklı sayıda dolu hücre var.

---

### 25. Eylem UP'ta tetiklenir — DOWN'da tetiklenirse combo ile çakışır

**Risk:** Eylemi `DOWN`'da çalıştırırsan, combo yapmak için ilk tuşa basar
basmaz o tuşun normal eylemi çalışır. Combo tamamlanmadan Safari açılır.

**Neden:** Combo, tanımı gereği **geleceğe bakan** bir olaydır: K10 + birinci
tuş + ikinci tuş. Birinci tuşa basıldığı anda bunun bir combo mu yoksa normal
basış mı olduğu **henüz bilinmez**. `UP` anına kadar beklemek bu belirsizliği
çözer; `UP` geldiğinde combo modunda olup olmadığımız kesindir.
Ek faydalar:
- Kullanıcı yanlış tuşa bastığını fark ederse parmağını kaydırıp bırakabilir
  (klasik "iptal" davranışı — tüm işletim sistemi düğmeleri böyle çalışır).
- İleride "uzun basış" ayrımı eklemek için doğal yer `UP`'tır.
- Tuş basılı tutulurken eylemin tekrar tekrar çalışması (auto-repeat) sorunu
  kendiliğinden ortadan kalkar.

**Çözüm:** Spec 5.1'e uy: `EV KEY <n> DOWN` **bilgi amaçlıdır** (uygulama LED
flaşı/animasyon için kullanır), eylem **yalnızca** `EV KEY <n> UP` üzerine
çalıştırılır. PC uygulamasında `DOWN` olayı `ActionRunner.run()` çağırmaz.

**Belirti:** Combo yaparken önce ilk tuşun eylemi, ardından combo eylemi
çalışıyor; bir tuşu basılı tutunca eylem defalarca tekrarlanıyor.

---

### 26. Combo'dan çıkarken "tüketilmiş tuş" bayrakları

**Risk:** Kullanıcı K10 + K2 + K5 combosunu yaptı, sonra parmaklarını kaldırdı.
Cihaz `EV COMBO 2 5` gönderdikten sonra bir de `EV KEY 2 UP` ve `EV KEY 5 UP`
gönderiyor → combo eylemi + iki normal eylem. Madde 23'ün gözden kaçan kardeşi.

**Neden:** Bastırma sadece "K10 basılıyken" kuralına bağlanırsa iki sızıntı yolu
kalır:
1. Kullanıcı **önce K2'ye**, sonra K10'a basarsa; K2 zaten basılıydı ve K10
   bırakıldığında K2'nin `UP`'ı normal sayılır.
2. Kullanıcı **önce K10'u bırakır**, sonra K2/K5'i bırakır; bırakma anında
   `comboState == IDLE` olduğu için `UP`'lar normal sayılır.

**Çözüm:** Her tuş için bir `consumed` (tüketildi) bayrağı tut:
- Combo moduna girildiğinde (`IDLE → ARMED`) **o an basılı olan tüm** K1..K9'un
  `consumed` bayrağı **true** yapılır.
- Combo modundayken basılan her tuşun `consumed` bayrağı **true** yapılır.
- `UP` işlenirken `consumed` true ise **hiçbir olay gönderilmez**, bayrak
  temizlenir.
- Bayrak yalnızca tuş fiziksel olarak bırakıldığında sıfırlanır.

**Belirti:** Combo çalışıyor ama arkasından bir veya iki fazladan eylem daha
tetikleniyor; uygulamanın olay günlüğünde `EV COMBO 2 5` satırının hemen
ardından `EV KEY 2 UP` görünüyor.

---

### 27. NVS yazma ömrü (~100 000 döngü) — her değişiklikte yazma

**Risk:** OS tuşuna (K11) her basışta NVS'e yazarsan, flash sektörü zamanla
yıpranır. Belirti aylar sonra ve **geri dönüşsüz** gelir: ayarlar artık
kaydedilmez ya da cihaz açılışta çöker.

**Neden — sayı:** NAND/NOR flash sektörünün tipik dayanımı **~100 000 silme
döngüsü**'dür. ESP-IDF'in NVS katmanı aşınma dengeleme (wear leveling) yapar ama
sınırlıdır: aynı anahtara sürekli yazmak sonunda aynı sektörü tüketir.
Kullanıcı günde 30 kez OS değiştirirse yılda ~11 000 yazma; birkaç yılda sınıra
yaklaşılır. Kötü senaryo: LED renk kaydırıcısını sürükleyen bir arayüz saniyede
20 `CMD LED` gönderir ve her birini kaydedersen **birkaç saatte** 100 000'i
geçersin.

**Çözüm:** İki katmanlı politika:
1. **RAM önce, flash sonra.** Ayar değişikliği anında RAM'deki yapıya yazılır ve
   `dirty = true` işaretlenir. Ayrı bir gecikmeli görev, son değişiklikten
   **5 saniye sonra** ve yalnızca `dirty` ise NVS'e yazar (debounce'lu kayıt).
2. **Aynı değeri yazma.** NVS'e yazmadan önce mevcut değeri oku, farklıysa yaz.
   ESP-IDF `nvs_set_*` zaten aynı değerde yazmayı atlar ama yapıyı toplu
   yazıyorsan bu koruma kaybolur.

`CMD SAVE` (spec 5.2) kullanıcının açık isteğidir; o anda beklemeden yaz.
`CMD LED ...` ve `CMD LED BRIGHT ...` çalışma anında etki eder ama **kendiliğinden
kaydedilmez** — kalıcı olması için `CMD SAVE` gerekir.

**Belirti:** Aylar sonra OS tercihi artık hatırlanmıyor; seri konsolda
`nvs: partition full` / `ESP_ERR_NVS_NO_FREE_PAGES` hataları.

---

### 28. HID Consumer Control macOS ve Windows'ta farklı davranır

**Risk:** Enkoder Windows'ta sesi düzgün değiştiriyor, macOS'ta hiçbir şey
yapmıyor (ya da tersi). "Aynı HID kodu, farklı sonuç."

**Neden:** `Volume Up` (Usage 0x00E9), `Volume Down` (0x00EA) ve `Mute` (0x00E2)
kodları Consumer Page (0x0C) altındadır ve iki sistem bunları farklı yorumlar:
- **Windows:** `Volume Increment/Decrement` (0x00E9/0x00EA) ana ses seviyesini
  değiştirir ve OSD gösterir. Adım büyüklüğü sistem tarafından belirlenir
  (genelde %2).
- **macOS:** Ses için `Volume Up/Down` çalışır ama macOS **rapor formatına
  duyarlıdır**; birçok gerçeklemede tuşun "bırakıldığı" raporu (0x0000)
  gönderilmezse ses **sürekli** artmaya devam eder ya da hiç tepki vermez.
  Ayrıca macOS bazı consumer kodlarını yalnızca cihaz gerçek bir klavye olarak
  tanınmışsa işler (madde 29 ile ilişkilidir).
- Adım büyüklüğü de farklıdır: macOS bir "tık"ta 1/16 birim değiştirir, Windows
  daha büyük adım atar. Aynı fiziksel çevirme iki sistemde farklı hızda ses
  değiştirir — bu bir hata değil, beklenen davranıştır.

**Çözüm:**
- Her consumer olayında **mutlaka çift rapor** gönder: önce kod, ardından
  (gecikmesiz veya ~5 ms sonra) **sıfır raporu** (tuş bırakıldı).

```cpp
consumer.press(HID_USAGE_CONSUMER_VOLUME_INCREMENT);
consumer.release();   // 0x0000 — bu satır YOKSA macOS'ta ses takılır
```

- Consumer Control'ü **ayrı bir HID arayüzü/rapor ID'si** olarak tanımla,
  klavye raporuyla karıştırma.
- Hem Windows hem macOS'ta ayrı ayrı test et; adım farkını "hata" sayma.
- Adım hassasiyeti kullanıcıyı rahatsız ediyorsa `CMD ENC MODE HOST` ile PC
  tarafına al ve `media` eylemini uygulamadan çalıştır (madde 60'a dikkat).

**Belirti:** macOS'ta enkoderi bir tık çevirince ses tavana çıkıyor veya hiç
değişmiyor; Windows'ta normal.

---

### 29. macOS "Klavye Kurulum Yardımcısı" penceresi

**Risk:** Cihaz ilk takıldığında macOS ekranın ortasında **"Klavye Kurulum
Yardımcısı"** penceresini açar ve *"Shift tuşunun sağındaki tuşa basın"* der.
Bizim klavyede öyle bir tuş yok; kullanıcı sıkışır, pencere kapanmaz gibi görünür.

**Neden:** macOS, tanımadığı her yeni USB HID klavye için fiziksel düzeni
(ANSI / ISO / JIS) belirlemek ister. Bu tespit, HID descriptor'daki **country
code** alanı 0 (belirtilmemiş) olduğunda tetiklenir. Sonuç, cihaz başına
`/Library/Preferences/com.apple.keyboardtype.plist` içinde **VID/PID + yerleşim
kimliği** ile saklanır.

**Çözüm — üç aşamalı:**
1. **Kullanıcıya:** Pencerede **"Devam"** deyip düzen seçme adımına gelince
   **ANSI (ABD)** seç, ya da pencereyi sol üstteki kırmızı düğmeyle kapat.
   Seçim VID/PID (`0x303A` / `0x82E1`) için kaydedilir ve **bir daha çıkmaz**.
2. **Firmware'de önlem:** HID descriptor'a `bCountryCode = 33` (ABD) yaz.
   Bu, macOS'un düzeni sorma ihtiyacını çoğu durumda ortadan kaldırır.
3. **Uyarı:** Spec bölüm 4'teki PID (`0x82E1`) değiştirilirse macOS cihazı
   **yeni** sayar ve pencere geri gelir. PID'i geliştirme sırasında oynatma.

Dokümantasyonda (`docs/05` montaj/ilk kurulum) bu pencerenin **normal** olduğunu
ve bir kez kapatılınca döneceğini yaz; kullanıcı korkmasın.

**Belirti:** İlk takışta ekranın ortasında klavye tanıma sihirbazı; kapatınca
tekrar açılıyorsa PID değişmiş ya da kaydetme izni yok demektir.

---

### 30. Seri buffer'ın dolması ve satırın bölünmesi

**Risk:** İki ayrı hata, aynı kökten:
(a) PC tarafında `EV COMBO 2 5` satırı `EV COM` + `BO 2 5` olarak iki parça
hâlinde okunur, ikisi de tanınmaz, combo hiç çalışmaz.
(b) Cihaz tarafında gönderim tamponu dolar ve `Serial.write()` bloklar →
`loop()` durur → enkoder tıkları kaybolur (madde 20'nin sinsi hâli).

**Neden:** USB CDC bir **bayt akışıdır**, mesaj sınırı garantisi yoktur. Bir
`read()` çağrısı yarım satır, tam satır ya da iki buçuk satır döndürebilir; bu
tamamen zamanlamaya ve USB paket sınırlarına (64 bayt) bağlıdır.
Gönderim tarafında ise: PC uygulaması portu açık tutup **okumazsa** (arayüz
donduysa, kullanıcı Arduino IDE monitörünü açık unuttuysa) host tarafındaki
tampon dolar; cihazın 256 baytlık TX tamponu da dolunca `Serial.write()`
tamponda yer açılana kadar bekler. Saniyede 1 `HB` + tuş olayları bu tamponu
dakikalar içinde doldurabilir.

**Çözüm — cihaz tarafı:**

```cpp
// Tampon doluysa satırı at, ASLA bloklama.
static bool sendLine(const char* line) {
    size_t need = strlen(line) + 1;             // + '\n'
    if (Serial.availableForWrite() < (int)need) return false;   // sessizce düş
    Serial.write((const uint8_t*)line, need - 1);
    Serial.write('\n');
    return true;
}
```

`HB` düşerse önemli değil (bir sonraki 1000 ms'de yenisi gelir); tuş olayları
öncelikli olduğu için `HB`'yi yalnızca tamponda bol yer varken gönder.
Gelen komutları da bayt bayt oku, `\n` görene kadar sabit boyutlu bir tampona
biriktir; tampon taşarsa satırı at ve tamponu sıfırla (asla `String +=` ile
sınırsız büyütme — madde 32).

**Çözüm — PC tarafı:**

```python
buf = ""
while running:
    chunk = ser.read(ser.in_waiting or 1).decode("utf-8", errors="replace")
    buf += chunk
    while "\n" in buf:
        line, buf = buf.split("\n", 1)
        handle_line(line.strip("\r"))
```

`readline()` de kullanılabilir ama **timeout mutlaka ayarlanmalıdır**
(`serial.Serial(..., timeout=0.2)`), yoksa kapanışta thread sonsuza kadar asılır.
Spec 5'in *"bilinmeyen satırlar sessizce yok sayılır"* kuralı burada hayat
kurtarır: bölünmüş bir satırın yarısı çöp olarak gelir ve gürültüsüzce atılır.

**Belirti:** Uygulamanın ham günlüğünde `EV KE`, `Y 3 UP` gibi kırık satırlar;
ya da cihaz bir süre sonra tamamen tepkisizleşiyor ama LED'ler son hâlinde
donmuş kalıyor.

---

### 31. Boot günlüğü CDC'ye karışır — "bilinmeyen satır" kuralı bunun içindir

**Risk:** Uygulama bağlanır bağlanmaz seri porttan `ESP-ROM:esp32s3-...`,
`rst:0x1 (POWERON)`, `entry 0x403c98...` gibi satırlar gelir. Ayrıştırıcı bunları
protokol mesajı sanıp hata verir veya çöker.

**Neden:** `ARDUINO_USB_CDC_ON_BOOT=1` iken ESP32-S3 açılış günlüğünü aynı CDC
arayüzünden basar. Ayrıca `log_e()`/`ESP_LOGx` çağrıları da oraya düşer.
Cihaz her resetlendiğinde (kullanıcı kabloyu çıkarıp taktığında) bu satırlar
tekrar akar.

**Çözüm:**
- **Uygulamada:** Spec 5'in kuralını harfiyen uygula — satır `EV `, `HB `, `ID `,
  `ACK `, `ERR ` ön eklerinden biriyle başlamıyorsa **sessizce yok say**.
  Ham günlük penceresinde göster, ama ayrıştırma denemesi bile yapma.
- **Firmware'de:** Üretim derlemesinde günlük seviyesini kapat:
  `-D CORE_DEBUG_LEVEL=0`. Kendi hata ayıklama çıktılarını protokole uygun
  `ERR <sebep>` satırlarıyla ver, serbest metin basma.
- Uygulama bağlandığında ilk iş `CMD ID` gönderip `ID 3.0.0 MK1 EK1-... WIN`
  yanıtını beklemektir; yanıt gelene kadar cihazı "hazır" sayma.

**Belirti:** Uygulama açılışta bir kez `ERR` gösteriyor veya günlük ekranı
anlamsız satırlarla doluyor; en kötüsü ayrıştırıcı `IndexError` ile thread'i
öldürüyor ve cihaz bir daha hiç yanıt vermiyor.

---

### 32. `String` birleştirme ve heap parçalanması

**Risk:** Cihaz saatlerce sorunsuz çalışır, sonra yavaşlar ve bir noktada
resetlenir. Sebep bellek sızıntısı değil, **parçalanma**dır.

**Neden:** Arduino `String` sınıfı her birleştirmede yeni bir heap bloğu ayırıp
eskisini bırakır. Saniyede en az bir `HB` satırı ürettiğimiz için bu döngü günde
~86 400 kez çalışır. Heap zamanla delik deşik olur; toplam boş bellek yeterli
görünse bile **bitişik** blok bulunamaz ve ayırma başarısız olur. ESP32'de bu
genelde `Guru Meditation Error` veya sessiz bir reset olarak biter.

**Çözüm:** Sıcak yollarda (her `loop()` turunda çalışan kod) `String`
**kullanma**. Sabit boyutlu tampon + `snprintf`:

```cpp
static char line[48];
snprintf(line, sizeof(line), "EV COMBO %u %u", (unsigned)a, (unsigned)b);
sendLine(line);
```

`sizeof(line)` verildiği için taşma imkânsızdır. En uzun protokol satırımız
`ID 3.0.0 MK1 EK1-A4C138 WIN` (~28 karakter) olduğundan 48 bayt fazlasıyla
yeter. Kurulum (`setup()`) içinde bir kez çalışan kodlarda `String` kullanmak
zararsızdır.

**Belirti:** Uzun süre açık kalınca rastgele resetler; seri konsolda
`Guru Meditation Error: Core 1 panic'ed (StoreProhibited)` ya da
`Failed to allocate` mesajları. `ESP.getMaxAllocHeap()` değeri zamanla düşüyorsa
teşhis kesindir.

---

### 33. LED güncellemesi kesmeleri kapatır ve akım darbesi üretir

**Risk:** Her LED yenilemesinde birkaç yüz mikrosaniye boyunca kesmeler kapanır;
sık yenilerken USB iletişimi bozulur, enkoder kesmeleri kaçar, en kötüsü LED
akım darbesi brownout dedektörünü tetikleyip cihazı resetler.

**Neden — sayı:** WS2812B protokolü ~1.25 µs'lik bit süreleriyle **kesin
zamanlama** ister. Bit-bang gerçeklemeler bu yüzden `portDISABLE_INTERRUPTS()`
çağırır. 3 LED × 24 bit × 1.25 µs ≈ **90 µs** + 50 µs reset darbesi ≈ **140 µs**
kesmesiz süre. Bunu her `loop()` turunda (saniyede binlerce kez) yaparsan USB
CDC'nin kesmeleri sürekli gecikir.
Ayrıca sönükten tam beyaza geçiş anlık **~140 mA'lik** bir akım sıçraması
demektir; 1000 µF kondansatör yoksa (madde 8) besleme çöker.

**Çözüm:**
- LED'leri **sadece durum değiştiğinde** yenile, her turda değil. Bir
  `led_dirty` bayrağı tut.
- Zorunlu periyodik yenileme gerekiyorsa **50 ms'de birden sık yapma** (20 Hz
  göz için fazlasıyla yeterli).
- ESP32-S3'te mümkünse **RMT** ya da **SPI** tabanlı sürücü kullan
  (`FastLED` ESP32 RMT arka ucu, `Adafruit_NeoPixel` ESP32'de RMT kullanır);
  bunlar kesmeleri kapatmadan donanımla zamanlama üretir.
- Renk geçişlerini yumuşat (bir kademede 0'dan 255'e atlama) — hem göze hoş
  gelir hem akım darbesini düşürür.

**Belirti:** LED flaşı sırasında seri satır kayboluyor veya bozuluyor; parlak
flaşta cihaz resetleniyor (`Brownout detector was triggered`); enkoder tam da
combo flaşı anında adım kaçırıyor.

---

## F. PC UYGULAMASI

### 34. Tkinter thread güvenli DEĞİLDİR — seri thread'inden widget'a dokunma

**Risk:** Bu, PC tarafının **bir numaralı** hatasıdır. Uygulama rastgele donar,
bazen sessizce çöker, bazen hiçbir hata mesajı vermeden kapanır. macOS'ta
`NSInternalInconsistencyException`, Windows'ta `RuntimeError: main thread is not
in main loop`, çoğu zaman ise **hiçbir şey** — sadece kilitlenmiş bir pencere.

**Neden:** Tk/Tcl yorumlayıcısı tek thread'lidir ve global bir yorumlayıcı
durumu tutar. Başka bir thread'den `label.configure(...)` çağırmak bu durumu
kilitsiz değiştirmek demektir. Hata **anında** oluşmaz; bozulan yapı dakikalar
sonra rastgele bir yerde patlar — bu yüzden teşhisi çok zordur.
macOS'ta ayrıca AppKit tüm arayüz çağrılarının **ana thread**'de olmasını şart
koşar; ihlal doğrudan çökmeyle sonuçlanabilir.

Spec bölüm 8 bunu açıkça yazar: *"`on_event` arka plan thread'inden çağrılır.
UI, `self.after(0, ...)` ile ana thread'e aktarmak zorundadır."*

**Çözüm — iki kabul edilebilir desen:**

1. **`after(0, ...)` ile devretme** (spec'in yazdığı, en kısa yol):

```python
def on_device_event(self, ev: DeviceEvent) -> None:
    # DİKKAT: bu metot ARKA PLAN thread'inden çağrılır.
    # Burada widget'a dokunma, sadece ana thread'e devret.
    self.after(0, self._handle_event_ui, ev)

def _handle_event_ui(self, ev: DeviceEvent) -> None:
    # Burası ana thread — widget'a dokunmak serbest.
    self.status_label.configure(text=ev.raw)
```

2. **Kuyruk + yoklama** (en sağlam; olay seli varsa bunu tercih et):

```python
self._queue: queue.Queue[DeviceEvent] = queue.Queue()

def on_device_event(self, ev):        # arka plan thread
    self._queue.put(ev)

def _pump(self):                       # ana thread, 50 ms'de bir
    try:
        while True:
            self._handle_event_ui(self._queue.get_nowait())
    except queue.Empty:
        pass
    self.after(50, self._pump)
```

Kural olarak: `DeviceLink`'in `on_event` geri çağrısında **tek bir widget
çağrısı bile** olmayacak. Kod incelemesinde ilk bakılacak yer burasıdır.

**Belirti:** Uygulama birkaç dakika sorunsuz çalışıp aniden donuyor; kapatınca
Python süreci arka planda kalıyor; günlükte hiçbir istisna yok.

---

### 35. macOS izinleri olmadan `pyautogui` sessizce hiçbir şey yapmaz

**Risk:** Uygulama çalışıyor, olaylar geliyor, günlükte *"Eylem çalıştırıldı"*
yazıyor, `run()` `(True, "...")` dönüyor — ama ekranda **hiçbir şey olmuyor**.
Hata da yok. En sinir bozucu hata sınıfı budur.

**Neden:** macOS'ta sentetik girdi üretmek iki ayrı TCC iznine tabidir ve
**ikisi de farklı şeyi kontrol eder**:
- **Gizlilik ve Güvenlik → Erişilebilirlik (Accessibility):** başka uygulamalara
  **tuş/fare göndermek** için gerekir. `pyautogui.hotkey()`, `write()`, `press()`
  buna bağlıdır. İzin yoksa `CGEventPost` çağrısı **hata döndürmez**, olay
  sessizce yutulur.
- **Gizlilik ve Güvenlik → Girdi İzleme (Input Monitoring):** klavye olaylarını
  **dinlemek** için gerekir (v2'deki `pynput` dinleyicisi bunu kullanıyordu).
  v3'te dinleme yok — cihaz CDC üzerinden konuşuyor — ama `pyautogui`/`pynput`
  içe aktarıldığında yine sorulabilir.

İzin **binary'ye** verilir, koda değil. Terminal'den çalıştırdığında izin
"Terminal"e; `.app` paketinden çalıştırdığında "ExtraKeyboard"a; PyCharm'dan
çalıştırdığında "PyCharm"a verilir. Üçü **birbirinin yerine geçmez**.

**Çözüm:**
1. **Sistem Ayarları → Gizlilik ve Güvenlik → Erişilebilirlik**'i aç, kilidi
   çöz, uygulamayı listeye ekle ve **anahtarı aç**.
2. Aynısını **Girdi İzleme** için yap.
3. Uygulama açılışta izni **kontrol etsin** ve yoksa Türkçe, yönlendirici bir
   uyarı göstersin — sessiz başarısızlıktan bin kat iyidir:

```python
def macos_erisilebilirlik_var_mi() -> bool:
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception:
        return True   # kontrol edilemiyorsa engelleme
```

4. Uyarıdaki düğme ayar panelini doğrudan açsın:
   `open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"`

**Belirti:** `shortcut` ve `text` eylemleri hiçbir şey yapmıyor ama `url`, `app`,
`folder` eylemleri sorunsuz çalışıyor. Bu ayrım teşhisi kesinleştirir: ilk ikisi
sentetik girdi ister, diğerleri istemez.

---

### 36. macOS'ta izin verdikten sonra uygulama yeniden başlatılmalıdır

**Risk:** İzni verirsin, hâlâ çalışmaz, "izin de işe yaramadı" deyip madde 35'i
eleyip yanlış yönde saatler harcarsın.

**Neden:** TCC izni süreç **başlangıcında** değerlendirilip önbelleğe alınır.
Çalışan bir sürece sonradan verilen izin, o süreç için etkinleşmez. macOS
bazen "uygulamayı çıkıp yeniden açın" der, ama çoğu zaman **hiçbir şey demez**.
Ayrıca uygulama **taşınırsa** (Downloads → Applications), **yeniden
imzalanırsa** ya da Python sürümü güncellenirse TCC kaydı geçersizleşir ve izin
sıfırlanır.

**Çözüm:**
- İzin verildikten sonra uygulamayı **tamamen kapat** (Dock'ta simge kalmasın,
  gerekirse `Cmd+Q`) ve yeniden aç.
- İzni verdiğin uygulamayı **taşımadan önce** taşı, sonra izin ver.
- Takılırsan TCC kaydını sıfırla: `tccutil reset Accessibility` (tüm uygulamalar
  için sıfırlar, sonra hepsini yeniden vermen gerekir — son çare).
- Uygulama içindeki "İzinleri kontrol et" düğmesi, izin yoksa
  **"İzni verdikten sonra uygulamayı kapatıp yeniden açın"** metnini
  açıkça göstersin.

**Belirti:** Ayarlar panelinde anahtar açık görünüyor ama tuşlar hâlâ
çalışmıyor; uygulamayı kapatıp açınca birden çalışıyor.

---

### 37. `pyautogui.write()` Türkçe karakter yazamaz — pano yedeği şart

**Risk:** `text` eylemine *"merhaba dünya, çğıöşü"* yazarsın; ekrana
*"merhaba dnya, "* düşer. Karakterler **sessizce** kaybolur.

**Neden:** `pyautogui.write()` metni karakter karakter **tuş basışına** çevirir.
Bunu yapmak için ABD (US QWERTY) düzenine göre sabit bir eşleme tablosu kullanır.
`ç ğ ı ö ş ü İ` gibi karakterler bu tabloda **yoktur**; `pyautogui` bilinmeyen
karakteri atlar (hata bile vermez). Türkçe klavye düzeni açık olsa bile durum
değişmez, çünkü sorun düzende değil kütüphanenin eşleme tablosundadır.

**Çözüm — pano üzerinden yapıştır:**

```python
import pyperclip, time, pyautogui

def metin_yaz(metin: str, os_key: str) -> None:
    ascii_mi = all(ord(c) < 128 for c in metin)
    if ascii_mi:
        pyautogui.write(metin, interval=0.01)
        return
    yedek = ""
    try:
        yedek = pyperclip.paste()          # kullanıcının panosunu koru
    except Exception:
        pass
    pyperclip.copy(metin)
    time.sleep(0.05)                        # panonun yerleşmesi için
    pyautogui.hotkey("command" if os_key == "mac" else "ctrl", "v")
    time.sleep(0.25)                        # YAPIŞTIRMA BİTMEDEN GERİ YÜKLEME!
    try:
        pyperclip.copy(yedek)
    except Exception:
        pass
```

**Kritik ayrıntı:** Panoyu geri yüklemeden önce **en az 200 ms** bekle. Hedef
uygulama `Cmd+V`'yi işlemeden panoyu geri alırsan eski içerik yapışır — ve bu
hata ancak bazı uygulamalarda ortaya çıkar, teşhisi zordur.
İkinci ayrıntı: Bazı uygulamalar (terminaller, sanal makineler, uzak masaüstü)
yapıştırmayı farklı kısayolla alır; `text` eylemi her yerde çalışmayabilir,
bunu doküman ve arayüz ipucunda belirt.

**Belirti:** Türkçe karakterler kayboluyor ama ASCII harfler yazılıyor; ya da
metin yazıldıktan sonra panoda beklenmedik bir içerik kalıyor.

---

### 38. macOS'ta `pyautogui` medya tuşlarını desteklemez — `osascript` yedeği

**Risk:** `media` eylem tipi (spec 7.2: `volume_up`, `volume_down`, `mute`,
`play_pause`, `next`, `prev`) Windows'ta çalışır, macOS'ta **hiçbir şey**
yapmaz veya `KeyError` fırlatır.

**Neden:** `pyautogui.KEYBOARD_KEYS` listesinde `volumeup`, `volumedown`,
`volumemute`, `playpause`, `nexttrack`, `prevtrack` girdileri **yalnızca
Windows** eşlemesinde (sanal tuş kodu VK_VOLUME_UP vb.) tanımlıdır. macOS'ta
medya tuşları normal klavye olayları değil, **`NSSystemDefined` türü özel
olaylardır**; `CGEventCreateKeyboardEvent` ile üretilemezler, bu yüzden
`pyautogui` onları desteklemez.

**Çözüm — platforma göre ayrı yol:**

```python
import subprocess, sys, pyautogui

_WIN_MEDIA = {
    "volume_up": "volumeup", "volume_down": "volumedown", "mute": "volumemute",
    "play_pause": "playpause", "next": "nexttrack", "prev": "prevtrack",
}

def medya_calistir(value: str) -> tuple[bool, str]:
    if sys.platform == "darwin":
        if value == "volume_up":
            s = 'set volume output volume (output volume of (get volume settings) + 6)'
        elif value == "volume_down":
            s = 'set volume output volume (output volume of (get volume settings) - 6)'
        elif value == "mute":
            s = 'set volume output muted (not (output muted of (get volume settings)))'
        elif value == "play_pause":
            s = 'tell application "System Events" to key code 16 using {function down}'
        elif value == "next":
            s = 'tell application "Music" to next track'
        elif value == "prev":
            s = 'tell application "Music" to previous track'
        else:
            return False, f"Bilinmeyen medya değeri: {value}"
        subprocess.run(["osascript", "-e", s], check=False)
        return True, "Medya komutu gönderildi"
    key = _WIN_MEDIA.get(value)
    if not key:
        return False, f"Bilinmeyen medya değeri: {value}"
    pyautogui.press(key)
    return True, "Medya tuşu gönderildi"
```

`osascript` ile ses ayarı **sistem sesini** değiştirir ve güvenilirdir; oynat/
duraklat ve şarkı geçişi ise **uygulamaya bağımlıdır** (Music, Spotify, tarayıcı
sekmesi ayrı ayrı davranır). Tam çözüm için `pyobjc` ile `NSSystemDefined` olayı
göndermek gerekir; bunu ek bağımlılık olarak değerlendirmek makul.

**En sağlam yol:** Ses için macOS'ta **cihazın kendi HID Consumer Control'ünü**
kullan (`CMD ENC MODE HID`) — hem izin gerektirmez hem her uygulamada çalışır.
Bu zaten spec 5.3'ün varsayılan davranışıdır. Ancak madde 60'taki çift tetikleme
tuzağına dikkat.

**Belirti:** macOS'ta `media` eylemi hiçbir şey yapmıyor veya günlükte
`KeyError: 'volumeup'` görünüyor; aynı config Windows'ta çalışıyor.

---

### 39. Windows'ta yönetici yetkili pencerelere tuş gönderilemez (UIPI)

**Risk:** Kullanıcı Görev Yöneticisi, `regedit`, yönetici olarak açılmış bir
terminal ya da bazı oyun/anti-hile pencereleri öndeyken kısayol eylemi
**sessizce hiçbir şey yapmaz**.

**Neden:** Windows'un **UIPI (User Interface Privilege Isolation)** mekanizması,
düşük bütünlük seviyesindeki bir sürecin yüksek bütünlük seviyesindeki bir
pencereye mesaj/girdi göndermesini engeller. `SendInput` başarılı döner ama olay
hedefe ulaşmaz — yine **sessiz başarısızlık**.
Ek olarak: bazı oyunlar `SendInput` yerine DirectInput/Raw Input okur ve sentetik
olayları hiç görmez; bu UIPI değil, ayrı bir sınırlamadır.

**Çözüm:**
- Kullanıcı bu senaryoya ihtiyaç duyuyorsa uygulamayı **"Yönetici olarak
  çalıştır"** ile başlatsın (kısayolun özelliklerinden kalıcı hâle getirilebilir).
  Bunun bedeli: otomatik başlatma UAC istemi gösterir; kalıcı çözüm için
  **Görev Zamanlayıcı**'da "En yüksek ayrıcalıklarla çalıştır" seçili bir görev
  oluşturulmalıdır (madde 46 ile birlikte düşün).
- Uygulama bu sınırı **belgelemeli**: Ayarlar sekmesinde tek satırlık bir not.
- Yönetici gerektirmeyen eylemler (`app`, `url`, `file`, `folder`, `command`)
  bu sınırdan etkilenmez; kullanıcıya alternatif olarak önerilebilir.

**Belirti:** `shortcut` eylemi çoğu uygulamada çalışıyor ama Görev Yöneticisi
öndeyken çalışmıyor; oyun içinde hiç çalışmıyor.

---

### 40. `pyautogui.FAILSAFE` ve `pyautogui.PAUSE` tuzakları

**Risk:** İki ayrı sinsi davranış:
(a) İmleç ekranın **sol üst köşesinde** duruyorken herhangi bir `pyautogui`
çağrısı `FailSafeException` fırlatır — fare hiç hareket etmemiş olsa bile.
Eylem çalışmaz, thread ölür.
(b) 10 adımlık bir `macro` eylemi beklenenden **1 saniye** uzun sürer.

**Neden:**
(a) `pyautogui` her fonksiyon çağrısının başında `_failSafeCheck()` çalıştırır;
bu fonksiyon **o anki fare konumunu** okur ve `FAILSAFE_POINTS` (varsayılan:
ekranın dört köşesi, öntanımlı olarak `(0,0)`) içindeyse istisna fırlatır.
Bizim eylemlerimiz fareyi hiç oynatmaz, ama kullanıcının imleci köşede durabilir
(Hot Corner kullananlarda çok sık).
(b) `pyautogui.PAUSE` varsayılan **0.1 s**'dir ve **her** çağrıdan sonra
uygulanır. 10 adımlı bir makro = 10 × 0.1 = **1 s** ek gecikme.

**Çözüm:** Uygulama başlangıcında tek bir yerde ayarla:

```python
import pyautogui
pyautogui.FAILSAFE = False   # fareyi hiç oynatmıyoruz, acil durdurmaya gerek yok
pyautogui.PAUSE = 0.0        # gecikmeyi biz macro adımlarıyla yönetiyoruz
```

`FAILSAFE = False` yapmanın bedeli, kaçak bir fare döngüsünü köşeye giderek
durdurma imkânını kaybetmektir; fare hareketi üretmediğimiz için bu bedel
sıfırdır. Buna karşılık her `pyautogui` çağrısını yine de `try/except` içine al
ve hatayı `(False, "mesaj")` olarak döndür — spec 8'deki
`run() -> tuple[bool, str]` sözleşmesi tam bunun içindir.
Makro adımları arasındaki beklemeyi spec 7.2'deki `|` ayraçlı sayılardan al
(`ctrl+c|500|ctrl+v` → 500 ms), `PAUSE`'a bırakma.

**Belirti:** Bazı kullanıcılarda eylemler hiç çalışmıyor ve günlükte
`FailSafeException: PyAutoGUI fail-safe triggered...` yazıyor; makrolar
beklenenden yavaş akıyor.

---

### 41. `config.json`'a atomik yazma — yoksa tüm ayarlar gider

**Risk:** Kaydetme sırasında uygulama çökerse, bilgisayar kapanırsa ya da disk
dolarsa `config.json` **yarım** kalır. Bir sonraki açılışta JSON ayrıştırılamaz;
uygulama varsayılanlara döner ve kullanıcının 36 combo + 9 tuş + 4 enkoder ayarı
**tamamen** kaybolur.

**Neden:** `open(path, "w")` çağrısı dosyayı **anında sıfırlar**. Yazma
tamamlanmadan süreç ölürse geriye 0 baytlık ya da yarım JSON kalır. Ayrıca
`f.write()` işletim sistemi tamponuna yazar; `close()` bile verinin diske
indiğini garanti etmez.

**Çözüm — spec 8'in şart koştuğu desen (`.tmp` + `os.replace`):**

```python
import json, os, tempfile, shutil

def save(self) -> None:
    dizin = os.path.dirname(os.path.abspath(self.path)) or "."
    os.makedirs(dizin, exist_ok=True)
    # 1) Bir önceki iyi sürümü yedekle
    if os.path.exists(self.path):
        try:
            shutil.copy2(self.path, self.path + ".bak")
        except OSError:
            pass
    # 2) Geçici dosyaya yaz, diske indir
    fd, tmp = tempfile.mkstemp(dir=dizin, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())      # KRİTİK: veriyi gerçekten diske yaz
        os.replace(tmp, self.path)    # atomik yer değiştirme
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
```

`os.replace` hem POSIX'te hem Windows'ta atomiktir (Windows'ta `MoveFileEx`
`MOVEFILE_REPLACE_EXISTING` ile). Geçici dosya **aynı dizinde** olmalıdır;
farklı diskteki `/tmp`'ye yazıp taşırsan işlem atomikliğini kaybeder.
`ensure_ascii=False` Türkçe karakterlerin okunabilir kalmasını sağlar
(`"Tuş 1"`, `"\u0054u\u015f 1"` değil).
Yüklemede sıra: `config.json` → bozuksa `config.json.bak` → o da bozuksa
varsayılan üret; **bozuk dosyayı silme**, `config.json.hatali-<zaman>` adıyla
sakla ki kullanıcı elle kurtarabilsin.

**Belirti:** Uygulama açılışta tüm ayarları sıfırlanmış gösteriyor;
`config.json` 0 bayt ya da son satırı yarım kalmış.

---

### 42. Seri port aynı anda tek uygulama tarafından açılabilir

**Risk:** Arduino IDE'nin Seri Monitörü, PlatformIO monitörü, `screen`, başka
bir ExtraKeyboard kopyası ya da uygulamanın önceki (donmuş) örneği portu tutar.
Uygulama bağlanamaz ve kullanıcı "cihaz bozuldu" sanır.

**Neden:** İşletim sistemleri seri portu **münhasır (exclusive)** açar:
- **Windows:** COM portları OS düzeyinde münhasırdır; ikinci açış
  `PermissionError: could not open port 'COM7': Access is denied.` verir.
- **macOS/Linux:** `pyserial` varsayılan olarak `TIOCEXCL` ile münhasır açar;
  ikinci açış `SerialException: [Errno 16] Resource busy`.

**Çözüm:**
- Uygulama bu istisnayı **yakalayıp** kullanıcıya Türkçe, eyleme dönük mesaj
  göstersin: *"Seri port başka bir uygulama tarafından kullanılıyor. Arduino IDE
  Seri Monitörü'nü veya PlatformIO monitörünü kapatıp yeniden deneyin."*
- `DeviceLink` yeniden bağlanma döngüsünü **sonsuza kadar sessizce** dönmesin;
  aynı hatayı arka arkaya görüyorsa arayüzde kalıcı bir uyarı bandı göstersin.
- Firmware yüklemeden önce uygulamayı kapat (madde 69).
- Tekil örnek kontrolü (madde 45) bu sorunun en yaygın sebebini baştan keser.

**Belirti:** LED3 kırmızı (bağlantı yok) kalıyor ama cihaz Aygıt Yöneticisi'nde
sorunsuz görünüyor; günlükte `Access is denied` / `Resource busy`.

---

### 43. macOS'ta `/dev/cu.*` ile `/dev/tty.*` farkı — daima `cu.*`

**Risk:** `/dev/tty.usbmodem...` açmayı denersen çağrı **bloklanır** ve
uygulama açılışta donar; en iyi ihtimalle timeout'a düşer. Ekranda hiçbir hata
görünmez.

**Neden:** macOS (ve BSD) her seri aygıt için **iki** düğüm oluşturur:
- **`/dev/tty.*` — "call-in" (gelen arama):** Modem çağını beklemek için
  tasarlanmıştır. `open()` çağrısı **DCD (Data Carrier Detect) sinyali gelene
  kadar bloklar** (`O_NONBLOCK` verilmedikçe). USB CDC cihazlarda DCD hiç
  gelmeyebilir → sonsuz bekleme.
- **`/dev/cu.*` — "call-out" (giden arama):** Doğrudan açılır, akış denetimi
  sinyallerini beklemez. Bizim kullanmamız gereken budur.

**Çözüm:** `DeviceLink.find_ports()` içinde macOS'ta **yalnızca `cu.` ile
başlayan** aygıtları kabul et:

```python
import sys
from serial.tools import list_ports

def find_ports(cfg) -> list[str]:
    bulunan = []
    for p in list_ports.comports():
        if sys.platform == "darwin" and "/tty." in p.device:
            continue                      # tty.* asla kullanılmaz
        if p.vid == 0x303A and p.pid == 0x82E1:      # spec bölüm 4
            bulunan.insert(0, p.device)   # VID/PID eşleşmesi önceliklidir
        elif p.product and "ExtraKeyboard MK1" in p.product:
            bulunan.append(p.device)      # yedek: Product string
    return bulunan
```

Spec bölüm 4'ün *"portu önce VID/PID, bulamazsa Product string ile bulur"*
kuralı burada uygulanır. Kullanıcının elle port seçebildiği açılır listede de
`tty.*` girdilerini gösterme — gösterirsen mutlaka seçilir.

**Belirti:** macOS'ta uygulama açılışta donuyor ya da "bağlanılıyor..."
durumunda kalıyor; aynı cihaz `screen /dev/cu.usbmodem...` ile sorunsuz açılıyor.

---

### 44. Cihaz yeniden takıldığında port adı değişir

**Risk:** `config.json`'a `"port": "COM7"` yazarsın; kullanıcı kabloyu başka bir
USB soketine takar, port `COM12` olur, uygulama bir daha asla bağlanamaz.

**Neden:**
- **Windows:** COM numarası **USB fiziksel yoluna** (port + hub) göre atanır ve
  kayıt defterinde saklanır. Farklı sokete takmak yeni bir numara üretir. Numara
  20'nin üzerine de çıkabilir.
- **macOS:** `/dev/cu.usbmodem<konum>` adındaki sayı USB **konum kimliğinden**
  türetilir; farklı soket/hub farklı ad demektir. Bazı kartlarda seri numaraya
  göre `cu.usbmodemEK1A4C1381` gibi kararlı bir ad da oluşabilir.
- Ayrıca cihaz her resetlendiğinde (kablo çıkarma, firmware yükleme) USB
  numaralandırması tekrarlanır ve düğüm **kaybolup yeniden belirir**.

**Çözüm:**
- `config.json`'da varsayılan **`"port": "auto"`**'dur (spec bölüm 7) ve öyle
  kalmalıdır. Port adı **kimlik değil, geçici bir tanıtıcıdır**.
- Bağlanma daima **VID/PID** (`0x303A` / `0x82E1`) ile yapılır; bulunamazsa
  Product string ile. Elle port seçimi yalnızca bir kaçış kapısıdır.
- `DeviceLink` kopan bağlantıyı fark edip **kendi kendine yeniden bağlanmalıdır**
  (spec 8: *"otomatik bulur ve yeniden bağlanır"*). Yeniden deneme aralığını
  sabit 1–2 s tut; üstel geri çekilme kullanıcıyı bekletir.
- Yeniden bağlanınca **`CMD ID` gönder** ve OS modunu senkronla; cihaz reset
  olmuş olabilir.

**Belirti:** Kabloyu başka sokete takınca uygulama bağlanmıyor; ayarlardan portu
elle seçince düzeliyor (ve bir dahaki sefere yine bozuluyor).

---

### 45. Tekil örnek kontrolü — iki kopya çalışırsa her eylem iki kez tetiklenir

**Risk:** Kullanıcı simgeye iki kez tıklar, ya da otomatik başlatma bir kopya
açarken kendisi ikincisini açar. İki kopya da... aslında **açılamaz** (madde 42
portu kilitler) ama daha kötüsü olur: ikinci kopya portu alamayıp sürekli
yeniden bağlanmaya çalışır, tepsi simgesi ikilenir, ayarları biri kaydederken
diğeri üzerine yazar ve config bozulur. Bağlantı sırayla el değiştirirse her
eylem **iki kez** çalışır.

**Neden:** Uygulama durumunun tek sahibi olmalıdır: seri port, `config.json` ve
tepsi simgesi paylaşılamaz kaynaklardır. İki süreç arasında hiçbir kilit yoktur.

**Çözüm (spec 8: *"tekil örnek kontrolü (port 64210)"*):** Yerel bir TCP
soketini dinlemeye çalış; başarısızsa zaten bir örnek var demektir.

```python
import socket, sys

_kilit_soketi = None

def tek_ornek_al(port: int = 64210) -> bool:
    global _kilit_soketi
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # DİKKAT: SO_REUSEADDR AYARLAMA — ayarlarsan ikinci örnek de bağlanabilir.
    try:
        s.bind(("127.0.0.1", port))
        s.listen(1)
    except OSError:
        s.close()
        return False
    _kilit_soketi = s          # süreç boyunca açık tut; kapanırsa kilit gider
    return True
```

Soket, süreç **nasıl ölürse ölsün** (çökme dahil) işletim sistemi tarafından
kapatılır — bu yüzden PID dosyasından çok daha sağlamdır (PID dosyası çökmeden
sonra "hayalet kilit" bırakır).
`_kilit_soketi` global tutulmalı, yoksa çöp toplayıcı soketi kapatır ve kilit
sessizce kaybolur. `127.0.0.1`'e bağlan, `0.0.0.0`'a değil — güvenlik duvarı
uyarısı çıkmasın.
İkinci örnek çıkarken kullanıcıya *"ExtraKeyboard zaten çalışıyor. Sistem
tepsisindeki simgeye bakın."* mesajını göstersin ve kapansın.

**Belirti:** Her tuşa basışta uygulama iki kez açılıyor; tepsi/menü çubuğunda
iki simge; `config.json` bazen eski hâline dönüyor.

---

### 46. Otomatik başlatmada çalışma dizini farklıdır — config bulunamaz

**Risk:** Uygulama elle açınca ayarları hatırlar, otomatik başlatmayla açılınca
**bomboş** gelir. Kullanıcı ayarlarını ikinci kez girer, sonra elle açar ve
eskiler geri gelir; ortada iki farklı config dosyası vardır.

**Neden:** `config.json` gibi **göreli** bir yol, sürecin **çalışma dizinine
(cwd)** göre çözülür. Otomatik başlatmada cwd uygulamanın dizini değildir:
- **Windows:** `HKCU\...\Run` anahtarından başlatılanlarda cwd genelde
  `C:\Windows\System32`.
- **macOS:** `~/Library/LaunchAgents/*.plist` ile başlatılanlarda cwd `/`
  (plist'te `WorkingDirectory` verilmedikçe).
- **PyInstaller ile paketlenmişse** `sys.executable` ile `__file__` farklı
  yerleri gösterir; `_MEIPASS` geçici dizindir ve **her açılışta silinir**.

Sonuç: `ConfigManager` dosyayı bulamaz, spec 8'e göre *"yoksa varsayılan
üretir"* ve **yanlış yere** yeni bir config yazar.

**Çözüm:** Yolu **asla** cwd'ye bırakma. İki kabul edilebilir strateji:

```python
import os, sys
from pathlib import Path

def varsayilan_config_yolu() -> str:
    # 1) Taşınabilir kullanım: uygulamanın yanındaki config.json
    if getattr(sys, "frozen", False):          # PyInstaller
        kok = Path(sys.executable).resolve().parent
    else:
        kok = Path(__file__).resolve().parent.parent.parent   # app/core/ -> proje kökü
    yanindaki = kok / "config.json"
    if yanindaki.exists() or os.access(kok, os.W_OK):
        return str(yanindaki)
    # 2) Yazılamıyorsa kullanıcı dizini (Program Files altına kurulum senaryosu)
    if sys.platform == "win32":
        taban = Path(os.environ.get("APPDATA", Path.home()))
    else:
        taban = Path.home() / "Library" / "Application Support"
    hedef = taban / "ExtraKeyboard"
    hedef.mkdir(parents=True, exist_ok=True)
    return str(hedef / "config.json")
```

Ek olarak:
- macOS LaunchAgent plist'ine `<key>WorkingDirectory</key>` ekle.
- Windows'ta Görev Zamanlayıcı kullanıyorsan "Başlangıç yeri (isteğe bağlı)"
  alanını doldur.
- Uygulama, kullandığı config yolunu **Ayarlar sekmesinde göstersin**. Teşhis
  süresini dakikalardan saniyelere indirir.

**Belirti:** Otomatik başlatmada ayarlar boş; diskte birden fazla `config.json`
var; elle açınca doğru, otomatikte yanlış davranıyor.

---

### 47. Eylemi arayüz thread'inde çalıştırma — uygulama donar

**Risk:** `app` tipinde ağır bir uygulama açan ya da `command` tipinde uzun süren
bir kabuk komutu çalıştıran bir eylem, arayüzü **saniyelerce** dondurur. Kullanıcı
bu sırada basılan tuşları kaybeder.

**Neden:** Madde 34'ün çözümü olan `after(0, ...)` deseni olayı **ana thread'e**
taşır. Eğer eylemi de orada çalıştırırsan, `subprocess.run(...)` bitene kadar
Tk olay döngüsü durur: pencere yeniden çizilmez, tepsi menüsü açılmaz,
`_pump()` çalışmaz ve gelen cihaz olayları kuyrukta birikir.
`pyautogui` çağrıları da (özellikle makrolar, `|500|` beklemeleriyle) saniyeler
sürebilir.

**Çözüm:** Rolleri net ayır — **üç** bağlam vardır:

| Bağlam | Görevi | Yapmayacağı |
|---|---|---|
| Seri thread (`DeviceLink`) | Port okuma, satır ayrıştırma, `on_event` çağırma | Widget'a dokunmak, eylem çalıştırmak |
| Ana thread (Tk) | Widget güncelleme, LED animasyonu, kullanıcı etkileşimi | Bloklayan iş yapmak |
| İşçi thread(ler) (`ActionRunner`) | `subprocess`, `pyautogui`, `webbrowser` | Widget'a dokunmak |

Eylemleri tek işçili bir kuyrukta sırayla çalıştır: hem arayüz akıcı kalır hem
iki eylem birbirine karışmaz (iki `pyautogui.hotkey()` aynı anda çalışırsa
değiştirici tuşlar birbirine geçer — `Ctrl` basılı kalır!). Sonucu
(`tuple[bool, str]`) yine `after(0, ...)` ile arayüze bildir.
Aynı slota çok hızlı ard arda gelen olaylar için basit bir koruma koy: aynı
slot 150 ms içinde ikinci kez tetiklenirse yut.

**Belirti:** Ağır bir uygulamayı açan tuşa basınca arayüz 2–3 saniye donuyor;
o sırada basılan tuşlar toplu hâlde sonradan çalışıyor; bazen `Ctrl` tuşu
takılı kalıyor.

---

### 48. Seri satır kod çözme (UTF-8) ve bozuk baytlar

**Risk:** Cihaz resetlenirken hatta yarım/gürültülü bayt düşer;
`bytes.decode("utf-8")` `UnicodeDecodeError` fırlatır; **arka plan thread'i
ölür** ve uygulama bir daha hiçbir olay almaz. Arayüz canlı görünür, cihaz
"bağlı" görünür, ama hiçbir tuş çalışmaz.

**Neden:** USB CDC bağlantısı kurulurken/koparken hatta tanımsız baytlar
oluşabilir; ayrıca boot günlüğü (madde 31) her zaman geçerli UTF-8 olmayabilir.
Python'da yakalanmamış bir istisna thread'i sessizce sonlandırır — ana thread
bunu **fark etmez**.

**Çözüm — üç katman:**
1. Kod çözerken asla katı olma: `chunk.decode("utf-8", errors="replace")`.
   Protokol saf ASCII olduğu için bozuk bayt zaten anlamsızdır; `replace` onu
   `\ufffd` yapar, satır tanınmaz ve spec 5'in kuralıyla sessizce atılır.
2. Okuma döngüsünün **tamamını** `try/except Exception` ile sar; hata olursa
   portu kapat, kısa bekle, yeniden bağlanma döngüsüne dön. Thread **asla**
   ölmemeli.
3. Ana thread bir **canlılık denetimi** yapsın: son `HB` üzerinden 3 saniyeden
   fazla geçtiyse bağlantıyı kopmuş say, LED3'ü/arayüz rozetini kırmızıya çevir
   ve yeniden bağlanmayı tetikle (madde 68).

**Belirti:** Uygulama "Bağlı" gösteriyor ama hiçbir tuş çalışmıyor; yeniden
başlatınca düzeliyor; `HB` sayacı bir noktada donmuş.

---

## G. MEKANİK

### 49. Plaka kalınlığı 1.50 mm ZORUNLUDUR — ve PLA'da çatlar

**Risk:** İki ayrı felaket:
(a) Plakayı 2 mm veya 3 mm yaparsan MX anahtarların klipsleri kilitlenmez;
anahtarlar tuşa her basışta yukarı doğru oynar, keycap'ler eğrilir, lehimler
zamanla kopar.
(b) 1.5 mm'yi PLA ile basarsan, 11 anahtar deliğinin arasındaki 5 mm'lik ince
köprüler ilk anahtar takma denemesinde **çatlar**.

**Neden — sayı:**
- MX anahtar gövdesindeki klipsler **1.5 mm** nominal plaka kalınlığına göre
  tasarlanmıştır (pratik aralık ≈ 1.2–1.6 mm). Bunun üstünde klips hiç
  oturmaz, altında ise tutuş gevşek olur.
- Plaka geometrisi: 19.05 mm adım − 14.00 mm delik = **5.05 mm** malzeme.
  Yani plaka, delikler arasında yalnızca **5 mm genişliğinde ve 1.5 mm
  kalınlığında** köprülerden oluşur. PLA sert ama **kırılgandır** (kopma uzaması
  ~%5); anahtarı klipsleyene kadar bu köprüyü bükersin ve kırılır.
- PETG'nin kopma uzaması ~%20'dir; aynı köprü bükülür ama kırılmaz.

**Çözüm:**
- Plaka kalınlığı **1.50 mm** — spec bölüm 2.1'de "ZORUNLU" yazar, oynatma.
- Plakayı **PETG** ile bas (ABS/ASA de olur, PLA **olmaz**).
- %100 dolgu ya da en az 4 üst / 4 alt katman kullan; 1.5 mm'de zaten neredeyse
  hepsi kabuktur.
- Yazıcın PETG basamıyorsa: plakayı **1.5 mm alüminyum, pirinç veya FR4** levhadan
  lazer/CNC kestir. `mechanical/` altındaki DXF üretici tam bunun için vardır.
- Anahtarları takarken plakayı sert ve düz bir zemine yasla, tek tek ve dik bastır.

**Belirti:** Anahtarlar plakada oynuyor / tık sesiyle oturmuyor (kalınlık yanlış);
ya da anahtar takarken "çıt" diye köprü çatlıyor ve delik büyüyor (yanlış malzeme).

---

### 50. 3D baskıda delikler küçük çıkar — +0.15 mm telafi

**Risk:** CAD'de 14.00 mm çizersin, basılan delik 13.75 mm çıkar, anahtar
girmez. Zorlarsan madde 49'daki çatlama olur. Aynı sorun ⌀7.20 enkoder deliğinde
ve heat-set insert deliklerinde de vardır.

**Neden — üç ayrı etki üst üste biner:**
1. **Ekstrüzyon genişliği ve yol hesabı:** Dilimleyici, iç kontur yolunu
   nozül genişliğinin yarısı kadar içeri alır; köşe geçişlerinde fazla malzeme
   birikir. Deliği tipik olarak **0.10–0.20 mm** daraltır.
2. **Malzeme büzülmesi:** PETG soğurken ~%0.3–0.5 çeker. 14 mm'de bu
   **0.04–0.07 mm**'dir.
3. **Fil ayağı (elephant foot):** İlk katman tabla basıncıyla yayılır ve deliğin
   **alt kenarını** 0.1–0.3 mm daraltır. Delik yukarıda doğru, aşağıda dar olur —
   anahtar yarıya kadar girip takılır.

**Çözüm:**
- Model dosyasında delikleri **+0.15 mm** büyüt: MX deliği CAD'de
  **14.15 × 14.15 mm** olarak modellensin, hedef ölçü 14.00 mm'dir.
- Dilimleyicide **"Elephant foot compensation" (fil ayağı telafisi) 0.15–0.20 mm**
  ayarla; bu ayrı bir düzeltmedir, model telafisinin yerine geçmez.
- **Kalibrasyon kuponu bas:** 13.90 / 14.00 / 14.10 / 14.20 mm dört delikli
  40×40 mm'lik bir test parçası bas, gerçek bir MX anahtarla dene, hangisi
  "çıt" diye oturuyorsa telafiyi ona göre kilitle. Bu 10 dakikalık iş, bozuk
  plaka basmaktan ucuzdur.
- Ölçmek için kumpası deliğin **orta yüksekliğinden** kullan, alt kenarından değil.

**Belirti:** Anahtar deliğe girmiyor veya yarıya kadar girip duruyor; deliğin
alt kenarında parlak bir bilezik (fil ayağı) görünüyor.

---

### 51. MX deliği toleransı: 13.8'de girmez, 14.3'te oynar

**Risk:** Toleransı gözden kaçırmak, 11 deliğin 11'ini de yeniden basmak demektir.

**Neden — sayı:** Spec bölüm 2.1: **14.00 × 14.00 mm, tolerans 13.95–14.05 mm**.
Bu 0.10 mm'lik pencere dar görünür ama fiziksel karşılığı nettir:

| Gerçek delik | Sonuç |
|---|---|
| **13.80 mm** | Anahtar gövdesi (14.0 mm nominal) girmez; zorlanırsa köprü çatlar |
| **13.95 mm** | Sıkı ama doğru — hafif bastırınca "çıt" oturur |
| **14.00 mm** | Hedef |
| **14.05 mm** | Üst sınır, klipsler hâlâ tutar |
| **14.30 mm** | Anahtar deliğe oturur ama **klipsler kavramaz**; keycap basınca gövde oynar |

MX anahtar gövdesinin plakaya oturan kısmı 14 mm karedir; klipsler bu karenin
iki kenarında, plakanın **altına** kancalanır. 0.3 mm boşluk, klipsin kanca
derinliğinin (~0.5 mm) yarısından fazlasını yer.

**Çözüm:** Baskıdan sonra rastgele **3 deliği kumpasla ölç** (bir köşe, bir orta,
bir kenar — yazıcı ekseni boyunca fark olabilir). 13.95–14.05 dışındaysa madde
50'deki telafiyi ayarla ve yeniden bas. Deliği eğeyle/maketbıçağıyla büyütmeye
çalışma; kare köşeleri bozulur, geri dönüşü yoktur.
Delik büyük çıktıysa kurtarma: anahtarın kenarına ince bir şerit bant sarmak
geçici bir çözümdür, kalıcı montaj için uygun değildir.

**Belirti:** Tuşa basınca anahtar gövdesi de aşağı iniyor / yana oynuyor;
keycap'ler birbirine göre eğri duruyor.

---

### 51a. 5 pinli (PCB-mount) anahtar düz plakada eğri oturur — 2 plastik ayağı kes

**Risk:** Anahtarları taktın, hepsi "tık" dedi, her şey yolunda görünüyor.
Keycap'leri taktığında **bazıları eğri duruyor** ve düzeltemiyorsun. Ya da
plaka altı yığın beklenenden 3 mm kalın çıkıyor, sünger sığmıyor, kapak
kapanmıyor. Sebep anahtarın **kaç pinli** olduğudur.

**Neden:** MX anahtar iki versiyonda satılır:

| | 3 pinli (**plate-mount**) | 5 pinli (**PCB-mount**) |
|---|---|---|
| ⌀4 mm plastik merkez direği | var | var |
| **Metal kontak pini** | **2** | **2** |
| **Plastik konumlandırma ayağı** | **yok** | **2 adet** (tipik ⌀1.6–1.7 mm, merkezden ~±5.1 mm, boy ~3 mm — *tipik değerler, kendi anahtarını ölç*) |

Bu iki plastik ayak, anahtarın bir **PCB** üzerinde dönmeden durması için
vardır ve PCB'deki karşılık deliklerine girer. **Bu projede PCB yoktur**:
anahtar sadece 1.50 mm'lik düz plakaya klipslenir ve bacaklarına elle tel
lehimlenir. Ayakların gireceği hiçbir delik yoktur, boşlukta sallanırlar ve
üç somut soruna yol açarlar:

1. **Plaka altı yükseklik bütçesi şişer.** MX gövdesinin plaka altında kalan
   kısmı ~6.6 mm, lehim + tel bükümü ile birlikte **~9 mm**'dir (madde 58).
   5 pinlinin ayakları bunun altına **~3 mm daha** ekler → **~12 mm**.
   18.00 mm'lik iç yükseklikte bu, sünger (madde 58a) ve kablo için kalan
   payı yer.
2. **Eğrilik kontrolü fiziksel olarak yapılamaz.** Montaj ADIM 4.3, plakayı
   anahtarlar aşağı bakacak şekilde düz masaya koyup "hepsi masaya değiyor
   mu" diye baktırır. 5 pinlide plaka **plastik ayakların üstünde** durur;
   anahtar gövdeleri masaya hiç değmez ve eğri duran anahtarı **göremezsin**.
3. **Lehimlerken anahtarı eğriltir.** Plakayı yüz üstü tezgâha yaslayıp lehim
   yaptığında anahtar bu iki ayak üzerinde **tahterevalli gibi sallanır**;
   havyanın bastırdığı yönde yamulur, klips tek taraftan boşalır. Eğrilik
   ancak keycap takıldığında görünür ve düzeltmek için anahtarı sökmen gerekir.

**Çözüm:**

- **En doğrusu: 3 pinli (plate-mount) sipariş et.** Satıcı listelemesinde
  "plate mount / 3 pin" yazar; fotoğrafta gövdenin altında **sadece** merkez
  direk + 2 metal pin görünür.
- **Elindeki 5 pinliyse ayakları kes:**
  1. Anahtarı ters çevir. Ortada büyük **⌀4 mm plastik merkez direği**,
     etrafında **2 parlak metal kontak pini**, merkezin sağ/sol yanında
     **2 ince plastik ayak** vardır.
  2. **Yan keskiyle sadece bu 2 plastik ayağı**, gövde yüzeyine dibinden kes.
     Kalan çıkıntıyı maket bıçağıyla düzle.
  3. Anahtarı düz bir cam/masa üstüne bastır: **alt yüz tam düz oturmalı**,
     hiç sallanmamalı. 11 anahtarın 11'ini de böyle kontrol et.

> 🔴 **METAL PİNLERİ SAKIN KESME.** Kesilecek olan **mat/beyaz plastik**
> ayaklardır. **Parlak metal 2 pin anahtarın elektrik kontağıdır** — kesersen
> anahtar geri dönüşsüz olarak çöp olur. Ayırt etme: plastik ayak tırnakla
> bastırılınca hafifçe verir ve keski altında yumuşak kesilir; metal pin
> serttir ve "çıt" diye kopar. Şüphedeysen **kesme**.

> **Merkez direği kesme.** ⌀4 mm plastik merkez direk hem 3 hem 5 pinlide
> vardır, bu tasarımda boşta kalır ve hiçbir zarar vermez. Kesmeye çalışırsan
> gövdenin alt kapağını çatlatırsın.

**Belirti:** Plakayı anahtarlar aşağı bakacak şekilde masaya koyunca plaka
masaya değil, ince plastik çubukların üstünde duruyor ve tıkır tıkır
sallanıyor; keycap'ler montaj sonunda birbirine göre eğri; kapak vidalanınca
ortadan kabarıyor.

---

### 52. EC11 somununun 1.5 mm plakada yeterli diş bulması

**Risk:** Somun sıkılamaz, enkoder plakaya sabitlenmez, çevirdikçe gövde döner ve
telleri koparır.

**Neden — hesap:** Standart EC11'in ön yüzündeki dişli burç:
- Diş: **M7 × 0.75**, burç yüksekliği (plakadan çıkan kısım) tipik **5.0 mm**
  (varyantlarda 7.0 mm de olur — satın alırken kontrol et).
- Somun kalınlığı: **≈ 2.0–2.4 mm**. Pul (varsa): **≈ 0.5 mm**.

Bütçe:

```
Burç yüksekliği           5.00 mm
− Plaka kalınlığı         1.50 mm   (spec 2.1)
= Somun için kalan        3.50 mm
− Pul                     0.50 mm
= Somuna kalan            3.00 mm   >  2.4 mm  ✓ (0.6 mm pay)
```

Yani **1.5 mm plakada rahatça sıkılır**. Tehlike, plakanın üstüne dekoratif bir
kaplama/ikinci kat eklenmesidir:

```
5.00 − 1.50 − 3.00 (dekoratif kat) = 0.50 mm  →  somun DİŞ TUTMAZ  ✗
```

**Çözüm:**
- Plaka üstüne enkoder deliğinin çevresinde **hiçbir ek kalınlık koyma**;
  gerekiyorsa o bölgeyi **havşalayarak inceltilmiş** modelle.
- Somunu **elle sık, sonra pense/anahtarla çeyrek tur** daha; aşırı sıkarsan
  PETG plakada delik çevresi çatlar.
- Deliği spec'e göre **⌀7.20 mm** yap (M7 burç için 0.2 mm boşluk). Madde 50'nin
  telafisiyle CAD'de **⌀7.35 mm** modellenmelidir.
- Somunun altına ince bir **tırtıllı pul** koymak gevşemeyi engeller.

**Belirti:** Somun sonuna kadar dönüyor ama sıkılmıyor; enkoderi çevirince gövde
plakada dönüyor ve bir süre sonra telleri kopuyor.

---

### 53. Enkoderin dönme engelleyici pim delikleri unutulursa gövde döner

**Risk:** Madde 52'deki somunu mükemmel sıksan bile, kullanıcı knob'u sürekli
aynı yöne çevirdikçe somun gevşer ve enkoder gövdesi plakada döner. Bir süre
sonra telleri kopar.

**Neden:** EC11 gövdesinin ön yüzünde, dişli burcun yanında **iki küçük
konumlandırma pimi** vardır (tipik ⌀2.0 mm civarı, gövdenin merkezine göre
simetrik). Bunlar tam da bu dönme momentini karşılamak için vardır. Plakada
karşılık delikleri yoksa pimler plakaya dayanır, enkoder **plakaya tam
oturmaz** (1–1.5 mm boşlukta kalır) ve tüm yükü sadece somun taşır.

**Çözüm — üç seçenekten biri:**
1. **En doğrusu:** Plakaya iki pim deliği aç. Elindeki enkoderin pim çapını ve
   merkez mesafesini **kumpasla ölç** (üretici arasında ufak farklar vardır),
   modele **+0.2 mm** boşlukla işle. `mechanical/` model dosyasında bu iki delik
   parametrik olarak bulunur; ölçüne göre değeri güncelle.
2. **Pratik:** Pimleri **yan keskiyle kes ve eğele**. Enkoder plakaya tam oturur;
   dönme engellemesini somun + tırtıllı pul üstlenir. Kabul edilebilir ama
   birinci seçenek kadar sağlam değildir.
3. **Kaba ama etkili:** Enkoderin gövdesini plakanın altından iki damla sıcak
   silikonla sabitle. Sökülebilirliği azaltır.

**Belirti:** Enkoder plakaya tam oturmuyor, knob ile plaka arası boşluk fazla;
birkaç haftalık kullanımdan sonra enkoder gövdesi elle döndürülebiliyor.

---

### 54. Heat-set insert sıcaklığı ve dik bastırma

**Risk:** İnsert eğri girer (vida yan girer, kapak oturmaz), ya da çok derine
kaçıp plastiği eritir ve deliğin çevresi kabarır; ya da yüzeyde kalıp vidayı
tutmaz.

**Neden:** Isıl geçirmeli insert (M3 × 5) plastiği eritip tırtıklı dış yüzeyiyle
kilitlenir. İşin tamamı **sıcaklık + diklik + derinlik** üçlüsüne bağlıdır:
- Çok soğuk havya → plastik akmaz, insert zorla girer ve etrafını çatlatır.
- Çok sıcak → plastik aşırı akar, insert kendi ağırlığıyla dibe kaçar, çevresi
  kabarır.
- Eğri bastırma → vida ekseni kayar; 4 köşe vidasının 4'ü de aynı düzlemde
  olmadığından kapak eğri kapanır.

**Çözüm — sayılarla:**

| Malzeme | Havya ucu sıcaklığı | Süre |
|---|---|---|
| PLA | 200–220 °C | 5–8 s |
| **PETG** (önerilen) | **240–260 °C** | 8–12 s |
| ABS/ASA | 230–250 °C | 8–12 s |

- Delik çapı = insert **dış çapı − 0.1 mm**. Yaygın M3×5 insert dış çapı
  **4.0 mm** → delik **⌀4.0 mm** (PETG'de ⌀4.1). Kendi insertini kumpasla ölç.
- **Delik derinliği insert boyundan 1 mm fazla** olsun (5 mm insert → 6 mm delik),
  aksi hâlde havada erimiş plastik sıkışır ve insert dışarı taşar.
- Havyayı **dikey** tut; parçayı düz bir zemine yasla, gözünle iki eksenden
  (önden ve yandan) diklik kontrol et. Mümkünse insert ucu (heat-set tip) kullan.
- Insert **yüzeyle aynı hizaya gelene kadar** bastır, **0.2 mm içeri** kaçırmak
  idealdir; taşmasın.
- **Soğumadan havyayı çekme** — çekersen insert havyaya yapışıp geri çıkar.
  2–3 saniye bekle, sonra dik olarak ayır.

**Belirti:** Vida sıkılırken insert dönüyor / plastikten sıyrılıyor (fazla sıcak,
gevşek delik); vida eğri giriyor ve kapak bir köşesinden açık kalıyor.

---

### 55. USB açıklığı DevKit konumuna göre olmalı — 1–2 mm kayma kabloyu engeller

**Risk:** Kasa kapanır, her şey mükemmel görünür, ama USB-C kablosunun **plastik
mahfazası** kasanın kenarına dayanır ve fiş sokete tam girmez. Cihaz bağlantıyı
sürekli kaybeder.

**Neden:** USB-C fişinin metal ucu 8.34 × 2.56 mm'dir; ama **kablonun plastik
gövdesi** tipik olarak **10–14 mm genişliğinde ve 6–8 mm yüksekliğindedir** ve
soketin 2–4 mm önünden başlar. Kasa deliğini sadece metal uca göre açarsan
plastik gövde dışarıda kalır ve fişi 2 mm eksik sokar → temas kararsız olur.
Ayrıca DevKitC-1'in USB-C soketleri kartın kenarından yaklaşık 1 mm **dışarı
taşar**; kart kasa içinde 1 mm kaysa açıklık hizadan çıkar.

**Çözüm:**
- Açıklığı **cömert** yap: en az **13 × 8 mm**, kenarları 1 mm pahlı (chamfer).
  Görsel olarak biraz büyük durur ama her kabloyu kabul eder.
- **Kartı kasaya sabitle** — kart oynarsa hizalama anlamsızdır. DevKitC-1 için
  kasanın tabanında iki adet konumlandırma kulakçığı veya çift taraflı bant
  yatağı bulunmalıdır.
- **Hangi soket?** Madde 2 gereği açıklık **"USB" (OTG) yazan sokete** göre
  konumlanır. İki soketi de açıkta bırakmak (14 × 8 mm'lik geniş bir yarık)
  firmware güncellemesini kolaylaştırır ve önerilir.
- **Kâğıt şablonla doğrula:** Kasayı basmadan önce açıklık konumunu 1:1
  yazdırıp karta tut. 2 dakikalık kontrol, 4 saatlik baskıyı kurtarır.

**Belirti:** Kablo takılıyor ama "klik" sesi gelmiyor; hafif dokununca bağlantı
kopuyor; kablo değiştirince (daha ince gövdeli) düzeliyor.

---

### 56. Keycap yüksekliği ve enkoder knob'unun çarpışması

**Risk:** K3 tuşuna (enkoderin hemen solundaki) basarken parmağın knob'a
sürtüyor; ya da profilli keycap'ler knob'un dönüşünü fiziksel olarak engelliyor.

**Neden — sayı:** Tuş adımı 19.05 mm; keycap tabanı 18 mm olduğundan komşu
elemanlar arası boşluk yalnızca **~1 mm**'dir.
- Yaygın **EC11 knob** çapları: 15, 17, 20 ve **25 mm**. 25 mm'lik bir knob'un
  merkezi 19.05 mm ötedeki keycap'in merkezine göre 12.5 mm yarıçapla uzanır;
  keycap'in yarı genişliği 9 mm → toplam 21.5 mm > 19.05 mm → **çakışır**.
- Yükseklik: SA/Cherry profil keycap'lerin üst yüzeyi plakadan **10–12 mm**
  yukarıdadır; XDA/DSA ~9 mm. Knob ise şaftın plakadan çıkan 15 mm'lik kısmına
  oturur ve üst yüzeyi **12–17 mm**'ye çıkabilir. Yandan bakınca knob keycap'ten
  yüksekte kalır; bu **istenen** görünümdür ama parmağın çarpmaması için yatay
  boşluk gerekir.

**Çözüm:**
- Knob çapı **maksimum 20 mm**; 25 mm'lik "hi-fi" knob'lardan kaçın. 17 mm ideal.
- Enkoder şaftını gerekiyorsa **kısalt** (D-tipi şaft, testereyle kesilebilir),
  knob'un üst yüzeyi keycap'lerden en fazla 4–5 mm yukarıda kalsın.
- Keycap profilini **düşük tut** (XDA, DSA, Cherry). Yüksek SA profilinden kaçın.
- **Kuru montaj yap:** Kasayı kapatmadan önce keycap'leri ve knob'u tak, K3 ve
  K6'ya parmakla bas, knob'u çevir. Sürtüyorsa knob'u küçült.
- Spec'in yerleşiminde enkoder **sütun 4, satır 1**'dedir; komşuları K3 (sol) ve
  K10 (alt). İkisini de test et.

**Belirti:** Knob'u çevirirken parmağın keycap'e çarpıyor; K3'e basarken knob
hafifçe dönüyor.

---

### 57. Ayak/kaymaz ped yoksa cihaz masada kayar ve tek elle kullanılamaz

**Risk:** Kullanıcı tuşa basar, cihaz masada kayar. Combo yapmak için iki elle
tutmak gerekir — makro klavyenin **tüm anlamı** kaybolur (asıl klavye için bir
el, makro için diğeri).

**Neden — sayı:** Cihazın toplam kütlesi yaklaşık **90–130 g**'dır (PETG kasa
~70 g + DevKit 8 g + 11 anahtar ~50 g + keycap'ler). Statik sürtünme katsayısı
PETG–ahşap için ≈ 0.3 → kaymaya karşı direnç ≈ 0.11 kg × 0.3 ≈ **0.33 N**.
Bu projedeki **MX Blue**'da tetikleme kuvveti **0.50 N (50 g)**, tık/taktil
tepe kuvveti ve dibe vurma ise **~0.60 N (60 g)** civarındadır.
Yani **basma kuvveti, kaymaya karşı direncin neredeyse iki katıdır** — cihaz
kaçınılmaz olarak kayar.
Silikon ayakla sürtünme katsayısı ≈ 0.8–1.0'a çıkar → direnç ≈ 0.9–1.1 N →
basma kuvvetinin üzerinde, cihaz sabit kalır.

**Çözüm:**
- Tabanın dört köşesine **⌀8 mm silikon/kauçuk ayak** yapıştır. Bu projede
  taban modelinde bunlar için `foot_d = 8.00` mm çapında,
  `foot_depth = 1.00` mm derinliğinde çukurlar hazırdır (yapıştırıcı
  kaymasın, ayaklar aynı düzlemde otursun). **⌀10 mm ayak bu çukura girmez.**
- Ayak yüksekliği 2–3 mm olsun; bu aynı zamanda kablonun taban altından kıvrılıp
  gitmesine izin verir.
- Ağırlık eklemek isteyen için: taban içine **bir veya iki adet M3 pul yatağı**
  ya da 30–50 g'lık bir çelik levha bölmesi koy. Toplam kütle 200 g'a çıkarsa
  ayaklarla birlikte cihaz "kaya gibi" olur.
- Öne doğru **4–6°'lik bir eğim** ergonomiyi belirgin şekilde iyileştirir; arka
  ayakları 2 mm daha yüksek yaparak bedelsiz elde edilir.

**Belirti:** Tuşa basınca cihaz 1–2 cm kayıyor; combo yapmak için cihazı elle
tutmak gerekiyor.

---

### 58. İç yükseklik 18.00 mm bütçesi — kablo ve lehimler sığmalı

**Risk:** Kapak kapanmıyor; zorlarsan lehim noktaları karta bastırır, teller
kısa devre yapar veya kopar.

**Neden — bütçe (spec 2.1: plaka altı → taban içi **18.00 mm**):**

| Bileşen | Yükseklik |
|---|---|
| MX anahtar gövdesinin plaka altında kalan kısmı | **~6.6 mm** |
| Anahtar pinlerine yapılan lehim + tel bükümü | ~3.0 mm |
| ESP32-S3-DevKitC-1 kart kalınlığı + pin başlıkları (dişi header ile) | ~14–16 mm |
| WS2812B modülü + telleri | ~4 mm |
| 1000 µF kondansatör (⌀10 × 20 mm, **yatık** yerleştirilir) | ~10 mm |

Toplam basit toplamla 18 mm'yi aşar — çünkü bileşenler **üst üste değil yan
yana** yerleşmelidir. Kritik nokta: DevKit dik durursa sığmaz; **yatay**
yatırılmalı ve anahtarların altında kalan boşluğa değil, plakanın enkoder/K10/K11
sütunu altındaki daha derin bölgeye yerleştirilmelidir.

**Çözüm:**
- DevKit'i **pin başlığı olmadan** kullan (kartı doğrudan lehimle) ya da düşük
  profilli başlık seç; bu tek başına 8 mm kazandırır.
- 1000 µF kondansatörü **yatık** monte et ve taban köşesine sabitle.
- Telleri **26–28 AWG silikon** seç: ince, esnek, ısıya dayanıklı. Sert PVC tel
  kapak kapanırken yay gibi iterek plakayı kaldırır.
- Anahtar lehimlerini **kısa kes** (1 mm), sivri uçlar kalmasın.
- Kapatmadan önce **kuru montaj**: kapağı vidalamadan bastır, 18 mm'lik boşluğun
  gerçekten yettiğini gör.

**Belirti:** Kapak vidalanınca ortadan kabarıyor; vidayı sıkınca plakadaki
anahtarlar yukarı itiliyor; bir süre sonra rastgele tuşlar kendiliğinden
tetikleniyor (tel bastırıyor).

---

### 58a. Boş 18 mm kovuk rezonans odasıdır — MX Blue "çınlamalı" duyulur

**Risk:** Cihaz çalışıyor, her şey doğru, ama tuş sesi **ucuz** duyuluyor:
her basışta boşluklu, çınlamalı, "plastik kutuya vuruyormuş gibi" bir yankı
(İngilizce literatürde *hollow* / *pingy*). Aynı anahtarın hazır bir klavyedeki
sesiyle karşılaştırınca fark rahatsız edici olur. **Anahtar suçlu değildir,
kasa suçludur.**

**Neden — sayı:** Plakanın hemen altında
**82.20 × 63.15 × 18.00 mm ≈ 93 cm³** boş hava vardır. Bu hacmin duvarları
sert (PETG/akrilik/alüminyum), yüzeyleri **birbirine paralel** ve içi
neredeyse tamamen **boştur** — DevKit tabanın bir köşesinde durur, geri
kalanı hava. Sert ve paralel yüzeyli boş bir hacim, tanım gereği bir
**rezonans odası**dır: anahtarın tık sesi ve yayın metalik "ping"i bu odada
yansıyıp güçlenir, plaka da 1.50 mm ince olduğu için diyafram gibi çalışıp
sesi dışarı verir.

MX Blue bunu özellikle belirgin yapar: click jacket'in ürettiği ses
darbesinin enerjisi lineer/taktil bir anahtardan **belirgin şekilde
yüksektir**, dolayısıyla odayı çok daha güçlü uyarır.

**Çözüm — kovuğu doldur (ayrıntılı ölçüler: `02-MEKANIK-TASARIM.md` § 10.4):**

1. **3 mm poron / EVA sünger**, kasa tabanının **iç** yüzeyine yapıştırılır
   (plakaya değil). Bulamazsan **kesilmiş kaymaz mutfak dolabı altlığı** iş
   görür.
2. Kovuk, DevKit yatağı (X 22.20–85.20, Y 30.00–55.50) yüzünden **üç şeride**
   bölünür. Kesim: **ön 80 × 25 mm**, **arka 80 × 9 mm**, **sol 18 × 24 mm**.
   Ön ve arka parçaların köşelerinden **8 × 8 mm** kare çentik kes — oralarda
   ⌀7.60 vida kuleleri var.
3. **DevKit'in ve tel demetinin altını boş bırak.** Kart 4.00 mm'lik pedlerin
   üstünde durur; altına sünger girerse kart yükselir ve USB-C soketi kasadaki
   açıklıkla hizasını kaybeder (madde 55).
4. **Yükseklik:** anahtar + lehim plaka altında ~9 mm yer kaplar, tabana
   ~9 mm serbest yükseklik kalır. 3 mm sünger → **6 mm hava** kalır. ✔
   **Üst sınır 6 mm**'dir; sünger anahtar gövdesine veya lehim uçlarına
   **DEĞMEMELİDİR** (değerse plaka yukarı itilir, kapak ortadan kabarır ve
   sünger zamanla izolasyonu aşındırır).
5. **Silikon ayak zorunludur** (madde 57 zaten kaymak için istiyor): ⌀8 × 2–3 mm
   silikon ayak, gövdenin titreşimini masaya iletmeyi keser. Çıplak taban veya
   sert plastik ayak, masayı rezonans tablasına çevirir.
6. Yetmezse: ön ve arka **iç duvarlara 2 mm kendinden yapışkanlı keçe** şerit.

> **Beklenti yönetimi:** Bunların hiçbiri MX Blue'yu **sessiz** yapmaz. Tık
> sesi anahtarın **içinden** gelir ve kasadan bağımsızdır. Sünger sesin
> **çınlamalı/boşluklu** bileşenini alır; geriye temiz ve tok bir "tık" kalır.
> Sessizlik istiyorsan çözüm sünger değil, farklı bir anahtardır.

**Belirti:** Her tuş basışında, özellikle dibe vurunca, kasanın içinden gelen
bir yankı/çınlama duyuluyor. Kasayı elinle masaya bastırarak tuşa basınca ses
belirgin şekilde azalıyorsa teşhis kesindir: sorun kovuk ve masa
bağlantısıdır, anahtar değil.

---

### 59. Baskı yönü, katman yönü ve plakanın delaminasyonu

**Risk:** Plaka baskıdan sağlam çıkar ama anahtar takarken **katmanlar arasından**
ayrılır (delaminasyon). Ya da kasa duvarı, USB kablosu takılırken katman
çizgisinden çatlar.

**Neden:** FDM baskıda parça **katmanlar arası (Z) yönde** en zayıftır — bu yönde
mukavemet, katman içi (XY) mukavemetin **%40–60'ı** kadardır.
- Plaka **yatay** (XY düzleminde, 1.5 mm kalınlık Z ekseninde) basılırsa:
  anahtar klipsinin uyguladığı kuvvet katman **düzlemine paralel** olur → güçlü.
- Plaka **dikey** basılırsa: aynı kuvvet katmanları **birbirinden ayırmaya**
  çalışır → 5 mm'lik köprüler katman çizgisinden ayrılır.
- Aynı mantık kasa için: USB açıklığının çevresi, kablo takarken zorlanan
  bölgedir; duvarlar dikey basıldığında bu bölge katman yönünde yüklenir.

**Çözüm:**
- **Plaka: mutlaka yatay bas** (geniş yüzey tablada). Destek gerekmez, delikler
  köprüsüz çıkar.
- **Kasa gövdesi: ağzı yukarı bakacak şekilde bas** (taban tablada). USB
  açıklığı yan duvarda kalır ve köprüleme gerektirir; açıklığın üst kenarını
  **damla/altıgen biçimli** modelleyerek destek ihtiyacını kaldır.
- Duvar sayısı (perimeter) **en az 3**, plaka için **4**. Dolgu %25–40 yeterli;
  mukavemeti duvar sayısı belirler, dolgu değil.
- Katman yüksekliği **0.20 mm**; 0.28 mm delik hassasiyetini bozar,
  0.12 mm gereksiz uzatır.
- Nozül **0.4 mm**. 0.6 mm nozülle 5 mm'lik köprüde yalnızca birkaç yol sığar ve
  parça zayıflar.

**Belirti:** Plakayı bükünce katman çizgisinden ayrılıyor; anahtar takarken
"çıt" yerine "kıtır" sesi; kırılma yüzeyi pürüzsüz ve parlak (delaminasyon
belirtisi), lifli değil.

---

## H. KULLANIM VE TASARIM KARARLARI

### 60. Enkoder `hid` / `host` modu — çifte ses değişimi tuzağı

**Risk:** Enkoderi bir tık çevirirsin, ses **iki kademe** değişir. Ya da mute'a
basarsın, susar ve hemen açılır. Donanımda hiçbir sorun yoktur; aynı komut iki
kez uygulanmaktadır.

**Neden:** Ses iki yoldan değiştirilebilir ve **ikisi aynı anda açık olabilir**:
1. **Cihaz yolu:** `CMD ENC MODE HID` iken cihaz doğrudan HID Consumer Control
   raporu gönderir (spec 5.2/5.3). İşletim sistemi sesi değiştirir.
2. **PC yolu:** Cihaz ayrıca `EV ENC CW` satırını da CDC'den gönderir. Uygulama
   bu olayı görüp config'deki `encoder.cw` eylemini çalıştırırsa
   (varsayılan: `{"type":"media","value":"volume_up"}` — spec bölüm 7)
   **ses ikinci kez** değişir.

Varsayılan config'de `encoder.mode` = `"hid"` **ve** `cw/ccw/press` medya
eylemleriyle doludur. Bu bir çelişki değildir: o değerler kullanıcı `host`
moduna geçtiğinde ne olacağını gösterir. Ama uygulama modu dikkate almazsa
çift tetikleme kesindir.

**Çözüm — tek cümlelik kural:**

> `encoder.mode == "hid"` ise uygulama `EV ENC CW/CCW/PRESS` olaylarını
> **yalnızca gösterir**, `ActionRunner.run()` **çağırmaz**.
> `encoder.mode == "host"` ise cihaz HID göndermeyi bırakır, eylemi **yalnızca**
> uygulama çalıştırır.

```python
def _on_enc(self, ev: DeviceEvent) -> None:
    self._enkoder_animasyonu(ev.slot)          # her zaman görsel geri bildirim
    enc = self.cfg.profile(self.os_key)["encoder"]
    if enc.get("mode", "hid") == "hid":
        return                                  # cihaz zaten hallediyor — ÇİFTLEME YOK
    self.runner.run(ev.slot)                    # yalnız "host" modunda çalıştır
```

Uygulama bağlandığında modu cihaza **açıkça bildirmeli**
(`CMD ENC MODE HID` veya `CMD ENC MODE HOST`) ki cihazın NVS'teki eski değeri
ile config birbirinden ayrışmasın. `long` slotu bu kuralın istisnasıdır:
cihaz uzun basış için HID göndermez, dolayısıyla `long` her iki modda da
uygulama tarafından çalıştırılır.

**Belirti:** Bir tıkta ses iki kademe değişiyor; enkodere basınca ses susup
hemen geri geliyor; `CMD ENC MODE HOST` gönderince düzeliyor.

---

### 61. Neden F13–F24 seçildi

**Risk:** Yedek mod için F1–F12 ya da harf tuşları seçilseydi, cihaz her
uygulamada mevcut kısayollarla çakışırdı: F5 tarayıcıyı yeniler, F2 dosya adını
değiştirir, Ctrl+S kaydeder.

**Neden:** USB HID Usage Table'da **F13–F24** için ayrılmış kullanım kodları
vardır (0x68–0x73), ama **hiçbir modern klavyede bu tuşlar fiziksel olarak
bulunmaz**. Sonuç:
- Hiçbir uygulama varsayılan olarak onlara kısayol atamamıştır → **çakışma yok**.
- Yine de standart HID kodlarıdır → sürücü gerekmez, her işletim sistemi tanır.
- Kullanıcı isterse başka programlarda (OBS, Photoshop, Premiere, AutoHotkey)
  bu tuşlara doğrudan kısayol atayabilir — bu, HID yedek modunun asıl gücüdür.

**Çözüm / eşleme (spec 5.3):** K1..K9 → **F13…F21**, K11 → **F22**.
F23 ve F24 bilinçli olarak **boş bırakılmıştır**; ileride eklenecek işlevler
(örneğin enkoder uzun basış) için ayrılmıştır.

**Belirti:** (Yanlış seçilseydi) Cihaz takılıyken tarayıcı sürekli yenileniyor,
metin editöründe rastgele menüler açılıyor olurdu.

---

### 62. macOS'ta F tuşlarının "fn" davranışı

**Risk:** Kullanıcı *"macOS'ta F tuşları çalışmıyor, fn'e basmam gerekiyor"*
diye şikâyet eder ve bunun cihazın hatası olduğunu sanır.

**Neden:** macOS'ta **F1–F12** tuşlarının varsayılan davranışı sistem işlevidir
(parlaklık, Mission Control, ses). Gerçek F1–F12 göndermek için `fn` basılı
tutmak gerekir; bu davranış **Sistem Ayarları → Klavye → Klavye Kısayolları →
İşlev Tuşları** altından ters çevrilebilir.

**Ama bu bizi ilgilendirmez:** Bizim gönderdiğimiz **F13–F22** tuşlarının
macOS'ta alternatif bir sistem işlevi **yoktur**, dolayısıyla `fn` davranışına
tabi değildirler. Doğrudan uygulamaya iletilirler.
İki gerçek incelik var:
- macOS'ta F-tuşu davranış ayarı **klavye başına** tutulur; bizim cihaz için
  ayrı bir satır olarak görünebilir. Değiştirmeye gerek yoktur.
- Apple'ın tam boyutlu klavyelerinde F13/F14/F15 fiziksel olarak vardır ve
  sırasıyla Print Screen / Scroll Lock / Pause karşılığı olarak da yorumlanabilir.
  Nadiren bir uygulama F13'e ekran görüntüsü işlevi bağlayabilir. Çakışma
  yaşarsan K1'i F13 yerine boş bırakıp uygulamanın CDC yolunu kullan.

**Çözüm:** Kullanıcı belgesinde açıkça yaz: *"Cihaz F13–F22 gönderir; macOS'ta
`fn` tuşuna basmanız gerekmez."* HID yedek modunun zaten geçici bir çözüm
olduğunu, asıl kullanımın uygulama açıkken olduğunu hatırlat.

**Belirti:** Kullanıcı `fn` ile denemeler yapıyor; F13'e bastığında ekran
görüntüsü alınıyor (nadir, uygulamaya özel çakışma).

---

### 63. Neden BLE değil USB

**Risk:** "Kablosuz olsa daha şık olurdu" baskısıyla BLE'ye geçmek, projenin en
güçlü özelliklerini (anında tepki, sıfır kurulum, iki yönlü protokol) feda eder.

**Neden — karşılaştırma:**

| Kriter | USB (seçilen) | BLE |
|---|---|---|
| Gecikme | < 2 ms, sabit | 7.5–30 ms, değişken |
| Eşleştirme | Yok — tak çalışır | Her bilgisayarda ayrı eşleştirme |
| Güç | USB'den, pil yok | Pil + şarj devresi + kapasite yönetimi |
| İki yönlü veri | CDC ile serbest, satır tabanlı | GATT karakteristikleri, ek karmaşa |
| BIOS/kilit ekranı | Çalışır | Genelde çalışmaz |
| Güvenlik | Fiziksel bağlantı | Havadan dinleme/eşleştirme saldırıları |
| macOS uyku sonrası | Anında | Yeniden bağlanma gecikmesi (bazen elle) |

Bu cihaz **masaüstünde sabit duran** bir yardımcı araçtır; zaten bilgisayarın
yanındadır. Kablo bir kısıt değil, aynı zamanda **güç kaynağı ve veri yolu**dur.
BLE ile CDC benzeri iki yönlü metin protokolü kurmak (spec bölüm 5) mümkündür
ama gereksiz karmaşıklık üretir.

**Çözüm:** USB'de kal. Kablosuzluk gerçekten gerekirse doğru yol, cihazı
ESP-NOW/BLE ile bir **USB dongle**'a bağlamaktır; ana bilgisayar yine USB HID
görür ve protokol değişmez.

**Belirti:** (BLE'ye geçilseydi) Bilgisayar uykudan uyanınca ilk 3–5 tuş basışı
kaybolur, combo zamanlaması bozulurdu.

---

### 64. Neden mantık PC'de, cihazda değil

**Risk:** "Eylemleri cihaza gömelim, uygulama gerekmesin" fikri cazip gelir.
Sonuç: her ayar değişikliği için firmware derleme + yükleme; cihazın flash'ına
sığmayan uygulama yolları; iki işletim sistemi için ayrı firmware.

**Neden:** Spec bölüm 1'in temel kararı: *"Mantık cihazda değil PC'dedir."*
Gerekçeler:
- **Güncelleme kolaylığı:** Kullanıcı bir combo'yu değiştirmek için firmware
  yüklemek zorunda kalmaz; `config.json`'daki bir alan değişir, o kadar.
- **Sınırsız eylem:** Cihaz yalnızca HID tuş kodu gönderebilir. PC ise uygulama
  açabilir, URL açabilir, kabuk komutu çalıştırabilir, klasör açabilir, makro
  akıtabilir — spec 7.2'deki **10 eylem tipi**'nin çoğu cihazda **imkânsızdır**.
- **Uzun metin ve Türkçe:** `text` eylemi 200 karakterlik bir imza yazabilir;
  cihazın NVS'inde 36 combo × 200 karakter tutmak hem yer hem de yazma ömrü
  sorunudur (madde 27).
- **İki OS, tek firmware:** Windows'ta `C:\...\notepad.exe`, macOS'ta
  `/Applications/Safari.app`. Aynı slot, farklı değer. Bunu cihazda tutmak iki
  profili birden flash'ta saklamayı gerektirirdi.
- **Hata ayıklama:** Python'da bir `print` eklemek 2 saniye; firmware'de derleme
  + yükleme + yeniden bağlanma 60 saniye.

**Çözüm:** Cihaz "**ne oldu**"yu söyler (`EV KEY 3 UP`), PC "**ne yapılacak**"a
karar verir. Cihazın bildiği tek eylem, uygulama yokken devreye giren HID yedek
modudur (madde 65) — o da kasıtlı olarak minimumdur.

**Belirti:** (Ters yapılsaydı) Kullanıcı bir kısayolu değiştirmek için PlatformIO
kurmak zorunda kalırdı.

---

### 65. HID yedek modu ne kadarını kurtarır

**Risk:** Kullanıcı, uygulama kapalıyken cihazın **her şeyi** yapmasını bekler ve
hayal kırıklığına uğrar; ya da geliştirici yedek modu "gereksiz" görüp kaldırır
ve cihaz uygulama olmadan tuğlaya döner.

**Neden:** Yedek mod, PC uygulaması bağlı **değilken** (CDC DTR düşük) devreye
girer ve kasıtlı olarak sınırlıdır. Kapsam tablosu:

| İşlev | Uygulama AÇIK | Uygulama KAPALI (HID yedek) |
|---|---|---|
| K1..K9 | 9 özel eylem (10 tipten) | `F13`…`F21` — **başka programlar** yakalayabilir |
| K10 combo | **36 combo** | ✗ Devre dışı (LED3 kırmızı yanıp söner) |
| K11 OS | Profil değiştirir, uygulamaya bildirir | `F22` gönderir + cihaz içi OS modu değişir |
| Enkoder çevir | `cw`/`ccw` eylemi ya da HID ses | ✓ **HID ses açma/kısma** |
| Enkoder bas | `press` eylemi ya da HID mute | ✓ **HID sessize alma** |
| Enkoder uzun bas | `long` eylemi | ✗ |
| LED anlamları | Tam | LED3 kırmızı, diğerleri son hâlinde |

Yani kurtarılan kısım: **ses kontrolü tam**, **9 tuş dolaylı olarak** (OBS,
AutoHotkey, Karabiner gibi bir program F13–F21'i yakalarsa), **combo hiç**.
Combo'nun devre dışı olması bir eksiklik değil bilinçli karardır: üç tuşluk bir
kombinasyonu tek bir F-tuşuna indirgemenin anlamlı bir yolu yoktur ve 36 combo'yu
36 ayrı HID koduna eşlemek için yeterli boş tuş kodu yoktur.

**Çözüm:** Kullanıcıya bunu **açıkça anlat** ve uygulamanın otomatik
başlatılmasını öner (spec 7: `"autostart"`). LED3'ün kırmızı olması "bir şey
bozuk" değil, "**uygulama kapalı, kısıtlı moddasın**" demektir; arayüzde ve
kullanım kılavuzunda bu tek cümleyi yaz.

**Belirti:** Kullanıcı *"combo çalışmıyor"* diyor; LED3'e bakınca kırmızı — sorun
combo'da değil, uygulamanın kapalı olmasında.

---

### 66. Windows ve macOS profillerinin neden ayrı tutulduğu

**Risk:** Tek profil kullanılsa, kullanıcı macOS'ta `/Applications/Safari.app`
atar, Windows'a geçince aynı slot geçersiz bir yolu göstermeye devam eder ve
eylem sessizce başarısız olur. Kullanıcı her OS değişiminde 9 tuş + 36 combo'yu
**yeniden** ayarlamak zorunda kalır.

**Neden:** Slot değerlerinin **çoğu platforma bağımlıdır**:

| Eylem tipi | Windows | macOS |
|---|---|---|
| `app` | `C:\Program Files\...\chrome.exe` | `/Applications/Google Chrome.app` |
| `file` / `folder` | `C:\Users\ali\Downloads` | `/Users/ali/Downloads` |
| `shortcut` | `ctrl+c` | `command+c` |
| `command` | `cmd /c ...` / PowerShell | `sh -c ...` / `osascript` |
| `media` | `pyautogui` tuş kodları | `osascript` (madde 38) |

Yalnızca `url` ve `text` platformdan bağımsızdır. Yani slotların büyük kısmı
zaten iki değer taşımak zorundadır — spec bölüm 7 bunu şema düzeyinde çözer:
`profiles.<ad>.windows` ve `profiles.<ad>.mac` **ayrı ve tam** yapılardır.

**Çözüm:**
- Aktif OS anahtarı `ActionRunner.current_os_key()` ile belirlenir ve `K11` /
  `EV OS WIN|MAC` olayıyla değişir.
- Arayüz **hangi profilde olduğunu** her zaman görünür biçimde göstersin (LED1
  rengiyle uyumlu bir rozet: Windows mavi `#1E90FF`, macOS beyaz `#FFFFFF`).
- Kullanıcıya **"Windows profilini Mac'e kopyala"** düğmesi sun: platformdan
  bağımsız tipler (`url`, `text`, `none`, `media`) doğrudan kopyalanır,
  platforma bağlı olanlar (`app`, `file`, `folder`, `command`) kopyalanır ama
  arayüzde **"yol doğrulanmalı"** işaretiyle vurgulanır.
- `shortcut` kopyalanırken spec 7.2'deki normalizasyon uygulanır (madde 67).

**Belirti:** OS değiştirince eylemlerin yarısı sessizce çalışmıyor; günlükte
"dosya bulunamadı" hataları.

---

### 67. Kısayol normalizasyonu — macOS'ta `ctrl` olduğu gibi kalır

**Risk:** Geliştirici "her iki yönde çevirelim" diye düşünür ve macOS profilinde
`ctrl` → `command` dönüşümü yapar. Sonuç: kullanıcının bilinçli olarak yazdığı
`ctrl+←` (macOS'ta Mission Control masaüstü geçişi) `command+←` olur ve tamamen
başka bir şey yapar.

**Neden:** Windows ve macOS'ta değiştirici tuşların **sayısı ve rolü farklıdır**:
- Windows'ta birincil değiştirici **Ctrl**'dür; `Command` tuşu **yoktur**.
  Bu yüzden Windows profilinde `command`/`cmd` yazılmışsa **`ctrl`'e çevirmek
  zorunludur**, aksi hâlde `pyautogui` bilinmeyen tuş hatası verir.
- macOS'ta ise **Control ve Command ayrı ve ikisi de mevcut** tuşlardır.
  `ctrl+tab` (sekme değiştirme), `ctrl+←/→` (masaüstü geçişi), `ctrl+space`
  (girdi kaynağı) gerçek ve yaygın kısayollardır. Bunları `command`'a çevirmek
  **veri kaybıdır**.

Spec bölüm 7.2 bunu net yazar: *"Windows profilinde `command`/`cmd` → `ctrl`,
macOS profilinde `ctrl` olduğu gibi kalır."*

**Çözüm:**

```python
def kisayolu_normalize_et(value: str, os_key: str) -> list[str]:
    parcalar = [p.strip().lower() for p in value.split("+") if p.strip()]
    if os_key == "windows":
        parcalar = [("ctrl" if p in ("command", "cmd") else p) for p in parcalar]
    # macOS: HİÇBİR dönüşüm yapma — ctrl de command de geçerli ve farklıdır.
    return parcalar
```

Arayüz, aktif profile göre **ipucu metnini** değiştirmelidir (spec 7.2:
*"Uygulama arayüzü aktif profile göre ipucu gösterir"*):
- Windows profilinde: `Örn: ctrl+c`
- macOS profilinde: `Örn: command+c`

Ayrıca macOS'ta `option` (`alt`) ve `command` isimlerini de kabul et;
`pyautogui` bunları tanır.

**Belirti:** macOS'ta `ctrl+tab` yazılan kısayol sekme değiştirmek yerine başka
bir şey yapıyor; Windows'ta `command+c` yazılan kısayol `KeyError` veriyor.

---

### 68. Bağlantı tespiti: yalnız DTR yetmez, `HB` ile teyit et

**Risk:** LED3 yeşil (bağlı) gösterirken uygulama aslında ölmüştür; ya da tersi:
uygulama çalışıyorken cihaz HID yedek moduna düşer ve tuşlar F13–F21 göndermeye
başlar — kullanıcının metin kutusuna `F13` düşer.

**Neden:** Spec 5.3 bağlantıyı **CDC DTR** sinyaline bağlar. DTR pratik ama tek
başına yetersizdir:
- Bazı terminal programları ve kütüphaneler portu açarken **DTR'yi hiç
  yükseltmez** → cihaz uygulama açıkken bile "kapalı" sanır.
- Uygulama çöktüğünde işletim sistemi portu kapatır ve DTR düşer — bu iyi.
  Ama uygulama **donduğunda** (madde 34) port açık kalır, DTR yüksek kalır ve
  cihaz "bağlı" sanmaya devam eder.
- Karşı yönde: PC uygulaması da cihazın canlı olduğunu bilmek zorundadır.

**Çözüm — iki yönlü canlılık:**
- **Cihaz tarafı:** `DTR yüksek` **VE** son 3 saniye içinde PC'den en az bir
  satır (`CMD ...`) gelmiş olması → "bağlı". Uygulama zaten bağlandığında
  `CMD ID` gönderir; ayrıca 1–2 saniyede bir `CMD PING` göndermesi önerilir
  (cihaz `ACK PING` ile yanıtlar). Bu şart sağlanmıyorsa **HID yedek moduna geç**
  ve LED3'ü kırmızıya çevir.
- **PC tarafı:** Cihaz zaten 1000 ms'de bir `HB <uptime_ms>` gönderir (spec 5.1).
  Son `HB` üzerinden **3 saniyeden** fazla geçtiyse bağlantıyı kopmuş say, portu
  kapat ve yeniden bağlanma döngüsüne gir (madde 44, 48).
- `HB` içindeki `uptime_ms` **azaldıysa** cihaz resetlenmiştir: OS modunu,
  LED renklerini ve enkoder modunu **yeniden gönder**.

**Belirti:** Uygulama donmuşken cihaz hâlâ yeşil LED gösteriyor ve hiçbir tuş
çalışmıyor; ya da uygulama açıkken metin kutusuna F13 karakterleri düşüyor.

---

### 69. Uygulama açıkken firmware yüklenemez

**Risk:** Firmware yüklerken `Failed to connect` / `Serial port busy` hatası
alırsın; birkaç deneme sonrası kabloyu çıkarıp takarsın, yükleme yarıda kalır ve
cihaz bootloader'da asılı kalır.

**Neden:** Madde 42'nin doğrudan sonucu: `esptool`/PlatformIO da aynı seri porta
münhasır erişim ister. Uygulamanın `DeviceLink`'i portu tutuyorsa yükleme
başlayamaz. Daha sinsi hâli: uygulama **yeniden bağlanma döngüsünde** olduğu için
port bir açılır bir kapanır; `esptool` tam kapalı olduğu anı yakalayıp başlar,
sonra uygulama portu geri kapar ve yükleme **ortasında** kesilir.

**Çözüm — akış:**
1. Uygulamayı **tamamen kapat** (tepsi simgesinden Çıkış; pencereyi kapatmak
   yetmez, `minimize_to_tray` açıksa arka planda çalışmaya devam eder).
2. Açık tüm seri monitörleri kapat.
3. Firmware'i yükle.
4. Cihaz yeniden başladıktan **sonra** uygulamayı aç.

Uygulamaya bir de **"Cihaz bağlantısını geçici kes"** düğmesi eklemek çok
kullanışlıdır: `DeviceLink.stop()` çağırır, port serbest kalır, kullanıcı
uygulamayı kapatmadan firmware yükleyebilir.
Yükleme yarıda kalıp cihaz asılı kalırsa kurtarma: **BOOT** düğmesini basılı
tutarken **RESET**'e bas, bırak, sonra BOOT'u bırak → indirme modu; yeniden yükle.

**Belirti:** `A fatal error occurred: Failed to connect to ESP32-S3`;
`Could not open port ... Access is denied`.

---

### 70. Tuş numaralandırması firmware, arayüz ve etiketlerde aynı olmalı

**Risk:** Firmware'de K1 sol üsttür, arayüzde K1 sol alta çizilmiştir, kasadaki
etikette ise 1 sağ üsttedir. Kullanıcı bir eylem atar, başka tuş çalışır. Bu hata
**hiçbir zaman** hata mesajı vermez, sadece kafa karıştırır.

**Neden:** Spec bölüm 2 tek bir okuma yönü tanımlar:
*"Tuş numaralandırması sol-üstten sağa doğru okunur (K1 sol üst, K9 sağ alt).
Uygulama arayüzü de tuşları bu düzende gösterir."*

Yani:

```
K1  K2  K3   | ENC
K4  K5  K6   | K10 (COMBO)
K7  K8  K9   | K11 (OS)
```

Üç ayrı yerde bu eşlemenin bozulma ihtimali vardır:
1. **Firmware:** GPIO → K numarası dizisi. Spec 3.1 sırası:
   K1=GPIO4, K2=5, K3=6, K4=7, K5=15, K6=16, K7=17, K8=18, K9=8, K10=9, K11=10.
   GPIO numaraları **artan sırada değildir** (K5'te 7'den 15'e atlar, K9'da 8'e
   döner) — bu yüzden "sırayla lehimlersem tutar" varsayımı **yanlıştır**.
2. **Kablolama:** Kasada teller birbirine benzer; yanlış GPIO'ya lehimlemek çok
   kolaydır.
3. **Arayüz:** `ui/key_grid.py` 4×3 ızgarayı çizerken satır/sütun sırasını ters
   kurabilir.

**Çözüm:**
- Lehimleme sırasında **her teli etiketle** (kâğıt bant + kalem) ve spec 3.1
  tablosunu yanına aç.
- Montaj bitince **doğrulama turu** yap: uygulamanın ham günlük penceresini aç,
  K1'den K11'e sırayla bas, gelen satırların `EV KEY 1 UP` … `EV KEY 9 UP`,
  `EV MODE COMBO_ON`, `EV OS ...` sırasına uyduğunu gör. Uymayan varsa
  **firmware'deki diziyi değil, teli** düzelt (yazılımdan düzeltirsen şema ile
  gerçeklik ayrışır ve bir sonraki kişi aynı tuzağa düşer).
- Kasaya kalıcı etiket basacaksan bunu doğrulama turundan **sonra** yap.
- `ui/key_grid.py` ve `ui/combo_matrix.py` aynı numaralandırmayı kullanmalıdır;
  combo matrisinde satır `a`, sütun `b` ve **yalnızca `a < b`** hücreleri
  doludur (üst üçgen, 36 hücre — madde 24).

**Belirti:** K2'ye basınca K4'ün eylemi çalışıyor; combo matrisinde seçtiğin
hücre ile tetiklenen combo farklı.

---

### 70a. MX Blue'nun 0.5 mm histerezisi — tuşu yeterince bırakmazsan ikinci basış yok

**Risk:** Aynı tuşa çok hızlı iki kez basarsın, eylem **bir kez** çalışır.
Debounce'u suçlarsın, 8 ms'i 5 ms'e indirirsin, bu sefer çift tetikleme
başlar (madde 22a) ve iki ateş arasında kalırsın. Oysa sorun ne yazılımda ne
lehimdedir — **anahtarın mekaniğindedir.**

**Neden — sayı:** MX Blue'da tetikleme ve sıfırlama noktaları **aynı yerde
değildir**:

```
   Tuş üstü (0.0 mm)
        │
        │   ▼ basarken:  2.2 mm'de TETİKLENİR  (pretravel)
        │   ▲ bırakırken: 1.7 mm'de SIFIRLANIR  (reset)
        │
        │        histerezis = 2.2 − 1.7 = 0.5 mm
        │
   Dip  (4.0 mm toplam hareket)
```

Anahtar bir kez tetiklendikten sonra, **tekrar tetiklenebilmesi için 1.7 mm
kotunun üstüne çıkması** gerekir. Parmağını 2.0 mm civarında "titretirsen"
anahtar hiç sıfırlanmaz ve ikinci basış **elektriksel olarak hiç
gerçekleşmez** — firmware'in görebileceği bir olay yoktur.

Bu bir arıza değil, **tasarım özelliğidir**: histerezis, tetikleme noktasında
parmağın doğal titremesinin sürekli açma-kapama yapmasını engeller.
Lineer/taktil anahtarlarda da vardır, clicky'de biraz belirgindir.

**Çözüm:** Bir makro klavyede bu pratikte sorun değildir — aynı tuşa saniyede
8 kez basılmaz ve normal basışta parmak zaten dibe kadar iner, bırakırken de
tuş yukarı fırlar. Yine de:

- **Tuşu tam bırak.** Parmağını tuşun üstünde yarım kotta tutma alışkanlığın
  varsa, ikinci basış kaybolur. Bu, debounce ile **düzeltilemez**.
- **Debounce'u düşürerek çözmeye çalışma.** `EK_KEY_DEBOUNCE_MS`'i 8'in altına
  indirmek burada hiçbir şeye yaramaz (olay zaten üretilmiyor), sadece
  madde 22a'daki çift tetiklemeyi geri getirir.
- **Ayırt etme testi:** seri konsolu aç, tuşa hızlı iki kez bas.
  `EV KEY <n> DOWN` **bir kez** geliyorsa histerezistir (anahtar sıfırlanmadı);
  `UP` **iki kez** geliyorsa sıçramadır (madde 22a).
- Gerçekten hızlı tekrar gerekiyorsa (örn. bir tuşu "spam" edeceksen) o slota
  tek basışta çalışan bir `macro` ata; parmakla tekrarlamaya çalışma.

**Belirti:** Çok hızlı çift basışta eylem bir kez çalışıyor; yavaş basınca her
seferinde çalışıyor. Konsolda ikinci basış için hiç `DOWN` satırı yok
(eksik olay), fazladan satır değil.

---

## EK: SPEC DIŞI VARSAYIMLAR

Aşağıdakiler `00-CEKIRDEK-SPEC.md`'de **yer almayan**, bu dokümanda en makul
seçim olarak alınan kararlardır. Spec güncellenirse bunlar da güncellenmelidir.

1. **Enkoder varyant sabiti `ENC_STEPS_PER_DETENT`** (madde 13) ve
   **`ENC_REVERSED`** (madde 14) firmware sabitleri spec'te tanımlı değildir.
   Protokolü değiştirmedikleri, yalnızca donanım varyantını telafi ettikleri
   için eklenmeleri güvenlidir.
2. **HID descriptor `bCountryCode = 33`** önerisi (madde 29) spec bölüm 4'te
   yoktur; USB kimliği alanlarını (VID/PID/string) değiştirmez.
3. **`CMD PING`'in periyodik gönderilmesi** (madde 68) spec 5.2'de komut olarak
   tanımlıdır ama gönderim sıklığı belirtilmemiştir; 1–2 saniye önerilmiştir.
   `HB` zaman aşımı eşiği (3 s) da spec'te yoktur.
4. **`encoder.mode == "hid"` iken uygulamanın enkoder eylemini çalıştırmaması**
   (madde 60) spec'te açıkça yazmaz; spec 5.3'ün *"Enkoder HID modu her zaman
   aktiftir"* ifadesi ile spec 7'deki varsayılan medya eylemlerinin birlikte
   çifte tetikleme üreteceği gözlemine dayanan bir yorumdur.
5. **Gecikmeli NVS yazma penceresi (5 s)** ve **aynı slot için 150 ms tekrar
   koruması** (madde 27, 47) spec'te yoktur; ölçüye dayalı makul değerlerdir.
6. **`config.json.bak` yedeği ve `config.json.hatali-<zaman>` karantinası**
   (madde 41) spec 8'in "atomik yazma" şartının üstüne eklenmiş bir güvenlik
   katmanıdır.
7. **Config yolunun kullanıcı dizinine düşmesi** (madde 46), yalnızca uygulama
   dizini yazılabilir değilse devreye giren bir yedek stratejidir; spec bölüm 9
   config'i proje kökünde gösterir ve **birincil yol odur**.
8. **Mekanik ayrıntılar:** silikon ayak çapı/yuvası, 4–6° eğim, knob çapı üst
   sınırı (20 mm), baskı parametreleri (0.4 mm nozül, 0.20 mm katman, 3–4 duvar),
   heat-set sıcaklıkları ve delik çapları spec 2.1'de yoktur; standart pratiğe ve
   madde içindeki hesaplara dayanır. Spec'in verdiği ölçüler (1.50 mm plaka,
   14.00 mm delik, ⌀7.20 enkoder, 19.05 adım, M3×12 vida) **değiştirilmemiştir**.
9. **EC11 burç yüksekliği 5.0 mm ve somun kalınlığı ~2.2 mm** (madde 52) tipik
   değerlerdir; farklı üreticide değişebilir, kumpasla doğrulanmalıdır.
10. **F23/F24'ün ileriye ayrılmış olması** (madde 61) bir yorumdur; spec 5.3
    yalnızca F13–F22'yi tanımlar ve kalanları boş bırakır.
11. **Anahtar tipi = Cherry MX Blue (`MX1A-E1NN`, clicky, 3 pinli, 50 g)** ve
    buna bağlı olarak **tuş debounce'unun 5 ms yerine 8 ms** olması
    (madde 22a). Spec 6.1 yalnızca "5 ms" der ve anahtar tipi belirtmez;
    8 ms, clicky bir anahtarın bırakış tarafındaki ek sıçramasını kapatmak
    için seçilmiştir ve `firmware/src/config.h` içindeki
    **`EK_KEY_DEBOUNCE_MS`** ile tek noktadan geri alınabilir. Enkoder butonu
    (`EK_ENC_SW_DEBOUNCE_MS`) spec değerinde, **5 ms**'de bırakılmıştır.
    Kasa içi sünger (madde 58a) da spec'te yoktur; hiçbir ölçüyü değiştirmez,
    yalnızca boş kovuğun rezonansını keser. **MX Blue boyutsal olarak diğer MX
    anahtarlarıyla aynıdır; plaka/kasa/DXF ölçüleri değişmemiştir.**

---

## EK: 5 DAKİKALIK KONTROL LİSTESİ

İlk çalıştırmadan önce sırayla işaretle. Her satırın yanındaki numara ilgili
maddedir.

**Lehimden önce**
- [ ] Anahtarlar **3 pinli**; 5 pinli aldıysan 2 plastik ayak kesildi (metal pinler sağlam) — **51a**
- [ ] Kullanılan GPIO'lar yalnızca 4–18 aralığında (4,5,6,7,8,9,10,11,12,13,14,15,16,17,18) — 3, 4, 5
- [ ] LED besleme hattında 1N4148 var, bandı LED tarafına bakıyor — 7
- [ ] 1000 µF kondansatör LED tarafında, polaritesi doğru — 8
- [ ] Veri hattında 330 Ω, MCU pinine yakın — 9
- [ ] Enkoder A/B kanallarında 10 kΩ + 100 nF RC filtresi — 12
- [ ] LED zinciri DIN→DOUT sırasında, LED1 = OS, LED2 = Combo, LED3 = Bağlantı — 10

**Güç vermeden önce**
- [ ] 5 V ↔ GND kısa devre yok — 17
- [ ] 3V3 ↔ GND kısa devre yok — 17
- [ ] 11 tuşun her biri basılıyken kendi GPIO'sunu GND'ye çekiyor — 17, 70
- [ ] LED GND'si ayrı telle doğrudan ESP32 GND'sine gidiyor — 16
- [ ] Kablo **veri** kablosu — 19

**Firmware'i yüklemeden önce**
- [ ] `platformio.ini` içinde `-D ARDUINO_USB_MODE=0` var — **1**
- [ ] `-D ARDUINO_USB_CDC_ON_BOOT=1` var — 1
- [ ] `loop()` içinde hiç `delay()` yok — 20
- [ ] Tüm zaman karşılaştırmaları `millis() - t >= X` biçiminde — 21
- [ ] Combo `a < b` normalize ediliyor — 24
- [ ] Combo modunda `EV KEY` ve HID bastırılıyor, `consumed` bayrakları var — 23, 26
- [ ] `config.h`: `EK_KEY_DEBOUNCE_MS = 8` (MX Blue clicky), `EK_ENC_SW_DEBOUNCE_MS = 5` — **22a**

**Uygulamayı çalıştırmadan önce**
- [ ] `on_event` içinde hiçbir widget çağrısı yok — **34**
- [ ] macOS: Erişilebilirlik + Girdi İzleme izinleri verildi, uygulama yeniden başlatıldı — 35, 36
- [ ] `pyautogui.FAILSAFE = False`, `pyautogui.PAUSE = 0.0` — 40
- [ ] `save()` atomik (`.tmp` + `fsync` + `os.replace`) — 41
- [ ] Port bulma VID/PID öncelikli, macOS'ta `tty.*` eleniyor — 43, 44
- [ ] Tekil örnek kilidi (127.0.0.1:64210) alınıyor — 45
- [ ] Config yolu `cwd`'ye değil, mutlak yola dayanıyor — 46
- [ ] Arduino IDE / PlatformIO seri monitörü kapalı — 42

**Kasayı kapatmadan önce**
- [ ] Plaka 1.50 mm ve PETG (veya metal) — 49
- [ ] Delikler kumpasla ölçüldü, 13.95–14.05 mm — 50, 51
- [ ] Enkoder somunu sıkı, pim delikleri açık ya da pimler kesildi — 52, 53
- [ ] USB açıklığı **"USB" (OTG)** soketine hizalı, en az 13 × 8 mm — 2, 55
- [ ] Keycap'ler + knob takılı hâlde çakışma yok — 56
- [ ] Silikon ayaklar yapıştırıldı — 57
- [ ] 3 mm sünger taban içine yapıştırıldı; DevKit/kablo altı boş, sünger anahtara değmiyor — **58a**
- [ ] Tek basışta tek eylem tetikleniyor (konsolda tek `EV KEY … UP`) — **22a**
- [ ] Kuru montajda kapak zorlanmadan kapanıyor — 58

---

**Son söz:** Bu listedeki maddelerin çoğu bir kez öğrenilir, sonra bir daha
unutulmaz. Ama ilk seferinde her biri saatler yiyebilir. Bir şey çalışmıyorsa,
tahmin yürütmeden önce **belirti** satırlarını tara — büyük ihtimalle
yaşadığın şey burada zaten yazılı.
