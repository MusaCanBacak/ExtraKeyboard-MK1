# ExtraKeyboard MK1 — Kablolama Tablosu

> **Bu doküman `docs/00-CEKIRDEK-SPEC.md` bölüm 3.1'e tabidir.**
> Pin numaraları değiştirilemez. Header konumları için
> `docs/01-DONANIM-PIN-SEMASI.md` bölüm 3'e bakın.
> Devre şemaları için `hardware/sematik.md`, malzeme için `hardware/BOM.csv`.

---

## 0. Özet

| Büyüklük | Değer |
|---|---|
| **Toplam tel sayısı** | **42** |
| Anahtar sinyal telleri | 11 |
| Ortak GND papatya dizisi | 11 |
| Enkoder + RC filtre telleri | 9 |
| WS2812B zinciri telleri | 11 |
| Ayrıca lehimlenecek eleman | 2 × 10 kΩ, 2 × 100 nF, 1 × 330 Ω, 1 × 1N4148, 1 × 1000 µF |
| Tahmini net tel uzunluğu | ≈ 1.90 m (bkz. bölüm 5 dökümü) |
| Fire dahil alınacak tel | **7 renk × 2 m = 14 m** (BOM'daki tek kalem bunu karşılar) |
| Tahmini lehimleme süresi | 60 – 90 dk (ilk yapımda 2 saat) |

**Tel sayısı nasıl çıktı:**

```
11 anahtar x 1 sinyal teli (bir bacak -> GPIO)          = 11
11 anahtarlik GND papatya dizisi:
     10 anahtar-arasi baglanti + 1 karta donus teli     = 11
Enkoder: A, B, C, SW1, SW2 + RC dugum ve besleme telleri =  9
WS2812B: veri, guc, GND ve zincir ici baglantilar        = 11
                                                         ----
                                            TOPLAM       = 42
```

---

## 1. Adlandırma ve Kısaltmalar

| Kısaltma | Anlamı |
|---|---|
| `J1-n` | DevKitC-1'in **sol** header'ında üstten `n`. pin |
| `J3-n` | DevKitC-1'in **sağ** header'ında üstten `n`. pin |
| `Kx.1` | `Kx` anahtarının **1. kontak bacağı** (GPIO'ya giden) |
| `Kx.2` | `Kx` anahtarının **2. kontak bacağı** (GND'ye giden) |
| `RC.3V3` | RC filtre kartındaki 3.3 V rayı |
| `RC.GND` | RC filtre kartındaki GND rayı |
| `RC.NA` | RC filtre kartındaki A kanalı düğümü (R1 + C1 + EC11 A + GPIO11 birleşimi) |
| `RC.NB` | RC filtre kartındaki B kanalı düğümü (R2 + C2 + EC11 B + GPIO12 birleşimi) |
| `LED1.DIN` | LED1'in veri **girişi** |
| `LED1.DOUT` | LED1'in veri **çıkışı** |
| `LEDn.VDD` | LEDn'in +4.30 V besleme pini (1N4148 sonrası ray) |
| `LEDn.GND` | LEDn'in toprak pini |

**Anahtar:** 11 tuşun tamamı **Cherry MX Blue `MX1A-E1NN`** — clicky (tıklı),
**3 pinli plate-mount**, 50 g tetikleme. Kablolama açısından MX Brown'dan hiçbir
farkı yoktur: aynı gövde, aynı 14.00 mm plaka deliği, aynı iki kontak bacağı.

> **3 pinli alın.** 5 pinli (PCB-mount) versiyonda gövde altında **2 adet
> ekstra plastik konumlandırma ayağı** vardır; bu projede PCB olmadığı ve düz
> 1.50 mm plakada bu ayaklar için delik bulunmadığı için anahtar plakaya tam
> oturmaz, eğri durur. Zorunda kalırsanız **yalnızca bu 2 plastik ayağı** yan
> keskiyle kesin — **metal kontak pinlerini KESMEYİN**, tel onlara lehimlenecek.

**MX anahtarların iki kontak bacağı polaritesizdir.** Hangi bacağın `.1`,
hangisinin `.2` olduğunu siz seçersiniz — ama **tüm anahtarlarda aynı tarafı
seçin**, aksi halde papatya dizisi karışır. Öneri: kart yönünden bakıldığında
**sol bacak `.1` (sinyal), sağ bacak `.2` (GND)**.

**Kartın yönü:** iki USB-C konnektör aşağıda, anten yukarıda, serigrafi
yazıları okunur şekilde. J1 solda, J3 sağda. Pin 1 her iki header'da da
en üstteki pindir.

---

## 2. Ortak GND Papatya Dizisi (Daisy Chain) — Neden ve Nasıl

11 anahtarın **hepsinin** bir bacağı GND'ye gitmek zorundadır. Bunu yapmanın
iki yolu vardır:

| Yöntem | Tel sayısı | Sonuç |
|---|---|---|
| **Yıldız:** her anahtardan ayrı ayrı karta tel | 11 | Kartın tek GND pinine 11 tel lehimlenir → fiziksel olarak imkânsız |
| **Papatya dizisi:** anahtardan anahtara zincir | 11 | Karta tek tel döner, her anahtar bacağına en fazla 2 tel gelir → temiz |

**Papatya dizisi (daisy chain)**, GND'yi anahtardan anahtara "aktararak"
tek bir kesintisiz iletken hat oluşturur. Elektriksel olarak hepsi aynı
düğümdür; fark yalnızca montaj kolaylığındadır.

**Yol seçimi kritiktir:** zincir, tuşların **fiziksel komşuluğunu** takip
etmelidir; yoksa teller birbirinin üstünden geçer. 4 sütun × 3 satır
yerleşimde (çekirdek spesifikasyon bölüm 2) yılan (serpentine) yolu izlenir:

```
   SUTUN 1     SUTUN 2     SUTUN 3     SUTUN 4
 +-----------+-----------+-----------+-----------+
 |    K1  ---+--> K2  ---+--> K3     |   [ENC]   |  SATIR 1
 |           |           |     |     |           |
 +-----------+-----------+-----|-----+-----------+
 |    K4 <---+--- K5 <---+--- K6     |    K10    |  SATIR 2
 |     |     |           |           |     ^     |
 +-----|-----+-----------+-----------+-----|-----+
 |    K7  ---+--> K8  ---+--> K9 ----+--> K11    |  SATIR 3
 +-----------+-----------+-----------+-----------+
                                            |
                            K10.2 --------> J1-22 (GND)
```

Zincir sırası:

```
K1.2 -> K2.2 -> K3.2 -> K6.2 -> K5.2 -> K4.2 -> K7.2 -> K8.2 -> K9.2
     -> K11.2 -> K10.2 -> J1-22 (GND)
```

11 anahtar için **10 adet anahtar-arası tel** + **1 adet karta dönüş teli**
= toplam **11 tel**.

**Lehimleme tekniği:** telin ucundaki izolasyonu 4 mm soyun, anahtar
bacağının deliğinden geçirip bükün, sonra lehimleyin. İki tel aynı bacağa
geliyorsa (zincirin ortasındaki anahtarlar) **ikisini birlikte** bükün ve
tek seferde lehimleyin — üst üste iki kat lehim soğuk lehime yol açar.

**Alternatif teknik (daha temiz):** izolasyonu **soymadan**, telin ortasında
4 mm'lik bir pencere açın (tel soyucunun ucuyla izolasyonu kesip kaydırın),
kesintisiz tek bir teli tüm anahtarlara bu pencerelerden lehimleyin. Böylece
9 lehim noktası tek bir telle geçilir. Bu, ticari klavyelerde kullanılan
yöntemdir ancak daha fazla el becerisi ister.

**Üç ayrı GND dönüşü:** kartta 4 GND pini vardır. Bu projede üçü kullanılır
ve **birbirine karıştırılmaz**:

| GND pini | Ne bağlanır | Neden ayrı |
|---|---|---|
| **J1-22** | 11 anahtarın papatya dizisi | Sinyal toprağı, akım ≈ 0.8 mA |
| **J3-1** | RC filtre kartı + enkoder ortak ucu | Filtre referansı temiz kalmalı |
| **J3-22** | WS2812B zinciri | 45–180 mA anahtarlamalı akım; sinyal toprağından ayrılır |

Bu **yıldız topraklama**dır: yüksek akımlı LED dönüş yolu, hassas enkoder
filtresinin toprak referansına gürültü bindiremez.

---

## 3. TEL TABLOSU

Format: `Kaynak Pin -> Hedef`. Her satır **bir tel**dir.
Sırayla lehimleyin; kutucukları işaretleyin.

### BÖLÜM A — Anahtar sinyal telleri (11 tel)

| ☐ | Tel | Kaynak Pin | → | Hedef | Sinyal | Renk | Uzunluk | Not |
|---|---|---|---|---|---|---|---|---|
| ☐ | **W01** | `J1-4` (GPIO4) | → | `K1.1` | K1 | sarı | 70 mm | Sol üst tuş |
| ☐ | **W02** | `J1-5` (GPIO5) | → | `K2.1` | K2 | sarı | 60 mm | |
| ☐ | **W03** | `J1-6` (GPIO6) | → | `K3.1` | K3 | sarı | 55 mm | |
| ☐ | **W04** | `J1-7` (GPIO7) | → | `K4.1` | K4 | yeşil | 70 mm | |
| ☐ | **W05** | `J1-8` (GPIO15) | → | `K5.1` | K5 | yeşil | 60 mm | GPIO15, GPIO8 DEĞİL |
| ☐ | **W06** | `J1-9` (GPIO16) | → | `K6.1` | K6 | yeşil | 55 mm | |
| ☐ | **W07** | `J1-10` (GPIO17) | → | `K7.1` | K7 | mavi | 75 mm | |
| ☐ | **W08** | `J1-11` (GPIO18) | → | `K8.1` | K8 | mavi | 65 mm | |
| ☐ | **W09** | `J1-12` (GPIO8) | → | `K9.1` | K9 | mavi | 60 mm | GPIO8, GPIO18 DEĞİL |
| ☐ | **W10** | `J1-15` (GPIO9) | → | `K10.1` | K10 COMBO | turuncu | 55 mm | J1-13 ve J1-14 **ATLANIR** |
| ☐ | **W11** | `J1-16` (GPIO10) | → | `K11.1` | K11 OS | turuncu | 60 mm | |

> **En sık yapılan hata:** `GPIO8` ile `GPIO18` ve `GPIO15` ile `GPIO5`
> karıştırılır. Kart üzerindeki serigrafi küçüktür. W05, W08, W09
> lehimlendikten sonra multimetre ile mutlaka doğrulayın.

> **J1-13 (GPIO3) ve J1-14 (GPIO46) boş kalır** — bunlar strapping
> pinleridir, kullanılmaz. Bu iki pini atladığınızı görsel olarak
> teyit edin, yoksa aşağıdaki tüm pinler bir kayar.

### BÖLÜM B — Ortak GND papatya dizisi (11 tel)

| ☐ | Tel | Kaynak Pin | → | Hedef | Renk | Uzunluk | Not |
|---|---|---|---|---|---|---|---|
| ☐ | **W12** | `K1.2` | → | `K2.2` | siyah | 25 mm | Zincirin başı |
| ☐ | **W13** | `K2.2` | → | `K3.2` | siyah | 25 mm | |
| ☐ | **W14** | `K3.2` | → | `K6.2` | siyah | 25 mm | Satır 1 → satır 2 geçişi |
| ☐ | **W15** | `K6.2` | → | `K5.2` | siyah | 25 mm | Satır 2 ters yönde |
| ☐ | **W16** | `K5.2` | → | `K4.2` | siyah | 25 mm | |
| ☐ | **W17** | `K4.2` | → | `K7.2` | siyah | 25 mm | Satır 2 → satır 3 geçişi |
| ☐ | **W18** | `K7.2` | → | `K8.2` | siyah | 25 mm | |
| ☐ | **W19** | `K8.2` | → | `K9.2` | siyah | 25 mm | |
| ☐ | **W20** | `K9.2` | → | `K11.2` | siyah | 25 mm | Sütun 3 → sütun 4 geçişi |
| ☐ | **W21** | `K11.2` | → | `K10.2` | siyah | 25 mm | Zincirin sonu |
| ☐ | **W22** | `K10.2` | → | `J1-22` (GND) | siyah | 60 mm | **Karta tek dönüş** |

**Kontrol:** bu bölüm bitince multimetreyi süreklilik moduna alın.
`J1-22` ile **her** anahtarın `.2` bacağı arasında `< 5 Ω` okunmalıdır.
Bir anahtarda açık devre çıkarsa zincirin o halkası kopuktur.

### BÖLÜM C — Enkoder ve RC debounce filtresi (9 tel + 4 eleman)

Önce RC filtre kartını hazırlayın, sonra bağlayın.

**Pertinaks kart üzerine lehimlenecek elemanlar (tel değil):**

| ☐ | Eleman | Değer | Bacak 1 | Bacak 2 |
|---|---|---|---|---|
| ☐ | **R1** | 10 kΩ | `RC.3V3` | `RC.NA` |
| ☐ | **C1** | 100 nF | `RC.NA` | `RC.GND` |
| ☐ | **R2** | 10 kΩ | `RC.3V3` | `RC.NB` |
| ☐ | **C2** | 100 nF | `RC.NB` | `RC.GND` |

> R1/R2 ve C1/C2 polaritesizdir, ters takılamaz.
> `τ = 10 kΩ × 100 nF = 1 ms`.

**Teller:**

| ☐ | Tel | Kaynak Pin | → | Hedef | Renk | Uzunluk | Not |
|---|---|---|---|---|---|---|---|
| ☐ | **W23** | `J1-1` (3V3) | → | `RC.3V3` | kırmızı ince | 70 mm | Filtre pull-up beslemesi. **5V DEĞİL** |
| ☐ | **W24** | `RC.NA` | → | `J1-17` (GPIO11) | beyaz | 70 mm | ENC_A okuma hattı |
| ☐ | **W25** | `RC.NA` | → | `EC11 A pini` | beyaz | 45 mm | Enkoder A kanalı |
| ☐ | **W26** | `RC.NB` | → | `J1-18` (GPIO12) | beyaz | 70 mm | ENC_B okuma hattı |
| ☐ | **W27** | `RC.NB` | → | `EC11 B pini` | beyaz | 45 mm | Enkoder B kanalı |
| ☐ | **W28** | `EC11 C pini` (ortak) | → | `RC.GND` | siyah | 45 mm | Enkoderin orta pini |
| ☐ | **W29** | `EC11 SW1 pini` | → | `J1-19` (GPIO13) | beyaz | 70 mm | Buton — RC filtresi YOK |
| ☐ | **W30** | `EC11 SW2 pini` | → | `RC.GND` | siyah | 45 mm | Buton diğer ucu |
| ☐ | **W31** | `RC.GND` | → | `J3-1` (GND) | siyah | 80 mm | Filtre toprak dönüşü |

**EC11 pin yerleşimi:** enkoderi mili size bakacak, 3 pinli tarafı aşağıda
olacak şekilde tutun.

```
        EC11 ALTTAN GORUNUS
     (mil size bakiyor, 3 pinli taraf altta)

        SW1  o           o  SW2      <-- 2 pinli taraf: entegre buton
             |           |
        +----+-----------+----+
        |                     |
        |      [ EC11 ]       |
        |                     |
        +--+-------+-------+--+
           |       |       |
           o       o       o
           A       C       B         <-- 3 pinli taraf: quadrature cikis
                (ortak)
```

| EC11 pini | Bağlantı | Tel |
|---|---|---|
| **A** | `RC.NA` (→ GPIO11 üzerinden okunur) | W25 |
| **C** (ortak, ortadaki) | `RC.GND` | W28 |
| **B** | `RC.NB` (→ GPIO12 üzerinden okunur) | W27 |
| **SW1** | `J1-19` (GPIO13) | W29 |
| **SW2** | `RC.GND` | W30 |

> **A ve B ters lehimlenirse** enkoder çalışır ama yönler ters olur:
> sağa çevirince `EV ENC CCW` gelir. Düzeltmek için W25 ile W27'yi
> yer değiştirin (firmware'e dokunmayın — pin tablosu değiştirilemez).
> **A ile C karıştırılırsa** enkoder hiç event üretmez veya rastgele davranır.

### BÖLÜM D — WS2812B LED zinciri (11 tel + 2 eleman)

LED'ler üst bezeldeki `⌀3.00 mm` pencerelerin arkasına, **8.00 mm aralıkla**,
soldan sağa LED1 → LED2 → LED3 sırasıyla yerleşir. Veri de bu yönde akar.

**Lehimlenecek elemanlar (tel değil):**

| ☐ | Eleman | Değer | Bacak 1 | Bacak 2 | Polarite |
|---|---|---|---|---|---|
| ☐ | **R3** | 330 Ω | W32 ucu | W33 ucu | Yok |
| ☐ | **D1** | 1N4148 | anot ← W34 | katot (**siyah bant**) → W35 | **VAR** |
| ☐ | **C3** | 1000 µF / 10 V | (+) → `LED1.VDD` | (−) (**beyaz şerit**) → `LED1.GND` | **VAR** |

**Teller:**

| ☐ | Tel | Kaynak Pin | → | Hedef | Renk | Uzunluk | Not |
|---|---|---|---|---|---|---|---|
| ☐ | **W32** | `J1-20` (GPIO14) | → | `R3` bacak 1 | yeşil | 20 mm | **Direnç GPIO'ya yakın olmalı** |
| ☐ | **W33** | `R3` bacak 2 | → | `LED1.DIN` | yeşil | 80 mm | Veri girişi |
| ☐ | **W34** | `J1-21` (5V) | → | `D1` anot | kırmızı kalın | 25 mm | Diyot girişi |
| ☐ | **W35** | `D1` katot (bantlı uç) | → | `LED1.VDD` | kırmızı kalın | 80 mm | 4.30 V LED rayı |
| ☐ | **W36** | `LED1.GND` | → | `J3-22` (GND) | siyah kalın | 90 mm | **Ayrı LED güç dönüşü** |
| ☐ | **W37** | `LED1.DOUT` | → | `LED2.DIN` | yeşil | 12 mm | Zincir 1→2 veri |
| ☐ | **W38** | `LED1.VDD` | → | `LED2.VDD` | kırmızı | 12 mm | Zincir 1→2 güç |
| ☐ | **W39** | `LED1.GND` | → | `LED2.GND` | siyah | 12 mm | Zincir 1→2 toprak |
| ☐ | **W40** | `LED2.DOUT` | → | `LED3.DIN` | yeşil | 12 mm | Zincir 2→3 veri |
| ☐ | **W41** | `LED2.VDD` | → | `LED3.VDD` | kırmızı | 12 mm | Zincir 2→3 güç |
| ☐ | **W42** | `LED2.GND` | → | `LED3.GND` | siyah | 12 mm | Zincir 2→3 toprak |

`LED3.DOUT` **boş kalır** — bağlanmaz.

> **Veri yönü tek yönlüdür.** `DOUT` daima bir sonraki LED'in `DIN`'ine
> gider. Ters bağlanırsa hiçbir LED yanmaz. WS2812B gövdesinde giriş/çıkış
> yönü bir ok veya köşe pahı ile işaretlidir.

> **1N4148 yönü:** gövdedeki **siyah bant katottur** ve **LED tarafına**
> bakar. Ters takılırsa LED'ler hiç yanmaz (zarar görmez, düzeltilebilir).

> **1000 µF polaritesi:** **beyaz şeritli / kısa bacaklı** uç eksidir (GND).
> Ters takılırsa enerji verildiğinde **patlar**. İki kez kontrol edin.

---

## 4. Önerilen Lehimleme Sırası

Sıra rastgele değildir: en zor erişilen noktalar önce, en kırılgan
elemanlar sonra lehimlenir.

| Adım | İş | Süre | Kontrol noktası |
|---|---|---|---|
| **1** | Heat-set insert'leri gövdeye göm (havya 220 °C, 4 köşe) | 10 dk | Insert'ler yüzeyle aynı hizada, eğik değil |
| **2** | 11 Cherry MX Blue anahtarı üst plakaya klipsle. Klik sesi duyulmalı | 10 dk | Plaka kalınlığı 1.50 mm; anahtarlar oynamamalı. **3 pinli mi?** 5 pinliyse önce 2 plastik ayağı kes |
| **3** | EC11 enkoderi plakaya tak, somunu sık | 3 dk | Somun aşırı sıkılmasın, gövde çatlar |
| **4** | **BÖLÜM B** — GND papatya dizisini lehimle (W12–W22) | 20 dk | Multimetre: J1-22 ↔ her `Kx.2` < 5 Ω |
| **5** | **BÖLÜM A** — 11 sinyal telini lehimle (W01–W11) | 25 dk | Multimetre: her GPIO ↔ GND, tuş basılıyken < 5 Ω, serbestken ∞ |
| **6** | RC filtre kartını kur (R1, C1, R2, C2) | 12 dk | R1 ve R2 arası ∞ olmalı (ortak nokta yalnızca 3V3) |
| **7** | **BÖLÜM C** — enkoderi bağla (W23–W31) | 15 dk | Multimetre: `RC.NA` ↔ `RC.3V3` = 10 kΩ |
| **8** | LED zincirini tezgâhta kur (W37–W42, üç LED yan yana) | 15 dk | Zinciri gövdeye takmadan önce bitir — yerinde lehimlemek çok zordur |
| **9** | R3 (330 Ω) ve D1 (1N4148) elemanlarını lehimle | 8 dk | Diyot bandı LED tarafında |
| **10** | C3 (1000 µF) kondansatörünü LED1'e en yakın noktaya lehimle | 5 dk | **Polarite!** Beyaz şerit GND'de |
| **11** | **BÖLÜM D** — kalan LED tellerini karta bağla (W32–W36) | 10 dk | Multimetre diyot modu: J1-21 ↔ LED1.VDD ileri yönde ≈ 0.6 V |
| **12** | Tüm lehim noktalarını makaronla yalıt | 10 dk | Çıplak bakır kalmasın |
| **13** | **Enerji vermeden** doğrulama listesini uygula | 10 dk | `docs/01-DONANIM-PIN-SEMASI.md` bölüm 8.1 |
| **14** | LED zincirini gövdeye, kartı yuvasına yerleştir | 10 dk | Teller sıkışmasın, USB portu delikle hizalı olsun |
| **15** | USB'yi tak, enerjili ölçümleri yap | 5 dk | `docs/01-DONANIM-PIN-SEMASI.md` bölüm 8.2 — **LED VDD 4.2–4.4 V** |
| **16** | Firmware'i yükle ve fonksiyon testini yap | 15 dk | `docs/01-DONANIM-PIN-SEMASI.md` bölüm 8.3 |
| **17** | Tabanı kapat, 4 × M3×12 vidayı sık, silikon ayakları yapıştır | 10 dk | Vidalar aşırı sıkılmasın |

**Toplam:** ≈ 3 saat (ilk yapımda), ≈ 1.5 saat (deneyimli).

> **Adım 14 ile 17 arasında: akustik dolgu (MX Blue için önerilir).**
> Plaka altındaki 18.00 mm boş kovuk rezonans odası gibi çalışır ve clicky
> anahtarın tık sesini "çınlamalı / boşluklu" hâle getirir. Taban kapatılmadan
> önce:
> 1. Tabanın **iç yüzeyine** 2–3 mm poron/EVA sünger yapıştırın (100 × 100 mm
>    levhadan ≈ 80 × 60 mm kesin; M3 insert kolonlarının ve DevKit yuvasının
>    etrafını boşaltın).
> 2. Kovukta kalan serbest hacmi sünger artığı veya kesilmiş kaymaz dolap
>    altlığı ile **gevşekçe** doldurun — **DevKit'i ve kabloları
>    SIKIŞTIRMADAN**, arka duvardaki USB açıklığını kapatmadan.
> 3. Vidaları sıktıktan sonra kartın oynamadığını ve USB portunun gövde
>    deliğiyle hizalı kaldığını doğrulayın.
>
> Malzeme: `hardware/BOM.csv` → "Poron/EVA sünger levha 3 mm".
> Gerekçe ve ayrıntı: `docs/01-DONANIM-PIN-SEMASI.md` bölüm 5.1.7.

### Genel lehimleme kuralları

- Havya sıcaklığı **330–350 °C**. Daha düşükte soğuk lehim, daha yükseğinde
  anahtar plastiği erir.
- Bir lehim noktasında **3 saniyeden fazla** kalmayın. MX anahtarın kontak
  bacağı ısıyı gövdeye iletir ve plastik yumuşar.
- Lehim **parlak ve konik** olmalı. Mat, topak veya çatlaklı görünüm =
  soğuk lehim, sökülüp tekrar yapılmalı.
- 26 AWG teli **4 mm** soyun. Daha uzun soyulursa komşu bacağa değme riski
  doğar.
- Her bölüm bitiminde ölçün. 42 telin hepsini lehimleyip sonra arıza aramak
  saatler alır.
- DevKit header pinlerine lehimlemeden önce **flux** sürün; bu pinler kalın
  ve ısıyı hızlı çeker.

### Header'a lehimleme mi, soket mi?

| Yöntem | Artı | Eksi |
|---|---|---|
| Doğrudan pine lehimle | Güvenilir, titreşime dayanıklı, ince | Kartı sökmek için lehimleri kesmek gerekir |
| Dişi header soketi kullan | Kart takılıp çıkarılabilir, firmware geliştirme kolay | 2 mm ek yükseklik; iç yükseklik 18.00 mm'dir, sığar |

**Öneri:** ilk prototipte **dişi soket** kullanın (kartı sökebilmek geliştirme
sırasında hayat kurtarır), seri üretimde doğrudan lehimleyin.

---

## 5. Tel Uzunluğu ve Renk Bütçesi

| Renk | Kullanım | Teller | Tel adedi | Toplam uzunluk |
|---|---|---|---|---|
| Siyah | GND papatya dizisi + enkoder GND + LED GND | W12–W22, W28, W30, W31, W36, W39, W42 | 17 | 594 mm |
| Sarı | K1, K2, K3 | W01–W03 | 3 | 185 mm |
| Yeşil | K4, K5, K6 + LED veri hatları | W04–W06, W32, W33, W37, W40 | 7 | 309 mm |
| Mavi | K7, K8, K9 | W07–W09 | 3 | 200 mm |
| Turuncu | K10, K11 | W10, W11 | 2 | 115 mm |
| Beyaz | Enkoder A, B, SW ve düğüm bağlantıları | W24–W27, W29 | 5 | 300 mm |
| Kırmızı | 3V3 besleme + LED 5 V hatları | W23, W34, W35, W38, W41 | 5 | 199 mm |
| **TOPLAM** | | | **42** | **1 902 mm** |

Tabloda **7 farklı renk** kullanılır. Fire, yeniden lehimleme ve hata payıyla
birlikte **her renkten 2 m** alınması önerilir; bu da toplam **7 × 2 = 14 m**
eder ve BOM'daki `26 AWG silikon tel, 7 renk × 2 m` kalemi tam olarak bunu
karşılar (bkz. `hardware/BOM.csv` satır 15).

En çok harcanan renk siyahtır (**594 mm**), ama 2 m bunun üç katından
fazlasıdır — **ayrıca siyah tel almaya gerek yoktur**. Toplam net tüketim
1 902 mm olduğu için 14 m'lik set, tüm cihazın yaklaşık **yedi katını**
lehimlemeye yeter.

> Yukarıdaki uzunluklar tablodaki nominal değerlerin toplamıdır. Gerçek
> gövde içi yerleşime göre ±20 mm sapabilir. **Telleri gerekenden 10 mm
> uzun kesin** — kısa kalan tel yeniden lehimlenemez, uzun tel kıvrılır.

---

## 6. Hızlı Referans — Pin Kartı

Lehimleme sırasında yanınızda bulundurulacak tek sayfalık özet.

```
+========================================================================+
|            EXTRAKEYBOARD MK1 - LEHIMLEME HIZLI REFERANSI               |
+========================================================================+
|                                                                        |
|  J1 SOL HEADER (usten asagi)          BAGLANTI                         |
|  -------------------------------------------------------------         |
|   1  3V3    ------------------------>  RC.3V3        (W23)             |
|   2  3V3                               bos                             |
|   3  RST                               bos                             |
|   4  GPIO4  ------------------------>  K1.1          (W01)             |
|   5  GPIO5  ------------------------>  K2.1          (W02)             |
|   6  GPIO6  ------------------------>  K3.1          (W03)             |
|   7  GPIO7  ------------------------>  K4.1          (W04)             |
|   8  GPIO15 ------------------------>  K5.1          (W05)             |
|   9  GPIO16 ------------------------>  K6.1          (W06)             |
|  10  GPIO17 ------------------------>  K7.1          (W07)             |
|  11  GPIO18 ------------------------>  K8.1          (W08)             |
|  12  GPIO8  ------------------------>  K9.1          (W09)             |
|  13  GPIO3     ## YASAK - BOS BIRAK                                    |
|  14  GPIO46    ## YASAK - BOS BIRAK                                    |
|  15  GPIO9  ------------------------>  K10.1 COMBO   (W10)             |
|  16  GPIO10 ------------------------>  K11.1 OS      (W11)             |
|  17  GPIO11 <------------------------  RC.NA  ENC_A  (W24)             |
|  18  GPIO12 <------------------------  RC.NB  ENC_B  (W26)             |
|  19  GPIO13 <------------------------  EC11 SW1      (W29)             |
|  20  GPIO14 ------------------------>  R3 330ohm     (W32)             |
|  21  5V     ------------------------>  D1 anot       (W34)             |
|  22  GND    <------------------------  K10.2 zincir  (W22)             |
|                                                                        |
|  J3 SAG HEADER                        BAGLANTI                         |
|  -------------------------------------------------------------         |
|   1  GND    <------------------------  RC.GND        (W31)             |
|  22  GND    <------------------------  LED1.GND      (W36)             |
|  digerleri                             BOS - DOKUNMA                   |
|                                                                        |
+========================================================================+
|  ELEMANLAR                                                             |
|  R1 = 10k   : RC.3V3 -> RC.NA          C1 = 100nF : RC.NA -> RC.GND    |
|  R2 = 10k   : RC.3V3 -> RC.NB          C2 = 100nF : RC.NB -> RC.GND    |
|  R3 = 330   : GPIO14 -> LED1.DIN                                       |
|  D1 = 1N4148: 5V -> LED VDD     (BANT = KATOT = LED TARAFI)            |
|  C3 = 1000uF: LED1.VDD -> LED1.GND  (BEYAZ SERIT = EKSI = GND)         |
+========================================================================+
|  GND PAPATYA DIZISI (siyah tel, 11 adet)                               |
|  K1 - K2 - K3 - K6 - K5 - K4 - K7 - K8 - K9 - K11 - K10 - J1-22        |
+========================================================================+
|  KRITIK KONTROLLER                                                     |
|  [ ] J1-13 ve J1-14 BOS mu?                                            |
|  [ ] GPIO15 (J1-8) ile GPIO5 (J1-5) karismadi mi?                      |
|  [ ] GPIO8 (J1-12) ile GPIO18 (J1-11) karismadi mi?                    |
|  [ ] 1N4148 banti LED tarafinda mi?                                    |
|  [ ] 1000uF beyaz seridi GND'de mi?                                    |
|  [ ] LED zinciri DOUT -> DIN yonunde mi?                               |
|  [ ] Enerji vermeden once 5V-GND kisa devre yok, degil mi?             |
+========================================================================+
```

---

## 7. Arıza Bulma — Kablolama Kaynaklı

| Belirti | Olası tel/eleman | Nasıl doğrulanır |
|---|---|---|
| Bir tuş hiç çalışmıyor | O tuşun **W01–W11** sinyal teli kopuk | GPIO ↔ GND arası, tuş basılıyken < 5 Ω olmalı |
| Bir tuş sürekli basılı görünüyor | Sinyal teli GND'ye kaçmış | Tuş serbestken GPIO ↔ GND açık devre olmalı |
| Bir tuş tek basışta **iki kez** tetikliyor | Kablolama değil: MX Blue'nun click jacket'i bırakışta ek sıçrama üretiyor, debounce yetersiz | `firmware/src/config.h` → `EK_KEY_DEBOUNCE_MS` **8 ms** olmalı; yıpranmış anahtarda 12 ms'e çıkarın |
| Anahtar plakaya tam oturmuyor, eğri duruyor | 5 pinli (PCB-mount) anahtar alınmış | Gövde altındaki **2 plastik konumlandırma ayağını** kesin; **metal kontak pinlerine dokunmayın** |
| Tuş sesi çınlamalı / boşluklu (hollow) | Plaka altındaki 18.00 mm kovuk boş, rezonans odası gibi çalışıyor | Akustik dolguyu uygulayın (bölüm 4 sonundaki not) |
| Birkaç tuş birden çalışmıyor | GND papatya dizisinde kopukluk (**W12–W22**) | J1-22 ↔ her `Kx.2` süreklilik testi |
| İki tuş aynı anda tetikleniyor | İki sinyal teli birbirine değmiş | İki GPIO arası açık devre olmalı |
| Yanlış tuş numarası geliyor | **W05 / W08 / W09** karışmış (GPIO5↔15, GPIO8↔18) | J1 header'da pin sayımını tekrarla |
| Enkoder bir tıkta 2–3 event | **C1 / C2** takılı değil veya yanlış düğümde | `RC.NA` ↔ `RC.GND` arası kapasite ölçümü 100 nF |
| Enkoder yönleri ters | **W25** ve **W27** yer değişmiş | İki teli takas et |
| Enkoder hiç çalışmıyor | **W28** (EC11 C ortak ucu) bağlı değil | `RC.GND` ↔ EC11 orta pin < 5 Ω |
| Enkoder butonu çalışmıyor | **W29 / W30** kopuk | GPIO13 ↔ GND, butona basılıyken < 5 Ω |
| Hiçbir LED yanmıyor | **D1** ters, veya **W33** kopuk, veya `DIN`/`DOUT` ters | LED1.VDD ↔ GND = 4.2–4.4 V mi? |
| LED1 yanıyor, LED2/3 yanmıyor | **W37** (LED1.DOUT → LED2.DIN) kopuk | Zincir veri tellerini kontrol et |
| LED'ler rastgele renk atıyor | **D1** atlanmış (VDD 5.0 V), veya **C3** yok | LED VDD 5.0 V okunuyorsa diyot yok demektir |
| LED'ler titreşiyor / MCU resetleniyor | **C3** takılı değil veya çok uzakta | 1000 µF'ı LED1 besleme uçlarına yakınlaştır |
| PC cihazı görmüyor | Şarj-only USB kablosu, veya yanlış USB portu | Native "USB" portuna, veri kablosuyla tak |
| Cihaz hiç açılmıyor | J1-13 / J1-14'e (GPIO3 / GPIO46) tel lehimlenmiş | O telleri sök; bunlar strapping pinleridir |

---

## 8. Sürüm Geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 3.0.0 | 2026-08-04 | İlk yayın. Çekirdek spesifikasyon v3.0.0 ile hizalı. 42 tel. |
| 3.0.1 | 2026-08-04 | Anahtar **Cherry MX Blue `MX1A-E1NN`** olarak belirtildi; 3 pinli zorunluluğu ve 5 pinli için plastik ayak kesme notu eklendi. Montaj sırasına akustik dolgu notu, arıza tablosuna 3 satır eklendi. **Tel tablosu, tel sayısı (42), renkler, uzunluklar ve pin eşlemesi değişmedi.** |
