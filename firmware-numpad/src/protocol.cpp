// =====================================================================
//  protocol.cpp — CDC satır tabanlı protokol gerçeklemesi
//  Spec bölüm 5.1 (event) ve 5.2 (command)
// =====================================================================

#include "protocol.h"

#if EK_HAS_USB_CDC
#include "USB.h"
#include "USBCDC.h"
// usb_persist_restart() / RESTART_BOOTLOADER — "CMD BOOTLOADER CONFIRM" için.
#include "esp32-hal-tinyusb.h"
#include "soc/rtc_cntl_reg.h"  // RTC_CNTL_OPTION1_REG: FORCE_DOWNLOAD_BOOT
#include "esp_system.h"        // esp_restart(): TX tikanma kurtarmasi
#endif

#include <string.h>
#include <stdio.h>
#include <stdlib.h>

namespace {

char     g_rxBuffer[EK_LINE_BUFFER_SIZE];
uint16_t g_rxLen      = 0;
bool     g_rxOverflow = false;   // satır çok uzunsa tamamı atılır

char     g_txBuffer[EK_TX_BUFFER_SIZE];

const EkProtocolHandlers *g_handlers = nullptr;

uint32_t g_lastCommandMs = 0;
bool     g_gotCommand    = false;

// CDC TX'e YAZILAMADIGI andan itibaren gecen sure icin baslangic damgasi.
// 0 = tikanma yok. Bkz. Protocol::txWatchdog / EK_TX_STUCK_MS.
uint32_t g_txBlockedSinceMs = 0;

// Baştaki ve sondaki boşlukları temizler; işlenecek ilk karakteri döndürür.
char *trimLine(char *line) {
    while (*line == ' ' || *line == '\t') {
        line++;
    }
    size_t len = strlen(line);
    while (len > 0 && (line[len - 1] == ' ' || line[len - 1] == '\t' ||
                       line[len - 1] == '\r')) {
        line[len - 1] = '\0';
        len--;
    }
    return line;
}

// "1E90FF" biçimindeki 6 haneli onaltılık rengi çözer.
bool parseHexColor(const char *text, uint32_t *out) {
    if (text == nullptr || strlen(text) != 6) {
        return false;
    }
    uint32_t value = 0;
    for (uint8_t i = 0; i < 6; i++) {
        char c = text[i];
        uint8_t digit;
        if (c >= '0' && c <= '9') {
            digit = (uint8_t)(c - '0');
        } else if (c >= 'A' && c <= 'F') {
            digit = (uint8_t)(c - 'A' + 10);
        } else if (c >= 'a' && c <= 'f') {
            digit = (uint8_t)(c - 'a' + 10);
        } else {
            return false;
        }
        value = (value << 4) | digit;
    }
    *out = value;
    return true;
}

// Yalnızca rakamlardan oluşan bir tam sayıyı çözer.
bool parseUnsigned(const char *text, uint32_t *out) {
    if (text == nullptr || *text == '\0') {
        return false;
    }
    uint32_t value = 0;
    for (const char *p = text; *p != '\0'; p++) {
        if (*p < '0' || *p > '9') {
            return false;
        }
        value = value * 10 + (uint32_t)(*p - '0');
        if (value > 100000UL) {
            return false;
        }
    }
    *out = value;
    return true;
}

// CMD OS ... komutunu işler.
void handleOsCommand(char *arg) {
    if (arg != nullptr && strcmp(arg, "WIN") == 0) {
        if (g_handlers != nullptr && g_handlers->onSetOs != nullptr) {
            g_handlers->onSetOs(EK_OS_WIN);
        }
        Protocol::sendAck("OS WIN");
    } else if (arg != nullptr && strcmp(arg, "MAC") == 0) {
        if (g_handlers != nullptr && g_handlers->onSetOs != nullptr) {
            g_handlers->onSetOs(EK_OS_MAC);
        }
        Protocol::sendAck("OS MAC");
    } else if (arg == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);   // "CMD OS"
    } else {
        Protocol::sendErr(EK_ERR_BAD_VALUE);  // "CMD OS LINUX"
    }
}

