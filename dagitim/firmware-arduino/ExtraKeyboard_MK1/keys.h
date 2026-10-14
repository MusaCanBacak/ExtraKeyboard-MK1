#ifndef EK_KEYS_H
#define EK_KEYS_H

// =====================================================================
//  keys — 12 tuşun okunması, 5 ms yazılım debounce ve combo durum makinesi
//  Spec bölüm 3.1 (pinler), 6.1 (debounce), 6.2 (combo), 6.3 (OS tuşu)
//
//  Tuş dizisi indeksleri (bkz. keys.cpp KEY_PINS ve config.h):
//    0..8  -> K1..K9  (işlev tuşları, PC'ye EV KEY olarak bildirilir)
//    9     -> K12     (10. işlev tuşu, PC'ye EV KEY 10 olarak bildirilir)
//    10    -> K10     (COMBO, kendi başına olay üretmez)
//    11    -> K11     (OS tuşu, kısa/uzun basış ayrımı yapılır)
// =====================================================================

#include <Arduino.h>
#include "config.h"

// Combo durum makinesi durumları (spec bölüm 6.2 — BAS-ÇEK / LATCH)
//  K10 basılı tutulMAZ: bir kez basılır, mod kilitlenir, sıradaki iki tuş
//  basışı comboyu oluşturur. Mod KALICIDIR: combo tetiklenince kapanmaz,
//  ARMED durumuna dönüp sıradaki ikiliyi bekler. Kapanma yolları:
//  K10'a tekrar basmak, EK_COMBO_LATCH_TIMEOUT_MS (0 = kapalı) ve uygulama
//  bağlı değilken EK_COMBO_OFFLINE_TIMEOUT_MS zaman aşımı.
enum EkComboState : uint8_t {
    EK_COMBO_IDLE = 0,   // mod kapalı
    EK_COMBO_ARMED,      // K10'a basıldı, birinci tuş bekleniyor
    EK_COMBO_ONE_HELD    // birinci tuş seçildi (basılı tutulması GEREKMEZ),
                         // ikinci tuş bekleniyor
};

// İşlev tuşları (K1..K9, K12) için normal tuş olayı. keyNo 1..10
// (K12 -> 10), pressed=true ise DOWN.
typedef void (*EkKeyEventCb)(uint8_t keyNo, bool pressed);

// Combo tetiklendi. a < b garantilidir (normalize edilmiştir).
typedef void (*EkComboEventCb)(uint8_t a, uint8_t b);

// Combo modu açıldı / kapandı (K10 bas-çek ile açılır; combo tetiklenince,
// K10'a tekrar basılınca veya zaman aşımında kapanır).
typedef void (*EkComboModeCb)(bool on);

// K11 basışı tamamlandı. longPress=false -> OS geçişi, true -> HID yedek toggle.
typedef void (*EkOsKeyCb)(bool longPress);

namespace Keys {

// Pinleri INPUT_PULLUP olarak kurar ve başlangıç durumlarını okur.
void begin();

// Olay geri çağırımlarını kaydeder. Hepsi nullptr olabilir.
void setCallbacks(EkKeyEventCb onKey,
                  EkComboEventCb onCombo,
                  EkComboModeCb onComboMode,
                  EkOsKeyCb onOsKey);

// Bloklamayan güncelleme; her loop() turunda çağrılmalıdır.
void update(uint32_t now);

// PC uygulamasının bağlı olup olmadığını bildirir (main.cpp updateLinkState).
// Bağlı DEĞİLKEN combo olayı hiçbir yere teslim edilemediği için combo modu
// EK_COMBO_OFFLINE_TIMEOUT_MS sonunda kendiliğinden kapatılır; böylece 10
// işlev tuşu süresiz ölü kalmaz. Varsayılan: bağlı kabul edilir.
void setLinked(bool linked);

// Combo durum makinesinin anlık durumu.
EkComboState comboState();

// Combo modu kilitli mi (ARMED veya ONE_HELD)?
bool comboModeActive();

// Verilen dizi indeksindeki tuş (debounce sonrası) basılı mı? index 0..11
bool isPressed(uint8_t index);

}  // namespace Keys

#endif  // EK_KEYS_H
