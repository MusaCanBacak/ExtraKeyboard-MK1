// =====================================================================
//  storage.cpp — NVS (Preferences) tabanlı kalıcı ayar yönetimi
// =====================================================================

#include "storage.h"
#include <Preferences.h>

namespace {

Preferences g_prefs;
bool        g_open = false;

const char *NVS_NAMESPACE = "extrakb";

const char *KEY_OS_MODE   = "os_mode";
const char *KEY_HID_FB    = "hid_fb";
const char *KEY_ENC_MODE  = "enc_mode";
const char *KEY_LED_BR    = "led_br";

// LED temel renk yuvaları: OS_WIN, OS_MAC, COMBO, LINK_OK, LINK_ERR
// (Eski "led_ov0..2" anahtarları artık okunmaz; NVS'te kalırlarsa zararsızdır.)
const char *KEY_LED_COLOR[EK_LED_SLOT_COUNT] = {
    "led_c0", "led_c1", "led_c2", "led_c3", "led_c4"
};

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

// NVS ad alanını okuma/yazma kipinde açar.
void Storage::begin() {
    if (!g_open) {
        g_open = g_prefs.begin(NVS_NAMESPACE, false);
    }
}

// Spec'teki varsayılan değerleri yazar.
void Storage::resetDefaults(EkSettings *out) {
    if (out == nullptr) {
        return;
    }
    out->osMode        = EK_OS_WIN;
    out->hidFallback   = true;                       // uygulama yokken HID aktif
    out->encoderMode   = EK_ENC_MODE_HID;            // config.json: "mode":"hid"
    out->ledBrightness = EK_LED_DEFAULT_BRIGHTNESS;  // 60/255
    for (uint8_t i = 0; i < EK_LED_SLOT_COUNT; i++) {
        out->ledColor[i] = -1;                       // spec varsayılanı
    }
}

// Kayıtlı ayarları okur; eksik anahtarlar için varsayılan kullanılır.
void Storage::load(EkSettings *out) {
    if (out == nullptr) {
        return;
    }
    resetDefaults(out);
    if (!g_open) {
        return;
    }

    uint8_t osMode = g_prefs.getUChar(KEY_OS_MODE, out->osMode);
    out->osMode = (osMode == EK_OS_MAC) ? EK_OS_MAC : EK_OS_WIN;

    out->hidFallback = g_prefs.getBool(KEY_HID_FB, out->hidFallback);

    uint8_t encMode = g_prefs.getUChar(KEY_ENC_MODE, out->encoderMode);
    out->encoderMode = (encMode == EK_ENC_MODE_HOST) ? EK_ENC_MODE_HOST
                                                     : EK_ENC_MODE_HID;

    out->ledBrightness = g_prefs.getUChar(KEY_LED_BR, out->ledBrightness);

    for (uint8_t i = 0; i < EK_LED_SLOT_COUNT; i++) {
        int32_t value = g_prefs.getInt(KEY_LED_COLOR[i], out->ledColor[i]);
        out->ledColor[i] = (value < 0) ? -1 : (value & 0x00FFFFFFL);
    }
}

// Ayarları NVS'e yazar. Değişmeyen anahtarlar tekrar yazılmaz;
// böylece flash aşınması ve yazma süresi asgaride kalır.
// Tüm yazımlar başarılıysa true döner.
bool Storage::save(const EkSettings *in) {
    if (in == nullptr || !g_open) {
        return false;
    }

    bool ok = true;

    if (g_prefs.getUChar(KEY_OS_MODE, 0xFF) != in->osMode) {
        ok = (g_prefs.putUChar(KEY_OS_MODE, in->osMode) > 0) && ok;
    }
    if (g_prefs.getBool(KEY_HID_FB, !in->hidFallback) != in->hidFallback) {
        ok = (g_prefs.putBool(KEY_HID_FB, in->hidFallback) > 0) && ok;
    }
    if (g_prefs.getUChar(KEY_ENC_MODE, 0xFF) != in->encoderMode) {
        ok = (g_prefs.putUChar(KEY_ENC_MODE, in->encoderMode) > 0) && ok;
    }
    if (g_prefs.getUChar(KEY_LED_BR, 0xFF) != in->ledBrightness) {
        ok = (g_prefs.putUChar(KEY_LED_BR, in->ledBrightness) > 0) && ok;
    }
    for (uint8_t i = 0; i < EK_LED_SLOT_COUNT; i++) {
        if (g_prefs.getInt(KEY_LED_COLOR[i], 0x7FFFFFFFL) != in->ledColor[i]) {
            ok = (g_prefs.putInt(KEY_LED_COLOR[i], in->ledColor[i]) > 0) && ok;
        }
    }
    return ok;
}