// CMD LED ... komutunu işler (hem renk hem parlaklık biçimi).
void handleLedCommand(char *arg1, char *arg2) {
    if (arg1 == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);   // "CMD LED"
        return;
    }

    // --- CMD LED BRIGHT <0-255> ---
    if (strcmp(arg1, "BRIGHT") == 0) {
        uint32_t value = 0;
        if (arg2 == nullptr) {
            Protocol::sendErr(EK_ERR_BAD_ARGS);    // "CMD LED BRIGHT"
            return;
        }
        if (!parseUnsigned(arg2, &value)) {
            Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD LED BRIGHT ABC"
            return;
        }
        if (value > 255) {
            Protocol::sendErr(EK_ERR_RANGE);       // "CMD LED BRIGHT 300"
            return;
        }
        if (g_handlers != nullptr && g_handlers->onSetBrightness != nullptr) {
            g_handlers->onSetBrightness((uint8_t)value);
        }
        snprintf(g_txBuffer, sizeof(g_txBuffer), "LED BRIGHT %lu",
                 (unsigned long)value);
        Protocol::sendAck(g_txBuffer);
        return;
    }

    // --- CMD LED <i> <RRGGBB>  (veya AUTO ile varsayılan renge dönüş) ---
    uint32_t index = 0;
    if (!parseUnsigned(arg1, &index)) {
        Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD LED X FFFFFF"
        return;
    }
    // index 0 yalnızca TEST için geçerlidir ("hepsi"); renk komutunda değil.
    if (index > EK_LED_COUNT || (index == 0 && (arg2 == nullptr ||
                                                strcmp(arg2, "TEST") != 0))) {
        Protocol::sendErr(EK_ERR_RANGE);       // "CMD LED 4 FFFFFF"
        return;
    }
    if (arg2 == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);    // "CMD LED 1"
        return;
    }

    // --- CMD LED <i> TEST : donanım testi (düz LED'de renk yerine yakma) ---
    if (strcmp(arg2, "TEST") == 0) {
        if (g_handlers != nullptr && g_handlers->onLedTest != nullptr) {
            g_handlers->onLedTest((uint8_t)index);
        }
        snprintf(g_txBuffer, sizeof(g_txBuffer), "LED %lu TEST",
                 (unsigned long)index);
        Protocol::sendAck(g_txBuffer);
        return;
    }

    int32_t color;
    if (strcmp(arg2, "AUTO") == 0) {
        color = -1;   // spec bölüm 6.4'teki varsayılan renge dön
    } else {
        uint32_t rgb = 0;
        if (!parseHexColor(arg2, &rgb)) {
            Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD LED 1 ZZZZZZ"
            return;
        }
        color = (int32_t)rgb;
    }

    if (g_handlers != nullptr && g_handlers->onSetLed != nullptr) {
        g_handlers->onSetLed((uint8_t)index, color);
    }
    if (color < 0) {
        snprintf(g_txBuffer, sizeof(g_txBuffer), "LED %lu AUTO",
                 (unsigned long)index);
    } else {
        snprintf(g_txBuffer, sizeof(g_txBuffer), "LED %lu %06lX",
                 (unsigned long)index, (unsigned long)color);
    }
    Protocol::sendAck(g_txBuffer);
}

// CMD ENC MODE ... komutunu işler.
void handleEncCommand(char *arg1, char *arg2) {
    if (arg1 == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);    // "CMD ENC"
        return;
    }
    if (strcmp(arg1, "MODE") != 0) {
        Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD ENC HIZ"
        return;
    }
    if (arg2 != nullptr && strcmp(arg2, "HID") == 0) {
        if (g_handlers != nullptr && g_handlers->onEncoderMode != nullptr) {
            g_handlers->onEncoderMode(EK_ENC_MODE_HID);
        }
        Protocol::sendAck("ENC MODE HID");
    } else if (arg2 != nullptr && strcmp(arg2, "HOST") == 0) {
        if (g_handlers != nullptr && g_handlers->onEncoderMode != nullptr) {
            g_handlers->onEncoderMode(EK_ENC_MODE_HOST);
        }
        Protocol::sendAck("ENC MODE HOST");
    } else if (arg2 == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);    // "CMD ENC MODE"
    } else {
        Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD ENC MODE AUTO"
    }
}

