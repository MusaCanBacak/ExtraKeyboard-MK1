# ExtraKeyboard MK1 — Sorun Giderme (v3.0.0)

> Belirti → Olası neden → Çözüm biçiminde başvuru tablosu.
> Tüm pin, protokol ve renk bilgileri `docs/00-CEKIRDEK-SPEC.md`
> dosyasından alınmıştır; çelişki durumunda çekirdek spesifikasyon kazanır.

---

## Önce bunu oku — 60 saniyelik teşhis akışı

Herhangi bir soruna dalmadan önce şu dört soruyu cevapla. Sorunların
büyük kısmı burada çözülür.

```
  1) LED1 yanıyor mu?
     HAYIR ─► Cihaz hiç beslenmiyor.        → Bölüm A (1, 2, 3)
     EVET  ─► Cihaz açık, firmware çalışıyor. Devam et.

  2) LED3 hangi renkte?
     KIRMIZI (#E04F5F) ─► Uygulama BAĞLI DEĞİL. → Bölüm F
     YEŞİL   (#2CC985) ─► Uygulama bağlı. Devam et.

  3) Tuşa basınca LED3 kısa MAVİ flaş atıyor mu?
     HAYIR ─► Cihaz tuşu görmüyor.          → Bölüm B / C
     EVET  ─► Cihaz tuşu görüyor. Devam et.

  4) Uygulamanın olay günlüğünde satır görünüyor mu?
     HAYIR ─► Seri iletişim kopuk.           → Bölüm F
     EVET  ─► Eylem çalıştırma tarafında sorun var. → Bölüm G / H / I
```

**Altın kural:** Cihaz mı suçlu yoksa uygulama mı, şu testle ayır:
uygulamayı tamamen kapat (LED3 kırmızıya dönsün), bir metin editörü aç
ve K1'e bas. **`F13` yazılıyorsa donanım sağlamdır**, sorun uygulama
tarafındadır.

**Seri konsolu her zaman kullan.** `pio device monitor -b 115200` ile
cihazın ne gönderdiğini doğrudan görürsün. Uygulama açıkken port meşgul
olacağından önce uygulamayı kapat.

---

## A. Cihaz görünmüyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **1** | Kabloyu taktım, **hiçbir LED yanmıyor**, bilgisayar da hiçbir şey algılamıyor | Kablo **şarj kablosu** — içinde veri damarı yok | Bilinen bir veri kablosuyla dene. Telefonla dosya aktarabildiğin kablo veri kablosudur. |
| **2** | Aynı belirti, kablo veri kablosu | DevKit'in **yanlış USB portuna** takılmışsın | DevKitC-1'de iki USB-C soketi vardır. Normal kullanım için **`USB`** yazan (yerleşik OTG, GPIO19/20) porta tak. `UART` portu yalnızca firmware yükleme içindir. |
| **3** | Güç LED'i yanıyor ama LED1/2/3 sönük, seri port yok | **Firmware yüklü değil** veya cihaz bootloader'da takılı | `UART` portundan `pio run -t upload` ile firmware yükle. Bkz. madde 57–62. |
| **4** | Windows'ta Aygıt Yöneticisi'nde **"Bilinmeyen USB Aygıtı (Aygıt Tanımlayıcı İsteği Başarısız)"** | USB veri hattı sorunu, kablo kalitesi veya hub | Kabloyu doğrudan bilgisayara tak, **hub kullanma**. Farklı bir USB portu dene (arka paneldeki anakart portlarını tercih et). |
| **5** | macOS'ta `ls /dev/cu.usbmodem*` boş dönüyor | Cihaz CDC olarak sayılmamış | USB'yi çıkar, 10 saniye bekle, tekrar tak. Hâlâ yoksa: `system_profiler SPUSBDataType \| grep -A6 "ExtraKeyboard"` ile USB katmanında görünüyor mu bak. |
| **6** | Cihaz bir bilgisayarda görünüyor, diğerinde görünmüyor | Ön panel USB portu yetersiz akım veriyor veya USB 2.0 hub arkasında | Arka paneldeki doğrudan USB portunu kullan. Toplam çekim < 150 mA'dır, normal bir port fazlasıyla yeter — sorun genelde hub'dadır. |

---

## B. Tuş hiç çalışmıyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **7** | **Hiçbir tuş** çalışmıyor, LED'ler normal | Ortak **GND papatya dizimi** kopuk | Multimetre süreklilik modunda DevKit GND ile her anahtarın GND ucu arasında bip olmalı. İlk kopan lehimi bul. Bkz. Montaj Adım 7. |
| **8** | **Tek bir tuş** çalışmıyor, diğerleri sorunsuz | O tuşun GPIO teli kopuk veya lehimi soğuk | Kablolama tablosundan o tuşun GPIO'sunu bul (örn. K5 → **GPIO15**). Tuş basılıyken o GPIO ile GND arasında bip olmalı. Yoksa lehimi yenile. |
| **9** | Tek tuş çalışmıyor, tel sağlam ve süreklilik var | **Anahtarın kendisi arızalı** veya kontağı kirli | Anahtarı sök, iki bacağı arasına multimetreyi bağla, elle bastır — basınca bip ötmeli. Ötmüyorsa anahtarı değiştir. |
| **10** | Tuş bazen çalışıyor bazen çalışmıyor | Soğuk lehim (mat, topaklı görünüm) veya tel çatlağı | Lehimi eritip yeniden yap. Parlak, koni şeklinde bir lehim olmalı. Teli hafifçe oynatırken tuşa bas — davranış değişiyorsa sorun oradadır. |
| **11** | Tuş **sürekli basılı** gibi davranıyor (uygulama durmadan eylem tetikliyor) | GPIO teli GND'ye sürekli değiyor / anahtar mekanik sıkışmış | USB'yi çek, o GPIO ile GND arasında **tuşa basmadan** süreklilik ölç. Bip geliyorsa kısa devre var. Keycap'ı sök, anahtarın serbest hareket ettiğini doğrula. |

