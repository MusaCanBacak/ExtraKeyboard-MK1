#ifndef EK_CONFIG_H
#define EK_CONFIG_H

// =====================================================================
//  ExtraKeyboard MK1 — Ortak yapılandırma başlığı
//  Buradaki her değer docs/00-CEKIRDEK-SPEC.md ile BİREBİR aynıdır.
//  Pin numaraları, renkler, süreler ve sürümler burada tek yerden
//  yönetilir; başka hiçbir dosyada sabit sayı yazılmaz.
// =====================================================================

#include <Arduino.h>

// ---------------------------------------------------------------------
//  1) Sürüm bilgileri (spec bölüm 10)
// ---------------------------------------------------------------------
#define EK_FW_VERSION       "3.0.0"
#define EK_HW_REV           "MK1"
#define EK_SERIAL_PREFIX    "EK1-"

// ---------------------------------------------------------------------
//  2) USB kimliği (spec bölüm 4)
// ---------------------------------------------------------------------
#define EK_USB_VID          0x303A
#define EK_USB_PID          0x82E1
#define EK_USB_MANUFACTURER "BlueDevelopment"
#define EK_USB_PRODUCT      "ExtraKeyboard MK1"

// ---------------------------------------------------------------------
//  3) CDC (native USB seri) nesnesinin adı
//     arduino-esp32 2.x  -> nesne adı `Serial`
//     arduino-esp32 3.x  -> nesne adı `USBSerial`
//     Tüm modüller doğrudan bu takma adı kullanır.
// ---------------------------------------------------------------------
#if ARDUINO_USB_CDC_ON_BOOT && !ARDUINO_USB_MODE
  #if defined(ESP_ARDUINO_VERSION_MAJOR) && (ESP_ARDUINO_VERSION_MAJOR >= 3)
    #define EK_SERIAL     USBSerial
  #else
    #define EK_SERIAL     Serial
  #endif
  #define EK_HAS_USB_CDC  1
#else
  // Bu durumda TinyUSB kapalıdır; HID çalışmaz. platformio.ini'yi kontrol et!
  #define EK_SERIAL       Serial
  #define EK_HAS_USB_CDC  0
#endif

// ---------------------------------------------------------------------
//  4) Pin şeması (spec bölüm 3.1 — DEĞİŞTİRİLEMEZ)
//     Tüm anahtarlar aktif-LOW, INPUT_PULLUP, matris yok, diyot yok.
// ---------------------------------------------------------------------
#define EK_PIN_K1        4
#define EK_PIN_K2        5
#define EK_PIN_K3        6
#define EK_PIN_K4        7
#define EK_PIN_K5        15
#define EK_PIN_K6        16
#define EK_PIN_K7        17
#define EK_PIN_K8        18
#define EK_PIN_K9        8
#define EK_PIN_K10       9    // COMBO tuşu
#define EK_PIN_K11       10   // OS tuşu (Windows / macOS)
#define EK_PIN_K12       21   // 10. işlev tuşu (J3-18)

#define EK_PIN_ENC_A     11   // EC11 A kanalı (+ RC donanım debounce)
#define EK_PIN_ENC_B     12   // EC11 B kanalı (+ RC donanım debounce)
#define EK_PIN_ENC_SW    13   // EC11 buton

// Durum LED'leri: 3 ayrı DÜZ (tek renk) LED, her biri kendi pininde.
// Devre: GPIO -> 330 Ω -> LED anot (uzun bacak); katot (kısa bacak) -> GND.
//   LED1 (Windows) : Windows modunda yanar
//   LED2 (macOS)   : macOS modunda yanar
//   Aktif OS LED'i : uygulama bağlıyken SABİT, bağlı değilken YAVAŞ yanıp söner
//   LED3 (COMBO)   : combo modunda yanar; tetiklenince çift flaş
#define EK_PIN_LED_WIN   14   // J1-20 (sol header)
#define EK_PIN_LED_MAC   42   // J3-6  (sağ header)
#define EK_PIN_LED_COMBO 41   // J3-7  (sağ header)

// ---------------------------------------------------------------------
//  5) Sayılar ve dizin sabitleri
//
//  TUŞ SAYISINI ARTIRMAK (bkz. docs/09-GENISLETME.md):
//    1. Yukarıya yeni EK_PIN_K13... tanımı ekle (boş GPIO'lar: 1, 2,
//       39, 40, 41, 42, 47; 38 ve 48 bazı kartlarda dahili RGB LED'dir).
//    2. EK_FN_KEY_COUNT değerini artır.
//    3. keys.cpp'deki KEY_PINS tablosuna pini AYNI SIRADA ekle.
//    4. PC tarafında app/core/config.py -> KEY_COUNT ve
//       app/ui/key_grid.py -> KEY_POSITIONS tablosunu güncelle.
//  K10/K11 indeksleri ve toplam sayı buradan OTOMATİK türetilir.
//  HID yedek modu F13..F24 ile sınırlıdır -> işlev tuşu en fazla 11 olabilir.
// ---------------------------------------------------------------------
#define EK_FN_KEY_COUNT   10                       // K1..K9 + K12 (işlev tuşları)
#define EK_KEY_INDEX_K10  (EK_FN_KEY_COUNT)        // dizide K10 (COMBO)
#define EK_KEY_INDEX_K11  (EK_FN_KEY_COUNT + 1)    // dizide K11 (OS)
#define EK_KEY_COUNT      (EK_FN_KEY_COUNT + 2)    // işlev + K10 + K11
#define EK_LED_COUNT      3   // LED1..LED3