// CMD HIDFB ON|OFF komutunu işler.
void handleHidFbCommand(char *arg) {
    if (arg != nullptr && strcmp(arg, "ON") == 0) {
        if (g_handlers != nullptr && g_handlers->onHidFallback != nullptr) {
            g_handlers->onHidFallback(true);
        }
        Protocol::sendAck("HIDFB ON");
    } else if (arg != nullptr && strcmp(arg, "OFF") == 0) {
        if (g_handlers != nullptr && g_handlers->onHidFallback != nullptr) {
            g_handlers->onHidFallback(false);
        }
        Protocol::sendAck("HIDFB OFF");
    } else if (arg == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);    // "CMD HIDFB"
    } else {
        Protocol::sendErr(EK_ERR_BAD_VALUE);   // "CMD HIDFB BELKI"
    }
}

// CMD BOOTLOADER CONFIRM — kartı KASITLI olarak indirme (flash) moduna alır.
//
// NEDEN VAR: Protocol::begin() içinde `enableReboot(false)` yapılıyor; bu,
// host'un DTR/RTS hatlarıyla kartı KAZARA bootloader'a atmasını engelliyor
// (bkz. oradaki uzun açıklama — "bağlandı/koptu" salınımının kök nedeni).
// Ama aynı koruma, esptool'un otomatik reset yolunu da kapatıyor: kart
// yalnızca FİZİKSEL BOOT+RST ile flash'lanabilir hâle geliyor. Kartlar kapalı
// kutuda olduğu için bu her güncellemede vida sökmek demek.
//
// Bu komut o dengeyi kuruyor: kazara tetiklenmesi imkânsız (tam metin + ayrı
// onay kelimesi gerekiyor, hat gürültüsü bunu üretemez), ama PC uygulaması ya
// da yükleme betiği isteyerek çağırabiliyor. Böylece kutuyu açmadan güncelleme
// yapılabilir.
//
// ONAY KELİMESİ ŞART: "CMD BOOTLOADER" tek başına hiçbir şey yapmaz.
void handleBootloaderCommand(char *arg) {
#if EK_HAS_USB_CDC
    if (arg == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);     // "CMD BOOTLOADER"
        return;
    }
    if (strcmp(arg, "CONFIRM") != 0) {
        Protocol::sendErr(EK_ERR_BAD_VALUE);    // "CMD BOOTLOADER BELKI"
        return;
    }

    // Yanıtı ÖNCE gönder: usb_persist_restart() geri dönmez, cihaz yeniden
    // başlar. ACK'in hatta çıkabilmesi için TX'in boşalmasını bekliyoruz;
    // burada bloklamak sakıncasız, zaten yeniden başlatıyoruz.
    Protocol::sendAck("BOOTLOADER");
    EK_SERIAL.flush();
    delay(200);

    // FORCE_DOWNLOAD_BOOT bayrağı USB geçişinden ÖNCE kurulur. Çekirdek onu
    // ancak esp_restart() sırasında yazıyor; oysa usb_persist_restart() önce
    // USB'yi ROM'un USB-Serial-JTAG'ine çevirip host'un veri yolu resetini
    // ~1 sn bekliyor. Ölçüldü (2026-10-22): önceki esptool oturumu kartı
    // USB-JTAG hattından resetlediyse JTAG tarafı bu bekleme sırasında kartı
    // bir kez resetliyor; bayrak henüz yokken kart indirme modu yerine yine
    // firmware'e açılıyordu (ROM portu ~0,2 sn görünüp kayboluyor). Bayrak
    // önceden kuruluysa o reset de indirme moduna düşer.
    REG_WRITE(RTC_CNTL_OPTION1_REG, RTC_CNTL_FORCE_DOWNLOAD_BOOT);

    // RESTART_BOOTLOADER: USB'yi ROM'un USB-Serial-JTAG'ine çevirir ve
    // yeniden başlatır. Sonuç, BOOT tuşunu basılı tutup RST'ye basmakla aynıdır.
    usb_persist_restart(RESTART_BOOTLOADER);

    // Buraya yalnızca yeniden başlatma OLMADIYSA gelinir (kapanış işleyicisi
    // kaydedilemedi). Bayrak geri alınmazsa sonraki ilk reset kartı
    // beklenmedik biçimde indirme moduna atar.
    REG_WRITE(RTC_CNTL_OPTION1_REG, 0);
    Protocol::sendErr(EK_ERR_BUSY);
