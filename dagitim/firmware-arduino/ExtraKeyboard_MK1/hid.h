#ifndef EK_HID_H
#define EK_HID_H

// =====================================================================
//  hid — USB HID yedek modu (uygulama kapalıyken) ve ses kontrolü
//  Spec bölüm 5.3
//
//  K1..K9 + K12 -> F13 … F22
//  K11          -> F23
//  K10          -> devre dışı (combo HID ile gönderilmez)
//  Enkoder-> Consumer Control: Volume Up / Volume Down / Mute
//
//  Not: Bu modülün çalışması için platformio.ini içinde
//       ARDUINO_USB_MODE=0 olmalıdır (TinyUSB yığını).
// =====================================================================

#include <Arduino.h>
#include "config.h"

namespace Hid {

// HID klavye ve tüketici kontrol arayüzlerini kaydeder.
// USB.begin() çağrılmadan ÖNCE çalıştırılmalıdır.
void begin();

// İşlev tuşları K1..K9 + K12 (keyNo 1..10) için F13..F22 tuşunu basılı yapar.
void keyDown(uint8_t keyNo);

// İşlev tuşları K1..K9 + K12 (keyNo 1..10) için F13..F22 tuşunu bırakır.
// Yalnızca o tuş gerçekten HID ile basılmışsa rapor gönderir; uygulama
// bağlıyken (HID yedek modu kapalıyken) gereksiz rapor üretilmez.
void keyUp(uint8_t keyNo);

// HID ile basılı tutulan en az bir işlev tuşu var mı?
bool anyKeyHeld();

// K11 için F23 tuşuna kısa bas-bırak yapar.
void osKeyTap();

// Basılı kalmış tüm HID tuşlarını bırakır (mod değişimlerinde çağrılır).
void releaseAll();

// Consumer Control: ses artır.
void volumeUp();

// Consumer Control: ses azalt.
void volumeDown();

// Consumer Control: sessize al / aç.
void mute();

}  // namespace Hid

#endif  // EK_HID_H