> **Tuş *bazen* hiç tetiklenmiyorsa** (özellikle çok hızlı ardışık basışta)
> önce **Bölüm M / madde 92**'ye bak — büyük ihtimalle kablo değil, MX Blue'nun
> **0.5 mm histerezisi**dir.

---

## C. Yanlış tuş tetikleniyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **12** | K1'e basıyorum ama uygulama **K3**'ün eylemini çalıştırıyor | Teller **karışık lehimlenmiş** | Seri konsolu aç, tuşlara tek tek bas, gelen `EV KEY <n>` numarasını not et. Kablolama tablosuyla karşılaştır: K1→GPIO4, K2→GPIO5, K3→GPIO6, K4→GPIO7, K5→GPIO15, K6→GPIO16, K7→GPIO17, K8→GPIO18, K9→GPIO8. Yanlış olanları düzelt. |
| **13** | Tuş sıralaması **tamamen ters** (sol üst = K9) | Plakayı 180° ters monte etmişsin | Kasayı aç, plakayı doğru yönde çevir. Alternatif olarak telleri yeniden dağıtman gerekir — plakayı çevirmek daha kolaydır. |
| **14** | Bir tuşa basınca **iki FARKLI** eylem birden çalışıyor | İki tel birbirine değiyor (izolasyon delinmiş) veya lehim köprüsü var | İki GPIO arasında süreklilik ölç — bip gelmemeli. Kasa kapanırken telin sıkıştığı noktaya bak (Montaj Adım 10.3). |

> **AYNI eylem iki kez çalışıyorsa** bu tel sorunu değildir — anahtar
> sıçramasıdır. **Bölüm M / madde 91**'e git.

---

## D. Enkoder sorunları

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **15** | Enkoderi sağa çeviriyorum, **ses azalıyor** (yön ters) | EC11'in A/B pin sırası üreticiye göre değişir — bu **normaldir** | İki çözüm: (a) firmware'de yön ters çevirme ayarını kullan (kasayı açmadan), (b) `GPIO11` ve `GPIO12` tellerini yer değiştir. |
| **16** | Bir tıkta **iki `EV ENC CW`** geliyor (çift sayım) | **RC debounce devresi yok veya yanlış** | Spec §3.4 gereği RC **zorunludur**. Her kanal için: 3V3 → 10 kΩ → GPIO, GPIO → 100 nF → GND. Değerleri multimetreyle ölç: 3V3-GPIO11 arası ≈ 10 kΩ olmalı. |
| **17** | Çevirirken **rastgele ters yön** olayları geliyor (`CW CW CCW CW`) | RC var ama değerler yanlış (örn. 1 kΩ veya 10 nF) | Dirençlerin renk kodunu doğrula: 10 kΩ = kahverengi-siyah-turuncu-altın. Kondansatörün üzerinde **`104`** yazmalı (100 nF). |
| **18** | Enkoder **hiç çalışmıyor**, `EV ENC` olayı hiç gelmiyor | ENC_A / ENC_B telleri kopuk veya enkoderin ortak ucu GND'ye bağlı değil | EC11'in **3 pinli** tarafında ortadaki pin daima ortak (C) uçtur ve GND'ye gitmelidir. Yanlara A ve B gelir. Bunu doğrula. |
| **19** | Enkoder dönüyor ama **basış (`EV ENC PRESS`) çalışmıyor** | ENC_SW teli GPIO13'e gitmemiş veya buton ucu karışmış | EC11'in **2 pinli** tarafı butondur. Biri GPIO13'e, diğeri GND'ye gitmeli. Şafta basılıyken bu iki pin arasında bip olmalı. |
| **20** | Uygulama açıkken enkoder ses değiştirmiyor ama `EV ENC CW` olayı geliyor | Enkoder **HOST modunda** ve `cw` slotu `none` atanmış | Uygulamada **Enkoder** sekmesinden modu **HID** yap (`CMD ENC MODE HID`), ya da HOST modunda kalıp `cw`/`ccw`/`press` slotlarına `media` eylemi ata. |

---

