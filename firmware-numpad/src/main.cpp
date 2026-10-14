// =====================================================================
//  ExtraKeyboard MK1 — Ana firmware
//  Kaynak: docs/00-CEKIRDEK-SPEC.md (tek doğruluk kaynağı)
//
//  Cihaz "aptal"dır: hangi tuşa basıldığını CDC üzerinden bildirir,
//  ne yapılacağına PC uygulaması karar verir. Uygulama bağlı değilse
//  cihaz HID yedek moduna düşerek F13..F23 ve ses tuşlarını gönderir.
//
//  loop() içinde HİÇBİR bekleme yoktur; tüm zamanlamalar millis() ile
//  yapılır ve LED flaşları bloklamayan zamanlayıcılarla yürütülür.
// =====================================================================

#include <Arduino.h>
#include "USB.h"
#include "esp_system.h"   // esp_reset_reason(): tanılama satırı için
#include "esp_task_wdt.h" // loop() kilitlenirse otomatik reset (EK_LOOP_WDT_SEC)

#include "config.h"
#include "storage.h"
#include "keys.h"
// NUMPAD: enkoder YOK — encoder modülü bu varyanta dahil değildir.
#include "leds.h"
#include "protocol.h"
#include "hid.h"

// ---------------------------------------------------------------------
//  Genel durum
// ---------------------------------------------------------------------
static EkSettings g_settings;
static char       g_serialNumber[EK_SERIAL_STR_SIZE];

static bool     g_linked           = false;  // PC uygulaması bağlı mı
static bool     g_hidActive        = false;  // HID yedek modu şu an devrede mi
static uint32_t g_lastHeartbeatMs  = 0;

static EkProtocolHandlers g_handlers;

// ---------------------------------------------------------------------
//  Yardımcılar
// ---------------------------------------------------------------------

// Çip MAC adresinin son 3 baytından "EK1-A4C138" biçiminde seri no üretir.
static void buildSerialNumber() {
    uint64_t mac = ESP.getEfuseMac();
    uint8_t b3 = (uint8_t)((mac >> 24) & 0xFF);
    uint8_t b4 = (uint8_t)((mac >> 32) & 0xFF);
    uint8_t b5 = (uint8_t)((mac >> 40) & 0xFF);
    snprintf(g_serialNumber, sizeof(g_serialNumber), "%s%02X%02X%02X",
             EK_SERIAL_PREFIX, b3, b4, b5);
}