#else
    (void)arg;
    Protocol::sendErr(EK_ERR_UNKNOWN_CMD);
#endif
}

// Tam bir satırı ayrıştırır ve ilgili komut işleyicisine yönlendirir.
void handleLine(char *rawLine) {
    char *line = trimLine(rawLine);
    if (*line == '\0') {
        return;
    }

    // PC'den herhangi bir satır gelmesi "uygulama yaşıyor" demektir.
    g_lastCommandMs = millis();
    g_gotCommand    = true;

    // Yalnızca "CMD " ile başlayan satırlar komuttur; gerisi sessizce atılır.
    if (strncmp(line, "CMD ", 4) != 0) {
        return;
    }

    char *token = strtok(line + 4, " ");
    if (token == nullptr) {
        Protocol::sendErr(EK_ERR_BAD_ARGS);   // yalnızca "CMD " gelmiş
        return;
    }

    if (strcmp(token, "ID") == 0) {
        if (g_handlers != nullptr && g_handlers->onIdRequest != nullptr) {
            g_handlers->onIdRequest();
        }
    } else if (strcmp(token, "PING") == 0) {
        if (g_handlers != nullptr && g_handlers->onPing != nullptr) {
            g_handlers->onPing();
        }
        Protocol::sendAck("PING");
    } else if (strcmp(token, "OS") == 0) {
        handleOsCommand(strtok(nullptr, " "));
    } else if (strcmp(token, "LED") == 0) {
        char *a1 = strtok(nullptr, " ");
        char *a2 = strtok(nullptr, " ");
        handleLedCommand(a1, a2);
    } else if (strcmp(token, "ENC") == 0) {
        char *a1 = strtok(nullptr, " ");
        char *a2 = strtok(nullptr, " ");
        handleEncCommand(a1, a2);
    } else if (strcmp(token, "HIDFB") == 0) {
        handleHidFbCommand(strtok(nullptr, " "));
    } else if (strcmp(token, "SAVE") == 0) {
        bool saved = true;
        if (g_handlers != nullptr && g_handlers->onSave != nullptr) {
            saved = g_handlers->onSave();
        }
        if (saved) {
            Protocol::sendAck("SAVE");
        } else {
            Protocol::sendErr(EK_ERR_NVS);
        }
    } else if (strcmp(token, "BOOTLOADER") == 0) {
        handleBootloaderCommand(strtok(nullptr, " "));
    } else {
        // Tanınmayan CMD fiili (docs/03-PROTOKOL.md 6.1).
        // NOT: "CMD " ile BAŞLAMAYAN satırlar hâlâ sessizce atılır.
        Protocol::sendErr(EK_ERR_UNKNOWN_CMD);
    }
}

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

// CDC portunu açar.
// NOT: setTxTimeoutMs(0) yazmayı BLOKLAMAZ YAPMAZ — arduino-esp32'de bu değer
// yalnızca USBCDC::write() başındaki mutex alımı (xSemaphoreTake) için
// kullanılır; asıl TX FIFO döngüsünün zaman aşımı YOKTUR. Host veri çekmeyi
// bırakırsa write() sonsuza kadar meşgul-bekler. Kilitlenmeye karşı gerçek
// koruma sendLine() içindeki availableForWrite() kontrolüdür.
void Protocol::begin() {
    EK_SERIAL.begin(115200);
#if EK_HAS_USB_CDC
    EK_SERIAL.setTxTimeoutMs(0);

    // !!! "BAĞLANDI/KOPTU" SALINIMININ KÖK NEDENİ — BURADA KAPATILIYOR !!!
    //
    // arduino-esp32 çekirdeğinin USBCDC sınıfı, VARSAYILAN olarak
    // (reboot_enable = true) host'un DTR/RTS hatlarını izleyen gizli bir
    // durum makinesi çalıştırır (cores/esp32/USBCDC.cpp, _onLineState):
    //
    //     BOŞTA --(DTR=0,RTS=1)--> 1 --(1,1)--> 2 --(1,0)--> 3
    //           --(DTR=0,RTS=0)--> usb_persist_restart(RESTART_BOOTLOADER)
    //
    // Yani host bu 4 adımlı diziyi ürettiği anda kart, firmware'i bırakıp
    // ROM BOOTLOADER'a atlar. Bu tam olarak esptool'un "indirme moduna al"
    // dizisidir. PC uygulaması portu kapatıp açtığında pyserial DTR/RTS'i
    // kaçınılmaz olarak bu adımlardan geçirir; birkaç aç/kapa döngüsünde
    // dizi tamamlanır ve kart bootloader'da ASILI kalır:
    //   - firmware çalışmadığı için HB (kalp atışı) kesilir,
    //   - uygulama "koptu" der, yeniden bağlanmayı dener (yeni aç/kapa),
    //   - kart yalnızca fiziksel RST/çıkar-tak ile kurtulur.
    // Kullanıcıya "bağlandı → düştü → kart yanıt vermiyor" olarak görünen
    // kısır döngünün kaynağı budur; kart bozulmuyor, BOOTLOADER'a düşüyor.
    //
    // Ayrıca aynı bayrak, host portu 1200 baud'a ayarlarsa da kartı
    // bootloader'a atar (Arduino IDE'nin "1200bps touch" yüklemesi).
    //
    // enableReboot(false) bu iki yolu da tamamen kapatır: host DTR/RTS ile
    // ne yaparsa yapsın kart firmware'de KALIR.
    //
    // KAYBIMIZ YOK: firmware'i zaten esptool ile FİZİKSEL BOOT+RST tutarak
    // (--before no_reset) yüklüyoruz; otomatik reset yolunu kullanmıyoruz.
    EK_SERIAL.enableReboot(false);
#endif
    g_rxLen         = 0;
    g_rxOverflow    = false;
    g_lastCommandMs = 0;
    g_gotCommand    = false;
}