## E. LED sorunları

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **21** | **Hiçbir LED yanmıyor**, cihaz çalışıyor (seri port var, tuşlar çalışıyor) | **1N4148 diyot ters takılmış** | Diyodun üzerindeki **siyah şerit (katot) LED tarafına** bakmalıdır. Ters takılıysa LED'lere gerilim gitmez. Diyot sonrası 5V hattında **≈ 4.3 V** ölçmelisin. |
| **22** | Hiçbir LED yanmıyor, diyot doğru | **DIN/DOUT yönü ters** bağlanmış | WS2812B tek yönlüdür. GPIO14 → 330 Ω → **LED1.DIN**. Sonra LED1.DOUT → LED2.DIN → LED2.DOUT → LED3.DIN. Son DOUT boşta kalır. Zinciri baştan ölç. |
| **23** | Hiçbir LED yanmıyor, diyot ve yön doğru | Veri hattı kopuk veya 330 Ω direnç eksik/yanlış | GPIO14 ile 330 Ω'un bir ucu, direncin diğer ucu ile LED1.DIN arasında süreklilik olmalı. Direnç renk kodu: turuncu-turuncu-kahverengi-altın. |
| **24** | **Sadece LED1 yanıyor**, LED2 ve LED3 sönük | LED1.DOUT → LED2.DIN bağlantısı kopuk **veya LED1 hasarlı** (veriyi iletmiyor) | Önce o lehimi yenile. Düzelmezse LED1'i değiştir — aşırı ısıtılmış WS2812B kendisi yanar ama veriyi geçirmez. |
| **25** | **İlk iki LED yanıyor**, üçüncü sönük | LED2.DOUT → LED3.DIN kopuk veya LED2 hasarlı | Madde 24'ün aynısı, bir sonraki halka için. |
| **26** | `CMD LED 1 FF0000` gönderiyorum ama **sağdaki** LED yanıyor | Zincir sırası ters — fiziksel LED1 aslında zincirin sonunda | Zinciri yeniden lehimle: soldaki LED **DIN'i GPIO14'ten alan** olmalı. Kasayı açmak istemiyorsan firmware'de indeks eşlemesini ters çevir. |
| **27** | LED'ler **titriyor**, rastgele renkler yanıp sönüyor | Veri seviyesi sınırda (3.3 V < V_IH) veya besleme gürültülü | Üç şeyi doğrula: (a) 1N4148 takılı ve LED hattı **≈ 4.3 V**, (b) 330 Ω direnç **MCU çıkışına yakın**, (c) **1000 µF / 10 V** kondansatör LED besleme uçlarına bağlı. Üçü de spec §3.3 gereği **zorunludur**. |
| **28** | Renkler yanlış — kırmızı istiyorum yeşil yanıyor | LED modülü **RGB** sıralı, firmware **GRB** bekliyor (veya tersi) | Donanım sorunu değildir. Firmware'deki renk sırası ayarını değiştir. Fiziksel bir müdahale gerekmez. |
| **29** | LED'ler çok parlak / göz alıyor | Parlaklık ayarı yüksek | `CMD LED BRIGHT 60` gönder (varsayılan). Uygulamada **LED & Cihaz** sekmesinden kaydırıcıyı kullan. Ayarı kalıcı yapmak için `CMD SAVE`. |
| **30** | Cihazı fişten çekince LED renkleri **varsayılana dönüyor** | Ayarlar NVS'e yazılmamış | Renkleri ayarladıktan sonra `CMD SAVE` gönder veya uygulamada **Cihaza kaydet** düğmesine bas. |
| **31** | LED3 sürekli **kırmızı yanıp sönüyor** | Bu bir hata değil — **HID yedek modunda K10'a bastın** | Uygulama kapalıyken combo devre dışıdır (spec §5.3). Uygulamayı aç, LED3 yeşile döner ve combo çalışmaya başlar. |

---

## F. Uygulama cihaza bağlanmıyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **32** | Durum çubuğu sürekli **"Aranıyor…"** yazıyor, LED3 kırmızı | Cihaz seri port olarak görünmüyor | Önce Bölüm A'yı çöz. macOS: `ls /dev/cu.usbmodem*`, Windows: Aygıt Yöneticisi > Bağlantı Noktaları (COM ve LPT). Port yoksa uygulama hatalı değildir. |
| **33** | Port var ama uygulama bağlanamıyor: **"Erişim reddedildi"** / **"Port meşgul"** | Portu **başka bir program tutuyor** | Şunları kapat: `pio device monitor`, Arduino IDE Seri Monitör, PuTTY/screen, ve **eski v2 uygulaması (`Main.py`)**. Aynı anda yalnızca bir program porta bağlanabilir. |
| **34** | Uygulama bağlanıyor ama 3–5 saniyede bir kopup yeniden bağlanıyor | Kalp atışı (`HB`) gelmiyor — kablo veya güç sorunu | Uygulama 3 saniye `HB` görmezse bağlantıyı kopmuş sayar. Kabloyu değiştir, hub kullanıyorsan çıkar, doğrudan anakart portuna tak. |
| **35** | Uygulama açılışta **"ExtraKeyboard zaten çalışıyor"** diyor ve kapanıyor | Tekil örnek kilidi — `127.0.0.1:64210` portu dolu | Zaten açık bir örnek vardır; tepsi simgesinden pencereyi göster. Örnek yoksa (çöktüyse) portu tutan süreci kapat: macOS `lsof -i :64210`, Windows `netstat -ano \| findstr 64210`. |
| **36** | Uygulama yanlış cihaza bağlanıyor (başka bir seri cihaz) | Otomatik bulma başka bir portu seçti | Uygulama önce `VID 0x303A` / `PID 0x82E1`, bulamazsa `ExtraKeyboard MK1` ürün metni ile arar. Yine de yanılıyorsa **LED & Cihaz** sekmesinden portu **elle** seç. |
| **37** | Uygulama açık, LED3 yeşil, ama **olay günlüğü boş** — tuşa basınca hiçbir satır gelmiyor | Cihaz CDC yerine yalnızca HID gönderiyor olabilir; ya da olaylar filtreleniyor | Uygulamayı kapat, `pio device monitor -b 115200` ile konsolu aç ve tuşa bas. `EV KEY 1 DOWN` görüyorsan sorun uygulamadadır — uygulamayı yeniden başlat. Görmüyorsan firmware/donanım sorunudur. |
| **38** | Uygulama açılırken **"serial modülü bulunamadı"** benzeri hata | Sanal ortam etkin değil veya bağımlılıklar kurulmamış | Sanal ortamı etkinleştir (`source .venv/bin/activate` / `.\.venv\Scripts\Activate.ps1`) ve `pip install -r requirements.txt` çalıştır. Komut satırının başında `(.venv)` görmelisin. |

