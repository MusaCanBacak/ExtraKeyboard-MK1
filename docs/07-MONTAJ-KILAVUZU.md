# ExtraKeyboard MK1 — Montaj Kılavuzu (v3.0.0)

> ⚠️ **Güncel donanım farklıdır.** Bu kılavuz projenin ilk tasarımını anlatır
> (11 tuş, 3 × WS2812B LED, delikli kart, M3 vida + heat-set insert). Güncel yapı:
> 12 tuş, 3 düz LED, hazır baskı dosyaları (`mechanical/stl/`); plaka 4 köşeden M2
> vidayla gövdedeki takozlara tutturulur, heat-set insert kullanılmaz. Güncel montaj
> sırası, kablolama ve ölçüler: [BASIT-YAPIM.md](BASIT-YAPIM.md) §3, §5 ve §6.
> Bu dosyadaki genel lehimleme teknikleri yine geçerlidir; pin ve parça listesi için
> [`PIN-HARITASI.md`](../PIN-HARITASI.md) ve BASIT-YAPIM.md'yi kullanın.


> Bu kılavuz, cihazın sıfırdan monte edilmesini adım adım anlatır.
> Tüm pin numaraları, ölçüler, renkler ve protokol mesajları
> `docs/00-CEKIRDEK-SPEC.md` dosyasından alınmıştır. Bir çelişki görürsen
> **çekirdek spesifikasyon kazanır**.

**Tahmini süre:** 3–4 saat (ilk kez yapıyorsan 5–6 saat ayır).
**Zorluk:** Orta. Nokta lehimleme ve tel soyma deneyimi gerekir; SMD lehim
gerekmez.

---

## Başlamadan önce — Güvenlik

| Kural | Neden |
|---|---|
| **Lehimleme sırasında USB kablosunu MUTLAKA çıkar.** | Enerjili devreye lehim ucu değdirmek MCU'yu ve USB portunu yakabilir. |
| Havyayı gövdesinden değil, sapından tut; ucu 350 °C'dir. | Yanık. |
| Havalandırma sağla veya duman emici kullan. | Reçine dumanı solunum yollarını tahriş eder. |
| Koruyucu gözlük tak — özellikle tel uçlarını keserken. | Uçan tel parçası göze kaçar. |
| Kurşunlu lehim kullandıysan elini yıka, çalışırken bir şey yeme/içme. | Kurşun. |
| ESD: metal bir yüzeye dokunarak boşal, DevKit'i pinlerinden değil kenarından tut. | Statik elektrik MCU'yu bozar. |
| 3D baskı yaparken kapalı odada bırakma. | ABS/ASA emisyonları. |

---

## ADIM 1 — Parça kontrolü

Montaja başlamadan **her parçayı say ve masaya diz.** Eksik bir parçayı
lehim yaparken fark etmek en can sıkıcı durumdur.

### 1.1 Elektronik parçalar

| # | Parça | Adet | Not / Kontrol |
|---|---|---|---|
| 1 | **ESP32-S3-DevKitC-1 (WROOM-1, N16R8)** | 1 | Üzerinde **iki** USB-C soketi olmalı: `UART` ve `USB`. N16R8 damgasını doğrula. |
| 2 | **Cherry MX Blue** (`MX1A-E1NN`), clicky | 11 | **3 pinli (plate-mount) olmalı.** 50 g tetikleme, 2.2 mm ön hareket. 🔴 **Kutuyu açar açmaz bir anahtarı ters çevir ve say:** ortada ⌀4 mm plastik direk + **2 parlak metal pin** varsa 3 pinlidir, sorun yok. Bunların yanında ayrıca **2 ince plastik ayak** varsa 5 pinlidir → **11 anahtarın hepsinde bu 2 plastik ayağı yan keskiyle dibinden kes** (metal pinlere DOKUNMA). Gerekçe ve resimli anlatım: `docs/02-MEKANIK-TASARIM.md` §10.3, `06-ONEMLI-NOTLAR.md` madde 51a. Uyumlu alternatifler: Gateron Blue, Kailh Box White, Outemu Blue. |
| 3 | **Keycap (tuş başlığı)** | 11 | 1u boyut, MX sap. Sağ sütun için farklı renk önerilir (COMBO / OS ayırt etmek için). |
| 4 | **EC11 döner enkoder** (butonlu, M7 burçlu) | 1 | Somunu ve pulunu kaybetme. 20 tık/tur tipik. |
| 5 | **Enkoder düğmesi (knob)** | 1 | 6 mm tırtıllı (knurled) veya D-şaftına uygun. |
| 6 | **WS2812B LED** (5 V, tekli modül veya çıplak 5050) | 3 | Üzerinde **DIN** ve **DOUT** işaretleri okunabilmeli. |
| 7 | **1N4148 diyot** | 1 | LED besleme hattı için (spec §3.3, ZORUNLU). |
| 8 | **1000 µF / 10 V elektrolitik kondansatör** | 1 | LED besleme uçlarına. Kutupludur. |
| 9 | **330 Ω direnç** (1/4 W) | 1 | LED veri hattına, MCU çıkışına yakın. Renk kodu: turuncu-turuncu-kahverengi-altın. |
| 10 | **10 kΩ direnç** (1/4 W) | 2 | Enkoder RC debounce (ENC_A ve ENC_B için birer adet). Kahverengi-siyah-turuncu-altın. |
| 11 | **100 nF seramik kondansatör** (104) | 2 | Enkoder RC debounce. Üzerinde `104` yazar. |
| 12 | **26 AWG çok telli (esnek) silikon izoleli tel** | 7 renk × 2 m | Net tüketim ≈ 1.90 m; gerisi firedir. **Tek damarlı (solid core) tel kullanma** — MX bacağının dibinde tekrarlı bükülmede kırılır. Renk dökümü: `hardware/kablolama-tablosu.md` bölüm 5. |
| 13 | **USB-C ↔ USB-A/C veri kablosu** | 1 | **Şarj kablosu olmaz**, veri hattı olmalı. |

### 1.2 Mekanik parçalar

| # | Parça | Adet | Kontrol |
|---|---|---|---|
| 14 | **Üst plaka** (1.50 mm kalınlık) | 1 | 88.20 × 69.15 mm. Kalınlık kritiktir; MX klipsleri ancak 1.5 mm'de tutar. |
| 15 | **Kasa gövdesi** (duvar 3.00 mm, iç yükseklik 18.00 mm) | 1 | İç boşluk 82.20 × 63.15 mm. |
| 16 | **Taban plakası** (2.50 mm) | 1 | Kasanın parçasıysa ayrıca yoktur. |
| 17 | **M3 × 12 vida** | 4 | Dört köşe. |
| 18 | **M3 × 5 heat-set insert** (pirinç) | 4 | Dış çapı ~4.0–4.6 mm. |
| 19 | **Kauçuk / silikon ayak** (kendinden yapışkanlı) | 4 | **⌀8 mm**, yükseklik 2 mm. Tabandaki çukur `foot_d = 8.00` mm'dir; ⌀10 mm ayak çukura girmez, taban üstünde şişkin durur ve dört köşe eşit oturmaz. **MX Blue ile bu ayaklar isteğe bağlı değildir** — hem kaymayı hem masaya iletilen sesi keser. |
| 20 | **Poron / EVA sünger, 3 mm** (veya kesilmiş kaymaz mutfak dolabı altlığı) | ~1 dm² | Kasa tabanının **iç** yüzeyine yapıştırılır; boş kovuğun çınlamasını keser (ADIM 14.2). Makasla kesilebilmeli. Kendinden yapışkanlı değilse ince çift taraflı bant da al. |

### 1.3 Alet listesi

| Alet | Not |
|---|---|
| Havya (sıcaklık ayarlı) | Lehim için 330–350 °C, insert için **200 °C**. |
| Lehim teli | 0.6–0.8 mm reçineli. |
| Havya ucu | Konik uç (lehim) + düz/insert ucu (insert basma). |
| Yan keski, tel soyucu | |
| **Dijital multimetre** | Süreklilik (bip) modu olan. **Bu montajda pazarlık konusu değildir.** |
| Cımbız, üçüncü el / mengene | |
| Rayba veya 14 mm eğe seti | Plaka delik düzeltmesi için. |
| Isıya dayanıklı bant (kapton) | Tel toplamak ve geçici sabitleme. |
| Çift taraflı köpük bant veya M2 vida | DevKit sabitleme. |
| Makara halinde spiral kablo düzenleyici | İsteğe bağlı. |

> ✅ **KONTROL:** 11 anahtar, 3 LED, 1 enkoder, 4 insert, 4 vida saydın mı?
> **Anahtarlar 3 pinli mi?** Bir anahtarı ters çevir: ⌀4 mm plastik merkez
> direği + **2 parlak metal pin** = 3 pinli, devam et. Bunların yanında
> ayrıca **2 ince plastik ayak** varsa 5 pinlidir → montaja başlamadan
> **11 anahtarın hepsinde bu 2 plastik ayağı yan keskiyle kes**, sonra her
> anahtarı düz bir cam/masa üstüne bastırıp **sallanmadığını** doğrula.
> 🔴 **Metal pinleri kesme** — anahtar geri dönüşsüz olarak bozulur.
> Süngeri kestin mi (ADIM 14.2 ölçüleri)? Multimetren var mı ve pili çalışıyor
> mu (uçları birbirine değdir, bip ötmeli)? Bir eksik varsa **şimdi** tamamla.

---

## ADIM 2 — Kasa ve plakanın hazırlanması

### 2.1 Baskı / imalat kontrolü

3D baskı yapıyorsan önerilen ayarlar:

| Parametre | Plaka | Kasa / taban |
|---|---|---|
| Katman yüksekliği | 0.16 mm | 0.20 mm |
| Duvar sayısı | 4 (tam dolu tercih edilir) | 4 |
| Dolgu | %100 | %30–40 |
| Malzeme | PETG veya ABS/ASA (PLA ısıya dayanmaz) | PETG / ABS / ASA |
| Destek | Gerekirse LED pencerelerinde | Gerekirse |

CNC veya lazer kesim yaptırıyorsan plaka için 1.5 mm alüminyum veya
1.5 mm FR4 mükemmel sonuç verir.

### 2.2 Destek temizliği

1.  Tüm destek malzemesini yan keski ve cımbızla sök.
2.  **Anahtar deliklerinin içindeki tek bir destek kalıntısı bile
    anahtarın eğri oturmasına sebep olur.** Her deliğe tek tek bak.
3.  Kenarlardaki fil ayağı (elephant foot) ve çapak varsa maket bıçağıyla
    45° pah kırarak temizle.

### 2.3 Delik raybalama

| Delik | Hedef ölçü | Tolerans | Kontrol yöntemi |
|---|---|---|---|
| MX anahtar deliği | 14.00 × 14.00 mm | 13.95 – 14.05 | Bir anahtarı **lehimsiz** deneme amaçlı otur-çıkar yap |
| Enkoder deliği | ⌀7.20 mm | ±0.1 | EC11 burcu zorlanmadan geçmeli |
| LED penceresi | ⌀3.00 mm × 3 adet, **8.00 mm aralık** | ±0.1 | Üst bezelde, sola dayalı olmamalı — ortalı |
| Vida delikleri | M3 geçme (⌀3.2) | | Vida serbest dönmeli |
| Insert yuvası | ⌀4.0–4.2 (insert dış çapına göre) | | Insert soğukken elle girmemeli, hafif sıkı olmalı |

**Deliği büyütme:** 14 mm delik dar geldiyse düz iğne eğesiyle **dört
kenardan eşit** al. Sadece bir kenardan alırsan anahtar merkezden kayar.
Bir seferde 0.05 mm'den fazla alma; sık sık deneme yap.

**Deliği küçültme mümkün değildir** — 14.10 mm ve üstü olduysa anahtar
klipsi tutmaz. Bu durumda anahtarları plakaya sıcak silikon veya
CA yapıştırıcı ile sabitlemek gerekir (istenmeyen çözüm, tercihen
plakayı yeniden bas).

> ✅ **KONTROL:** Bir anahtarı bir deliğe tak, sonra sök. Klips "klik"
> sesi çıkarmalı, anahtar plakaya dik durmalı, elle çekince kolayca
> çıkmamalı. Bu testi **köşe deliklerde ve orta delikte** ayrı ayrı yap
> (baskıda köşeler ile orta farklı çıkabilir).

---

## ADIM 3 — Heat-set insert yerleştirme

Dört köşedeki M3 × 5 pirinç insertler burada takılır. Kasa kapatıldıktan
sonra bunlara ulaşamazsın, **şimdi yap.**

### 3.1 Hazırlık

1.  Havyaya **insert ucu** tak. Yoksa eski/feda edilebilir bir düz uç kullan
    (uca pirinç bulaşacaktır).
2.  Havya sıcaklığını **200 °C**'ye ayarla.
    - PLA için 190–200 °C
    - PETG için 210–230 °C
    - ABS/ASA için 230–240 °C
    - **Çok sıcak = plastik erir ve delik ağzı kabarır.
      Çok soğuk = insert eğri girer.** 200 °C ile başla, gerekiyorsa 10'ar
      derece artır.
3.  Kasayı düz, ısıya dayanıklı bir zemine koy.

### 3.2 Basma

1.  Insert'ü deliğin ağzına elle otur. Tırtıklı yüzü aşağı bakmalı
    (dar taraf önce girer).
2.  Havya ucunu insert'ün ortasına değdir, **2–3 saniye bekle** (ısı
    insert'e geçsin).
3.  **Dik** bastır. Yandan itme, sadece aşağı doğru. Plastik yumuşadıkça
    insert kendiliğinden inmeye başlar.
4.  Insert'ün üst yüzeyi **yüzeyle aynı hizaya gelince** veya
    **0.2 mm içeride kalınca** dur.
5.  Havyayı çek ve **10 saniye** hareket ettirmeden bekle — plastik
    donarken insert'i tut, yoksa dışarı doğru geri çıkabilir.

### 3.3 Diklik kontrolü

Insert eğri girdiyse vida sıkışır ve kasa çarpılır.

- Gözle üstten bak: insert deliği kasa yüzeyine dik mi?
- Bir M3 vidayı elle çevirerek sok — **serbestçe, zorlanmadan** dönmeli.
- Eğri girdiyse: havyayı tekrar değdir, insert yumuşayınca dik konuma
  getir ve tekrar bastır.

> ✅ **KONTROL:** 4 insert takılı, hepsi yüzeyle aynı hizada, her birine
> M3 vida elle sokulup çıkarılabiliyor, kasa hiçbir köşede kabarmamış.

---

## ADIM 4 — Anahtarların plakaya oturtulması

### 4.1 Yerleşim

Anahtarları spec §2'deki düzene göre yerleştir:

```
        SÜTUN 1     SÜTUN 2     SÜTUN 3     SÜTUN 4
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |    ( )    |
  1   |    K1     |    K2     |    K3     |    ENC    |
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |           |
  2   |    K4     |    K5     |    K6     |    K10    |   COMBO
      +-----------+-----------+-----------+-----------+
SATIR |           |           |           |           |
  3   |    K7     |    K8     |    K9     |    K11    |   OS
      +-----------+-----------+-----------+-----------+
```

**K1 sol üsttedir, K9 sağ alttadır.** Uygulama arayüzü de tam bu düzeni
gösterir; yanlış yerleştirirsen ekrandaki kart ile fiziksel tuş uyuşmaz.

### 4.2 Oturtma

1.  Plakayı ters çevir (anahtar pinleri sana bakacak şekilde değil,
    anahtarları **üstten** takacaksın — plaka düz dursun).
2.  Anahtarın pinlerinin **eğri olmadığından** emin ol. Eğri pin varsa
    cımbızla düzelt; eğri pin plakadan geçmez ve içeri katlanır.
3.  Anahtarı deliğin üstüne dik olarak otur, iki başparmakla **eşit**
    bastır.
4.  Klipslerin oturduğunu **gözle ve elle** doğrula (aşağıdaki uyarı).

> 🔴 **CLICKY TUZAĞI — "klik sesi geldi" ölçüt DEĞİLDİR.**
> Bu projede **Cherry MX Blue (clicky)** kullanılıyor. Bu anahtar, gövdesinin
> içindeki **click jacket** yüzünden **stem her hareket ettiğinde tık sesi
> çıkarır** — anahtar plakaya hiç oturmamışken, elinde dururken bile.
> Klasik montaj tarifindeki *"klips oturunca klik sesi gelir"* kuralı burada
> **işe yaramaz**: bastırırken duyduğun ses büyük ihtimalle klipsin değil,
> parmağının stem'i hafifçe ittiği için **anahtarın kendi tık sesidir**.
> Gerçek bir tuzaktır; anahtarın yarım oturduğunu ancak keycap'leri taktıktan
> sonra fark edersin ve o noktada hepsini sökmen gerekir.
>
> **Bunun yerine üç kontrolü yap (üçü de geçmeden sonraki anahtara geçme):**
> 1. **Gözle, yandan:** anahtar gövdesinin **flanşı plakaya tam yaslanmalı**;
>    plaka ile flanş arasında ışık sızan bir aralık **olmamalı**.
> 2. **Elle çek:** anahtarı tırnağınla yukarı doğru hafifçe çekiştir.
>    Oynuyor veya "tık" diye biraz yükseliyorsa klips oturmamıştır.
> 3. **Döndürmeye çalış:** anahtar plaka içinde **hiç dönmemeli**.
>
> Ses istiyorsan doğru ses şudur: klipsin oturması **daha derin ve boğuk bir
> "çat"** sesidir; click jacket'in tık'ı ise **ince ve tiz**dir. İkisini
> ayırt etmeyi ilk anahtarda öğren, sonra kalan 10 tanesi kolay gelir.

### 4.3 Eğrilik kontrolü

Bu adımı atlamak, montajın sonunda keycap'ların eğri durmasına ve
düzeltilemeyen bir görüntüye yol açar.

1.  Plakayı göz hizasına kaldır ve **yandan** bak. Anahtar gövdeleri
    birbirine paralel ve plakaya dik mi?
2.  Plakayı düz bir masaya, anahtarlar aşağı bakacak şekilde koy.
    Anahtarların hepsi masaya değmeli, hiçbiri yükselmemeli.
    ⚠️ **Bu test yalnızca 3 pinli anahtarda çalışır.** 5 pinli anahtarda plaka,
    gövdelerin değil **plastik ayakların** üstünde durur ve eğri anahtarı
    göremezsin — bu yüzden ayakların ADIM 1'de kesilmiş olması gerekir.
3.  Bir anahtarı hafifçe döndürmeye çalış — dönmemeli.
4.  Eğri olan varsa: küçük düz tornavidayla klipsi bastırarak anahtarı
    çıkar (veya anahtar sökücü kullan), deliği kontrol et, tekrar tak.

