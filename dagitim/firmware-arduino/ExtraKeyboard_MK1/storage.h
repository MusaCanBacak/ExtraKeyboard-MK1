#ifndef EK_STORAGE_H
#define EK_STORAGE_H

// =====================================================================
//  storage — Kalıcı ayarlar (NVS / Preferences)
//  Spec bölüm 5.2 (CMD SAVE) ve 6.3 (K11 ile OS modunun kaydedilmesi)
//
//  Saklanan alanlar:
//    os_mode     : Windows / macOS modu
//    hid_fb      : HID yedek modu açık mı
//    enc_mode    : enkoder HID / HOST modu
//    led_br      : LED genel parlaklığı (0..255)
//    led_c0..4   : LED temel renk yuvaları (bkz. config.h / EkLedColorSlot)
//                  sırasıyla OS_WIN, OS_MAC, COMBO, LINK_OK, LINK_ERR
//                  (-1 = spec bölüm 6.4'teki varsayılan renk kullanılır)
// =====================================================================

#include <Arduino.h>
#include "config.h"

// Cihazın kalıcı ayar kümesi
struct EkSettings {
    uint8_t osMode;                          // EK_OS_WIN | EK_OS_MAC
    bool    hidFallback;                     // HID yedek modu etkin mi
    uint8_t encoderMode;                     // EK_ENC_MODE_HID | EK_ENC_MODE_HOST
    uint8_t ledBrightness;                   // 0..255
    int32_t ledColor[EK_LED_SLOT_COUNT];     // -1 = varsayılan, aksi 0xRRGGBB
};

namespace Storage {

// NVS ad alanını açar. setup() içinde bir kez çağrılır.
void begin();

// Kayıtlı ayarları okur; kayıt yoksa varsayılanları döndürür.
void load(EkSettings *out);

// Ayarları NVS'e yazar (yalnızca değişen anahtarlar güncellenir).
// Tüm yazımlar başarılıysa true; NVS açılamadıysa veya bir anahtar
// yazılamadıysa false döner (çağıran taraf `ERR NVS` üretir).
bool save(const EkSettings *in);

// Yapıyı spec'teki varsayılan değerlerle doldurur.
void resetDefaults(EkSettings *out);

}  // namespace Storage

#endif  // EK_STORAGE_H
