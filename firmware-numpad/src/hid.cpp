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

// NUMPAD: her tuş gerçek keypad HID usage kodu gönderir (F-tuşu DEĞİL).
// Kodlar USB HID Usage Table (Keyboard/Keypad, sayfa 0x07) keypad bölümü.
//
// SATIR SIRASI TERS: fiziksel montajda tuş numaraları EN ALT sıradan EN ÜST
// sıraya artıyor. Tuş 1-4 = fiziksel EN ALT sıra (0 . Enter +), Tuş 13-16 =
// EN ÜST sıra (7 8 9 /). Sonuç: standart numpad düzeni (üstte 789, altta 0).
// Fiziksel görünüm (üstten alta):
//     7 8 9 /
//     4 5 6 *
//     1 2 3 -
//     0 . ⏎ +
inline uint8_t functionKeyCode(uint8_t keyNo) {
    static const uint8_t NUMPAD_HID[16] = {
        0x62, 0x63, 0x58, 0x57,   // Tuş 1-4 :  KP0 KP. KPEnter KP+  (fiziksel EN ALT sıra)
        0x59, 0x5A, 0x5B, 0x56,   // Tuş 5-8 :  KP1 KP2 KP3 KP-
        0x5C, 0x5D, 0x5E, 0x55,   // Tuş 9-12:  KP4 KP5 KP6 KP*
        0x5F, 0x60, 0x61, 0x54    // Tuş 13-16: KP7 KP8 KP9 KP/      (fiziksel EN ÜST sıra)
    };
    if (keyNo >= 1 && keyNo <= 16) {
        return NUMPAD_HID[keyNo - 1];
    }
    return 0;
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
    uint8_t code = functionKeyCode(keyNo);
    if (code) g_keyboard.pressRaw(code);   // ham keypad HID kodu
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
    uint8_t code = functionKeyCode(keyNo);
    if (code) g_keyboard.releaseRaw(code);   // ham keypad HID kodu
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