> ✅ **KONTROL:** 11 anahtar takılı, hepsi dik, hiçbiri gevşek değil,
> pinlerin hiçbiri katlanmamış. Şimdi tüm pinlere alttan bak: **22 metal
> kontak pini** (11 × 2) düzgün ve birbirine değmiyor olmalı. Plastik ayak
> **görmemelisin** — görüyorsan ADIM 1'deki kesme işi eksik kalmış demektir,
> lehime başlamadan tamamla. Her anahtarın flanşı plakaya yaslı mı, son kez
> yandan bak (clicky tık sesine güvenme — ADIM 4.2'deki uyarı).

---

## ADIM 5 — Enkoderin montajı

1.  EC11'in burcunu (M7 dişli kısım) plakadaki **⌀7.20 mm** delikten
    geçir. Enkoder plakanın **altında**, şaft üstte kalır.
2.  EC11'in gövdesinde küçük bir **konumlandırma çıkıntısı (pim)** varsa:
    - Plakada karşılık deliği varsa oraya otur.
    - Yoksa **çıkıntıyı yan keskiyle kes** — yoksa enkoder plakaya
      düz oturmaz ve somun sıkıldığında yamulur.
3.  Varsa pulu (rondela) üstten geçir, sonra somunu elle sık.
4.  Somunu **ince pense veya uygun lokma ile** sık — ama **aşırı sıkma**.
    Enkoder gövdesi metal, plaka plastikse plakayı çatlatabilirsin.
    "Elle döndürünce enkoder dönmüyor" yeterlidir.
5.  Enkoderin **A / B / C (ortak)** üçlüsünün ve **buton (SW1/SW2)**
    ikilisinin yönünü not et. Genelde:
    - Bir tarafta **3 pin**: A – C(GND) – B (ortadaki daima ortak uçtur)
    - Karşı tarafta **2 pin**: buton kontakları

> ✅ **KONTROL:** Enkoder şaftını çevir — pürüzsüz tıklar gelmeli.
> Şafta bastır — net bir tık sesi ve geri yaylanma olmalı. Somun sıkı,
> enkoder plakada oynamıyor.

---

## ADIM 6 — LED'lerin yerleştirilmesi ve zincir lehimi

> ⚠️ **BU ADIMDA EN SIK YAPILAN HATA: DIN/DOUT YÖNÜNÜN TERS BAĞLANMASI.**
> WS2812B tek yönlüdür. Veri **DIN**'den girer, **DOUT**'tan çıkar.
> Ters bağlarsan **hiçbir LED yanmaz** ve devrede hiçbir hata belirtisi olmaz.

### 6.1 Yerleşim

Üç LED, üst bezelde **soldan sağa**, aralarında **8.00 mm** olacak şekilde
dizilir:

```
              (LED1)   (LED2)   (LED3)
                |←8.0→|  |←8.0→|
   ═════════════════════════════════════  ← üst bezel
```

| LED | Görevi (spec §6.4) |
|---|---|
| **LED1** | OS modu — Windows mavi `#1E90FF`, macOS beyaz `#FFFFFF` |
| **LED2** | Combo durumu — açık turuncu `#FF9500`, tetiklendi yeşil `#2CC985` |
| **LED3** | Bağlantı — bağlı yeşil `#2CC985`, yok kırmızı `#E04F5F`, tuş flaşı mavi `#3B8ED0` |

### 6.2 Zincir yönü (KRİTİK)

```
  ESP32 GPIO14 ──[330 Ω]──► DIN │ LED1 │ DOUT ──► DIN │ LED2 │ DOUT ──► DIN │ LED3 │ DOUT (boşta)
                                                                              
  +5V (VBUS) ──►|1N4148|──┬────► LED1 5V ────► LED2 5V ────► LED3 5V
                          │
                       1000 µF          (kondansatörün + ucu diyottan SONRAKİ 5V hattına)
                          │
  GND ────────────────────┴────► LED1 GND ───► LED2 GND ───► LED3 GND
```

**Veri zinciri kuralı:** Bir LED'in **DOUT**'u, bir sonrakinin **DIN**'ine
gider. İlk LED'in DIN'i 330 Ω direnç üzerinden **GPIO14**'e bağlanır.
Son LED'in DOUT'u **boşta kalır**.

Çıplak 5050 WS2812B kullanıyorsan üstündeki köşe pahını (chamfer) bul —
pin numaralandırması ondan başlar. Modül kullanıyorsan üzerindeki
ok işaretini takip et: **ok veri akış yönünü gösterir.**

### 6.3 1N4148 diyodun yönü (ZORUNLU)

Spec §3.3: WS2812B'nin V_IH değeri 0.7 × VDD = 3.5 V'tur; ESP32-S3'ün
veri çıkışı 3.3 V'tur, yani **sınırdadır**. LED besleme hattına seri bir
1N4148 koyunca VDD ≈ 4.3 V'a düşer, V_IH ≈ 3.0 V olur ve 3.3 V veri
**güvenle** tanınır.

```
   VBUS(+5V) ──►|──── LED'lerin 5V ucu
                 ↑
          1N4148, üzerindeki SİYAH ŞERİT (katot) LED tarafına bakar
```

**Şeridin yönü ters olursa LED'lere hiç gerilim gitmez ve hiçbiri yanmaz.**

### 6.4 Lehimleme sırası

1.  Üç LED'i bezel pencerelerinin arkasına, ışık yüzeyi pencereye bakacak
    şekilde konumlandır. Isıya dayanıklı bantla geçici sabitle.
2.  Önce **GND** hattını lehimle (LED1 GND → LED2 GND → LED3 GND).
3.  Sonra **5V** hattını lehimle (diyodun katodundan LED1 5V → LED2 5V → LED3 5V).
4.  Sonra **veri** zincirini lehimle: LED1 DOUT → LED2 DIN, LED2 DOUT → LED3 DIN.
5.  330 Ω direnci **MCU çıkışına yakın** yerleştir (spec §3.3) — yani
    GPIO14 ucunda, LED tarafında değil.
6.  1000 µF kondansatörü diyottan sonraki 5V ile GND arasına bağla.
    **Kutupludur:** üzerindeki beyaz şerit ve kısa bacak **eksi (GND)**
    ucudur. Ters bağlarsan patlar.

**Lehim tekniği (çıplak WS2812B için):**
- Havya 330 °C, temas süresi **maksimum 3 saniye**. WS2812B'nin plastik
  gövdesi kolay erir; eriyen LED "yanmayan LED" olur.
- Önce pede minik bir lehim damlası koy (tinning), sonra teli üstüne
  değdirip ısıt. Uzun süre ısıtma.
- Ardışık iki lehim arasında LED'in soğuması için 20 saniye bekle.

> ✅ **KONTROL:** Multimetreyi süreklilik moduna al ve şunları doğrula:
> - LED1 5V ile LED3 5V arası bip (aynı hat)
> - LED1 GND ile LED3 GND arası bip
> - **LED1 5V ile LED1 GND arası bip YOK** (bip varsa kısa devre!)
> - LED1 DOUT ile LED2 DIN arası bip
> - LED2 DOUT ile LED3 DIN arası bip
> - **LED1 DIN ile LED2 DIN arası bip YOK** (varsa DIN'leri paralel
>   bağlamışsın, zincir bozuk)
> - Diyot modunda VBUS→diyot yönünde ~0.6 V, ters yönde sonsuz

---

## ADIM 7 — Ortak GND papatya dizimi

Onbir anahtarın ve enkoderin **birer ucu ortak GND'ye** gider
(spec §3.1: her anahtar "Anahtar → GND"). Bunları tek tek DevKit'e
çekmek 14 tel demektir; bunun yerine **papatya dizimi (daisy chain)**
kullanılır: tek bir kalın tel tüm anahtarların bir ucunu birbirine bağlar
ve tek noktadan DevKit'in GND'sine gider.

### 7.1 Sıra

```
  DevKit GND ──┬─ K1 ─ K2 ─ K3 ── ENC(C ortak) ── ENC(SW ortak)
               │
               └─ K4 ─ K5 ─ K6 ─ K10
               │
               └─ K7 ─ K8 ─ K9 ─ K11
               │
               └─ LED GND hattı
```

Fiziksel olarak en pratik yol, **her satırı kendi içinde zincirlemek**
ve üç satır zincirini DevKit'in GND pininde birleştirmektir. Böylece tel
uzunlukları kısa kalır ve tek bir uzun tel tüm plakada dolaşmaz.

### 7.2 Teknik

1.  Yaklaşık 30 cm 26 AWG çok telli (esnek) **siyah** tel al.
2.  Ucu sıyır, ilk anahtarın GND bacağına lehimle.
3.  **İzolasyonu ortadan sıyır (kesme!):** tel soyucuyla telin ortasında
    3–4 mm'lik bir pencere aç, bakırı ortaya çıkar. Bu pencereyi bir
    sonraki anahtarın bacağına lehimle. Tel kesilmediği için elektriksel
    süreklilik kendiliğinden korunur.
4.  Aynı şekilde diğer anahtarlara devam et.
5.  Son anahtardan sonra tel ucunu DevKit'in **GND** pinine götür.

**Lehimleme tekniği:**
- Anahtar bacağını önce **tinle** (üstüne az lehim koy).
- Teli bacağa dola veya yasla, havyayı **bacağa** değdir — telin
  üstünden değil. Isı bacaktan tele geçmeli.
- 2–3 saniyede lehim akıp parlak bir koni oluşturmalı. Mat, topaklı,
  köpük gibi görünen lehim **soğuk lehimdir**, sökmen gerekir.

> ✅ **KONTROL:** Multimetre süreklilik modunda, DevKit GND ucunu bir
> proba, sırayla **11 anahtarın ve enkoderin ortak uçlarını** diğer proba
> değdir. **Hepsinde bip ötmeli.** Ötmeyen varsa o noktadaki lehim soğuk
> veya kopuk.

---

## ADIM 8 — Anahtarlardan GPIO'ya tel çekme

Her anahtarın **diğer ucu** kendi GPIO'suna gider. Matris yoktur,
diyot yoktur — bu sayede combo (aynı anda 3 tuş) hayalet tuş sorunu
olmadan çalışır (spec §3.1).

### 8.1 Kablolama tablosu — DEĞİŞTİRİLEMEZ

| Sinyal | GPIO | Mod | Bağlantı | Önerilen tel rengi |
|---|---|---|---|---|
| **K1** | **GPIO4** | INPUT_PULLUP | Anahtar → GND | Kahverengi |
| **K2** | **GPIO5** | INPUT_PULLUP | Anahtar → GND | Kırmızı |
| **K3** | **GPIO6** | INPUT_PULLUP | Anahtar → GND | Turuncu |
| **K4** | **GPIO7** | INPUT_PULLUP | Anahtar → GND | Sarı |
| **K5** | **GPIO15** | INPUT_PULLUP | Anahtar → GND | Yeşil |
| **K6** | **GPIO16** | INPUT_PULLUP | Anahtar → GND | Mavi |
| **K7** | **GPIO17** | INPUT_PULLUP | Anahtar → GND | Mor |
| **K8** | **GPIO18** | INPUT_PULLUP | Anahtar → GND | Gri |
| **K9** | **GPIO8** | INPUT_PULLUP | Anahtar → GND | Beyaz |
| **K10 (COMBO)** | **GPIO9** | INPUT_PULLUP | Anahtar → GND | Pembe |
| **K11 (OS)** | **GPIO10** | INPUT_PULLUP | Anahtar → GND | Turkuaz |
| **ENC_A** | **GPIO11** | INPUT_PULLUP | EC11 A (+ RC filtre) | Açık yeşil |
| **ENC_B** | **GPIO12** | INPUT_PULLUP | EC11 B (+ RC filtre) | Açık mavi |
| **ENC_SW** | **GPIO13** | INPUT_PULLUP | EC11 buton → GND | Lila |
| **LED_DATA** | **GPIO14** | OUTPUT | 330 Ω → WS2812B DIN | Sarı-siyah çizgili |
| **GND (ortak)** | GND | — | Papatya dizimi (Adım 7) | **Siyah** |
| **+5V (LED)** | 5V / VBUS | — | 1N4148 üzerinden | **Kırmızı** |

> Renk kodu **öneridir**, elektriksel bir zorunluluğu yoktur. Ama en az
> şu üçüne uy: **GND siyah**, **+5V kırmızı**, **veri hattı ayırt edici
> bir renk**. Aynı renkten iki sinyal çekersen bir hafta sonra hangisinin
> ne olduğunu bulamazsın.

Renk stoğun yetmiyorsa telleri numaralandırılmış etiket bandıyla işaretle
veya tel uçlarına farklı sayıda ısı büzüşmeli halka geçir.

### 8.2 KULLANILMAYACAK pinler

Yanlışlıkla bu pinlere bağlarsan cihaz açılmaz veya kararsız çalışır
(spec §3.2):

| GPIO | Neden yasak |
|---|---|
| 0, 46 | Boot strapping — açılışta LOW olursa bootloader'a düşer |
| 3 | JTAG kaynak seçimi strapping |
| **19, 20** | **Yerleşik USB D− / D+ — dokunulamaz** |
| 26–32 | SPI Flash |
| 33–37 | Octal PSRAM (N16R8 varyantında kullanılır) |
| 43, 44 | U0TXD / U0RXD — seri konsol |
| 45 | VDD_SPI strapping |
| 48 | DevKitC-1 üzerindeki dahili RGB LED |

> **GPIO15/16 notu:** Bu pinler yalnızca harici 32.768 kHz kristal
> takılırsa XTAL_32K_P/N olur. Bu projede kristal yok, normal GPIO'durlar.

### 8.3 Çekme tekniği

1.  Teli **gerektiğinden 3–4 cm uzun** kes. Kısa kesilen tel montajda
    gerginlik yaratır ve zamanla lehimden kopar.
2.  Her iki ucundan 3 mm sıyır, uçları tinle.
3.  Önce **anahtar tarafını** lehimle. Anahtar bacağını tin, teli değdir,
    2–3 saniye.
4.  Teli kasanın içinden geçirip DevKit'in konumuna kadar götür.
    Tüm telleri **tek bir demet** halinde topla, kablo bağı veya spiral
    düzenleyici kullan.
5.  DevKit tarafını **henüz lehimleme.** Önce Adım 10'da DevKit'i
    konumlandır, sonra telleri kısaltıp lehimle. Aksi halde teller
    ya çok kısa ya çok karışık olur.

**DevKit tarafı için iki seçenek:**

- **Doğrudan lehim** — kalıcı, en sağlam, ama DevKit'i değiştirmek
  isterseniz zahmetli.
- **Dişi header + erkek pin** — DevKit'e erkek header lehimle, tellerin
  ucuna Dupont dişi soket tak. Sökülebilir, servis dostu.
  **Bu seçenek önerilir.**

> ✅ **KONTROL:** Tabloyu bir kağıda yaz ve her teli lehimledikten sonra
> tik at. 15 sinyal teli + GND papatyası + 5V hattı = tamamlandığında
> hiçbir satır boş kalmamalı.

---

## ADIM 9 — Enkoder RC debounce devresi

EC11 mekanik enkoderin kontak sıçraması **yazılımla tam bastırılamaz**
(spec §3.4). Donanım filtresi **zorunludur**; atlarsan enkoder çift sayar
veya rastgele ters yönde tıklar.

### 9.1 Devre (her iki kanal için ayrı ayrı)

```
   3V3 ──[10 kΩ]──┬── ENC_A (GPIO11)
                  │
                 ═══ 100 nF
                  │
   EC11 A ────────┴── GND (ortak uç)
```

`ENC_B` (GPIO12) için **birebir aynısı** ikinci bir 10 kΩ + 100 nF ile
kurulur. `ENC_SW` (GPIO13) için RC gerekmez — dahili pull-up + yazılım
debounce yeterlidir.

**Dikkat:** 10 kΩ direnç **3V3 ile GPIO arasına** gelir (pull-up),
100 nF kondansatör ise **GPIO ile GND arasına** gelir. EC11'in A ucu
GPIO düğümüne bağlanır. Enkoder tık verdiğinde A ucu GND'ye çekilir,
kondansatör deşarj olurken sıçramalar yumuşar.

### 9.2 İki montaj yöntemi

**Yöntem A — Delik-pertinaks (önerilen).**

1.  Yaklaşık 15 × 20 mm bir delikli pertinaks parçası kes.
2.  İki 10 kΩ direnci ve iki 100 nF kondansatörü yerleştir.
3.  Alt yüzden bakır tel veya lehim köprüleriyle bağlantıları kur.
4.  Dört tel çıkışı bırak: `3V3`, `GND`, `ENC_A→GPIO11`, `ENC_B→GPIO12`,
    artı enkoderin `A` ve `B` uçlarına giden iki tel.
5.  Kartı kasanın içine çift taraflı köpük bantla yapıştır.
   **Kartın altına yalıtkan bir bant koy** — DevKit'in metal kutusuna veya
   başka bir lehime değmesin.

**Yöntem B — Havada lehim (dead-bug).**

1.  Direnci ve kondansatörü doğrudan enkoderin bacaklarına lehimle.
2.  Her bir birleşim noktasını **ısı büzüşmeli makaronla** yalıt.
3.  Bileşenleri sıcak silikonla enkoder gövdesine sabitle (titreşimle
    kopmasınlar).

Yöntem B daha hızlıdır ama daha kırılgandır ve sorun giderirken ölçüm
yapmak zordur. İlk montajında **Yöntem A**'yı tercih et.

> ✅ **KONTROL:** Multimetre ile:
> - 3V3 ile ENC_A düğümü arası ≈ **10 kΩ** (direnç modunda ölç)
> - ENC_A düğümü ile GND arası **süreklilik YOK** (enkoder boşta iken;
>   kondansatör yüzünden bip birkaç yüz ms ötüp kesilebilir, bu normaldir)
> - Enkoderi elle çevirirken ENC_A ile GND arasında bip **kesik kesik**
>   gelmeli
> - **3V3 ile GND arası kısa devre YOK** — bu en kritik ölçüm

---

## ADIM 10 — DevKit'in yerleştirilmesi ve sabitlenmesi

### 10.1 Konumlandırma

İç yükseklik 18.00 mm'dir (spec §2.1) — DevKit + kablo bu boşluğa
girmek zorundadır.

1.  DevKit'i kasanın içine, **USB soketleri kasanın arka duvarındaki
    çıkışa denk gelecek şekilde** yerleştir.
2.  DevKitC-1'de **iki USB-C soketi** vardır:
    - **`USB`** yazan (yerleşik USB OTG, GPIO19/20) — **normal kullanımda
      kullanılacak olan budur**. HID + CDC bu porttan gelir.
    - **`UART`** yazan (USB-Seri köprü) — yalnızca firmware yükleme ve
      seri konsol için.
    - Kasanın çıkış deliği **`USB`** portuna denk gelmelidir. Firmware
      yükleme için kasa açıkken `UART` portunu kullanacaksın.
3.  Kartın altına **yalıtkan bir tabaka** koy (kapton bant, ince plastik).
    Kasa iletken (alüminyum) ise bu zorunludur.

### 10.2 Sabitleme (üç seçenek)

| Yöntem | Artı | Eksi |
|---|---|---|
| **Çift taraflı köpük bant** | Hızlı, esnek, titreşim yutar | Kalıcı değil, sıcakta gevşeyebilir |
| **M2 vida + kasadaki kule** | En sağlam, sökülebilir | Kasada delik/kule olmalı |
| **3D basılmış klips/kızak** | Vidasız, sökülebilir | Baskı toleransına duyarlı |

Hangi yöntemi seçersen seç **kartın oynamadığından** emin ol. Oynayan
kart, zamanla lehimlerin kopmasına yol açar.

### 10.3 Kablo yönetimi

1.  Tel demetini kasanın bir kenarına yatır, kablo bağıyla topla.
2.  **Tellerin plakanın altına, anahtar gövdelerinin bastığı yere
    gelmediğinden** emin ol — kasa kapanırken sıkışıp izolasyonu delebilir.
3.  Enkoder RC kartını tellerin üstüne değil, boş bir köşeye yerleştir.
4.  Kasayı **vidalamadan**, sadece üst üste koyarak kapan(mıy)acağını
    kontrol et. 1–2 mm açık kalıyorsa içeride bir tel sıkışıyordur.

> ✅ **KONTROL:** Kasa vidasız olarak tam kapanıyor, hiçbir tel dışarı
> taşmıyor, USB soketi kasadaki delikten kablo takılabilecek şekilde
> erişilebilir.

---

## ADIM 11 — LEHİMLEME ÖNCESİ VE SONRASI TEST

> 🔴 **BU ADIMI ATLAMA.** Güç vermeden önce yapılan beş dakikalık ölçüm,
> yanmış bir DevKit'in yerine yenisini beklemekten iyidir.

### 11.1 Güç vermeden ÖNCE — kısa devre kontrolü (ZORUNLU)

USB kablosu **takılı değilken**, multimetre **süreklilik (bip)** modunda:

| # | Ölçüm | Beklenen | Bip gelirse ne demek? |
|---|---|---|---|
| 1 | **VBUS (5V) ↔ GND** | **BİP YOK** | 🔴 **KISA DEVRE. Güç verme!** En sık sebep: 1000 µF kondansatörün ters/yanlış bağlanması, LED besleme lehiminin kayması. |
| 2 | **3V3 ↔ GND** | **BİP YOK** | 🔴 Kısa devre. RC devresinde kondansatör yanlış bağlanmış olabilir. |
| 3 | **3V3 ↔ VBUS** | **BİP YOK** | 🔴 Regülatör atlanmış, kısa var. |
| 4 | Her GPIO ↔ komşu GPIO | **BİP YOK** | 🔴 İki tel birbirine değiyor / lehim köprüsü var. |
| 5 | Her GPIO ↔ GND | **BİP YOK** (tuş basılı değilken) | 🔴 Tel yanlış yere gitmiş veya anahtar sürekli kapalı. |

> **Not:** 1. ve 2. ölçümde kondansatörler yüzünden multimetre kısa süreli
> (yarım saniyeden az) bip ötüp kesebilir — bu **normaldir**, kondansatör
> şarj oluyordur. **Sürekli** bip kısa devredir.

### 11.2 Güç vermeden ÖNCE — süreklilik kontrolü

Şimdi olması **gereken** bağlantıları doğrula:

| # | Ölçüm | Beklenen |
|---|---|---|
| 6 | Her GPIO ↔ karşılık gelen anahtarın sinyal ucu | **BİP** |
| 7 | Her anahtarın GND ucu ↔ DevKit GND | **BİP** |
| 8 | Her GPIO ↔ GND, **o tuş basılıyken** | **BİP** (basınca kapanmalı) |
| 9 | GPIO14 ↔ 330 Ω'un bir ucu | **BİP** |
| 10 | 330 Ω'un diğer ucu ↔ LED1 DIN | **BİP** |
| 11 | LED1 DOUT ↔ LED2 DIN, LED2 DOUT ↔ LED3 DIN | **BİP** |
| 12 | LED 5V hattı ↔ 1N4148 katodu (şeritli uç) | **BİP** |
| 13 | 1N4148 anodu ↔ VBUS | **BİP** |
| 14 | ENC_A(GPIO11) ↔ 3V3, direnç modunda | **≈10 kΩ** |
| 15 | ENC_B(GPIO12) ↔ 3V3, direnç modunda | **≈10 kΩ** |
| 16 | GPIO13 ↔ enkoder buton ucu | **BİP** |

**Tuş testi tablosu** (8 numaralı ölçümü sistematik yapmak için):

| Tuş | GPIO | Basılıyken GND'ye bip? |
|---|---|---|
| K1 | 4 | ☐ |
| K2 | 5 | ☐ |
| K3 | 6 | ☐ |
| K4 | 7 | ☐ |
| K5 | 15 | ☐ |
| K6 | 16 | ☐ |
| K7 | 17 | ☐ |
| K8 | 18 | ☐ |
| K9 | 8 | ☐ |
| K10 | 9 | ☐ |
| K11 | 10 | ☐ |

Onbir kutunun hepsi işaretlenmeden devam etme.

### 11.3 Güç verdikten SONRA — gerilim kontrolü

USB'yi tak (Adım 12'den sonra), multimetre **DC gerilim** modunda:

| Ölçüm noktası | Beklenen | Sapma anlamı |
|---|---|---|
| VBUS ↔ GND | **4.75 – 5.25 V** | Düşükse kablo zayıf/uzun veya USB portu yetersiz |
| 3V3 ↔ GND | **3.25 – 3.35 V** | Düşükse regülatör aşırı yükleniyor (kısa devre olabilir) |
| 1N4148 sonrası LED 5V ↔ GND | **≈ 4.3 V** | 5.0 V görüyorsan diyot **atlanmış** (köprülenmiş); 0 V görüyorsan diyot **ters** takılmış |
| GPIO4 ↔ GND (K1 basılı değil) | **≈ 3.3 V** | 0 V ise pull-up yok veya tel GND'ye kısa |
| GPIO4 ↔ GND (K1 basılı) | **≈ 0 V** | 3.3 V kalıyorsa anahtar bağlantısı kopuk |

---

## ADIM 12 — İlk güç verme ve firmware yükleme

### 12.1 İlk güç verme

1.  **11.1'deki kısa devre kontrolünü yaptığından emin ol.**
2.  Mümkünse akım sınırlı bir USB kaynağı veya USB akım ölçer kullan.
3.  USB kabloyu DevKitC-1'in **`UART`** portuna tak (ilk yükleme için).
4.  İlk 5 saniyede şunları izle:
    - Kartın üzerindeki kırmızı güç LED'i yandı mı?
    - **Isınan bir bileşen var mı?** Elini kartın üstünde gezdir. Bir şey
      ısınıyorsa **derhal fişi çek** ve 11.1'e dön.
    - Duman/koku var mı? Varsa derhal çek.