// Bağlantı durumunu yeniden hesaplar ve LED / HID modunu günceller.
//
// ÖLÇÜT: yalnızca CDC DTR sinyali (spec bölüm 5.3 — "PC uygulaması bağlı
// değilken (CDC DTR düşük) cihaz HID yedek moduna düşer"). Cihaz PC'nin
// canlılığını ayrıca yoklamaz; uygulamadan periyodik komut BEKLENMEZ.
// (Komut tazeliği yalnızca tanılama için Protocol::commandRecent() ile
//  okunabilir; bağlantı kararında kullanılmaz.)
static void updateLinkState(uint32_t now, bool force) {
    // Bağlantı ölçütü İKİ kanallıdır:
    //   1) CDC DTR sinyali (spec 5.3) — hızlı ve doğrudan, ama bazı
    //      işletim sistemi/sürücü birleşimlerinde host tarafından hiç
    //      yükseltilmez; o durumda cihaz "uygulama yok" sanır ve OS LED'i
    //      boş yere yanıp söner.
    //   2) TAZE KOMUT — uygulama saniyede bir `CMD PING` gönderir; son
    //      3 sn içinde komut geldiyse uygulama kesinlikle bağlıdır.
    // İkisinden biri yeterlidir; böylece DTR'si çalışmayan ortamlarda da
    // bağlantı doğru algılanır.
    // ÖLÇÜT: son 3 saniye içinde uygulamadan komut geldi mi?
    //
    // DTR TEK BAŞINA GÜVENİLMEZ: kart USB'den düştüğünde ya da host portu
    // düzgün kapatmadığında CDC'nin "bağlı" bayrağı son değerinde takılı
    // kalabiliyor; cihaz bağlantı koptuğu hâlde bağlıymış gibi davranıyor
    // ve durum LED'i hiç değişmiyordu. Uygulama saniyede bir `CMD PING`
    // gönderdiği için komut tazeliği hem daha doğru hem de daha hızlıdır:
    // uygulama kapanır kapanmaz (veya kart USB'den düşer düşmez) 3 saniye
    // içinde bağlantı yok sayılır ve LED çift darbeye geçer.
    // hostDtr() yalnızca tanılama amacıyla korunur.
    bool linked = Protocol::commandRecent(now);

    // HID yedek modu yalnızca uygulama yokken ve özellik açıkken devrededir.
    bool hidActive = (!linked) && g_settings.hidFallback;

    if (!force && linked == g_linked && hidActive == g_hidActive) {
        return;
    }

    if (hidActive != g_hidActive) {
        g_hidActive = hidActive;
        Hid::releaseAll();   // mod değişiminde takılı tuş kalmasın
    }
    bool oncedenBagliydi = g_linked;
    g_linked = linked;

    // Combo durum makinesine bağlantı durumunu bildir: uygulama yokken
    // EV COMBO teslim edilemediği için combo modu çevrimdışı zaman aşımıyla
    // kendiliğinden kapanmalı, aksi hâlde 10 işlev tuşu süresiz ölü kalır.
    Keys::setLinked(g_linked);

    Leds::setLinkState(g_linked);
    Leds::setComboBlocked(Keys::comboModeActive() && g_hidActive);

    // TANILAMA (bağlantı kararlılığı analizi): her bağlantı kurulumunda
    // son sıfırlanma nedeni + çalışma süresi raporlanır. "DBG" satırları
    // PC uygulamasının ayrıştırıcısı tarafından sessizce yok sayılır
    // (docs/03 bölüm 7.2 bilinmeyen satır kuralı); yalnızca elle seri
    // izleme/analiz içindir. uptime küçükse cihaz yeni açılmış demektir
    // (çökme-döngüsü teşhisinde kritik ipucu).
    if (linked && !oncedenBagliydi) {
        static const char *NEDEN[] = {
            "BILINMIYOR", "GUC_ACILISI", "HARICI_RST", "YAZILIM_RST",
            "PANIK", "INT_WDT", "TASK_WDT", "DIGER_WDT",
            "DERIN_UYKU", "BROWNOUT", "SDIO", "USB", "JTAG"
        };
        int neden = (int)esp_reset_reason();
        const char *ad = (neden >= 0 && neden < 13) ? NEDEN[neden] : "?";
        // Doğrudan EK_SERIAL.printf() KULLANILMAZ: o yol host okumayı
        // bıraktığında TX FIFO'da sonsuz bloklar (bkz. protocol.cpp sendLine).
        // Satır ayrıca İKİYE bölündü; CDC TX FIFO'su 64 bayt olduğu için tek
        // parça hâlinde asla sığmıyordu ve tamamen düşerdi.
        char dbg[EK_TX_BUFFER_SIZE];
        snprintf(dbg, sizeof(dbg), "DBG BOOT reset=%d(%s) fw=%s",
                 neden, ad, EK_FW_VERSION);
        Protocol::sendLine(dbg);
        snprintf(dbg, sizeof(dbg), "DBG BOOT uptime_ms=%lu heap=%lu",
                 (unsigned long)millis(),
                 (unsigned long)ESP.getFreeHeap());
        Protocol::sendLine(dbg);
    }
}

// ---------------------------------------------------------------------
//  MOD DEĞİŞTİRME KOMBOSU: "0"ı BASILI TUT + Enter'a bas
//
//  Numpad'in ayrı OS tuşu yoktur; Windows/macOS geçişi iki tuşla yapılır.
//  Ters-satır düzeninde fiziksel EN ALT sıra 0 . ⏎ + olduğundan:
//    Tuş 1 = KP0 ("0")  -> DEĞİŞTİRİCİ (basılı tutulur)
//    Tuş 3 = KPEnter    -> TETİKLEYİCİ (0 basılıyken buna basınca mod değişir)
//
//  DAVRANIŞ:
//   - "0"ı basılı tut, Enter'a bas -> mod değişir; NE "0" NE Enter yazılır
//     (sızıntısız) ve iki LED birlikte yanıp söner (mod değişti geri bildirimi).
//   - "0"a bas-bırak (Enter gelmeden) -> normal "0" BIRAKIŞTA yazılır. Yani "0"
//     basılıyken YAZMAZ; bir değiştirici gibi bekler. (Not: "0" otomatik tekrar
//     etmez.) Bu cihaz hızlı yazı için değildir, gecikme hissedilmez.
//   - Enter'a "0" basılı DEĞİLKEN basmak -> normal Enter (anında).
//   - "0" basılı tutulurken her Enter basışı modu bir kez değiştirir (aç-kapa).
// ---------------------------------------------------------------------
static const uint8_t MOD_HOLD_KEY = 1;   // Tuş 1 = KP0 ("0")  — basılı tutulan (modifier)
static const uint8_t MOD_TRIG_KEY = 3;   // Tuş 3 = KPEnter    — tetikleyici

