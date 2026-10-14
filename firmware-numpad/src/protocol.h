#ifndef EK_PROTOCOL_H
#define EK_PROTOCOL_H

// =====================================================================
//  protocol — CDC seri üzerinden satır tabanlı ASCII haberleşme
//  Spec bölüm 5
//
//  Satır sonu '\n' (LF), komutlar BÜYÜK harf, alanlar tek boşlukla ayrılır.
//  Bilinmeyen satırlar sessizce yok sayılır (ileri uyumluluk).
//
//  Cihaz -> PC : EV KEY / EV COMBO / EV MODE / EV OS / EV ENC / HB / ID / ACK / ERR
//  PC -> Cihaz : CMD ID | PING | OS | LED | ENC MODE | HIDFB | SAVE
//                CMD BOOTLOADER CONFIRM -> kartı kasıtlı olarak flash (indirme)
//                moduna alır; BOOT+RST tutmaya gerek kalmaz. Onay kelimesi
//                ("CONFIRM") şarttır, kazara tetiklenemez.
// =====================================================================

#include <Arduino.h>
#include "config.h"

// ---------------------------------------------------------------------
//  ERR kodları (docs/03-PROTOKOL.md bölüm 6.1)
//  Kural: boşluksuz, BÜYÜK HARF, tek kelime.
// ---------------------------------------------------------------------
#define EK_ERR_UNKNOWN_CMD  "UNKNOWN_CMD"  // CMD fiili tanınmadı
#define EK_ERR_BAD_ARGS     "BAD_ARGS"     // alan sayısı yetersiz/anlamsız
#define EK_ERR_BAD_VALUE    "BAD_VALUE"    // alan var ama ayrıştırılamıyor
#define EK_ERR_RANGE        "RANGE"        // değer geçerli aralık dışında
#define EK_ERR_TOO_LONG     "TOO_LONG"     // satır tamponu aştı
#define EK_ERR_NVS          "NVS"          // NVS'e yazma başarısız
#define EK_ERR_BUSY         "BUSY"         // cihaz o an komut işleyemiyor

// Ayrıştırılmış komutların yönlendirileceği geri çağırımlar.
// Tümü nullptr olabilir; protokol katmanı ACK/ERR yanıtını kendisi üretir.
struct EkProtocolHandlers {
    void (*onIdRequest)();                            // CMD ID
    void (*onPing)();                                 // CMD PING
    void (*onSetOs)(uint8_t osMode);                  // CMD OS WIN|MAC
    void (*onSetLed)(uint8_t index, int32_t color);   // CMD LED <i> <RRGGBB>
    void (*onSetBrightness)(uint8_t value);           // CMD LED BRIGHT <0-255>
    void (*onLedTest)(uint8_t index);                 // CMD LED <i> TEST (0=hepsi)
    void (*onEncoderMode)(uint8_t mode);              // CMD ENC MODE HID|HOST
    void (*onHidFallback)(bool enabled);              // CMD HIDFB ON|OFF
    bool (*onSave)();                                 // CMD SAVE (NVS başarılı mı)
};

namespace Protocol {

// CDC portunu 115200'de açar.
void begin();

// Komut geri çağırım tablosunu kaydeder. İşaretçi kalıcı olmalıdır.
void setHandlers(const EkProtocolHandlers *handlers);

// Gelen baytları okur, satırlara böler ve ayrıştırır. Bloklamaz.
void update(uint32_t now);

// USB CDC DTR sinyali yüksek mi (host portu açmış mı)?
// Spec 5.3: "uygulama bağlı mı" kararının TEK ölçütü budur.
bool hostDtr();

// Son 3 saniyede PC'den bir satır alındı mı?
// YALNIZCA TANILAMA amaçlıdır; bağlantı kararında kullanılmaz.
bool commandRecent(uint32_t now);

// Son alınan satırın zaman damgası (millis).
uint32_t lastCommandMs();

// --- Ham gönderim ---
// ASLA BLOKLAMAZ: CDC TX FIFO'sunda (64 bayt) satırın tamamı için yer yoksa
// satır sessizce ATILIR. Host portu açık tutup okumayı bıraktığında loop()'un
// kilitlenmesini engelleyen tek koruma budur.
void sendLine(const char *line);

// CDC TX tikanma bekcisi — loop()'tan her turda cagrilir.
// sendLine() yazamadiginda sayac baslar; host portu ACIK tutarken
// (DTR yuksek) EK_TX_STUCK_MS boyunca hic yazilamazsa karti yeniden baslatir.
// Host bagli degilse sayac isletilmez (bos bekleyen cihaz resetlenmez).
void txWatchdog(uint32_t now);

// --- Olay gönderimleri (spec 5.1) ---
void sendKey(uint8_t keyNo, bool down);        // EV KEY <n> DOWN|UP
void sendCombo(uint8_t a, uint8_t b);          // EV COMBO <a> <b>
void sendComboMode(bool on);                   // EV MODE COMBO_ON|COMBO_OFF
void sendOs(uint8_t osMode);                   // EV OS WIN|MAC
void sendEncRotate(bool cw);                   // EV ENC CW|CCW
void sendEncPress();                           // EV ENC PRESS
void sendEncLong();                            // EV ENC LONG
void sendHeartbeat(uint32_t uptimeMs);         // HB <uptime_ms>
void sendId(const char *serial, uint8_t osMode);  // ID <fw> <hw> <serial> <os>
void sendAck(const char *command);             // ACK <komut>
void sendErr(const char *reason);              // ERR <sebep>

}  // namespace Protocol

#endif  // EK_PROTOCOL_H