5.  Toplam akım **150 mA'nın altında** olmalıdır (spec §3.3).

### 12.2 PlatformIO ile firmware yükleme

> **⚠️ Bu projenin kartlarında `pio run -t upload` KULLANMAYIN.** PlatformIO imajı
> QIO / 80 MHz yazar; bu kartlardaki Boya flash çipleri o ayarla açılmaz (boot
> döngüsü). Hazır imaj + yükleyici ya da `--flash_mode dio --flash_freq 40m` ile
> esptool kullanın: kök dizindeki **README.md → 4. Firmware**. Aşağıdaki komutlar
> genel PlatformIO başvurusu olarak bırakılmıştır.

```bash
# Proje kökünde
cd ~/ExtraKeyboard-MK1/firmware

# Derle
pio run

# Yükle (UART portundan)
pio run -t upload

# Seri konsolu aç
pio device monitor -b 115200
```

Yükleme "Connecting…" aşamasında takılırsa **elle bootloader moduna al**:

1.  **BOOT** düğmesini basılı tut
2.  Basılıyken **RESET (EN)** düğmesine bir kez bas ve bırak
3.  **BOOT**'u bırak
4.  Yüklemeyi tekrar başlat

### 12.3 İlk açılışta beklenen davranış

Firmware yüklendikten sonra `UART` kablosunu çıkarıp **`USB`** portuna tak.

| Ne olmalı | Nasıl doğrulanır |
|---|---|
| LED1 yanar (mavi veya beyaz) | Gözle. Renk kayıtlı OS moduna göre |
| LED2 sönük | Gözle |
| LED3 **kırmızı** (`#E04F5F`) | Gözle. PC uygulaması henüz açık değil = HID yedek modu |
| Cihaz seri port olarak görünür | macOS: `ls /dev/cu.usbmodem*` · Windows: Aygıt Yöneticisi > Bağlantı Noktaları |
| Cihaz klavye olarak görünür | macOS: Klavye Tanımlama Asistanı çıkabilir · Windows: Aygıt Yöneticisi > Klavyeler |
| Her saniye kalp atışı | Seri konsolda `HB 1000`, `HB 2000`… satırları |

**Kimlik testi.** Seri konsolda `CMD ID` yaz + Enter:

```
> CMD ID
ID 3.0.0 MK1 EK1-A4C138 WIN
```

Yanıt geliyorsa **CDC bağlantısı ve firmware çalışıyor demektir.**

---

## ADIM 13 — Fonksiyonel test listesi

Kasayı vidalamadan **önce** tüm testleri geçir. Kapattıktan sonra bir
sorun bulursan hepsini sökmen gerekir.

Test için seri konsolu açık tut (`pio device monitor -b 115200`) —
her fiziksel eylemin karşılığında bir protokol satırı görmelisin.

### 13.1 Onbir tuş testi

Her tuşa **tek tek** bas ve konsolda beklenen satırları gör:

| Tuş | GPIO | Basınca | Bırakınca | ☐ |
|---|---|---|---|---|
| K1 | 4 | `EV KEY 1 DOWN` | `EV KEY 1 UP` | ☐ |
| K2 | 5 | `EV KEY 2 DOWN` | `EV KEY 2 UP` | ☐ |
| K3 | 6 | `EV KEY 3 DOWN` | `EV KEY 3 UP` | ☐ |
| K4 | 7 | `EV KEY 4 DOWN` | `EV KEY 4 UP` | ☐ |
| K5 | 15 | `EV KEY 5 DOWN` | `EV KEY 5 UP` | ☐ |
| K6 | 16 | `EV KEY 6 DOWN` | `EV KEY 6 UP` | ☐ |
| K7 | 17 | `EV KEY 7 DOWN` | `EV KEY 7 UP` | ☐ |
| K8 | 18 | `EV KEY 8 DOWN` | `EV KEY 8 UP` | ☐ |
| K9 | 8 | `EV KEY 9 DOWN` | `EV KEY 9 UP` | ☐ |
| K10 | 9 | `EV MODE COMBO_ON` | `EV MODE COMBO_OFF` | ☐ |
| K11 | 10 | (kısa basış) | `EV OS MAC` / `EV OS WIN` | ☐ |