---

## G. Eylem tetiklenmiyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **39** | Tuşa basıyorum, olay günlüğünde `EV KEY 3 UP` görünüyor ama **hiçbir şey olmuyor** | Slot `none` atanmış | **Tuşlar** sekmesinde K3 kartına bak; `[none]` rozeti varsa bir eylem ata. Olay günlüğünde `K3 atanmamış` satırı da bunu söyler. |
| **40** | Eylem atalı ama çalışmıyor, **hata da vermiyor** (macOS) | **Erişilebilirlik izni yok** | Bu, macOS'ta en sık görülen sorundur. Bölüm H'ye git. Ayırt edici test: `app` ve `url` çalışıyor ama `shortcut` çalışmıyorsa kesinlikle izin sorunudur. |
| **41** | Eylem **yanlış OS profilinden** çalışıyor (Windows'ta `/Applications/...` deneniyor) | OS anahtarı yanlış tarafta | Durum çubuğundaki **OS:** göstergesini kontrol et. Yanlışsa uygulamadan değiştir veya cihazda **K11**'e kısa bas. LED1: Windows mavi `#1E90FF`, macOS beyaz `#FFFFFF`. |
| **42** | `app` tipi çalışmıyor: **"dosya bulunamadı"** | Yol yanlış veya uygulama taşınmış | **Gözat…** düğmesiyle yolu yeniden seç. macOS'ta `.app` paketinin kendisini seç, içindeki ikiliyi değil. Windows'ta tam `.exe` yolunu ver. |
| **43** | `url` tipi yanlış adrese gidiyor | Şema eksikliği yanlış yorumlanmış | Uygulama şema yoksa `https://` ekler. `bluedevelopment.com` → `https://bluedevelopment.com`. Farklı bir şema (`http://`, `slack://`) istiyorsan **tam olarak yaz**. |
| **44** | `shortcut` yanlış tuşa basıyor (macOS'ta Elma yerine Control) | Kısayol normalizasyonu | macOS profilinde `ctrl` **olduğu gibi kalır** — Elma tuşu için **`command`** yazmalısın. Windows profilinde `command`/`cmd` otomatik `ctrl`'ye çevrilir (spec §7.2). |
| **45** | `text` tipinde **Türkçe karakterler eksik** yazılıyor (`ç ğ ı ö ş ü İ`) | `pyautogui` bazı klavye düzenlerinde bu karakterleri atlar | Uzun Türkçe metinler için `text` yerine şu yolu kullan: metni panoya kopyalayan bir `command` + `macro` ile `ctrl+v` / `command+v`. |
| **46** | `macro` sadece ilk adımı çalıştırıyor | Ayraç yanlış veya bekleme değeri geçersiz | Adımlar **`\|`** (dikey çizgi) ile ayrılır, bekleme **milisaniye** sayısıdır: `ctrl+c\|500\|ctrl+v`. Boşluk bırakma, tırnak koyma. |
| **47** | `macro` çalışırken tuşa tekrar bastım, hiçbir şey olmadı | Makro yeniden girişi engellenir (bilinçli tasarım) | Olay günlüğünde `makro zaten çalışıyor` satırı görünür. Makronun bitmesini bekle. Bekleme sürelerini kısaltmayı düşün. |
| **48** | `command` tipi çalışmıyor ama terminalde aynı komut çalışıyor | Ortam değişkenleri (`PATH`) farklı | Komutta **tam yol** kullan (örn. `/usr/bin/say merhaba`, `C:\Windows\System32\shutdown.exe /h`). Uygulamanın kabuk ortamı, oturum açtığın terminalin ortamı değildir. |
| **49** | `media` tipi Windows'ta `next`/`prev` çalışmıyor | Aktif medya oturumu yok | Medya tuşları yalnızca dinleyen bir uygulama varken iş görür (Spotify, tarayıcı medya oturumu). Enkoderin **HID modunu** kullanmak daha güvenilirdir — o donanımdan gider. |

---

## H. macOS izin sorunları

> **Bu bölümün tamamı tek bir belirtiye çıkar: eylem sessizce çalışmaz.**
> macOS ne uygulamaya ne de sana hata gösterir. Uygulama "başarılı" der,
> ekranda hiçbir şey olmaz.

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **50** | `shortcut`, `text`, `macro`, `media` çalışmıyor; `app`, `url`, `file`, `folder`, `command` çalışıyor | **Erişilebilirlik izni verilmemiş** | Sistem Ayarları > **Gizlilik ve Güvenlik** > **Erişilebilirlik** > **+** ile **Terminal**'i (veya uygulamayı başlatan programı) ekle ve anahtarı aç. |
| **51** | İzni verdim, hâlâ çalışmıyor | **Uygulama yeniden başlatılmadı** | macOS izinleri **süreç başlangıcında** okur. Uygulamayı **ve Terminal'i** tamamen kapat (`⌘Q`, sadece sekmeyi değil), yeniden aç. Bu adım zorunludur ve en sık atlanandır. |
| **52** | Yeniden başlattım, hâlâ çalışmıyor | **Yanlış uygulamaya izin verilmiş** | İzni `run_app.py` değil, **Python'u başlatan program** alır: Terminal'den başlattıysan Terminal, PyCharm'dan başlattıysan PyCharm, VS Code'dan başlattıysan Code. Listede `.venv/bin/python3.11` de görünüyorsa **onu da** işaretle. |
| **53** | İzin listede **açık görünüyor** ama sistem tanımıyor | macOS izin veritabanı bozulmuş (bilinen bir sorun) | Listeden uygulamayı **−** ile kaldır, **+** ile yeniden ekle, oturumu kapatıp aç. Çözülmezse: `tccutil reset Accessibility` (tüm uygulamaların iznini sıfırlar, hepsini yeniden vermen gerekir). |
| **54** | *"Terminal, bu bilgisayarda yazdığınız tuşları izlemek istiyor"* kutusunu yanlışlıkla reddettim | **Girdi İzleme izni** reddedildi; kutu bir daha çıkmaz | Sistem Ayarları > **Gizlilik ve Güvenlik** > **Girdi İzleme** > uygulamayı ekle ve aç, sonra uygulamayı yeniden başlat. |
| **55** | Otomatik başlatmada çalışıyor ama tuşlar iş görmüyor | LaunchAgent, Terminal'i değil **doğrudan Python'u** çalıştırır | Erişilebilirlik ve Girdi İzleme izinlerini `.venv/bin/python3.11` ikilisine de ver. Bkz. `docs/05-UYGULAMA-KULLANIMI.md` §12.1. |
| **56** | Cihazı ilk taktığımda **Klavye Tanımlama Asistanı** açıldı, hangi tuşa basacağımı bilmiyorum | macOS yeni bir HID klavye gördüğünde düzen sorar | Pencereyi kapat (kırmızı nokta) — cihaz yine sorunsuz çalışır. İstersen **Devam** > **ANSI (ABD)** düzenini elle seç. |
| **57** | `F13`–`F15` tuşları beklemediğim şeyler yapıyor | macOS bu kodları tarihsel olarak Print Screen / Scroll Lock / Pause olarak yorumlayabilir | Kritik kısayollar için `F16`–`F21` aralığını tercih et. Bkz. `docs/05-UYGULAMA-KULLANIMI.md` §14. |

---

## I. Windows sorunları

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **58** | Kısayollar normal uygulamalarda çalışıyor ama **Görev Yöneticisi / regedit / yönetici PowerShell**'de çalışmıyor | **UIPI** — normal yetkili süreç, yükseltilmiş pencereye tuş gönderemez | Uygulamayı **yönetici olarak** çalıştır: PowerShell'e sağ tık > Yönetici olarak çalıştır. Bu Windows'un güvenlik tasarımıdır, uygulamanın hatası değildir. |
| **59** | `.exe` çalıştırınca **"Windows bilgisayarınızı korudu"** uyarısı | **SmartScreen** — imzasız uygulama | **Ek bilgi** > **Yine de çalıştır**. ZIP'ten çıkardıysan dosyaya sağ tık > **Özellikler** > **Engellemeyi kaldır**. Kaynak koddan `python run_app.py` ile çalıştırırsan SmartScreen devreye girmez. |
| **60** | PowerShell **"bu sistemde betik çalıştırma devre dışı"** diyor | Yürütme ilkesi kısıtlı | Tek seferlik: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, sonra `.\.venv\Scripts\Activate.ps1`. Alternatif: `cmd.exe` + `activate.bat`. |
| **61** | Antivirüs uygulamayı karantinaya aldı | `pyautogui` tuş gönderdiği için "keylogger benzeri" davranış işaretlenmiş | Proje klasörünü antivirüs istisnalarına ekle. Windows Defender bugüne kadar sorun çıkarmamıştır; sorun genelde üçüncü parti antivirüslerdedir. |
| **62** | Aygıt Yöneticisi'nde COM portu **sarı ünlem** ile görünüyor | Sürücü yüklenememiş | Aygıta sağ tık > **Aygıtı kaldır** > USB'yi çıkar-tak. Windows dahili `usbser.sys` sürücüsünü kendisi bağlar. **CH340/CP2102 sürücüsü kurma** — bu cihaz onları kullanmaz. |
| **63** | Tepsi simgesi görünmüyor | Windows simgeyi taşma menüsüne gizlemiş | Görev çubuğundaki **^** okuna tıkla, simgeyi bulup görev çubuğuna sürükle. Ya da Ayarlar > Kişiselleştirme > Görev çubuğu > Sistem tepsisi simgeleri. |
| **64** | Uygulama yönetici olarak çalışırken **sürükle-bırak ve tepsi menüsü tuhaf davranıyor** | UIPI kısıtları yönetici süreçlere de yansır | Gerçekten yönetici gerekmiyorsa (çoğu durumda gerekmez) normal kullanıcı olarak çalıştır. Sadece yükseltilmiş pencerelere tuş göndermen gerekiyorsa yönetici kullan. |

---

## J. Combo çalışmıyor

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **65** | K10'a basınca **LED2 turuncu yanmıyor**, `EV MODE COMBO_ON` gelmiyor | K10'un **GPIO9** teli kopuk veya lehimi soğuk | K10 basılıyken GPIO9 ile GND arasında süreklilik olmalı. Bkz. madde 8. |
| **66** | LED2 turuncu yanıyor ama **combo tetiklenmiyor** | Combo o slotta `none` atanmış | Uygulamada **Combolar** sekmesine git, ilgili hücreyi (örn. `C_2_5`) bul ve eylem ata. Olay günlüğünde `EV COMBO 2 5` görünüyorsa cihaz doğru çalışıyordur. |
| **67** | K10 basılıyken normal tuşlar da eylem tetikliyor | Firmware combo durum makinesi çalışmıyor | Spec §6.2 gereği K10 basılıyken K1..K9'un `EV KEY` eventleri **gönderilmemelidir**. Konsolda K10 basılıyken K2'ye bas — `EV KEY 2` geliyorsa firmware'i güncelle. |
| **68** | Combo çalışıyor ama **ters kombinasyonu** tetikliyor (`C_5_2` bekliyorum) | `C_5_2` diye bir slot **yoktur** | Combolar daima `a < b` olarak normalize edilir. `2+5` ve `5+2` **aynı** slottur: `C_2_5`. 36 combo, 9×9'un üst üçgenidir. |
| **69** | Uygulama kapalıyken combo hiç çalışmıyor, **LED3 kırmızı yanıp sönüyor** | Bu bir hata değil — HID yedek modunda combo **devre dışıdır** (spec §5.3) | Combo kullanmak için uygulamanın açık olması gerekir. Uygulamayı aç, LED3 yeşile döner. |
| **70** | Üç tuşa aynı anda basınca bazıları algılanmıyor | Ghosting sanılan bir sorun — ama bu tasarımda **ghosting yoktur** | Matris ve diyot yoktur; her tuş kendi GPIO'sundadır (spec §3.1). Belirti gerçekse sorun tellerdedir: iki tel birbirine değiyor olabilir (madde 14). |
| **71** | Combo tetikleniyor ama LED2 **yeşil flaş atmıyor** | LED2 hasarlı veya zincir kopuk | `CMD LED 2 00FF00` gönder — yanmıyorsa donanım sorunudur, Bölüm E'ye git. |

---

## K. Yapılandırma kayboldu / bozuldu

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **72** | Tüm atamalarım kayboldu, her şey `none` | Uygulama farklı bir çalışma dizininden başlatıldı, `config.json`'u bulamadı ve **yeni bir tane üretti** | `config.json` **proje kökünde** aranır. Uygulamayı her zaman proje kökünden başlat: `cd <proje kökü> && python run_app.py`. Eski dosyayı diskte ara: macOS `find ~ -name "config.json" -newermt "-30 days"`. |
| **73** | Uygulama açılışta **"yapılandırma okunamadı"** diyor | `config.json` bozulmuş (elle düzenlenirken geçersiz JSON yazılmış) | Dosyayı bir JSON doğrulayıcıda kontrol et (eksik virgül, fazla virgül, kapanmamış tırnak). Düzeltemiyorsan `config.json.bak` yedeğinden geri dön veya dosyayı silip yeniden oluşmasını sağla. |
| **74** | Ayarları değiştirdim ama kaydolmuyor | Dosya **salt okunur** veya klasörde yazma izni yok | Dosya izinlerini kontrol et. macOS: `ls -l config.json`, gerekirse `chmod u+w config.json`. Windows: Özellikler > **Salt okunur** kutusunun işaretini kaldır. Uygulama atomik yazma yapar (`.tmp` + `os.replace`); klasöre yazamıyorsa hiç yazamaz. |
| **75** | Eski v2 ayarlarım taşınmadı | `config.json` **zaten vardı**, otomatik taşıma yalnızca dosya yokken çalışır | Elle taşı: **Ayarlar** > **v2 ayarlarını içe aktar…** > `macro_config.json` seç. Ya da `python tools/migrate_v2_config.py macro_config.json config.json`. |
| **76** | Taşıma sonrası **combo ve enkoder slotları boş** | v2'de combo ve enkoder **yoktu** — taşınacak veri yok | Bu beklenen davranıştır. v2 yalnızca `F13`–`F20`'yi biliyordu; bunlar `K1`–`K8`'e taşınır, gerisi `none` olarak oluşturulur. |
| **77** | İçe aktardığım profil hiçbir şey yapmıyor | Profil karşı OS tarafını dolduruyor olabilir | Dışa aktarılan dosya hem `windows` hem `mac` taraflarını taşır. Durum çubuğundaki **OS:** göstergesinin doğru tarafta olduğundan emin ol. |
| **78** | Başkasından gelen `config.json`'u içe aktarmaya çekiniyorum | Haklısın — `command` tipi **her şeyi çalıştırabilir** | Uygulama içe aktarma öncesi `command` içeren slotları sarı uyarı panelinde listeler. Onaylamadan önce hepsini oku. Tanımadığın komut varsa içe aktarma. |
| **79** | Aktif profili sildim, uygulama karıştı | Son profil silinemez ama aktif profil silinebilir | Aktif profili silersen listedeki ilk profil aktif olur. **Ayarlar** > **Profiller**'den doğru profili seç. Yedeğin varsa **İçe Aktar…** ile geri yükle. |

---

## L. Firmware yükleme hataları

| # | Belirti | Olası neden | Çözüm |
|---|---|---|---|
| **80** | `pio run -t upload` **"Connecting…"** aşamasında takılıyor, sonra zaman aşımı | Cihaz bootloader moduna girmemiş | Elle bootloader'a al: **BOOT** düğmesini basılı tut → **RESET (EN)**'e bir kez bas ve bırak → **BOOT**'u bırak → yüklemeyi tekrar başlat. |
| **81** | Yükleme sırasında **"Serial port busy" / "Access denied"** | Port başka bir programda açık | `pio device monitor`, Arduino IDE, PuTTY/screen ve **ExtraKeyboard uygulamasını** kapat. |
| **82** | Yükleme **`UART` portundan** olmuyor | Yanlış porta bağlanmışsın | DevKitC-1'de iki USB-C soketi var. Firmware yükleme için **`UART`** yazan sokete tak. Normal kullanım için `USB` soketi. |
| **83** | Yükleme başarılı ama cihaz **hiç açılmıyor / sürekli yeniden başlıyor** | **Yasak bir GPIO** kullanılmış (boot strapping) | Spec §3.2'yi kontrol et: **GPIO0, 3, 19, 20, 26–32, 33–37, 43, 44, 45, 46** kullanılamaz. Özellikle **GPIO0 veya 46 açılışta LOW ise** cihaz bootloader'a düşer. Bir anahtar telini yanlışlıkla oraya bağlamış olabilirsin. |
| **84** | Cihaz açılıyor ama seri konsolda **boot loop / panic** mesajları akıyor | PSRAM/Flash pinlerine (26–37) müdahale edilmiş veya yanlış kart profili seçilmiş | Kablolamayı kontrol et. `platformio.ini`'de kartın **ESP32-S3-DevKitC-1 N16R8** olarak tanımlandığından emin ol (16 MB flash, 8 MB Octal PSRAM). |
| **85** | Yükleme sonrası cihaz **klavye olarak görünmüyor**, sadece seri port var | USB modu yanlış — yerleşik USB OTG yerine UART köprüsü kullanılıyor | Kabloyu **`USB`** soketine tak. HID + CDC composite yalnızca yerleşik USB OTG (GPIO19/20) üzerinden çalışır. |
| **86** | Cihaz klavye olarak görünüyor ama **CDC seri portu yok** | Composite tanım eksik | Cihaz `HID Keyboard` + `HID Consumer Control` + `CDC-ACM` olarak sayılmalıdır (spec §4). Firmware'i yeniden derleyip yükle; `platformio.ini`'de USB ayarlarını doğrula. |
| **87** | Windows cihazı yanlış VID/PID ile tanıyor / eski tanımı hatırlıyor | Windows USB aygıt önbelleği | Aygıt Yöneticisi > **Gizli aygıtları göster** > eski ExtraKeyboard girdilerini kaldır > USB'yi çıkar-tak. Beklenen kimlik: **VID `0x303A`**, **PID `0x82E1`**, Product `ExtraKeyboard MK1`. |
| **88** | `CMD ID` yanıt vermiyor ama `HB` satırları akıyor | Komutun satır sonu eksik | Komutlar `\n` (LF) ile bitmelidir. Seri konsolda satır sonu ayarını **LF** yap (CR veya CRLF değil). Ayrıca komutlar **büyük harftir**. |
| **89** | Gönderdiğim komut hiçbir yanıt vermiyor, `ERR` bile gelmiyor | Komut tanınmıyor — bilinmeyen satırlar **sessizce yok sayılır** (spec §5) | Yazımı kontrol et: `CMD PING`, `CMD LED 1 1E90FF`, `CMD ENC MODE HID`. Alanlar **tek boşlukla** ayrılır, renk `#` olmadan 6 hane hex'tir. |
| **90** | `CMD SAVE` gönderiyorum ama ayarlar fişten çekince kayboluyor | NVS yazma başarısız veya `ACK` gelmedi | Konsolda `ACK SAVE` görmelisin. `ERR` geliyorsa NVS bölümü dolu/bozuk olabilir; `pio run -t erase` ile flash'ı temizleyip firmware'i yeniden yükle (**bu tüm cihaz ayarlarını siler**). |

---

## Hızlı ölçüm başvurusu

Multimetreyi eline aldığında bakacağın değerler:

| Ölçüm noktası | Beklenen değer | Sapma anlamı |
|---|---|---|
| VBUS ↔ GND (süreklilik, güç yokken) | **BİP YOK** | 🔴 Kısa devre — güç verme |
| 3V3 ↔ GND (süreklilik, güç yokken) | **BİP YOK** | 🔴 Kısa devre |
| VBUS ↔ GND (DC gerilim) | 4.75 – 5.25 V | Düşükse kablo/port zayıf |
| 3V3 ↔ GND (DC gerilim) | 3.25 – 3.35 V | Düşükse aşırı yük veya kısa |
| 1N4148 sonrası LED 5V | **≈ 4.3 V** | 5.0 V = diyot atlanmış · 0 V = diyot ters |
| GPIO ↔ GND, tuş basılı **değil** | ≈ 3.3 V | 0 V = tel GND'ye kısa |
| GPIO ↔ GND, tuş **basılı** | ≈ 0 V | 3.3 V = tel kopuk / anahtar arızalı |
| 3V3 ↔ GPIO11 (direnç) | ≈ 10 kΩ | Yoksa RC devresi eksik |
| 3V3 ↔ GPIO12 (direnç) | ≈ 10 kΩ | Yoksa RC devresi eksik |
| GPIO14 ↔ LED1.DIN (direnç) | ≈ 330 Ω | Yoksa seri direnç eksik/kopuk |

---

## Pin başvurusu (sorun ararken elinin altında olsun)

| Sinyal | GPIO | | Sinyal | GPIO |
|---|---|---|---|---|
| K1 | **4** | | K9 | **8** |
| K2 | **5** | | K10 (COMBO) | **9** |
| K3 | **6** | | K11 (OS) | **10** |
| K4 | **7** | | ENC_A | **11** |
| K5 | **15** | | ENC_B | **12** |
| K6 | **16** | | ENC_SW | **13** |
| K7 | **17** | | LED_DATA | **14** |
| K8 | **18** | | | |

**YASAK:** 0, 3, 19, 20, 26–32, 33–37, 43, 44, 45, 46

---

## Protokol başvurusu

**Cihaz → PC:**
`EV KEY <n> DOWN/UP` · `EV COMBO <a> <b>` · `EV MODE COMBO_ON/COMBO_OFF` ·
`EV OS WIN/MAC` · `EV ENC CW/CCW/PRESS/LONG` · `HB <uptime_ms>` ·
`ID <fw> <hw> <serial> <os>` · `ACK <komut>` · `ERR <sebep>`

**PC → Cihaz:**
`CMD ID` · `CMD PING` · `CMD OS WIN/MAC` · `CMD LED <i> <RRGGBB>` ·
`CMD LED BRIGHT <0-255>` · `CMD ENC MODE HID/HOST` · `CMD HIDFB ON/OFF` ·
`CMD SAVE`

**LED anlamları:**
LED1 = OS (Windows `#1E90FF` / macOS `#FFFFFF`) ·
LED2 = Combo (açık `#FF9500` / tetiklendi `#2CC985`) ·
LED3 = Bağlantı (bağlı `#2CC985` / yok `#E04F5F` / tuş flaşı `#3B8ED0`)

---

## Hâlâ çözemedin mi? — Bilgi toplama listesi

Yardım isterken şunları hazır et; sorunun yarısı bu listeyi doldururken
çözülür:

1.  **`CMD ID` çıktısı** (örn. `ID 3.0.0 MK1 EK1-A4C138 WIN`)
2.  **Üç LED'in o anki rengi**
3.  **Seri konsol çıktısı** — sorunu yaratan eylemi yaparken alınan 20 satır
4.  **Uygulamanın olay günlüğü** — aynı anın ekran görüntüsü
5.  **İşletim sistemi ve sürümü** (örn. macOS 15.2, Windows 11 23H2)
6.  **Python sürümü** (`python --version`)
7.  **`config.json`'un ilgili bölümü** — `command` tipindeki değerleri
    paylaşmadan önce hassas bilgi içerip içermediğini kontrol et
8.  **Uygulamayı nasıl başlattığın** (Terminal / PyCharm / kısayol / otomatik)
9.  **macOS ise:** Erişilebilirlik ve Girdi İzleme listelerinin ekran görüntüsü
10. **Ne zamandan beri:** İlk montajdan beri mi, yoksa çalışırken mi bozuldu?

---

## İlgili dokümanlar

| Doküman | İçerik |
|---|---|
| `docs/00-CEKIRDEK-SPEC.md` | Tek doğruluk kaynağı — pinler, protokol, şema |
| `docs/05-UYGULAMA-KULLANIMI.md` | Kurulum, izinler, arayüz, eylem tipleri |
| `docs/07-MONTAJ-KILAVUZU.md` | Adım adım montaj ve fonksiyonel test listesi |