#if EK_FN_KEY_COUNT > 11
#error "HID yedek modu F13..F24 ile sinirli: islev tusu sayisi en fazla 11 olabilir"
#endif

// ---------------------------------------------------------------------
//  6) Zamanlama sabitleri (ms) — spec bölüm 5 ve 6
// ---------------------------------------------------------------------
// TUŞ DEBOUNCE — 8 ms (anahtar: Cherry MX Blue, clicky)
//  MX Blue iki parçalı bir slider kullanır: gövde içinde ayrı bir "click
//  jacket" (tık ceketi) vardır. Tuş BIRAKILIRKEN bu ceket stemden ayrılıp
//  geri çarpar; bu mekanik darbe, veri sayfasındaki <= 5 ms'lik tipik
//  sıçramanın ÜSTÜNE bırakış tarafında EK kontak sıçraması bindirir.
//  Yıpranmış bir mavi anahtarda bu ek sıçrama 10 ms'ye yaklaşabilir.
//  5 ms'de kalınırsa tek bir basış İKİ kez eylem tetikleyebilir — bir makro
//  klavyede bu, atanan uygulamanın iki kez açılması demektir.
//  8 ms bu senaryoyu kapatır ve makro klavyede hissedilmez (bu cihazla hızlı
//  yazı yazılmıyor; tuş başına saniyede birkaç basış en fazlası).
//
//  AYAR REHBERİ (tek yer burasıdır, başka dosyada sayı yazılmaz):
//    - Lineer (MX Red/Black) veya taktil (MX Brown) anahtara geçerseniz
//      click jacket olmadığı için 5 ms'e düşürebilirsiniz.
//    - Hâlâ çift tetikleme görüyorsanız (tek basışta iki EV KEY DOWN/UP)
//      12 ms'e çıkarın; 15 ms üzeri gecikme fark edilmeye başlar.
#define EK_KEY_DEBOUNCE_MS        8     // tuş yazılım debounce (MX Blue clicky)

// ENKODER BUTONU DEBOUNCE — 5 ms (bilinçli olarak tuşlardan FARKLI)
//  EC11'in gömülü butonu basit tek parçalı bir kubbe/kontak mekanizmasıdır;
//  click jacket yoktur, dolayısıyla bırakış tarafında ek sıçrama üretmez.
//  Veri sayfası sıçraması için 5 ms yeterlidir ve enkoder butonunu
//  gereksiz yavaşlatmamak için düşük tutulur.
#define EK_ENC_SW_DEBOUNCE_MS     5     // enkoder butonu debounce (EC11 kubbe)

// COMBO KİLİT ZAMAN AŞIMI — combo bas-çek (latch) ve KALICIDIR: KOMBO'ya
//  basınca mod açılır, combo tetiklense bile AÇIK KALIR; kapatmak için
//  KOMBO'ya tekrar basılır (kullanıcı kararı, 2026-08-18). 0 = zaman aşımı
//  yok; bir süre sonra kendiliğinden kapansın istenirse ms cinsinden değer
//  verilebilir.
#define EK_COMBO_LATCH_TIMEOUT_MS 0

// COMBO ÇEVRİMDIŞI ZAMAN AŞIMI — uygulama BAĞLI DEĞİLKEN geçerli üst sınır.
//  Combo modu açıkken 10 işlev tuşu ne EV KEY ne de HID kodu üretir; olay
//  yalnızca PC uygulamasına EV COMBO olarak teslim edilir. Uygulama bağlı
//  değilken bu olayı alacak kimse yoktur, dolayısıyla modda unutulan cihazda
//  10 tuş SÜRESİZ ölü kalır (tek çıkış: KOMBO'ya tekrar basmak).
//  Bu yüzden çevrimdışıyken EK_COMBO_LATCH_TIMEOUT_MS 0 (kapalı) olsa bile
//  mod bu süre sonunda kendiliğinden kapatılır. 0 yapılırsa bu koruma da
//  devre dışı kalır.
#define EK_COMBO_OFFLINE_TIMEOUT_MS 10000

