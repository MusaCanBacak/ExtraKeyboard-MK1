# ExtraKeyboard MK1 — Uygulama Kullanım Kılavuzu (v3.0.0)

> Bu doküman PC uygulamasının (`run_app.py`) kurulumunu, izinlerini ve
> günlük kullanımını anlatır. Tüm pin, protokol, slot ve şema bilgileri
> `docs/00-CEKIRDEK-SPEC.md` dosyasından alınmıştır; bir çelişki görürsen
> çekirdek spesifikasyon kazanır.

**Temel felsefe:** Mantık cihazda değil PC'dedir. Cihaz sadece
"hangi tuşa basıldı" bilgisini gönderir (`EV KEY 3 UP` gibi), "ne yapılacağına"
bu uygulama karar verir. Bu yüzden uygulama kapalıyken cihaz **HID yedek moduna**
düşer ve tuşlar sadece `F13…F22` gönderir.

---

## İçindekiler

1. [Kurulum](#1-kurulum)
2. [macOS izin ayarları (kritik)](#2-macos-izin-ayarları-kritik)
3. [Windows'a özel notlar](#3-windowsa-özel-notlar)
4. [İlk açılış](#4-i̇lk-açılış)
5. [Arayüz turu](#5-arayüz-turu)
6. [Tuş atama ve eylem tipleri](#6-tuş-atama-ve-eylem-tipleri)
7. [Combo kullanımı](#7-combo-kullanımı)
8. [Enkoder ayarları](#8-enkoder-ayarları)
9. [OS değiştirme](#9-os-değiştirme)
10. [Profil yönetimi](#10-profil-yönetimi)
11. [LED özelleştirme](#11-led-özelleştirme)
12. [Otomatik başlatma ve tepsi](#12-otomatik-başlatma-ve-tepsi)
13. [Eski v2 ayarlarını içe aktarma](#13-eski-v2-ayarlarını-i̇çe-aktarma)
14. [Klavye kısayolu çatışma tablosu (F13–F24)](#14-klavye-kısayolu-çatışma-tablosu-f13f24)

---

## 1. Kurulum

### 1.1 Ön koşullar

| Gereksinim | Sürüm / Not |
|---|---|
| Python | **3.11 veya üzeri** (3.11 / 3.12 test edildi) |
| İşletim sistemi | Windows 10/11 (64 bit) veya macOS 12 Monterey ve üzeri |
| USB | Doğrudan bilgisayara bağlı USB-C **veri** kablosu (sadece şarj kablosu olmaz) |
| Disk | ~200 MB (sanal ortam + bağımlılıklar) |

Python sürümünü kontrol et:

```bash
python3 --version      # macOS / Linux
python --version       # Windows
```

Çıktı `Python 3.11.x` veya üzeri değilse önce Python'u güncelle
(<https://www.python.org/downloads/>).

---

### 1.2 Kurulum — macOS

```bash
# 1) Proje klasörüne gir
cd ~/ExtraKeyboard-MK1

# 2) Sanal ortam oluştur
python3 -m venv .venv

# 3) Sanal ortamı etkinleştir
source .venv/bin/activate
#   (fish kabuğu kullanıyorsan: source .venv/bin/activate.fish)

# 4) pip'i güncelle
python -m pip install --upgrade pip

# 5) Bağımlılıkları kur
pip install -r requirements.txt

# 6) Uygulamayı başlat
python run_app.py
```

Komut isteminin başında `(.venv)` yazısını görüyorsan sanal ortam etkindir.
Terminali kapatıp açtığında 3. adımı tekrar çalıştırman gerekir.

> **Apple Silicon (M1/M2/M3/M4) notu:** Bağımlılıkların tamamı arm64 için
> hazır tekerlek (wheel) olarak gelir; Rosetta gerekmez. Eğer Homebrew Python
> yerine sistem Python'u (`/usr/bin/python3`) kullanıyorsan Tkinter'ın
> yüklü olduğundan emin ol — değilse `brew install python-tk@3.11` çalıştır.

---

### 1.3 Kurulum — Windows

PowerShell'i **normal kullanıcı** olarak aç (yönetici gerekmez):

```powershell
# 1) Proje klasörüne gir
cd $env:USERPROFILE\ExtraKeyboard-MK1

# 2) Sanal ortam oluştur
python -m venv .venv

# 3) Sanal ortamı etkinleştir
.\.venv\Scripts\Activate.ps1

# 4) pip'i güncelle
python -m pip install --upgrade pip

# 5) Bağımlılıkları kur
pip install -r requirements.txt

# 6) Uygulamayı başlat
python run_app.py
```

**"Bu sistemde betik çalıştırma devre dışı" hatası alırsan** (PowerShell
yürütme ilkesi), tek seferlik olarak:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternatif olarak klasik komut istemi (`cmd.exe`) kullanıp
`.\.venv\Scripts\activate.bat` çalıştırabilirsin.

> **Sürücü gerekmez.** Cihaz ESP32-S3'ün yerleşik USB OTG çevre birimini
> kullanır; Windows'un dahili `usbser.sys` sürücüsü otomatik bağlanır.
> CH340/CP2102 sürücüsü kurmana **gerek yoktur**.

---

### 1.4 Kısayol oluşturma (isteğe bağlı)

**macOS** — `~/ExtraKeyboard.command` adında dosya oluştur, içine:

```bash
#!/bin/bash
cd "$HOME/ExtraKeyboard-MK1"
source .venv/bin/activate
python run_app.py
```

Sonra `chmod +x ~/ExtraKeyboard.command`. Çift tıklayarak açabilirsin.

**Windows** — `ExtraKeyboard.bat` adında dosya oluştur:

```bat
@echo off
cd /d "%USERPROFILE%\ExtraKeyboard-MK1"
call .venv\Scripts\activate.bat
pythonw run_app.py
```

`pythonw.exe` kullanıldığında arkada siyah konsol penceresi açılmaz.

---

## 2. macOS izin ayarları (KRİTİK)

> **Bu bölümü atlarsan uygulama açılır, cihaza bağlanır, LED'ler çalışır —
> ama hiçbir tuş atamanız çalışmaz ve size hata da göstermez.**
> macOS'ta tuş gönderme (`pyautogui`) işletim sistemi tarafından sessizce
> engellenir; ne uygulama ne de sistem bir uyarı üretir. Belirti tam olarak
> şudur: "Uygulama bağlı görünüyor, LED3 yeşil, olay günlüğünde
> `EV KEY 3 UP` görünüyor ama ekranda hiçbir şey olmuyor."

### 2.1 Hangi uygulamaya izin verilecek?

İzni **Python yorumlayıcısını başlatan program** alır, `run_app.py` değil.
Yani:

| Uygulamayı nasıl başlattın? | İzin verilecek uygulama |
|---|---|
| Terminal.app'ten `python run_app.py` | **Terminal** |
| iTerm2'den | **iTerm** |
| PyCharm'ın Run düğmesinden | **PyCharm** |
| VS Code'un entegre terminalinden | **Code** (Visual Studio Code) |
| `.command` dosyasına çift tıklayarak | **Terminal** |
| Paketlenmiş `.app` olarak | **ExtraKeyboard** |

Sanal ortamdaki `python` ikilisi de listede görünebilir
(`.venv/bin/python3.11`). İkisi de görünüyorsa **ikisini de** işaretle.

### 2.2 Erişilebilirlik izni (Accessibility) — ZORUNLU

`pyautogui`'nin tuş basma, kısayol gönderme ve metin yazma işlemleri için
**mutlaka** gereklidir. Bu izin olmadan `shortcut`, `text`, `macro` ve
`media` eylem tipleri çalışmaz.

1.  Menü çubuğundan  > **Sistem Ayarları…**
2.  Sol taraftan **Gizlilik ve Güvenlik**
3.  Sağda aşağı kaydır → **Erişilebilirlik**
4.  Listede **Terminal** (veya 2.1'deki karşılığı) yoksa:
    - Sol alttaki **+** düğmesine bas
    - Açılan Finder penceresinde `⌘⇧G` (Klasöre Git) ile
      `/System/Applications/Utilities/` yolunu yaz → **Terminal.app**'i seç
    - PyCharm için `/Applications/PyCharm.app`
5.  Uygulamanın yanındaki anahtarı **açık** konuma getir
6.  Parolanı / Touch ID'ni onayla

### 2.3 Girdi İzleme izni (Input Monitoring)

Uygulamanın klavye olaylarını izlemesi ve bazı düşük seviyeli tuş
gönderimleri için gereklidir. Aynı yolu izle:

1.   > **Sistem Ayarları…** > **Gizlilik ve Güvenlik**
2.  **Girdi İzleme** (Input Monitoring)
3.  Aynı uygulamayı ekle ve anahtarı **aç**

> macOS bu izni bazen kendisi ister: ekranda
> *"Terminal, bu bilgisayarda yazdığınız tuşları izlemek istiyor"*
> şeklinde bir kutu çıkarsa **İzin Ver**'e bas. Kutuyu yanlışlıkla
> reddettiysen izni yukarıdaki yoldan elle vermelisin, kutu bir daha çıkmaz.

### 2.4 İzin verdikten sonra UYGULAMAYI YENİDEN BAŞLAT

> **Bu adım zorunludur ve en sık atlanan adımdır.**

macOS, Erişilebilirlik ve Girdi İzleme izinlerini **süreç başlangıcında**
okur. Uygulama açıkken izni versen bile o çalışan süreç izni almaz.

1.  ExtraKeyboard uygulamasını tamamen kapat (tepside de kalmasın —
    tepsi simgesine sağ tık > **Çıkış**)
2.  Terminal penceresini de kapat (`⌘Q`, sadece sekmeyi değil **uygulamayı**)
3.  Terminali yeniden aç, sanal ortamı etkinleştir, `python run_app.py`

macOS bazı sürümlerde iznin listede açık görünmesine rağmen uygulamayı
tanımaz. Bu durumda listeden uygulamayı **−** ile kaldır, **+** ile yeniden
ekle, sonra oturumu kapatıp aç.

### 2.5 İzin verilmezse tam olarak ne olur?

| Eylem tipi | İzinsiz davranış |
|---|---|
| `shortcut` | **Sessizce çalışmaz.** Hata yok, günlükte "başarılı" yazar, ekranda hiçbir şey olmaz. |
| `text` | Aynı şekilde sessizce çalışmaz. |
| `macro` | Adımların tamamı sessizce yutulur. |
| `media` | Ses/oynatma tuşları iletilmez (enkoderin **HID modu** bundan etkilenmez, o cihazdan gider). |
| `app`, `url`, `file`, `folder`, `command` | **Çalışır** — bunlar `open`/`subprocess` kullanır, Erişilebilirlik gerektirmez. |

**Teşhis ipucu:** `app` ve `url` çalışıyor ama `shortcut` çalışmıyorsa,
sorun kesinlikle Erişilebilirlik iznidir. Cihazı veya kabloyu suçlama.

### 2.6 İlk USB bağlantısında çıkan "Klavye Tanımlama Asistanı"

Cihaz bir HID klavye olarak göründüğü için macOS ilk takışta
**Klavye Tanımlama Asistanı** (Keyboard Setup Assistant) penceresini açabilir.
Bu pencere sizden "sol Shift'in sağındaki tuşa basın" der. ExtraKeyboard'da
o tuş yoktur.

- Pencereyi **kapatın** (kırmızı nokta) — cihaz yine de sorunsuz çalışır.
- Ya da **Devam** > **ANSI (ABD)** düzenini elle seçin.

---

## 3. Windows'a özel notlar

### 3.1 Yönetici olarak çalıştırma ne zaman gerekir?

Windows'ta **UIPI** (User Interface Privilege Isolation) kuralı gereği,
normal yetkili bir süreç **yönetici yetkisiyle çalışan bir pencereye**
sentetik tuş gönderemez. Bu, uygulamanın kendi hatası değil, Windows'un
güvenlik tasarımıdır.

**Yönetici olarak çalıştırmanız GEREKEN durumlar:**

| Durum | Neden |
|---|---|
| Görev Yöneticisi'ne kısayol göndermek | Görev Yöneticisi yükseltilmiş çalışır |
| Kayıt Defteri Düzenleyicisi'ne (`regedit`) | Yükseltilmiş |
| Yönetici olarak açılmış PowerShell/CMD'ye | Yükseltilmiş |
| Yönetici olarak açtığınız bir IDE veya araca | Yükseltilmiş |
| `command` tipiyle sistem servisleri yönetmek | Yönetici hakkı ister |

**Yönetici GEREKMEYEN durumlar (çoğunluk):** tarayıcı, Office, Discord,
oyunlar, Explorer, normal uygulamalar. Gündelik kullanımda yönetici
gerekmez ve **gereksiz yere yönetici olarak çalıştırmanız önerilmez.**

**Yönetici olarak başlatma:**

1.  Başlat menüsünde **PowerShell**'e sağ tık > **Yönetici olarak çalıştır**
2.  `cd`, `Activate.ps1`, `python run_app.py` adımlarını tekrarla

Kalıcı kısayol için: `ExtraKeyboard.bat` kısayoluna sağ tık >
**Özellikler** > **Gelişmiş** > **Yönetici olarak çalıştır**.

> **Uyarı:** Uygulama yönetici olarak çalışırken tepsi simgesine ve
> sürükle-bırak işlemlerine bazı kısıtlar gelebilir; ayrıca her açılışta
> UAC onayı istenir.

### 3.2 SmartScreen uyarısı

Uygulamayı `.exe` olarak paketlediysen (PyInstaller vb.), Windows
**Microsoft Defender SmartScreen** şu uyarıyı gösterebilir:

> *"Windows bilgisayarınızı korudu — tanınmayan bir uygulamanın
> başlatılması engellendi"*

Bu, imzasız (kod imzalama sertifikası olmayan) her yeni uygulamada çıkar.
Aşmak için:

1.  Uyarı kutusunda **Ek bilgi** bağlantısına tıkla
2.  Alt kısımda beliren **Yine de çalıştır** düğmesine bas

Kaynak koddan `python run_app.py` ile çalıştırıyorsan SmartScreen devreye
girmez.

**İndirilen ZIP'ten çıkarttıysan:** dosyaya sağ tık > **Özellikler** >
altta **Engellemeyi kaldır** kutusunu işaretle > **Uygula**.

### 3.3 Antivirüs ve `pyautogui`

Bazı üçüncü parti antivirüsler, tuş gönderen programları "keylogger benzeri"
davranış olarak işaretleyebilir. Uygulama klasörünü antivirüs istisnalarına
eklemen gerekebilir. Windows Defender bugüne kadar bir sorun çıkarmamıştır.

### 3.4 COM portu

Cihaz Aygıt Yöneticisi'nde **Bağlantı Noktaları (COM ve LPT)** altında
`USB Seri Aygıt (COM7)` gibi görünür. Uygulama portu otomatik bulur
(önce `VID 0x303A` / `PID 0x82E1`, bulamazsa `ExtraKeyboard MK1` ürün
metni ile). Elle seçmek istersen **LED & Cihaz** sekmesinden port
seçebilirsin.

---

## 4. İlk açılış

`python run_app.py` komutunu verdiğinde sırayla şunlar olur:

1.  **Tekil örnek kontrolü.** Uygulama `127.0.0.1:64210` portunu dinlemeye
    çalışır. Port doluysa "ExtraKeyboard zaten çalışıyor" uyarısı verip
    var olan pencereyi öne getirir ve kapanır.
2.  **Yapılandırma yüklenir.** Proje kökündeki `config.json` okunur.
    Dosya yoksa varsayılan (şema 3) üretilir. Eski `macro_config.json`
    varsa otomatik olarak v3'e taşınır (bkz. [13. bölüm](#13-eski-v2-ayarlarını-i̇çe-aktarma)).
3.  **Cihaz aranır.** `DeviceLink` arka plan thread'inde portları tarar.
    Cihaz takılıysa 1–2 saniye içinde bulunur.
4.  **Kimlik alınır.** Uygulama `CMD ID` gönderir, cihaz
    `ID 3.0.0 MK1 EK1-A4C138 WIN` şeklinde yanıt verir. Bu satırdan
    firmware sürümü, donanım revizyonu, seri numarası ve cihazın o anki
    OS modu okunur.
5.  **LED3 yeşil yanar** (`#2CC985`). Bu, "PC uygulaması bağlı" anlamına
    gelir ve cihaz HID yedek modundan çıkar. Bağlantı kopunca LED3
    kırmızıya (`#E04F5F`) döner.
6.  **Kalp atışı başlar.** Cihaz her 1000 ms'de `HB <uptime_ms>` gönderir.
    Durum çubuğundaki bağlantı noktası bu mesajla canlı kalır; 3 saniye
    kalp atışı gelmezse uygulama bağlantıyı kopmuş sayar ve yeniden bağlanır.

### 4.1 Durum çubuğu

Pencerenin en altındaki çubuk her zaman görünür:

```
 ● Bağlı — COM7        OS: Windows        Profil: Varsayilan        FW 3.0.0        HB 42.318 ms
 └─ yeşil nokta        └─ aktif profil OS  └─ aktif profil adı       └─ firmware      └─ son kalp atışı
```

| Gösterge | Anlamı |
|---|---|
| ● yeşil + "Bağlı — COM7" | Cihaz bulundu, protokol akıyor |
| ● sarı + "Aranıyor…" | Port taranıyor, cihaz henüz bulunamadı |
| ● kırmızı + "Bağlı değil" | Cihaz yok veya port açılamıyor |
| **OS: Windows / macOS** | O an hangi profil tarafının kullanıldığı |
| **HB** | Cihazın açık kalma süresi (ms). Sayı sıfırlanırsa cihaz yeniden başlamıştır |

---

## 5. Arayüz turu

### 5.1 Ekran yerleşimi

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  ExtraKeyboard MK1  ·  v3.0.0                                        ─  □  ✕  │
├───────────────────────────────────────────────────────────────────────────────┤
│  ┌────────┬───────────┬──────────┬───────────────┬──────────┐                 │
│  │ Tuşlar │ Combolar  │ Enkoder  │ LED & Cihaz   │ Ayarlar  │                 │
│  └────────┴───────────┴──────────┴───────────────┴──────────┘                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   Profil: [ Varsayilan  ▾ ]      OS: ( ● Windows )  (   macOS   )             │
│                                                                               │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│   │     K1      │ │     K2      │ │     K3      │ │    ENC      │             │
│   │  Tarayıcı   │ │  Kopyala    │ │  Terminal   │ │  ( ⟳ ses )  │             │
│   │  [url]      │ │  [shortcut] │ │  [app]      │ │  [enkoder]  │             │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│   │     K4      │ │     K5      │ │     K6      │ │    K10      │             │
│   │  Boş        │ │  Yapıştır   │ │  Boş        │ │  COMBO      │             │
│   │  [none]     │ │  [shortcut] │ │  [none]     │ │  (sabit)    │             │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│   │     K7      │ │     K8      │ │     K9      │ │    K11      │             │
│   │  İndirilen. │ │  Boş        │ │  Ekran gör. │ │  WIN / MAC  │             │
│   │  [folder]   │ │  [none]     │ │  [shortcut] │ │  (sabit)    │             │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘             │
│                                                                               │
│   ┌─ Olay günlüğü ──────────────────────────────────────────────────────────┐ │
│   │ 12:04:31  EV KEY 3 UP        → K3 "Terminal" çalıştırıldı               │ │
│   │ 12:04:35  EV MODE COMBO_ON                                              │ │
│   │ 12:04:36  EV COMBO 2 5       → C_2_5 "Ekran kaydı" çalıştırıldı         │ │
│   └─────────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────┤
│  ● Bağlı — COM7   │  OS: Windows  │  Profil: Varsayilan  │  FW 3.0.0  │ HB ✓  │
└───────────────────────────────────────────────────────────────────────────────┘
```

Izgara, cihazın **fiziksel yerleşimini birebir** yansıtır: K1 sol üst,
K9 sağ alt (3×3 numpad), sağ sütunda yukarıdan aşağı ENC, K10, K11.

### 5.2 Sekmeler ne işe yarar?

| Sekme | İçerik | Ne zaman kullanılır |
|---|---|---|
| **Tuşlar** | 4×3 fiziksel ızgara, K1…K9 için eylem kartları | Günlük atama işlerinin %90'ı |
| **Combolar** | 9×9 üst üçgen matris, 36 combo hücresi | K10 + iki tuş kombinasyonlarını atamak |
| **Enkoder** | `cw` / `ccw` / `press` / `long` slotları + HID/HOST mod seçimi | Ses davranışını değiştirmek, enkodere özel eylem vermek |
| **LED & Cihaz** | 5 renk seçici, parlaklık kaydırıcısı, port bilgisi, canlı olay akışı, `CMD` gönderme | Renk özelleştirme, teşhis, elle komut |
| **Ayarlar** | Profil yönetimi, tema, tepsi, otomatik başlatma, dışa/içe aktarma, v2 taşıma | Kurulum sonrası ve yedekleme |

### 5.3 Kart üzerindeki bilgiler

Her tuş/combo/enkoder kartında üç satır vardır:

```
┌─────────────────┐
│  K3             │  ← slot kimliği (değiştirilemez)
│  Terminal       │  ← name — sizin verdiğiniz görünen ad
│  [app]          │  ← type — eylem tipi rozeti
└─────────────────┘
```

Rozet renkleri: `none` gri, `app`/`file`/`folder` mavi `#3B8ED0`,
`url` yeşil `#2CC985`, `shortcut`/`text`/`macro` turuncu `#FF9500`,
`command` kırmızı `#E04F5F` (dikkat gerektirdiği için), `media` mavi.

---

## 6. Tuş atama ve eylem tipleri

### 6.1 Adım adım atama

1.  **Tuşlar** sekmesine geç.
2.  Üstteki **OS** seçicisinin doğru tarafta olduğundan emin ol.
    Windows seçiliyken yaptığın atama **sadece Windows profiline** yazılır.
3.  Atamak istediğin karta tıkla (örn. `K3`). **Eylem Düzenleyici**
    diyaloğu açılır.
4.  **Ad** alanına anlaşılır bir isim yaz (örn. `Terminal`). Bu ad kartta
    ve olay günlüğünde görünür, davranışı etkilemez.
5.  **Tip** açılır listesinden eylem tipini seç (10 tip, aşağıda).
6.  **Değer** alanını doldur. Tipe göre yanında farklı bir yardımcı çıkar:
    - `app`, `file` → **Gözat…** düğmesi (dosya seçici)
    - `folder` → **Gözat…** düğmesi (klasör seçici)
    - `media` → değer açılır liste olur (6 seçenek)
    - `shortcut` → **Yakala** düğmesi; basıp klavyeden kombinasyonu tuşlarsın
    - `macro` → çok satırlı alan + adım ekleme yardımcısı
7.  **Test Et** düğmesiyle eylemi hemen dene. Sonuç diyaloğun altında
    yeşil (başarılı) veya kırmızı (hata mesajıyla) görünür.
8.  **Kaydet**'e bas. Yapılandırma anında `config.json`'a **atomik** olarak
    yazılır (`.tmp` dosyası + `os.replace`), yani yazma sırasında elektrik
    kesilse bile eski dosya bozulmaz.

**Temizleme:** Bir tuşu boşaltmak için tipi `none` yap ve kaydet.
Karta sağ tıklayıp **Temizle** de aynı işi yapar.

**Kopyalama:** Bir karta sağ tık > **Kopyala**, sonra hedef karta sağ tık >
**Yapıştır**. Karşı OS profiline yapıştırırsan **değer aynen kopyalanır** —
yolları elle düzeltmen gerekir.

### 6.2 Eylem tetiklenme anı

> Eylem **`EV KEY <n> UP`** olayında, yani **tuşu bıraktığında** tetiklenir.
> `DOWN` sadece görsel geri bildirim (LED3 mavi flaş, arayüzde kartın
> vurgulanması) içindir. Bu, combo durum makinesinin ilk tuşu yutabilmesi
> için gereklidir.

### 6.3 On eylem tipi — gerçek örnekler

Aşağıdaki tablo `docs/00-CEKIRDEK-SPEC.md` §7.2'deki tip listesinin
tamamını, her iki OS için doldurulmuş `value` örnekleriyle gösterir.

---

#### 1) `none` — Hiçbir şey yapma

| | Değer |
|---|---|
| **Windows** | `` (boş) |
| **macOS** | `` (boş) |

Tuşu devre dışı bırakır. Yanlışlıkla basmak istemediğin tuşlar için kullan.
Olay günlüğünde `EV KEY 5 UP → K5 atanmamış` satırı görünür, başka bir şey olmaz.

---

#### 2) `app` — Uygulama başlat

| | Değer örneği |
|---|---|
| **Windows** | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| **Windows (2)** | `C:\Windows\System32\notepad.exe` |
| **macOS** | `/Applications/Safari.app` |
| **macOS (2)** | `/System/Applications/Utilities/Terminal.app` |

- Windows'ta tam `.exe` yolu verilir. `Gözat…` ile seçmek en güvenlisidir.
- macOS'ta `.app` paketinin kendisi verilir (içindeki ikili değil).
  Arka planda `open -a` kullanılır, uygulama zaten açıksa öne getirilir.
- Yolda boşluk olması sorun değildir, tırnak koymana gerek yok.
- Windows Store uygulamaları (`.exe` yolu olmayanlar) için `command` tipiyle
  `explorer.exe shell:AppsFolder\...` kullanman gerekir.

---

#### 3) `url` — Varsayılan tarayıcıda aç

| | Değer örneği |
|---|---|
| **Windows** | `bluedevelopment.com` |
| **Windows (2)** | `https://github.com/search?q=esp32-s3` |
| **macOS** | `bluedevelopment.com` |
| **macOS (2)** | `https://www.apple.com/tr/` |

- Şema (`http://` / `https://`) yoksa uygulama otomatik olarak
  **`https://`** ekler. Yani `bluedevelopment.com` → `https://bluedevelopment.com`.
- `mailto:`, `slack://`, `zoommtg://` gibi özel şemalar da çalışır.

---

#### 4) `shortcut` — Tuş kombinasyonu bas

| | Değer örneği | Ne yapar |
|---|---|---|
| **Windows** | `ctrl+shift+esc` | Görev Yöneticisi (yönetici gerekir, bkz. §3.1) |
| **Windows (2)** | `ctrl+c` | Kopyala |
| **Windows (3)** | `win+shift+s` | Ekran kırpma aracı |
| **macOS** | `command+c` | Kopyala |
| **macOS (2)** | `command+shift+4` | Ekran görüntüsü (seçim) |
| **macOS (3)** | `command+space` | Spotlight |

**Kısayol normalizasyonu (spec §7.2):**

- **Windows profilinde** `command` ve `cmd` yazarsan otomatik olarak
  **`ctrl`**'e çevrilir. Yani Windows tarafında `command+c` yazsan bile
  `ctrl+c` basılır.
- **macOS profilinde** `ctrl` **olduğu gibi kalır** — macOS'ta Control
  ayrı bir tuştur ve `ctrl+c` terminalde "işlemi durdur" demektir.
  Elma tuşunu istiyorsan **`command`** yazmak zorundasın.
- Eylem düzenleyici, aktif profile göre alanın altında ipucu gösterir:
  *"macOS profili: Elma tuşu için `command` yazın, `ctrl` Control tuşudur."*

**Geçerli değiştirici adları:** `ctrl`, `shift`, `alt` (macOS'ta `option`
ile aynı), `command` / `cmd` (macOS), `win` (Windows).
Tuşlar `+` ile birleştirilir, küçük harf yazılır, boşluk bırakılmaz.

---

#### 5) `text` — Metni yaz

| | Değer örneği |
|---|---|
| **Windows** | `merhaba dünya` |
| **Windows (2)** | `kullanici@ornek.com` |
| **macOS** | `merhaba dünya` |
| **macOS (2)** | `Saygılarımla,\nMusa` |

- Metin, imlecin bulunduğu yere karakter karakter yazılır.
- `\n` yeni satır, `\t` sekme olarak yorumlanır.
- **Türkçe karakter uyarısı:** `pyautogui` bazı klavye düzenlerinde
  `ç ğ ı ö ş ü İ` karakterlerini atlayabilir. Uzun Türkçe metinler için
  `text` yerine panoya kopyalayıp `shortcut` ile yapıştıran bir `macro`
  daha güvenilirdir.
- **Parola yazdırmak için kullanma** — değer `config.json` içinde düz
  metin olarak durur.

---

#### 6) `command` — Kabuk komutu çalıştır

| | Değer örneği | Ne yapar |
|---|---|---|
| **Windows** | `shutdown /h` | Hazırda beklet |
| **Windows (2)** | `powershell -NoProfile -Command "Get-Date \| Out-File $env:TEMP\zaman.txt"` | Tarihi dosyaya yaz |
| **Windows (3)** | `wt.exe -d C:\Projeler` | Windows Terminal'i klasörde aç |
| **macOS** | `say merhaba` | Sesli okuma |
| **macOS (2)** | `osascript -e 'display notification "Yedek bitti"'` | Bildirim göster |
| **macOS (3)** | `open -a "Visual Studio Code" ~/Projeler` | VS Code'u klasörde aç |

- Komut kabuk üzerinden çalıştırılır; boru (`|`), yönlendirme (`>`) ve
  ortam değişkenleri kullanılabilir.
- **Pencere açılmaz** — çıktı görmek istersen dosyaya yönlendir.
- **Güvenlik:** Bu tip sisteminde herhangi bir komutu çalıştırabilir.
  Başkasının gönderdiği `config.json`'u içe aktarmadan önce `command`
  tipindeki satırları gözden geçir. Uygulama, içe aktarma sırasında
  `command` içeren slotları sarı uyarı ile listeler.

---

#### 7) `file` — Dosyayı varsayılan uygulamada aç

| | Değer örneği |
|---|---|
| **Windows** | `C:\Users\musa\Belgeler\notlar.txt` |
| **Windows (2)** | `D:\Projeler\ExtraKeyboard\docs\00-CEKIRDEK-SPEC.md` |
| **macOS** | `~/notlar.txt` |
| **macOS (2)** | `~/Belgeler/toplanti-notlari.pdf` |

- `~` her iki platformda da kullanıcı klasörüne genişletilir.
- Windows'ta `%USERPROFILE%` gibi ortam değişkenleri de genişletilir.
- Dosya yoksa eylem başarısız olur ve olay günlüğüne kırmızı satır düşer:
  `K7 — dosya bulunamadı: ~/notlar.txt`

---

#### 8) `folder` — Klasörü Explorer/Finder'da aç

| | Değer örneği |
|---|---|
| **Windows** | `C:\Users\musa\Downloads` |
| **Windows (2)** | `%USERPROFILE%\Desktop` |
| **macOS** | `~/Downloads` |
| **macOS (2)** | `/Volumes/Yedek` |

Klasör penceresi açılır; zaten açıksa öne getirilir.

---

#### 9) `media` — Medya tuşu

Değer bir listeden seçilir, elle yazılmaz. Geçerli **6** değer
(spec §7.2, `MEDIA_VALUES`):

| Değer | Anlamı | Windows | macOS |
|---|---|---|---|
| `volume_up` | Ses aç | ✓ | ✓ |
| `volume_down` | Ses kıs | ✓ | ✓ |
| `mute` | Sessize al / aç | ✓ | ✓ |
| `play_pause` | Oynat / duraklat | ✓ | ✓ |
| `next` | Sonraki parça | ✓ | ✓ |
| `prev` | Önceki parça | ✓ | ✓ |

- macOS'ta bu tip **Erişilebilirlik izni ister** (bkz. §2.2).
- Enkoderin **HID modunda** medya kontrolü doğrudan cihazdan (Consumer
  Control) gider ve hiçbir izin gerektirmez — daha güvenilirdir.
- Windows'ta `next`/`prev` sadece medya tuşlarını dinleyen uygulamalarda
  (Spotify, Groove, tarayıcı medya oturumları) çalışır.

---

#### 10) `macro` — Çok adımlı dizi

Adımlar `|` (dikey çizgi) ile ayrılır. Bir adım **sayı** ise o kadar
**milisaniye beklenir**; değilse kısayol olarak basılır.

| | Değer örneği | Ne yapar |
|---|---|---|
| **Windows** | `ctrl+c\|500\|ctrl+v` | Kopyala, 500 ms bekle, yapıştır |
| **Windows (2)** | `ctrl+a\|100\|ctrl+c\|300\|alt+tab\|400\|ctrl+v` | Tümünü kopyala, pencere değiştir, yapıştır |
| **Windows (3)** | `win+d\|800\|win+d` | Masaüstünü göster, 0.8 s bekle, geri dön |
| **macOS** | `command+c\|500\|command+v` | Kopyala, bekle, yapıştır |
| **macOS (2)** | `command+a\|100\|command+c\|300\|command+tab\|400\|command+v` | Aynısının Mac karşılığı |
| **macOS (3)** | `command+shift+4\|1500\|escape` | Ekran görüntüsü modunu aç, 1.5 s sonra iptal et |

- Bekleme değerleri **milisaniye**dir; `500` = yarım saniye.
- Adım sayısı sınırsızdır ama toplam süre 10 saniyeyi geçerse uygulama
  uyarı gösterir (tuşa tekrar basılması karışıklık yaratır).
- Makro çalışırken tekrar aynı tuşa basılırsa ikinci istek **yok sayılır**;
  olay günlüğünde `K4 — makro zaten çalışıyor` satırı görünür.
- Makro içinde `text` adımı yoktur; metin yazmak istersen `text` tipini
  ayrı bir tuşa ata veya panodan yapıştır.

---

## 7. Combo kullanımı

### 7.1 Fiziksel olarak nasıl yapılır? — BAS-ÇEK

K10 **basılı tutulmaz**. Bir kez basılır, mod kilitlenir, sıradaki iki tuş
comboyu oluşturur:

```
  1. K10'a BİR KEZ bas ve bırak         →  LED2 turuncu yanar (#FF9500)
                                            cihaz: EV MODE COMBO_ON
  2. 1. tuşa bas (bırakabilirsin)       →  hiçbir şey olmaz (tuş SEÇİLDİ,
                                            normal eylemi bastırıldı)
  3. 2. tuşa bas                        →  LED2 yeşil flaş (150 ms)
                                            cihaz: EV COMBO 2 5  →  C_2_5 çalışır
                                            ve mod KENDİLİĞİNDEN kapanır
                                            (EV MODE COMBO_OFF, LED2 söner)
```

**Vazgeçmek:** K10'a tekrar bas → mod kapanır. **Unutursan:** 10 sn işlem
yapılmazsa mod kendiliğinden kapanır (LED2 söner).

**Kritik davranışlar:**

- **Mod açıkken K1…K9'un normal eylemleri ÇALIŞMAZ.** Cihaz `EV KEY`
  olayı da göndermez, HID kodu da basmaz. Bu kasıtlıdır; combo'nun ilk
  tuşunun yanlışlıkla eylem tetiklemesini önler.
- **Tuşları basılı tutmak gerekmez.** Sayılan şey basış anlarıdır (DOWN
  kenarı); ilk tuşu bırakıp sonra ikinciye basabilirsin.
- **Sıra önemsizdir.** Önce 2 sonra 5'e basmakla önce 5 sonra 2'ye basmak
  aynıdır; ikisi de `C_2_5` üretir. Cihaz `a < b` normalize eder.
- **Mod tek seferliktir.** Combo tetiklenince kapanır; ikinci combo için
  K10'a yeniden basarsın. Aynı tuşa iki kez basmak yok sayılır (`3+3` yok).
- **Eski alışkanlık da çalışır:** K10'u basılı tutup iki tuşa basarsan da
  aynı combo tetiklenir (mod, basış anında açıldığı için).
- **Ghosting yoktur.** Her tuş kendi GPIO'suna doğrudan bağlıdır (matris
  ve diyot yok).
- **HID yedek modunda combo devre dışıdır.** Uygulama kapalıyken K10'a
  basarsan LED3 kırmızı yanıp söner ve hiçbir combo tetiklenmez.

### 7.2 36 kombinasyonun matrisi

C(9,2) = **36** benzersiz combo vardır. Matris, 9×9'un **üst üçgenidir**
(köşegen ve alt üçgen boştur, çünkü `C_3_3` diye bir şey yok ve
`C_5_2` = `C_2_5`).

```
        b→   1     2     3     4     5     6     7     8     9
      ┌────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
  a=1 │    │  ·  │C_1_2│C_1_3│C_1_4│C_1_5│C_1_6│C_1_7│C_1_8│C_1_9│  8
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=2 │    │     │  ·  │C_2_3│C_2_4│C_2_5│C_2_6│C_2_7│C_2_8│C_2_9│  7
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=3 │    │     │     │  ·  │C_3_4│C_3_5│C_3_6│C_3_7│C_3_8│C_3_9│  6
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=4 │    │     │     │     │  ·  │C_4_5│C_4_6│C_4_7│C_4_8│C_4_9│  5
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=5 │    │     │     │     │     │  ·  │C_5_6│C_5_7│C_5_8│C_5_9│  4
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=6 │    │     │     │     │     │     │  ·  │C_6_7│C_6_8│C_6_9│  3
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=7 │    │     │     │     │     │     │     │  ·  │C_7_8│C_7_9│  2
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=8 │    │     │     │     │     │     │     │     │  ·  │C_8_9│  1
      ├────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
  a=9 │    │     │     │     │     │     │     │     │     │  ·  │  0
      └────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                                          TOPLAM: 8+7+6+5+4+3+2+1 = 36
```

Tam liste (uygulamanın `COMBO_IDS` sırası da budur):

```
C_1_2  C_1_3  C_1_4  C_1_5  C_1_6  C_1_7  C_1_8  C_1_9
C_2_3  C_2_4  C_2_5  C_2_6  C_2_7  C_2_8  C_2_9
C_3_4  C_3_5  C_3_6  C_3_7  C_3_8  C_3_9
C_4_5  C_4_6  C_4_7  C_4_8  C_4_9
C_5_6  C_5_7  C_5_8  C_5_9
C_6_7  C_6_8  C_6_9
C_7_8  C_7_9
C_8_9
```

### 7.3 Matriste hücre düzenleme

1.  **Combolar** sekmesine geç.
2.  Doldurulmuş hücreler renkli rozetli, boşlar (`none`) soluktur.
    Boş olanları gizlemek için üstteki **Sadece dolu combolar** kutusunu işaretle.
3.  İstediğin hücreye tıkla → aynı **Eylem Düzenleyici** açılır
    (tuşlarla birebir aynı 10 tip, aynı alanlar).
4.  Varsayılan ad `Combo 2+5` şeklinde önerilir; istediğin gibi değiştir.
5.  **Kaydet**.

**Öğrenme modu:** Matrisin üstündeki **Cihazdan yakala** düğmesine bas,
sonra cihazda K10 + iki tuş kombinasyonunu fiziksel olarak yap. Uygulama
gelen `EV COMBO a b` mesajını yakalar ve ilgili hücrenin düzenleyicisini
otomatik açar. Hangi hücreye tıklayacağını aramak yerine bu daha hızlıdır.

**Toplu işlemler:** Matrise sağ tık > **Tüm comboları temizle**
(onay ister), **Combo satırını temizle**, **Karşı OS profiline kopyala**.

---

## 8. Enkoder ayarları

Enkoderin **dört slotu** vardır (spec §7.1): `cw` (saat yönü),
`ccw` (saat yönü tersi), `press` (basma), `long` (800 ms basılı tutma).

### 8.1 HID modu ve HOST modu

| | **HID modu** (`hid`) | **HOST modu** (`host`) |
|---|---|---|
| Komut | `CMD ENC MODE HID` | `CMD ENC MODE HOST` |
| Ses kimin üzerinden gider? | **Cihaz** doğrudan USB Consumer Control gönderir | **PC uygulaması** eylem çalıştırır |
| Uygulama kapalıyken çalışır mı? | **Evet** | Hayır |
| Gecikme | Yok (donanım hızında) | Seri + Python turu (~5–20 ms) |
| macOS izni gerekir mi? | **Hayır** | Evet (`media`/`shortcut` için Erişilebilirlik) |
| `cw`/`ccw`/`press` slotlarına başka eylem atanabilir mi? | Hayır, sabit ses/sessiz | **Evet, 10 tipin hepsi** |
| `long` slotu | Uygulamaya `EV ENC LONG` olarak gelir, atanabilir | Atanabilir |
| Varsayılan | **Bu moddur** | — |

**Ne zaman hangisi?**

- **HID modunu seç** — enkoderi sadece ses için kullanıyorsan. En güvenilir,
  en hızlı, izin istemeyen seçenek. Uygulama kapalıyken de, oyun tam ekranken
  de, uyandırma ekranında da çalışır. **Önerilen varsayılan budur.**
- **HOST modunu seç** — enkoderi ses dışında bir şey için kullanmak
  istiyorsan: zoom seviyesi (`ctrl+plus` / `ctrl+minus`), fırça boyutu,
  video zaman çizelgesinde ilerleme, sekme değiştirme (`ctrl+tab`),
  ya da profil bazında farklı davranış.

> **Önemli:** Uygulama **bağlı değilken** enkoder, ayarın ne olduğuna
> bakılmaksızın HID ses/sessiz davranışına döner (spec §5.3:
> *"Enkoder HID modu her zaman aktiftir — uygulama olmadan da ses çalışır."*).
> HOST modu yalnızca uygulama bağlıyken devreye girer. Bu bilinçli bir
> tasarımdır: uygulamayı kapattığında ses kontrolünü kaybetmezsin.

### 8.2 Ayarlama adımları

1.  **Enkoder** sekmesine geç.
2.  Üstteki **Mod** seçicisinden `HID` veya `HOST` seç. Seçim anında
    cihaza `CMD ENC MODE HID` / `CMD ENC MODE HOST` olarak gönderilir ve
    cihaz `ACK` ile yanıtlar; durum çubuğunda onay görünür.
3.  HOST modundaysan dört slot kartı etkinleşir. Her birine tıklayıp
    normal Eylem Düzenleyici ile atama yap.
4.  HID modundaysan `cw`, `ccw`, `press` kartları gri ve kilitli görünür
    (değerleri `volume_up`, `volume_down`, `mute` olarak sabittir);
    yalnızca **`long`** kartı düzenlenebilir kalır.
5.  Ayarların cihazda kalıcı olması için **LED & Cihaz** sekmesinde
    **Cihaza kaydet** düğmesine bas — bu `CMD SAVE` gönderir ve mod
    ayarı ESP32'nin NVS belleğine yazılır.

### 8.3 HOST modu için örnek atamalar

| Slot | Windows | macOS | Sonuç |
|---|---|---|---|
| `cw` | `shortcut` → `ctrl+plus` | `shortcut` → `command+plus` | Yakınlaştır |
| `ccw` | `shortcut` → `ctrl+minus` | `shortcut` → `command+minus` | Uzaklaştır |
| `press` | `shortcut` → `ctrl+0` | `shortcut` → `command+0` | Yakınlaştırmayı sıfırla |
| `long` | `media` → `play_pause` | `media` → `play_pause` | Oynat/duraklat |

---

## 9. OS değiştirme

Windows ve macOS profilleri **ayrı tutulur.** Bunun tek sebebi vardır:
**yollar farklıdır.** `C:\Program Files\...` bir Mac'te anlamsızdır,
`/Applications/Safari.app` bir PC'de anlamsızdır. Ayrıca kısayol
değiştiricileri farklıdır (`ctrl` ⇄ `command`).

Yani tek bir profil içinde iki ayrı atama seti bulunur:

```
profiles.Varsayilan
├── windows
│   ├── keys     : K1…K9
│   ├── combos   : C_1_2…C_8_9  (36)
│   └── encoder  : mode + cw/ccw/press/long
└── mac
    ├── keys     : K1…K9
    ├── combos   : C_1_2…C_8_9  (36)
    └── encoder  : mode + cw/ccw/press/long
```

### 9.1 Fiziksel K11 tuşu ile değiştirme

- **Kısa basış (< 800 ms):** Windows ⇄ macOS geçişi.
  - LED1 rengi değişir: **Windows = mavi `#1E90FF`**, **macOS = beyaz `#FFFFFF`**
  - Cihaz `EV OS WIN` veya `EV OS MAC` gönderir
  - Ayar cihazın NVS belleğine kaydedilir (cihaz fişten çekilse bile korunur)
  - Uygulama bu olayı alır, `ActionRunner.set_os_key()` ile aktif tarafı
    değiştirir, arayüzdeki tüm kartlar anında yenilenir
- **Uzun basış (≥ 3 s):** HID yedek modunu açar/kapatır
  (`CMD HIDFB ON/OFF` eşdeğeri). Onay olarak **LED3 üç kez beyaz yanıp söner.**

### 9.2 Uygulamadan değiştirme

**Tuşlar** sekmesinin üstündeki **OS** anahtarını (Windows / macOS)
değiştir. Uygulama cihaza `CMD OS WIN` veya `CMD OS MAC` gönderir,
cihaz LED1'i günceller ve NVS'e yazar. Sonuç fiziksel tuşla aynıdır.

### 9.3 Sık yapılan hata

> Bir Windows makinesinde çalışırken OS anahtarını yanlışlıkla **macOS**
> yaparsan, uygulama macOS profilindeki atamaları çalıştırmaya çalışır ve
> `/Applications/...` yolları bulunamadığı için eylemler başarısız olur.
> Durum çubuğundaki **OS:** göstergesini kontrol et.

**KVM / iki bilgisayar senaryosu:** Aynı cihazı bir Windows PC ile bir
Mac arasında paylaşıyorsan, kabloyu taktığın makinede uygulamayı açtığında
uygulama kendi platformunu algılar ve OS anahtarını buna göre önerir.
Öneriyi kabul edersen `CMD OS ...` gönderilir. Bu davranışı **Ayarlar** >
**Bağlanınca OS modunu bu bilgisayara göre ayarla** kutusundan kapatabilirsin.

---

## 10. Profil yönetimi

Profil, "bir işe özel tam atama seti"dir. Örneğin `Video Kurgu`,
`Yayın`, `Ofis`, `Oyun` diye ayrı profiller tutabilirsin. Her profil
kendi içinde `windows` ve `mac` taraflarını barındırır.

Tüm profil işlemleri **Ayarlar** sekmesindeki **Profiller** bölümündedir.

| İşlem | Nasıl yapılır | Ne olur |
|---|---|---|
| **Aktif profili değiştir** | Üstteki açılır listeden seç | `active_profile` güncellenir, arayüz yenilenir. Anında etkindir. |
| **Ekle** | **Yeni…** > ad gir | Tamamen boş bir profil oluşur (tüm slotlar `none`). |
| **Kopyala** | Profili seç > **Kopyala** > yeni ad gir | Var olan profilin birebir kopyası (hem `windows` hem `mac` tarafı) oluşur. Yeni profile başlarken sıfırdan başlamak yerine bunu kullan. |
| **Yeniden adlandır** | Profili seç > **Adı Değiştir** | Aktif profilse `active_profile` de güncellenir. |
| **Sil** | Profili seç > **Sil** | Onay ister. **Son profil silinemez** — en az bir profil kalmak zorundadır. Aktif profili silersen listedeki ilk profil aktif olur. |
| **Dışa aktar** | **Dışa Aktar…** > kaydetme yeri seç | `ConfigManager.export_to()` ile **tüm yapılandırma** (bütün profiller + LED + arayüz ayarları) tek bir `.json` dosyasına yazılır. |
| **İçe aktar** | **İçe Aktar…** > dosya seç | `ConfigManager.import_from()`. Şema sürümü kontrol edilir; v2 dosyası verirsen otomatik taşınır. **Mevcut yapılandırmanın üzerine yazar** — önce yedek almanı önerir. |

### 10.1 Yedekleme önerisi

`config.json` düz bir metin dosyasıdır. En basit yedek:

```bash
# macOS
cp ~/ExtraKeyboard-MK1/config.json ~/Belgeler/config-yedek-$(date +%F).json
```

```powershell
# Windows
Copy-Item config.json "$env:USERPROFILE\Belgeler\config-yedek-$(Get-Date -f yyyy-MM-dd).json"
```

Uygulama ayrıca her başarılı yazmadan önce dosyayı `.tmp` üzerinden
değiştirir (`os.replace`), bu yüzden yarım yazılmış bozuk `config.json`
oluşması mümkün değildir.

### 10.2 Profil paylaşma

Dışa aktardığın dosyayı başkasına verebilirsin. Karşı taraf içe aktarmadan
önce şunları kontrol etmeli:

- `app`, `file`, `folder` yolları o makinede var mı?
- `command` tipinde tanımadığı bir komut var mı? **Bu tip her şeyi
  çalıştırabilir — bilmediğin kaynaktan gelen dosyayı içe aktarma.**
- Uygulama içe aktarma öncesi `command` içeren slotların listesini
  sarı uyarı panelinde gösterir; onaylamadan devam edilemez.

---

## 11. LED özelleştirme

**LED & Cihaz** sekmesinden 3 LED'in tüm durumları ve genel parlaklık
ayarlanır. Değerler `config.json`'daki `leds` bölümünde tutulur.

### 11.1 Varsayılan anlamlar ve renkler

| LED | Durum | Varsayılan renk | Yapılandırma anahtarı |
|---|---|---|---|
| **LED1** | OS = Windows | Mavi `#1E90FF` | `leds.os_win` |
| **LED1** | OS = macOS | Beyaz `#FFFFFF` | `leds.os_mac` |
| **LED2** | Combo kapalı | Sönük | — (sabit) |
| **LED2** | Combo modu kilitli (K10 bas-çek) | Turuncu `#FF9500` | `leds.combo` |
| **LED2** | Combo tetiklendi (150 ms flaş) | Yeşil `#2CC985` | `leds.link_ok` ile aynı renk kullanılır |
| **LED3** | PC uygulaması bağlı | Yeşil `#2CC985` | `leds.link_ok` |
| **LED3** | Uygulama yok / HID yedek | Kırmızı `#E04F5F` | `leds.link_err` |
| **LED3** | Tuş aktivitesi (80 ms flaş) | Mavi `#3B8ED0` | — (sabit) |

### 11.2 Nasıl değiştirilir?

1.  **LED & Cihaz** sekmesindeki beş renk kutusundan birine tıkla.
2.  Renk seçici açılır; HEX kodunu (`1E90FF` gibi, `#` olsun ya da olmasın)
    elle de yazabilirsin.
3.  **Uygula**'ya bastığın anda uygulama cihaza `CMD LED <i> <RRGGBB>`
    gönderir (örn. `CMD LED 1 1E90FF`) ve LED anında değişir.
4.  **Parlaklık** kaydırıcısı 0–255 arasıdır, `CMD LED BRIGHT <0-255>`
    gönderir. **Varsayılan 60'tır** ve gözü yormaması için bilinçli olarak
    düşük tutulmuştur. 150'nin üzeri karanlık odada rahatsız edicidir ve
    toplam akımı artırır.
5.  Ayarların cihaz fişten çekilince kaybolmaması için **Cihaza kaydet**
    (`CMD SAVE`) düğmesine bas.

### 11.3 Test düğmeleri

- **LED Testi** — üç LED'i sırayla kırmızı/yeşil/mavi yakar, sonra
  yapılandırmadaki renklere döndürür. Lehim ve zincir yönü kontrolü için
  kullanılır.
- **Tümünü söndür** — üç LED'e de `000000` gönderir. Gece kullanımı veya
  fotoğraf çekimi için pratiktir (yapılandırmayı değiştirmez).

> **Not:** Toplam çekim 150 mA'nın altında tutulmalıdır (spec §3.3).
> Üç WS2812B tam beyaz + tam parlaklıkta bu sınırı zorlar. Varsayılan 60
> parlaklıkta sorun yoktur.

---

## 12. Otomatik başlatma ve tepsi

Tüm bu ayarlar **Ayarlar** sekmesindedir ve `config.json`'da saklanır.

| Ayar | Anahtar | Varsayılan | Açıklama |
|---|---|---|---|
| **Bilgisayar açılınca başlat** | `autostart` | `false` | Aşağıya bak |
| **Kapatınca tepsiye küçült** | `ui.minimize_to_tray` | `true` | ✕ düğmesi uygulamayı kapatmaz, tepsiye indirir |
| **Küçültülmüş başlat** | `ui.start_minimized` | `false` | Açılışta pencere gösterilmez, doğrudan tepsiye gider |
| **Tema** | `ui.theme` | `"Dark"` | Koyu tema (`#1a1a2e` / `#16213e` / `#1e1e2e`) |

### 12.1 Otomatik başlatma nasıl kurulur?

Kutuyu işaretlediğinde uygulama gerekli sistem kaydını **kendisi** yapar:

- **Windows:** `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
  altına `ExtraKeyboard` adında bir değer eklenir. Yönetici hakkı gerekmez
  (yalnızca mevcut kullanıcı için).
- **macOS:** `~/Library/LaunchAgents/com.bluedevelopment.extrakeyboard.plist`
  adında bir LaunchAgent dosyası oluşturulur ve `launchctl` ile yüklenir.

Kutunun işaretini kaldırdığında kayıt/dosya temizlenir.

> **macOS uyarısı:** Otomatik başlatmada uygulamayı Terminal başlatmaz;
> LaunchAgent doğrudan sanal ortamdaki `python`'u çalıştırır. Bu durumda
> **Erişilebilirlik iznini `.venv/bin/python3.11` ikilisine de vermelisin**,
> yoksa açılışta çalışan örnek tuş gönderemez (bkz. §2.1).

### 12.2 Tepsi (sistem tepsisi) menüsü

Tepsi simgesine tıklandığında açılan menü:

```
  ExtraKeyboard MK1
  ─────────────────────
  ● Bağlı — COM7
  Profil: Varsayilan  ▸     (profiller arası hızlı geçiş)
  OS: Windows         ▸     (Windows / macOS)
  ─────────────────────
  Pencereyi Göster
  Ayarlar…
  ─────────────────────
  Çıkış
```

Simge rengi bağlantı durumunu yansıtır: **yeşil = bağlı**,
**kırmızı = bağlı değil**. macOS'ta simge menü çubuğunda,
Windows'ta saatin yanındaki bildirim alanında görünür
(Windows'ta simgeyi kalıcı göstermek için görev çubuğu taşma menüsünden
yukarı sürüklemen gerekebilir).

**Tam çıkış:** Tepsi > **Çıkış**. Uygulama kapanınca cihaz CDC DTR
sinyalinin düştüğünü görür, LED3 kırmızıya döner ve **HID yedek moduna**
geçer — yani tuşlar `F13…F22` göndermeye başlar.

---

## 13. Eski v2 ayarlarını içe aktarma

Eski sürüm (v2, `Main.py`) ayarlarını proje kökündeki
`macro_config.json` dosyasında `F13`…`F20` anahtarlarıyla tutuyordu:

```json
{
  "F13": { "type": "url",      "value": "bluedevelopment.com",           "name": "Buton 1" },
  "F14": { "type": "app",      "value": "/Applications/AnyDesk.app", "name": "Buton 2" },
  "F15": { "type": "shortcut", "value": "command+c",              "name": "Buton 3" }
}
```

### 13.1 Otomatik taşıma

**Hiçbir şey yapmana gerek yoktur.** v3 ilk açıldığında `config.json` yoksa
ve `macro_config.json` varsa, `ConfigManager.load()` taşımayı kendisi yapar
ve size bir özet penceresi gösterir.

### 13.2 Eşleme tablosu

| v2 anahtarı | v3 slotu | Not |
|---|---|---|
| `F13` | `K1` | |
| `F14` | `K2` | |
| `F15` | `K3` | |
| `F16` | `K4` | |
| `F17` | `K5` | |
| `F18` | `K6` | |
| `F19` | `K7` | |
| `F20` | `K8` | |
| `F21` | `K9` | v2'de yoksa `none` kalır |

- v2 dosyasındaki `type`, `value`, `name` alanları **birebir taşınır**;
  bu üç alan v2 ve v3'te aynı anlamdadır.
- v2'de `command`, `file`, `folder`, `macro` tipleri yoksa taşınacak bir
  şey de yoktur; kalan slotlar `none` olarak oluşturulur.
- v2'de tanınmayan bir `type` varsa o slot `none` yapılır ve özet
  penceresinde sarı uyarı olarak listelenir.

### 13.3 Hangi profile taşınır?

- Taşınan atamalar **`Varsayilan` profiline**, **çalıştığın bilgisayarın
  platformuna karşılık gelen tarafa** yazılır. Yani Mac'te taşıma
  yaparsan `profiles.Varsayilan.mac.keys` doldurulur, karşı taraf
  (`windows`) boş kalır.
- v2 yalnızca 8 tuşu biliyordu; **combolar ve enkoder slotları boş
  (`none`) olarak oluşturulur** — v2'de karşılıkları yoktu.

### 13.4 Elle taşıma

Otomatik taşımayı atladıysan veya sonradan yapmak istersen iki yol var:

1.  **Ayarlar** sekmesi > **v2 ayarlarını içe aktar…** > `macro_config.json` seç
2.  Komut satırından:

```bash
python tools/migrate_v2_config.py macro_config.json config.json
```

Betik, var olan `config.json`'un üzerine yazmadan önce
`config.json.bak` yedeği alır.

> **`macro_config.json` silinmez.** v2 dosyası olduğu gibi durur;
> istersen eski uygulamayı (`Main.py`) çalıştırmaya devam edebilirsin.
> Ancak **ikisini aynı anda çalıştırma** — ikisi de aynı seri porta
> bağlanmaya çalışır ve biri portu kilitler.

---

## 14. Klavye kısayolu çatışma tablosu (F13–F24)

Bu bölüm yalnızca **HID yedek modu** için önemlidir. Uygulama bağlıyken
cihaz hiçbir HID tuşu göndermez, sadece `EV KEY` mesajı yollar —
dolayısıyla çatışma olmaz.

### 14.1 HID yedek modunda hangi tuş ne gönderir?

| Cihaz tuşu | Gönderilen HID kodu |
|---|---|
| K1 | `F13` |
| K2 | `F14` |
| K3 | `F15` |
| K4 | `F16` |
| K5 | `F17` |
| K6 | `F18` |
| K7 | `F19` |
| K8 | `F20` |
| K9 | `F21` |
| K11 (OS) | `F22` |
| K10 (COMBO) | *(devre dışı — LED3 kırmızı yanıp söner)* |
| Enkoder | Consumer Control: Volume Up / Volume Down / Mute |

`F23` ve `F24` **kullanılmaz**; ileride genişletme için ayrılmıştır.

### 14.2 Çatışma tablosu

| Tuş | Windows'ta bilinen kullanım | macOS'ta bilinen kullanım | Risk |
|---|---|---|---|
| `F13` | Windows'un kendisi kullanmaz. Bazı IBM/AS-400 terminal emülatörlerinde "Alan Çıkışı". | Apple Genişletilmiş Klavye'de fiziksel **F13 = Print Screen** konumundadır. Bazı uygulamalar ekran görüntüsü için dinler. | **Orta** |
| `F14` | Kullanılmaz. | Apple klavyelerde tarihsel olarak **Scroll Lock**; bazı Mac modellerinde **ekran parlaklığı azalt**. | **Orta** |
| `F15` | Kullanılmaz. | Tarihsel olarak **Pause/Break**; bazı Mac modellerinde **ekran parlaklığı artır**. | **Orta** |
| `F16` – `F19` | Kullanılmaz. Üretici yazılımları (Logitech G HUB, Corsair iCUE, Razer Synapse) makro hedefi olarak sıkça kullanır. | Sistem tarafından kullanılmaz. **Sistem Ayarları > Klavye > Klavye Kısayolları** altında serbestçe atanabilir. | **Düşük** |
| `F20` | Kullanılmaz. Bazı konferans yazılımları (Teams, Zoom) mikrofon sustur için önerir. | Sistem tarafından kullanılmaz. | **Düşük** |
| `F21` | Kullanılmaz. | Kullanılmaz. | **Çok düşük** |
| `F22` | Kullanılmaz. Bazı dizüstülerde üretici yazılımı klavye ışığı için kullanır. | Kullanılmaz. | **Düşük** |
| `F23` | Kullanılmaz (projede de kullanılmıyor). | Kullanılmaz. | — |
| `F24` | Bazı Microsoft ergonomik klavyelerinde ve eski POS yazılımlarında rezerve. | Kullanılmaz. | — |

### 14.3 F13–F24'ü aktif olarak kullanan yaygın uygulamalar

Bu uygulamalarda ExtraKeyboard'ın HID yedek modu istenmeyen tetiklemelere
sebep olabilir. Her ikisini birden kullanıyorsan uygulamayı açık tut
(yedek moda düşmesin) veya çakışan kısayolu ilgili uygulamadan kaldır.

| Uygulama | Ne için kullanır |
|---|---|
| **OBS Studio / Streamlabs** | Sahne değiştirme, kayıt başlat/durdur — F13+ en çok önerilen hotkey aralığıdır |
| **Discord** | Bas-konuş (push-to-talk) tuşu olarak F13+ yaygın seçimdir |
| **Adobe Premiere Pro / After Effects** | Özel klavye düzenlerinde atanabilir |
| **DaVinci Resolve** | Klavye özelleştirmede F13–F20 kullanılabilir |
| **Karabiner-Elements (macOS)** | F13–F24'ü yakalar ve yeniden eşler; kural tanımlıysa tuşun davranışı değişir |
| **AutoHotkey (Windows)** | Betiklerde `F13::` gibi kancalar yaygındır |
| **Logitech G HUB / Corsair iCUE / Razer Synapse** | G-tuşlarını F13+ olarak eşler; aynı kodu iki cihaz gönderirse karışıklık olur |
| **VMware / Parallels / Uzak masaüstü** | F tuşlarını misafir işletim sistemine iletir; ana makinede beklediğin şey olmayabilir |

### 14.4 macOS'ta F tuşlarının varsayılan davranışı

macOS'ta **F1–F12** varsayılan olarak **donanım işlevi** üretir
(parlaklık, Mission Control, ses…). Bunları gerçek işlev tuşu yapmak için
 > **Sistem Ayarları** > **Klavye** > **Klavye Kısayolları…** >
**İşlev Tuşları** > *"F1, F2 vb. tuşları standart işlev tuşları olarak kullan"*
açılır.

**F13–F24 bu ayardan ETKİLENMEZ.** Onların donanım karşılığı yoktur,
her zaman düz işlev tuşu olarak gider. Yani ExtraKeyboard'ın HID yedek
modu bu ayardan bağımsız çalışır — ayrı bir şey yapmana gerek yoktur.

**macOS'ta F13–F22'yi kendine kısayol yapmak istersen:**

1.   > **Sistem Ayarları** > **Klavye** > **Klavye Kısayolları…**
2.  Soldan bir kategori seç (örn. **Uygulama Kısayolları**)
3.  **+** ile yeni kısayol ekle, menü komutunun adını yaz
4.  Kısayol alanına tıkla ve cihazdaki tuşa bas — `F13` görünür
5.  **Bitti**

**Uyarı:** macOS'ta bazı sistem iletişim kutuları F13–F15'i eski
Print Screen / Scroll Lock / Pause anlamlarıyla yorumlayabilir. Kritik
işler için `F16`–`F21` aralığını tercih et.

---

## Ek — Hızlı başvuru

### Sık kullanılan protokol komutları (LED & Cihaz > Elle Komut)

| Komut | Etki |
|---|---|
| `CMD PING` | Cihaz canlı mı? → `ACK PING` |
| `CMD ID` | Sürüm/seri/OS bilgisi → `ID 3.0.0 MK1 EK1-A4C138 WIN` |
| `CMD OS WIN` / `CMD OS MAC` | OS modunu zorla |
| `CMD LED 1 1E90FF` | LED1'i mavi yak |
| `CMD LED BRIGHT 60` | Parlaklığı 60 yap |
| `CMD ENC MODE HID` / `HOST` | Enkoder modunu değiştir |
| `CMD HIDFB ON` / `OFF` | HID yedek modunu aç/kapat |
| `CMD SAVE` | Ayarları cihazın NVS belleğine yaz |

### Yapılandırma dosyasının yeri

| | Yol |
|---|---|
| **v3 yapılandırma** | `<proje kökü>/config.json` |
| **v2 yapılandırma (eski)** | `<proje kökü>/macro_config.json` |
| **Yedek (taşıma sırasında)** | `<proje kökü>/config.json.bak` |

### İlgili dokümanlar

| Doküman | İçerik |
|---|---|
| `docs/00-CEKIRDEK-SPEC.md` | Tek doğruluk kaynağı — pinler, protokol, şema |
| `docs/07-MONTAJ-KILAVUZU.md` | Cihazın fiziksel montajı |
| `docs/08-SORUN-GIDERME.md` | Belirti → neden → çözüm tablosu |
