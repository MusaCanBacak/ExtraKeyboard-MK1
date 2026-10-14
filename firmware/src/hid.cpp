// =====================================================================
//  hid.cpp — USBHIDKeyboard (F13..F23) ve USBHIDConsumerControl (ses)
//  Spec bölüm 5.3
// =====================================================================

#include "hid.h"

#include "USB.h"
#include "USBHIDKeyboard.h"
#include "USBHIDConsumerControl.h"

// Çekirdek sürümleri arasında ad değişikliğine karşı güvenlik ağı.
#ifndef KEY_F13
#define KEY_F13 0xF0
#endif
#ifndef CONSUMER_CONTROL_VOLUME_INCREMENT
#define CONSUMER_CONTROL_VOLUME_INCREMENT 0xE9
#endif
#ifndef CONSUMER_CONTROL_VOLUME_DECREMENT
#define CONSUMER_CONTROL_VOLUME_DECREMENT 0xEA
#endif
#ifndef CONSUMER_CONTROL_MUTE
#define CONSUMER_CONTROL_MUTE 0xE2
#endif

namespace {

USBHIDKeyboard        g_keyboard;
USBHIDConsumerControl g_consumer;

bool g_started = false;

// Hangi işlev tuşlarının HID ile BASILI tutulduğunu izleyen bit maskesi
// (bit 0 = K1 … bit 8 = K9, bit 9 = K12).
// Sayesinde HID yedek modu kapalıyken (uygulama bağlıyken) gereksiz
// klavye raporu gönderilmez — spec 5.3: HID kodları yalnızca yedek modda.
uint16_t g_heldMask = 0;

// keyNo (1..10) -> F13..F22 HID kodu. K11 için keyNo = 11 kullanılır (F23).
inline uint8_t functionKeyCode(uint8_t keyNo) {
    return (uint8_t)(KEY_F13 + (keyNo - 1));
}

// Tek atımlık tüketici kontrol kodu gönderir (bas + hemen bırak).
inline void tapConsumer(uint16_t code) {
    if (!g_started) {
        return;
    }
    g_consumer.press(code);
    g_consumer.release();
}

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

// HID arayüzlerini TinyUSB'ye kaydeder. USB.begin() öncesi çağrılmalıdır.
void Hid::begin() {
    g_keyboard.begin();
    g_consumer.begin();
    g_started = true;
}

// F13..F22 tuşunu basılı yapar (keyNo 1..10).
void Hid::keyDown(uint8_t keyNo) {
    if (!g_started || keyNo < 1 || keyNo > EK_FN_KEY_COUNT) {
        return;
    }
    uint16_t bit = (uint16_t)(1u << (keyNo - 1));
    if (g_heldMask & bit) {
        return;   // zaten basılı; tekrar rapor gönderme
    }
    g_heldMask |= bit;
    g_keyboard.press(functionKeyCode(keyNo));
}

// F13..F22 tuşunu bırakır (keyNo 1..10).
// Yalnızca o tuş gerçekten HID ile basılmışsa rapor gönderilir.
void Hid::keyUp(uint8_t keyNo) {
    if (!g_started || keyNo < 1 || keyNo > EK_FN_KEY_COUNT) {
        return;
    }
    uint16_t bit = (uint16_t)(1u << (keyNo - 1));
    if (!(g_heldMask & bit)) {
        return;   // hiç basılmamıştı; gereksiz rapor üretme
    }
    g_heldMask &= (uint16_t)~bit;
    g_keyboard.release(functionKeyCode(keyNo));
}

// Herhangi bir HID tuşu basılı tutuluyor mu?
bool Hid::anyKeyHeld() {
    return g_heldMask != 0;
}

// K11 için F23 tuşuna kısa bas-bırak yapar.
void Hid::osKeyTap() {
    if (!g_started) {
        return;
    }
    uint8_t code = functionKeyCode(EK_FN_KEY_COUNT + 1);  // F13 + 10 = F23
    g_keyboard.press(code);
    g_keyboard.release(code);
}

// Basılı kalmış tüm HID tuşlarını bırakır.
void Hid::releaseAll() {
    if (!g_started) {
        return;
    }
    if (g_heldMask != 0) {
        g_heldMask = 0;
        g_keyboard.releaseAll();
    }
    g_consumer.release();
}

// Consumer Control: ses artır.
void Hid::volumeUp() {
    tapConsumer(CONSUMER_CONTROL_VOLUME_INCREMENT);
}

// Consumer Control: ses azalt.
void Hid::volumeDown() {
    tapConsumer(CONSUMER_CONTROL_VOLUME_DECREMENT);
}

// Consumer Control: sessize al / aç.
void Hid::mute() {
    tapConsumer(CONSUMER_CONTROL_MUTE);
}