#define EK_ENC_LONG_PRESS_MS      800   // EV ENC LONG eşiği
#define EK_OS_SHORT_PRESS_MS      800   // K11 kısa basış üst sınırı
#define EK_OS_LONG_PRESS_MS       3000  // K11 uzun basış (HID yedek toggle)
#define EK_HEARTBEAT_MS           1000  // HB <uptime_ms> gönderim aralığı
#define EK_LINK_TIMEOUT_MS        3000  // yalnızca tanılama: son komuttan bu
                                        // yana geçen "tazelik" süresi.
                                        // DİKKAT: bağlı/değil kararı SADECE
                                        // CDC DTR sinyaline bakar (spec 5.3).

// ---------------------------------------------------------------------
//  7) LED zamanlamaları (ms) — spec bölüm 6.4
// ---------------------------------------------------------------------
#define EK_LED_COMBO_FLASH_MS     150   // LED2 combo tetiklendi yeşil flaş
#define EK_LED_KEY_FLASH_MS       80    // LED3 tuş aktivitesi mavi flaş
#define EK_LED_WHITE_BLINK_MS     120   // beyaz flaş yarı periyodu
#define EK_LED_WHITE_BLINK_COUNT  3     // K11 uzun basışta 3 kez beyaz
#define EK_LED_RED_BLINK_MS       250   // combo engelli kırmızı yanıp sönme
#define EK_LED_MIN_REFRESH_MS     10    // iki show() arası asgari süre

// ---------------------------------------------------------------------
//  8) Renkler (0xRRGGBB) — spec bölüm 6.4 ve 7
// ---------------------------------------------------------------------
#define EK_COLOR_OFF              0x000000UL
#define EK_COLOR_OS_WIN           0x1E90FFUL  // Windows — mavi
#define EK_COLOR_OS_MAC           0xFFFFFFUL  // macOS — beyaz
#define EK_COLOR_COMBO            0xFF9500UL  // combo modu — turuncu
#define EK_COLOR_COMBO_FIRED      0x2CC985UL  // combo tetiklendi — yeşil
#define EK_COLOR_LINK_OK          0x2CC985UL  // uygulama bağlı — yeşil
#define EK_COLOR_LINK_ERR         0xE04F5FUL  // uygulama yok — kırmızı
#define EK_COLOR_KEY_FLASH        0x3B8ED0UL  // tuş aktivitesi — mavi
#define EK_COLOR_WHITE            0xFFFFFFUL  // beyaz bildirim flaşı

#define EK_LED_DEFAULT_BRIGHTNESS 60          // spec: varsayılan 60/255

// LED TEMEL RENK YUVALARI
//  `CMD LED <i> <RRGGBB>` bir LED'i sabit renge KİLİTLEMEZ; o LED'in o anki
//  duruma karşılık gelen TEMEL rengini günceller. Durum mantığı (combo flaşı,
//  tuş flaşı, beyaz bildirim, bağlantı rengi) bu temel rengin üzerinde
//  çalışmaya devam eder (bkz. docs/03-PROTOKOL.md 3.2).
//    LED1 -> o anki OS moduna göre OS_WIN veya OS_MAC yuvası
//    LED2 -> COMBO yuvası (combo modu turuncusu)
//    LED3 -> o anki bağlantı durumuna göre LINK_OK veya LINK_ERR yuvası
enum EkLedColorSlot : uint8_t {
    EK_LED_SLOT_OS_WIN   = 0,
    EK_LED_SLOT_OS_MAC   = 1,
    EK_LED_SLOT_COMBO    = 2,
    EK_LED_SLOT_LINK_OK  = 3,
    EK_LED_SLOT_LINK_ERR = 4,
    EK_LED_SLOT_COUNT    = 5,
    EK_LED_SLOT_NONE     = 0xFF   // geçersiz indeks
};

// ---------------------------------------------------------------------
//  9) Mod numaralandırmaları
// ---------------------------------------------------------------------

// İşletim sistemi modu (K11 ile veya `CMD OS ...` ile değişir)
enum EkOsMode : uint8_t {
    EK_OS_WIN = 0,
    EK_OS_MAC = 1
};

// Enkoder modu (`CMD ENC MODE HID|HOST`)
//  HID  : cihaz doğrudan Consumer Control ses tuşu gönderir
//  HOST : ne yapılacağına PC uygulaması karar verir
enum EkEncoderMode : uint8_t {
    EK_ENC_MODE_HID  = 0,
    EK_ENC_MODE_HOST = 1
};

// ---------------------------------------------------------------------
//  10) Protokol tampon boyutları (spec bölüm 5)
// ---------------------------------------------------------------------
#define EK_LINE_BUFFER_SIZE   128   // gelen komut satırı azami uzunluğu
                                    // (docs/03-PROTOKOL.md 2.1: 128 bayt;
                                    //  aşan satır atılır -> ERR TOO_LONG)
#define EK_TX_BUFFER_SIZE     96    // giden olay satırı azami uzunluğu
#define EK_RX_CHUNK_LIMIT     256   // update() başına okunacak azami bayt
#define EK_SERIAL_STR_SIZE    16    // "EK1-A4C138" + sonlandırıcı

#endif  // EK_CONFIG_H