static bool g_zeroHeld     = false;  // "0" fiziksel olarak basılı mı
static bool g_zeroConsumed = false;  // "0" komboda kullanıldı -> bırakışta yazma
static bool g_enterIsChord = false;  // Enter'ın bu basışı komboyu tetikledi

// Windows <-> macOS geçişi: NVS'e yaz, LED göstergesini güncelle, geri bildir.
static void doModeSwitch() {
    g_settings.osMode = (g_settings.osMode == EK_OS_WIN) ? EK_OS_MAC : EK_OS_WIN;
    Storage::save(&g_settings);
    Leds::setOsMode(g_settings.osMode);
    Leds::blinkWhite();                   // iki LED birlikte 3x = "mod değişti"
    Protocol::sendOs(g_settings.osMode);  // uygulama varsa haber ver (yoksa yok sayılır)
}

// ---------------------------------------------------------------------
//  Tuş olay geri çağırımları
// ---------------------------------------------------------------------

// İşlev tuşu basıldı/bırakıldı: PC'ye bildir, HID gönder. NUMPAD'de HID
// KOŞULSUZDUR (eş uygulama yok, tak-çalıştır). "0" ve Enter, mod kombosu için
// özel yoldan geçer (yukarıya bakınız).
static void onKeyEvent(uint8_t keyNo, bool pressed) {
    Protocol::sendKey(keyNo, pressed);

    // --- "0" tuşu: mod değiştirici. Basılıyken YAZMAZ; bekler. ---
    if (keyNo == MOD_HOLD_KEY) {
        if (pressed) {
            Leds::flashKeyActivity();
            g_zeroHeld     = true;
            g_zeroConsumed = false;
        } else {
            g_zeroHeld = false;
            if (g_zeroConsumed) {
                g_zeroConsumed = false;        // komboda kullanıldı -> "0" yazma
            } else {
                Hid::keyDown(MOD_HOLD_KEY);    // normal tık -> bırakışta "0" yaz
                Hid::keyUp(MOD_HOLD_KEY);
            }
        }
        return;
    }

    // --- Enter tuşu: "0" basılıysa KOMBO, değilse normal Enter ---
    if (keyNo == MOD_TRIG_KEY) {
        if (pressed) {
            if (g_zeroHeld) {
                g_zeroConsumed = true;         // KOMBO: modu değiştir, yazma yok
                g_enterIsChord = true;
                doModeSwitch();
            } else {
                g_enterIsChord = false;
                Leds::flashKeyActivity();
                Hid::keyDown(MOD_TRIG_KEY);
            }
        } else {
            if (g_enterIsChord) {
                g_enterIsChord = false;        // komboydu -> keyUp yok
            } else {
                Hid::keyUp(MOD_TRIG_KEY);
            }
        }
        return;
    }

    // --- Normal tuşlar: anında HID (gecikme yok) ---
    if (pressed) {
        Leds::flashKeyActivity();
        Hid::keyDown(keyNo);   // NUMPAD: koşulsuz gerçek keypad kodu
    } else {
        Hid::keyUp(keyNo);
    }
}

// Combo tetiklendi: EV COMBO gönder ve LED2'yi 150 ms yeşil flaşla.
static void onComboEvent(uint8_t a, uint8_t b) {
    Protocol::sendCombo(a, b);
    Leds::flashComboFired();
}

// K10 basıldı/bırakıldı: combo modunu bildir, LED2'yi ve LED3 uyarısını ayarla.
static void onComboMode(bool on) {
    Protocol::sendComboMode(on);
    Leds::setComboMode(on);
    Leds::setComboBlocked(on && g_hidActive);
    if (on) {
        // Combo modunda işlev tuşları için HID kodu gönderilmez; takılı tuş varsa bırak.
        Hid::releaseAll();
    }
}