// Komut geri çağırım tablosunu kaydeder.
void Protocol::setHandlers(const EkProtocolHandlers *handlers) {
    g_handlers = handlers;
}

// Gelen baytları okuyup satır tamamlandıkça ayrıştırır. Bloklamaz.
void Protocol::update(uint32_t now) {
    (void)now;
    uint16_t budget = EK_RX_CHUNK_LIMIT;

    while (budget > 0 && EK_SERIAL.available() > 0) {
        budget--;
        int value = EK_SERIAL.read();
        if (value < 0) {
            break;
        }
        char c = (char)value;

        if (c == '\n') {
            if (g_rxOverflow) {
                // Satır 128 baytlık tamponu aştı: içerik atıldı, PC'ye bildir.
                Protocol::sendErr(EK_ERR_TOO_LONG);
            } else {
                g_rxBuffer[g_rxLen] = '\0';
                handleLine(g_rxBuffer);
            }
            g_rxLen      = 0;
            g_rxOverflow = false;
            continue;
        }
        if (c == '\r') {
            continue;   // CRLF gönderen istemcileri de kabul et
        }
        if (g_rxLen < (EK_LINE_BUFFER_SIZE - 1)) {
            g_rxBuffer[g_rxLen++] = c;
        } else {
            g_rxOverflow = true;   // aşırı uzun satır: tamamını at
        }
    }
}

// USB CDC DTR sinyalinin durumunu döndürür (host portu açtı mı).
bool Protocol::hostDtr() {
#if EK_HAS_USB_CDC
    return (bool)EK_SERIAL;
#else
    return true;
#endif
}

// Son 3 saniye içinde PC'den satır alındı mı?
// YALNIZCA TANILAMA amaçlıdır: bağlı/değil kararı hostDtr() ile verilir
// (spec bölüm 5.3 — "CDC DTR düşük").
bool Protocol::commandRecent(uint32_t now) {
    if (!g_gotCommand) {
        return false;
    }
    // İŞARETLİ FARK ŞART (2026-09-29 düzeltmesi). g_lastCommandMs handleLine
    // içinde millis() ile atanır; handleLine ise loop()'un başında `now`
    // alındıktan SONRA (Protocol::update içinde) çalışır. Milisaniye tam o
    // arada değişirse g_lastCommandMs = now + 1 olur ve uint32
    // `now - g_lastCommandMs` = 4294967295 çıkar -> "son komut 49 gün önce"
    // sanılıp cihaz bir tur "uygulama bağlı değil" sayılıyordu: HID yedek
    // moduna girip Hid::releaseAll() ile basılı tuşları bırakıyor, LED
    // titriyor, her geri dönüşte iki DBG BOOT satırı gönderiyordu.
    // Ölçüm: 90 sn'de 86/86 PING cevaplanırken 5 sahte kopma. Bu hata
    // orijinal firmware'den beri vardı.
    // Negatif fark = komut bu turda geldi = taze. (int32 fark, millis()'in
    // ~49 günlük taşmasında da doğru sonuç verir.)
    int32_t yas = (int32_t)(now - g_lastCommandMs);
    return yas < (int32_t)EK_LINK_TIMEOUT_MS;
}