**Tek basış = tek eylem testi (MX Blue için ZORUNLU).**
Her tuş için, konsolda **tek** `EV KEY <n> DOWN` ve **tek** `EV KEY <n> UP`
satırı görmelisin. Onbir tuşa da **onar kez** bas ve say:

| Tuş | 10 basışta kaç `UP` geldi? | Beklenen | ☐ |
|---|---|---|---|
| K1…K9, K11 | ____ | **tam 10** | ☐ |

10'dan fazla satır sayıyorsan **çift tetikleme** var. Sebep neredeyse her
zaman MX Blue'nun click jacket'inin **bırakış** tarafında ürettiği ek kontak
sıçramasıdır (`06-ONEMLI-NOTLAR.md` madde 22a). Sırayla:

1. `firmware/src/config.h` → **`EK_KEY_DEBOUNCE_MS`** değerini **8 → 12** yap,
   yeniden derle ve yükle. Sayı **yalnızca burada** durur, başka dosyada
   değiştirme.
2. Hâlâ varsa lehimi kontrol et (soğuk lehim aynı belirtiyi verir) ve o
   anahtarı bir yedeğiyle değiştir.
3. **20 ms'i geçme** — o noktadan sonra tuş "gecikmeli" hissettirir.

> Bu maddeyi kasayı kapatmadan **mutlaka** geçir: bir makro klavyede çift
> tetikleme, atadığın uygulamanın **iki kez açılması** demektir ve kapalı
> kasada teşhis etmek çok daha zordur.

**Dikkat edilecekler:**

- **Sıra kontrolü:** Sol üstteki tuşa bastığında `EV KEY 1` gelmeli.
  `EV KEY 3` geliyorsa telleri karıştırmışsın — Adım 8'deki tabloya dön.
- **Çift sayım:** Tek basışta iki `DOWN`/`UP` satırı geliyorsa **8 ms**
  debounce yetmemiş demektir (yukarıdaki test). Anahtarın kirli veya lehimin
  soğuk olması da aynı belirtiyi verir.
- **Eksik sayım:** Çok hızlı iki basışta **tek** `DOWN` geliyorsa bu debounce
  değil, MX Blue'nun **0.5 mm histerezisi**dir: tuş 2.2 mm'de tetiklenir ama
  ancak 1.7 mm'ye kadar bırakılınca sıfırlanır. Tuşu tam bırakıp tekrar dene;
  düzeliyorsa sorun yoktur (madde 70a). **Debounce'u düşürerek çözmeye
  çalışma.**
- **Takılı kalma:** Bıraktığın halde `UP` gelmiyorsa anahtar mekanik
  olarak sıkışmış veya tel GND'ye sürekli değiyordur.
- **Basmadan gelen olay:** Hiç dokunmadığın halde olay akıyorsa o GPIO'nun
  teli başka bir yere değiyor veya kopuk uç dolaşıyordur.

### 13.2 Enkoder testi

| Test | Yöntem | Beklenen | ☐ |
|---|---|---|---|
| **Saat yönü** | Düğmeyi sağa 1 tık çevir | Tam **bir** adet `EV ENC CW` | ☐ |
| **Saat yönü tersi** | Sola 1 tık çevir | Tam **bir** adet `EV ENC CCW` | ☐ |
| **10 tık sağ** | Sağa 10 tık çevir | Tam **10** adet `EV ENC CW`, hiç `CCW` yok | ☐ |
| **10 tık sol** | Sola 10 tık çevir | Tam **10** adet `EV ENC CCW`, hiç `CW` yok | ☐ |
| **Basış** | Düğmeye kısa bas | `EV ENC PRESS` | ☐ |
| **Uzun basış** | 800 ms basılı tut | `EV ENC LONG` | ☐ |
| **HID ses** | Sağa çevir | Bilgisayarın ses seviyesi **artmalı** | ☐ |
| **HID sessiz** | Düğmeye bas | Ses **kapanmalı/açılmalı** | ☐ |

**Yön ters geliyorsa** (sağa çevirince `CCW`): enkoderin **A ve B
tellerini yer değiştir** (GPIO11 ↔ GPIO12). Bu tamamen normaldir,
EC11'lerin pin sırası üreticiye göre değişir.

**Çift sayım varsa** (1 tıkta 2 event): RC devresi ya eksik ya yanlış
bağlanmış. Adım 9'a dön ve 10 kΩ / 100 nF değerlerini ölç.

### 13.3 LED testi

Seri konsoldan elle komut göndererek:

| Komut | Beklenen | ☐ |
|---|---|---|
| `CMD LED 1 FF0000` | **Sol** LED kırmızı yanar | ☐ |
| `CMD LED 2 00FF00` | **Orta** LED yeşil yanar | ☐ |
| `CMD LED 3 0000FF` | **Sağ** LED mavi yanar | ☐ |
| `CMD LED 1 1E90FF` | Sol LED spec mavisi | ☐ |
| `CMD LED BRIGHT 10` | Üç LED de belirgin şekilde söner | ☐ |
| `CMD LED BRIGHT 60` | Varsayılan parlaklığa döner | ☐ |
| `CMD LED BRIGHT 255` | Çok parlak (uzun süre bırakma) | ☐ |

**Sık görülen sonuçlar ve anlamları:**

| Gördüğün | Anlamı | Çözüm |
|---|---|---|
| Hiçbiri yanmıyor | Veri hattı, 5V veya diyot yönü hatalı | 1N4148 yönünü ve GPIO14→330 Ω→DIN zincirini ölç |
| Sadece LED1 yanıyor | LED1 DOUT → LED2 DIN kopuk | O lehimi tekrar yap |
| İlk ikisi yanıyor, üçüncü yok | LED2 DOUT → LED3 DIN kopuk | O lehimi tekrar yap |
| Yanlış LED yanıyor (`LED 1` deyince sağdaki) | Zincir sırası ters | Fiziksel LED sırasını değiştir veya zinciri yeniden lehimle |
| Renkler karışık (kırmızı deyince yeşil) | LED GRB yerine RGB varyantı | Firmware'de renk sırası ayarı — donanım sorunu değil |
| Titriyor / rastgele renkler | Seviye sorunu veya gürültü | Diyodun takılı olduğunu, 330 Ω'un MCU'ya yakın olduğunu, 1000 µF'ın bağlı olduğunu doğrula |

### 13.4 Combo testi

| Adım | Beklenen konsol çıktısı | LED2 | ☐ |
|---|---|---|---|
| K10'a bir kez bas (bas-çek) | `EV MODE COMBO_ON` | Turuncu `#FF9500` yanar ve YANIK KALIR | ☐ |
| K2'ye bas-bırak | **Hiçbir şey** (`EV KEY 2` GELMEMELİ) | Turuncu kalır | ☐ |
| K5'e bas | `EV COMBO 2 5` + `EV MODE COMBO_OFF` | Yeşil 150 ms flaş, sonra söner | ☐ |
| K10'u bırak | `EV MODE COMBO_OFF` | Söner | ☐ |
| **Ters sıra:** K10 + K5 sonra K2 | Yine `EV COMBO 2 5` (a<b normalize) | Yeşil flaş | ☐ |
| K10'a tekrar bas, K1+K3 | `EV COMBO 1 3` + `COMBO_OFF` | Yeşil flaş | ☐ |
| K10'a bas, 10 sn bekle | `EV MODE COMBO_OFF` (zaman aşımı) | Turuncu kendiliğinden söner | ☐ |
| K10'a bas, K10'a tekrar bas | `COMBO_ON` + `COMBO_OFF` (iptal) | Turuncu yanar-söner | ☐ |

> **Bu testin en kritik satırı ikinci satırdır.** K10 basılıyken
> K1..K9'un normal `EV KEY` eventleri **gönderilmemelidir** (spec §6.2).
> Geliyorsa firmware combo durum makinesi çalışmıyordur.

### 13.5 OS geçişi testi

| Adım | Beklenen | ☐ |
|---|---|---|
| K11'e kısa bas (< 800 ms) | `EV OS MAC` (veya `EV OS WIN`), **LED1 beyaza** (`#FFFFFF`) döner | ☐ |
| K11'e tekrar kısa bas | `EV OS WIN`, **LED1 maviye** (`#1E90FF`) döner | ☐ |
| USB'yi çek, tekrar tak | Son seçilen OS **korunmuş** olmalı (NVS'e yazıldı) | ☐ |
| K11'i **3 saniye** basılı tut | HID yedek modu değişir, **LED3 üç kez beyaz yanıp söner** | ☐ |
| Konsoldan `CMD OS MAC` | LED1 beyaz olur, `ACK` gelir | ☐ |

### 13.6 Uygulama ile uçtan uca test

1.  `python run_app.py` çalıştır (bkz. `docs/05-UYGULAMA-KULLANIMI.md`).
2.  **LED3 kırmızıdan yeşile döner** (`#2CC985`) — uygulama bağlandı.
3.  Uygulamada `K1`'e `url` → `bluedevelopment.com` ata, **Kaydet**.
4.  Cihazda K1'e bas-bırak → tarayıcıda site açılmalı.
5.  Uygulamayı kapat → **LED3 kırmızıya döner**, cihaz HID yedek moduna
    geçer. Şimdi K1'e basınca `F13` gönderilir.