// K11 basışı tamamlandı.
//  kısa (<800 ms) -> Windows/macOS geçişi, NVS'e kaydet, EV OS gönder
//  uzun (>=3 s)   -> HID yedek modunu aç/kapat, LED3 üç kez beyaz yanar
static void onOsKey(bool longPress) {
    if (longPress) {
        g_settings.hidFallback = !g_settings.hidFallback;
        Storage::save(&g_settings);
        Leds::blinkWhite();
        updateLinkState(millis(), true);
    } else {
        g_settings.osMode = (g_settings.osMode == EK_OS_WIN) ? EK_OS_MAC
                                                             : EK_OS_WIN;
        Storage::save(&g_settings);
        Leds::setOsMode(g_settings.osMode);
        Protocol::sendOs(g_settings.osMode);
        if (g_hidActive) {
            Hid::osKeyTap();   // spec 5.3: K11 -> F23
        }
    }
}

// NUMPAD: enkoder yok — onEncRotate/onEncButton kaldırıldı.

// ---------------------------------------------------------------------
//  Protokol komut işleyicileri
// ---------------------------------------------------------------------

// CMD ID -> "ID <fw> <hw> <serial> <os>"
static void handleIdRequest() {
    Protocol::sendId(g_serialNumber, g_settings.osMode);
}

// CMD PING -> ACK yanıtı protokol katmanında üretilir; ek iş yok.
static void handlePing() {
    // Kalp atışı cevabı zaten bağlantı zamanlayıcısını tazeledi.
}

// CMD OS WIN|MAC -> OS modunu PC'den zorla ve NVS'e yaz.
// (docs/03-PROTOKOL.md 3.2: "OS modunu ayarlar, NVS'e yazar" — K11 ile
//  yapılan geçişle birebir aynı davranış.)
static void handleSetOs(uint8_t osMode) {
    g_settings.osMode = osMode;
    Leds::setOsMode(osMode);
    Storage::save(&g_settings);
}

// CMD LED <i> <RRGGBB> -> ilgili LED'in TEMEL rengini güncelle.
// LED sabitlenmez: combo/tuş/beyaz flaşlar ve bağlantı rengi çalışmaya
// devam eder. color < 0 (CMD LED <i> AUTO) spec varsayılanına döner.
static void handleSetLed(uint8_t index, int32_t color) {
    uint8_t slot = Leds::slotForIndex(index);
    if (slot >= EK_LED_SLOT_COUNT) {
        return;
    }
    Leds::setSlotColor(slot, color);
    g_settings.ledColor[slot] = (color < 0) ? -1 : (color & 0x00FFFFFFL);
}

// CMD LED BRIGHT <0-255> -> genel parlaklık.
// CMD LED <i> TEST -> donanım testi: LED'i durum mantığından bağımsız yakar.
static void handleLedTest(uint8_t index) {
    Leds::testPulse(index);
}

static void handleSetBrightness(uint8_t value) {
    g_settings.ledBrightness = value;
    Leds::setBrightness(value);
}

// CMD ENC MODE HID|HOST -> enkoderin ses tuşunu kimin göndereceği.
static void handleEncoderMode(uint8_t mode) {
    g_settings.encoderMode = mode;
}

// CMD HIDFB ON|OFF -> HID yedek modu özelliğini aç/kapat ve NVS'e yaz.
// (docs/03-PROTOKOL.md 3.2: "Ayar NVS'e yazılır" — K11 uzun basışıyla aynı.)
static void handleHidFallback(bool enabled) {
    g_settings.hidFallback = enabled;
    Storage::save(&g_settings);
    updateLinkState(millis(), true);
}

// CMD SAVE -> ayarları NVS'e yaz. Başarısızsa protokol katmanı ERR NVS üretir.
static bool handleSave() {
    return Storage::save(&g_settings);
}

// ---------------------------------------------------------------------
//  setup / loop
// ---------------------------------------------------------------------