// Son alınan satırın zaman damgası.
uint32_t Protocol::lastCommandMs() {
    return g_lastCommandMs;
}

// CDC TX tıkanma bekçisi (loop()'tan her turda çağrılır).
//
// NEDEN AYRI BİR BEKÇİ GEREKİYOR: EK_LOOP_WDT_SEC bekçisi yalnızca loop()
// DÖNMEYİ BIRAKIRSA tetiklenir. Ölçülen arızada loop() gayet dönüyordu
// (tuşlar/HID çalışıyor, gelen komutlar işleniyor) ama CDC TX kalıcı
// tıkandığı için cihaz hiçbir şey gönderemiyordu; uygulama "koptu" görüyor,
// loop bekçisi ise düzenli beslendiği için HİÇ devreye girmiyordu.
//
// Sayaç yalnızca host portu GERÇEKTEN açıkken (TinyUSB DTR yüksek) işler:
// uygulama bağlı değilken yazamamak normaldir, boşta bekleyen cihaz
// resetlenmemelidir.
void Protocol::txWatchdog(uint32_t now) {
#if EK_HAS_USB_CDC
    if (g_txBlockedSinceMs == 0) {
        return;                       // tıkanma yok
    }
    if (!tud_cdc_n_connected(0)) {
        g_txBlockedSinceMs = 0;       // host portu kapalı -> normal, sayacı sıfırla
        return;
    }
    // İŞARETLİ FARK ŞART — bkz. commandRecent. g_txBlockedSinceMs sendLine
    // içinde millis() ile atanır ve sendLine, loop()'ta txWatchdog(now)'dan
    // ÖNCE (Keys::update / Protocol::update içinde) çalışabilir. Milisaniye
    // arada değişirse uint32 fark ~4 milyara taşar ve bu bekçi kartı gerçek
    // bir 5 sn tıkanma OLMADAN, ANINDA resetlerdi. 2026-09-29'da 4 saatte
    // görülen 5 YAZILIM_RST resetinin hiçbirinden önce uygulamada sessizlik
    // görülmemişti; sebep buydu. (2026-09-18'de bekçi eklenirken yapılan hata.)
    int32_t sure = (int32_t)(now - g_txBlockedSinceMs);
    if (sure >= (int32_t)EK_TX_STUCK_MS) {
        // Host portu açık tutuyor ama bu süre boyunca tek bayt bile
        // yazamadık -> TX kalıcı tıkanmış. Tek güvenilir çıkış yeniden
        // başlatmaktır; kart birkaç saniyede kendiliğinden geri gelir.
        esp_restart();
    }
#else
    (void)now;
#endif
}