| Test | Beklenen | ☐ |
|---|---|---|
| Uygulama açık, K1'e bas | Atanan eylem çalışır, LED3 kısa mavi flaş | ☐ |
| Uygulama kapalı, K1'e bas | `F13` gönderilir (bir metin editöründe test et) | ☐ |
| Uygulama kapalı, K10'a bas | **Combo çalışmaz**, LED3 kırmızı yanıp söner | ☐ |
| Uygulama kapalı, enkoderi çevir | Ses **yine çalışır** (HID her zaman aktif) | ☐ |

---

## ADIM 14 — Sünger, kapatma, vidalama, ayak yapıştırma

Tüm testler geçtiyse artık kapatabilirsin.

### 14.1 Son iç kontrol

1.  Tel demetinin plakanın altında, anahtar gövdelerinin altına
    girmediğini doğrula.
2.  Enkoder RC kartının başka bir lehime değmediğini doğrula.
3.  1000 µF kondansatörün kasa kapanınca ezilmediğini kontrol et
    (18 mm iç yükseklik dar olabilir — gerekirse kondansatörü yan yatır).
4.  Hiçbir bileşenin kasanın iç duvarına baskı yapmadığını doğrula.
5.  Tel demetinin son güzergâhına karar ver ve sabitle — süngeri (14.2)
    telleri yerleştirdikten **sonra** koyacaksın, tersi değil.

### 14.2 Sünger (foam) yerleştirme — kapatmadan hemen önce

Bu adım **isteğe bağlı değildir**: MX Blue yüksek sesli bir anahtardır ve
plakanın altında **82.20 × 63.15 × 18.00 mm ≈ 93 cm³** boş hava vardır.
Boş kovuk rezonans odası gibi çalışır; sünger konmazsa tuş sesi
**çınlamalı / boşluklu (hollow, pingy)** çıkar. Gerekçenin tamamı:
`docs/02-MEKANIK-TASARIM.md` §10.4 ve `06-ONEMLI-NOTLAR.md` madde 58a.

**Malzeme:** 3 mm **poron** veya 3 mm **EVA köpük**. Bulamazsan **kaymaz
mutfak dolabı altlığını** (~2–3 mm PVC/EVA ağ köpük) makasla kes — iş görür.

**Kesim ölçüleri.** DevKit yatağı kovuğu üç şeride böler; her parçadan
~1 mm pay bırakılmıştır:

| Parça | Kes | Nereye | Not |
|---|---|---|---|
| **Ön** | **80 × 25 mm** | Kasanın ön iç tabanına (kullanıcıya yakın kenar) | İki köşesinden **8 × 8 mm** kare çentik kes — orada ⌀7.60 vida kuleleri var |
| **Arka** | **80 × 9 mm** | Arka iç tabana | Aynı şekilde iki köşe çentiği |
| **Sol** | **18 × 24 mm** | DevKit'in solundaki boşluğa | Çentik gerekmez |

Toplam ≈ 29 cm², yani kullanılabilir tabanın (~34 cm²) yaklaşık **%85'i**.
Kalan %15'i doldurmaya çalışıp kabloyu sıkıştırma.

**Yapıştırma:**

1.  Kasanın **iç tabanını** izopropil alkolle sil, kurumasını bekle.
2.  Parçaları **taban iç yüzeyine** yapıştır — plakaya değil.
    Kendinden yapışkanlı değilse ince çift taraflı bantla tut.
3.  Kesim şablonunu önce **kâğıttan** yapıp kasaya oturt; kule çentikleri
    tutmuyorsa kâğıtta düzelt, sonra süngeri kes. 2 dakika, bir parça sünger
    kurtarır.

> 🔴 **Süngerin DEĞMEMESİ gerekenler:**
> - **Anahtar gövdeleri ve lehim uçları.** Anahtar + lehim plaka altında
>   ~9 mm yer kaplar; tabana ~9 mm serbest yükseklik kalır. 3 mm süngerle
>   arada **~6 mm hava** olur — doğru olan budur. Sünger anahtara değerse
>   plaka yukarı itilir, vidalar sıkılınca kapak ortadan kabarır ve sünger
>   zamanla lehim uçlarının izolasyonunu aşındırır.
>   **6 mm'den kalın sünger kullanma.**
> - **DevKit'in altı.** Kart 4.00 mm'lik pedlerin üstünde durur; altına
>   sünger girerse kart yükselir ve **USB-C soketi kasadaki açıklıkla
>   hizasını kaybeder**. DevKit yatağını (kasanın sağ-orta bölgesi) tamamen
>   boş bırak.
> - **Tel demetinin güzergâhı.** Sünger telin üstüne binerse kapak kapanmaz.
>   Telleri önce yerleştir, süngeri onların yanına oturt.

4.  **Kuru montaj:** süngerler yerindeyken plakayı vidalamadan üstüne koy.
    Zorlanmadan oturmalı, hiçbir yerde 1–2 mm açık kalmamalı. Kalıyorsa
    süngeri incelt veya küçült — **plakayı zorlama.**

**Hâlâ çınlıyorsa** (kasayı kapattıktan sonra denersin): ön ve arka **iç
duvarlara 2 mm kendinden yapışkanlı keçe** şerit ekle. Sol/sağ duvarlara
gerek yok, oralarda zaten kule ve DevKit var.

> **Beklenti:** Sünger MX Blue'yu **sessiz yapmaz** — tık sesi anahtarın
> içindeki click jacket'ten gelir ve kasadan bağımsızdır. Sünger sesin
> **çınlamalı/boşluklu** kısmını alır; geriye temiz, tok bir "tık" kalır.

> ✅ **KONTROL:** Üç sünger parçası yapışık, DevKit'in altı ve tel koridoru
> boş, plaka vidasız olarak zorlanmadan oturuyor, sünger hiçbir anahtara veya
> lehime değmiyor.

---

### 14.3 Kapatma ve vidalama

1.  Plakayı kasanın üstüne otur. **Zorlamadan** oturmalı; zorluyorsan
    içeride bir şey sıkışıyordur.
2.  Dört M3 × 12 vidayı köşelere tak.
3.  **Vidaları çapraz sırayla** sık: sol-üst → sağ-alt → sağ-üst → sol-alt.
    Bu, plakanın eşit oturmasını sağlar.
4.  Vidaları **elle, tornavidayla, hafif sıkı** kapat. Aşırı sıkmak
    heat-set insert'i plastikten söker — bu geri dönüşü olmayan bir hatadır.
    Direnç hissettiğin noktada dur.

### 14.4 Keycap ve knob takma

1.  Keycap'ları anahtar saplarına dik olarak bastır. "Tık" hissi gelmeli.
2.  Sağ sütundaki iki tuşu (K10 COMBO, K11 OS) **farklı renk** keycap ile
    ayır — kullanırken hangisinin ne olduğunu şaşırmazsın.
3.  Enkoder düğmesini şafta geçir. D-şaftlıysa düzlemi hizala.
    Vidalı knob varsa allen anahtarla sık.
    Düğmenin altındaki **⌀13.00 × 3.20 mm somun havşası** M7 somununun
    üzerine oturur; düğme plakadan 1.00 mm yukarıda durmalıdır. Düğme
    somuna binip yükseliyorsa havşa yok veya sığdır — bkz.
    `docs/02-MEKANIK-TASARIM.md` bölüm 5.3.1.

### 14.5 Ayak yapıştırma

1.  Tabanı izopropil alkolle sil, kurumasını bekle (yağ kalırsa ayaklar
    düşer).
2.  Dört ⌀8 mm kauçuk ayağı tabandaki **⌀8.00 × 1.00 mm çukurlara** otur
    (çukur merkezleri her iki kenardan **10.00 mm** içeridedir). Çukursuz bir
    taban bastıysan aynı konumu ölçüp yapıştır.
3.  Cihazı masaya koy ve **sallanma testi** yap. Sallanıyorsa bir ayağı
    sök, taban düzlüğünü kontrol et, ince bir keçe ile telafi et.
    ℹ️ Silikon ayaklar MX Blue ile **çift görev** yapar: hem cihazın kaymasını
    (madde 57) hem de gövde titreşiminin masaya iletilmesini keser. Çıplak
    taban veya sert plastik ayak, masayı rezonans tablasına çevirir ve
    süngerin kazandırdığının bir kısmını geri verir.
4.  Vidaların kafası dışarı çıkıyorsa ayakları vidaları gizleyecek şekilde
    konumlandırabilirsin.

> ✅ **KONTROL:** Cihaz masada sallanmıyor, kaymıyor. Tüm keycap'lar aynı
> hizada ve dik. Enkoder düğmesi plakaya sürtmüyor, serbest dönüyor.
> USB kablosu kasadaki delikten rahat giriyor.

---

## ADIM 15 — Montaj sonrası kalibrasyon ve ince ayar

### 15.1 Enkoder yönü

Sağa çevirince ses **artmalı**. Ters geliyorsa iki seçeneğin var:

- **Donanım:** GPIO11 ve GPIO12 tellerini yer değiştir (kasayı açman gerekir).
- **Yazılım:** Firmware'de yön ters çevirme ayarı — kasayı açmadan çözülür.
  Tercih edilen yöntem budur.

### 15.2 LED parlaklığı

Varsayılan **60/255**'tir (spec §6.4) ve gözü yormaması için bilinçli
olarak düşük tutulmuştur.

- Aydınlık ofiste LED'ler soluk kalıyorsa 90–120 arasını dene.
- Karanlık odada rahatsız ediciyse 25–40'a düşür.
- **150'nin üzerine çıkma** — hem göz yorar hem toplam akımı 150 mA
  sınırına yaklaştırır.

Ayarı `CMD LED BRIGHT <0-255>` ile dene, beğendiğinde `CMD SAVE` ile
cihazın NVS belleğine yaz. Uygulamadan da **LED & Cihaz** sekmesinden
yapabilirsin.

### 15.3 LED renkleri