// Donanımı, USB kimliğini ve tüm modülleri kurar.
void setup() {
    // 0) Kart üzerindeki dahili RGB LED'ini (GPIO48) söndür.
    //
    // Bu firmware dahili RGB LED'i KULLANMAZ; durum LED'leri harici (GPIO14/
    // 41/42). Ancak DevKitC tipi kartlarda WS2812 data hattı boşta kalınca LED
    // rastgele (çoğunlukla BEYAZ) yanar. Açıkça bir "kapalı" (0,0,0) çerçevesi
    // göndermek onu söndürür ve öyle bırakır.
    //
    // TinyUSB ÇAKIŞMA NOTU: bu projede daha önce RMT tabanlı sürekli LED
    // sürüşü TinyUSB ile çakışıp boot-loop yapmıştı. Burada RMT YALNIZCA BİR
    // KEZ, USB.begin()'den ÖNCE kullanılır ve hemen serbest bırakılır; sürekli
    // bir sürüş yoktur, bu yüzden USB yığınıyla çakışmaz.
#ifdef RGB_BUILTIN
    neopixelWrite(RGB_BUILTIN, 0, 0, 0);
#endif

    // 1) USB kimliği — HID kaydı ve USB.begin() çağrılmadan ÖNCE ayarlanır.
    buildSerialNumber();
    USB.VID(EK_USB_VID);
    USB.PID(EK_USB_PID);
    USB.manufacturerName(EK_USB_MANUFACTURER);
    USB.productName(EK_USB_PRODUCT);
    USB.serialNumber(g_serialNumber);

    // 2) Kalıcı ayarlar
    Storage::begin();
    Storage::load(&g_settings);

    // 3) Girişler
    Keys::begin();
    Keys::setCallbacks(onKeyEvent, onComboEvent, onComboMode, onOsKey);
    // NUMPAD: enkoder yok — Enc::begin()/setCallbacks() çağrılmaz.

    // 4) Durum LED'leri
    Leds::begin(g_settings.ledBrightness);
    Leds::setOsMode(g_settings.osMode);
    Leds::setComboMode(false);
    Leds::setLinkState(false);
    Leds::setComboBlocked(false);
    // Kayıtlı temel renkler yuva bazlı geri yüklenir; böylece OS modu veya
    // bağlantı durumu ne olursa olsun doğru renk doğru duruma bağlanır.
    for (uint8_t i = 0; i < EK_LED_SLOT_COUNT; i++) {
        Leds::setSlotColor(i, g_settings.ledColor[i]);
    }

    // 5) HID arayüzleri TinyUSB'ye kaydedilir, ardından USB başlatılır.
    Hid::begin();
    USB.begin();

    // 6) CDC protokol katmanı
    g_handlers.onIdRequest     = handleIdRequest;
    g_handlers.onPing          = handlePing;
    g_handlers.onSetOs         = handleSetOs;
    g_handlers.onSetLed        = handleSetLed;
    g_handlers.onSetBrightness = handleSetBrightness;
    g_handlers.onLedTest       = handleLedTest;
    g_handlers.onEncoderMode   = handleEncoderMode;
    g_handlers.onHidFallback   = handleHidFallback;
    g_handlers.onSave          = handleSave;

    Protocol::begin();
    Protocol::setHandlers(&g_handlers);

    // 7) Başlangıç durumu
    uint32_t now = millis();
    g_lastHeartbeatMs = now;
    updateLinkState(now, true);
    Leds::update(now);

    // 8) Bekçi köpeği — loop() kilitlenirse kart KENDİ KENDİNE kurtulsun.
    // Bu setup() zaten loopTask içinde çalıştığı için esp_task_wdt_add(NULL)
    // doğrudan loop görevini abone eder. loop() her turda beslemezse
    // (EK_LOOP_WDT_SEC boyunca) panic=true ile kart resetlenir.
    // Ayrıntılı gerekçe config.h'de EK_LOOP_WDT_SEC yanında.
    esp_task_wdt_init(EK_LOOP_WDT_SEC, true);
    esp_task_wdt_add(NULL);
}

// Ana olay döngüsü — hiçbir adım bloklamaz.
void loop() {
    uint32_t now = millis();

    // Bekçi köpeğini besle. Buraya ulaşamazsak (aşağıdaki adımlardan biri
    // kilitlendiyse) EK_LOOP_WDT_SEC sonunda kart kendini resetler.
    esp_task_wdt_reset();

    Keys::update(now);        // 16 tuş + debounce
    Protocol::update(now);    // gelen CDC satırlarını ayrıştır
    Protocol::txWatchdog(now);// CDC TX kalıcı tıkandıysa kurtar (bkz. EK_TX_STUCK_MS)
    updateLinkState(now, false);
    Leds::update(now);        // renkleri hesapla, değiştiyse şeride yaz

    // Kalp atışı: her 1000 ms'de bir "HB <uptime_ms>"
    if ((uint32_t)(now - g_lastHeartbeatMs) >= EK_HEARTBEAT_MS) {
        g_lastHeartbeatMs = now;
        Protocol::sendHeartbeat(now);
    }
}