// Ham bir satırı LF ile sonlandırarak gönderir. ASLA BLOKLAMAZ.
//
// KİLİTLENME KORUMASI: USBCDC::write(), host portu AÇIK tutup (DTR yüksek)
// veri çekmeyi bırakırsa TX FIFO'da sonsuz meşgul-bekleme yapar; tek çıkışı
// DTR'nin düşmesidir. Bu durumda loop() bir daha dönmez (tuş tarama, enkoder,
// LED ve HID tamamen durur) ve loop watchdog kapalı olduğu için yalnızca RST
// kurtarır. Bu yüzden yazmadan ÖNCE FIFO'da satırın tamamı + '\n' için yer
// olduğunu doğruluyoruz; yer yoksa satır ATILIR. Tek bir olayın kaybı,
// cihazın kalıcı kilitlenmesinden iyidir.
//
// Ayrıca satır ile '\n' TEK yazımda gönderilir: eskiden iki ayrı print()
// çağrısı vardı ve aralarında FIFO dolarsa satır sonu düşüp iki satır
// birbirine yapışabiliyordu.
//
// DİKKAT: CDC TX FIFO'su bu çekirdekte 64 bayttır; sendLine ile gönderilen
// satırlar (sonlandırıcı dahil) bu sınırın altında kalmalıdır.
void Protocol::sendLine(const char *line) {
    if (line == nullptr) {
        return;
    }

    char   out[EK_TX_BUFFER_SIZE + 2];
    size_t len = strlen(line);
    if (len > EK_TX_BUFFER_SIZE) {
        len = EK_TX_BUFFER_SIZE;   // taşan satırı kırp (normalde oluşmaz)
    }
    memcpy(out, line, len);
    out[len++] = '\n';

    // availableForWrite() bloklamaz: host bağlı değilse 0, aksi hâlde
    // FIFO'daki boş bayt sayısını anında döndürür.
    int space = EK_SERIAL.availableForWrite();
    if (space < (int)len) {
        // ÖNEMLİ: satırı atmadan ÖNCE FIFO'yu endpoint'e itmeyi DENE.
        // Eskiden burada doğrudan return ediliyordu; FIFO bir kez dolunca
        // onu boşaltacak kimse kalmadığı için availableForWrite() sonsuza
        // dek 0 dönüyor ve cihaz KALICI olarak susuyordu (loop() dönmeye
        // devam ettiğinden loop bekçisi de tetiklenmiyordu). flush()
        // bloklamaz; yalnızca birikmiş veriyi USB endpoint'ine iter.
#if EK_HAS_USB_CDC
        EK_SERIAL.flush();
        if (g_txBlockedSinceMs == 0) {
            uint32_t t = millis();
            g_txBlockedSinceMs = t ? t : 1;  // tıkanma sayacı (0 = "tıkanma yok" işareti)
        }
#endif
        return;   // bu satırı yine de at, ASLA bloklama
    }
    EK_SERIAL.write((const uint8_t *)out, len);
    g_txBlockedSinceMs = 0;   // yazabildik -> tıkanma yok
}

// EV KEY <n> DOWN|UP
void Protocol::sendKey(uint8_t keyNo, bool down) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "EV KEY %u %s",
             (unsigned)keyNo, down ? "DOWN" : "UP");
    sendLine(buffer);
}

// EV COMBO <a> <b>   (a < b garantilidir)
void Protocol::sendCombo(uint8_t a, uint8_t b) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "EV COMBO %u %u",
             (unsigned)a, (unsigned)b);
    sendLine(buffer);
}

// EV MODE COMBO_ON | EV MODE COMBO_OFF
void Protocol::sendComboMode(bool on) {
    sendLine(on ? "EV MODE COMBO_ON" : "EV MODE COMBO_OFF");
}

// EV OS WIN | EV OS MAC
void Protocol::sendOs(uint8_t osMode) {
    sendLine((osMode == EK_OS_MAC) ? "EV OS MAC" : "EV OS WIN");
}

// EV ENC CW | EV ENC CCW
void Protocol::sendEncRotate(bool cw) {
    sendLine(cw ? "EV ENC CW" : "EV ENC CCW");
}

// EV ENC PRESS
void Protocol::sendEncPress() {
    sendLine("EV ENC PRESS");
}

// EV ENC LONG
void Protocol::sendEncLong() {
    sendLine("EV ENC LONG");
}

// HB <uptime_ms>
void Protocol::sendHeartbeat(uint32_t uptimeMs) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "HB %lu", (unsigned long)uptimeMs);
    sendLine(buffer);
}

// ID <fw> <hw> <serial> <os>   örn. "ID 3.0.0 MK1 EK1-A4C138 WIN"
void Protocol::sendId(const char *serial, uint8_t osMode) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "ID %s %s %s %s",
             EK_FW_VERSION, EK_HW_REV,
             (serial != nullptr) ? serial : "?",
             (osMode == EK_OS_MAC) ? "MAC" : "WIN");
    sendLine(buffer);
}

// ACK <komut>
void Protocol::sendAck(const char *command) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "ACK %s",
             (command != nullptr) ? command : "");
    sendLine(buffer);
}

// ERR <sebep>
void Protocol::sendErr(const char *reason) {
    char buffer[EK_TX_BUFFER_SIZE];
    snprintf(buffer, sizeof(buffer), "ERR %s",
             (reason != nullptr) ? reason : "");
    sendLine(buffer);
}