Varsayılanlar spec §6.4'tedir. Kişiselleştirmek istersen renk körlüğü
veya ortam ışığı sebebiyle şu değişiklikler faydalı olabilir:

| Durum | Varsayılan | Alternatif öneri |
|---|---|---|
| OS = Windows | `#1E90FF` (mavi) | `#00A2FF` daha doygun |
| OS = macOS | `#FFFFFF` (beyaz) | `#FFE9C4` sıcak beyaz, mavi ile karışmaz |
| Combo açık | `#FF9500` (turuncu) | `#FFC400` sarı, kırmızı-yeşil körlüğünde daha ayırt edici |
| Bağlantı hatası | `#E04F5F` (kırmızı) | `#FF2D55` daha uyarıcı |

### 15.4 Anahtar hissi ve sesi (Cherry MX Blue)

- **Tuş takılıyor / geri gelmiyorsa:** plaka deliği dar, anahtar gövdesi
  sıkışıyordur. Deliği çok az genişlet.
- **Tuş sesi çınlamalı / boşluklu (hollow, pingy) ise:** boş kovuk rezonansı.
  ADIM 14.2'deki süngeri koy veya kalınlığını 3 mm'ye tamamla; silikon
  ayakların takılı olduğunu doğrula. Ayrıntı: `06-ONEMLI-NOTLAR.md` madde 58a.
- **Tık sesinin kendisi çok yüksekse:** bu **anahtarın tasarımıdır**, montajla
  düzeltilemez. Tık, gövdenin içindeki **click jacket**'ten gelir ve kasadan
  bağımsızdır. Sünger yalnızca yankıyı alır, tık'ı almaz. Gerçekten daha sessiz
  bir cihaz istiyorsan anahtarı değiştirmen gerekir (MX Brown taktil / MX Red
  lineer) — bu durumda `firmware/src/config.h` içindeki
  **`EK_KEY_DEBOUNCE_MS`** değerini 8 → 5'e indirebilirsin, plaka ve kasada
  hiçbir değişiklik gerekmez (MX ailesi boyutsal olarak aynıdır).
- **Aynı tuşa çok hızlı iki kez basınca ikincisi kaybolıyorsa:** bu arıza
  değil, MX Blue'nun **0.5 mm histerezisidir** (tetikleme 2.2 mm, sıfırlama
  1.7 mm). Tuşu tam bırak. Debounce'u düşürerek çözmeye çalışma — madde 70a.

### 15.5 Yazılım tarafı ince ayar

1.  Uygulamayı aç, **Ayarlar** > **Profiller**'den işine uygun bir profil
    oluştur (`Video Kurgu`, `Ofis`…).
2.  Hem `windows` hem `mac` taraflarını doldur — yollar farklı olacaktır.
3.  **Ayarlar** > **Dışa Aktar…** ile yapılandırmanı yedekle. Kasayı
    sökmen gerekirse bile ayarların güvende olur.
4.  Enkoder modunu seç: sadece ses kullanacaksan **HID**, özel eylem
    istiyorsan **HOST** (bkz. `docs/05-UYGULAMA-KULLANIMI.md` §8).
5.  `CMD SAVE` ile cihaz içi ayarları (OS modu, enkoder modu, LED renkleri,
    parlaklık) NVS'e kalıcı yaz.

### 15.6 Bir haftalık burn-in

İlk hafta şunlara dikkat et:

| İzlenecek | Sorun belirtisi |
|---|---|
| Tuş çift sayımı | Zamanla artıyorsa anahtar kontağı yıpranıyordur. MX Blue'da click jacket bırakışta ek sıçrama üretir; `config.h` → `EK_KEY_DEBOUNCE_MS` 8 → 12 (madde 22a) |
| Tuş sesi | İlk haftadan sonra çınlama artıyorsa sünger kaymış veya vidalar gevşemiş olabilir (14.2 / 14.3) |
| Enkoder kaçık sayım | RC devresi gevşemiş olabilir |
| Bağlantı kopmaları | Kabloyu değiştir; kopmaya devam ederse USB soketi lehimini kontrol et |
| LED renk kayması | Isınma varsa parlaklığı düşür |
| Kasa gevşemesi | Vidaları çapraz sırayla yeniden hafifçe sık |

---

## Ek A — Tam kablolama özeti (tek sayfa)

```
  ESP32-S3-DevKitC-1 (WROOM-1, N16R8)
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  GPIO4  ──────────── K1  ──┐                             │
  │  GPIO5  ──────────── K2  ──┤                             │
  │  GPIO6  ──────────── K3  ──┤                             │
  │  GPIO7  ──────────── K4  ──┤                             │
  │  GPIO15 ──────────── K5  ──┤                             │
  │  GPIO16 ──────────── K6  ──┤                             │
  │  GPIO17 ──────────── K7  ──┼── ORTAK GND (papatya)       │
  │  GPIO18 ──────────── K8  ──┤        │                    │
  │  GPIO8  ──────────── K9  ──┤        │                    │
  │  GPIO9  ──────────── K10 ──┤        │                    │
  │  GPIO10 ──────────── K11 ──┘        │                    │
  │                                     │                    │
  │  GPIO11 ──[10k→3V3]──┬── ENC_A ─────┤                    │
  │                     ═══ 100nF       │                    │
  │  GPIO12 ──[10k→3V3]──┬── ENC_B ─────┤                    │
  │                     ═══ 100nF       │                    │
  │  GPIO13 ──────────── ENC_SW ────────┤                    │
  │                                     │                    │
  │  GPIO14 ──[330Ω]──► LED1.DIN        │                    │
  │                     LED1.DOUT ──► LED2.DIN               │
  │                                   LED2.DOUT ──► LED3.DIN │
  │                                                          │
  │  VBUS(5V) ──►|1N4148|──┬── LED 5V hattı (≈4.3 V)         │
  │                        │                                 │
  │                    1000µF/10V                            │
  │                        │                                 │
  │  GND ──────────────────┴─────────────┴───────────────────│
  └──────────────────────────────────────────────────────────┘

  YASAK PİNLER: 0, 3, 19, 20, 26-32, 33-37, 43, 44, 45, 46
```

---

## Ek B — Montaj kontrol listesi (yazdır ve tik at)

```
  ADIM 1  ☐ Tüm parçalar sayıldı, eksik yok
          ☐ Anahtarlar 3 PINLI (5 pinliyse 2 plastik ayak kesildi, metal
            pinlere dokunulmadı)
          ☐ 3 mm sünger alındı / kesildi (80×25, 80×9, 18×24 mm)
  ADIM 2  ☐ Destekler temizlendi, 14 mm delikler kontrol edildi
          ☐ Enkoder deliği ⌀7.20, LED pencereleri ⌀3.00 × 3
  ADIM 3  ☐ 4 heat-set insert takıldı, hepsi dik, M3 vida serbest dönüyor
  ADIM 4  ☐ 11 anahtar takıldı, flanşlar plakaya yaslı, hiçbiri eğri değil
            (clicky tık sesine GÜVENME — gözle + elle çek + döndür)
  ADIM 5  ☐ Enkoder somunla sabitlendi, şaft pürüzsüz dönüyor
  ADIM 6  ☐ 3 LED zinciri lehimlendi, DIN/DOUT yönü doğru
          ☐ 1N4148 şeridi LED tarafına bakıyor
          ☐ 1000 µF kutbu doğru
  ADIM 7  ☐ GND papatya dizimi tamam, 11 anahtar + enkoder GND'ye bipliyor
  ADIM 8  ☐ 15 sinyal teli kablolama tablosuna göre çekildi
          ☐ Yasak pinlerin hiçbiri kullanılmadı
  ADIM 9  ☐ 2× 10 kΩ + 2× 100 nF RC devresi kuruldu
  ADIM 10 ☐ DevKit sabitlendi, USB deliği hizalı, kasa vidasız kapanıyor
  ADIM 11 ☐ VBUS↔GND kısa devre YOK
          ☐ 3V3↔GND kısa devre YOK
          ☐ 11 tuşun hepsi basılıyken GND'ye bipliyor
          ☐ Güç sonrası 3V3 = 3.3 V, LED hattı ≈ 4.3 V
  ADIM 12 ☐ Firmware yüklendi, CMD ID yanıt veriyor, HB akıyor
  ADIM 13 ☐ 11 tuş doğru sırada olay üretiyor
          ☐ TEK BASIŞ = TEK EYLEM (10 basış = tam 10 UP; çift tetikleme
            varsa config.h → EK_KEY_DEBOUNCE_MS 8 → 12)
          ☐ Enkoder her iki yön + basış + uzun basış
          ☐ 3 LED ayrı ayrı doğru renkte yanıyor
          ☐ Combo çalışıyor, K10 basılıyken EV KEY GELMİYOR
          ☐ OS geçişi çalışıyor, NVS'e kaydediyor
          ☐ Uygulama bağlanıyor, LED3 yeşil
  ADIM 14 ☐ Sünger taban içine yapıştırıldı; DevKit altı ve tel koridoru boş;
            sünger hiçbir anahtara/lehime değmiyor
          ☐ Kasa çapraz sırayla vidalandı, keycap ve knob takıldı
          ☐ Ayaklar yapıştırıldı, cihaz sallanmıyor
  ADIM 15 ☐ Enkoder yönü doğru, parlaklık ayarlandı, CMD SAVE yapıldı
          ☐ Yapılandırma dışa aktarılarak yedeklendi
```

---

## İlgili dokümanlar

| Doküman | İçerik |
|---|---|
| `docs/00-CEKIRDEK-SPEC.md` | Tek doğruluk kaynağı — pinler, protokol, ölçüler |
| `docs/05-UYGULAMA-KULLANIMI.md` | PC uygulamasının kurulumu ve kullanımı |
| `docs/08-SORUN-GIDERME.md` | Belirti → olası neden → çözüm tablosu |
