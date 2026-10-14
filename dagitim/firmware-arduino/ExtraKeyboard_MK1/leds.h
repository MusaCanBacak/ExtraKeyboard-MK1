#ifndef EK_LEDS_H
#define EK_LEDS_H

// =====================================================================
//  leds — 3 adet DÜZ (tek renk) durum LED'i
//
//  Donanım: her LED kendi GPIO'sunda, seri 330 Ω dirençle, aktif HIGH.
//    LED1 (EK_PIN_LED_WIN,   GPIO14 / J1-20) : Windows modu göstergesi
//    LED2 (EK_PIN_LED_MAC,   GPIO42 / J3-6)  : macOS modu göstergesi
//    LED3 (EK_PIN_LED_COMBO, GPIO41 / J3-7)  : Combo göstergesi
//
//  Davranış:
//    - OS LED'leri: aktif moda ait LED yanar (diğeri söner).
//      Uygulama BAĞLIYKEN sabit yanar; bağlı DEĞİLKEN yavaş yanıp söner
//      (bağlantı göstergesi ayrı LED olmadan bu şekilde korunur).
//    - COMBO LED'i: combo modu açıkken yanar; combo tetiklenince çift
//      flaş yapar; HID yedek modunda combo engelliyse hızlı yanıp söner.
//    - HID yedek modu değişince üç LED birlikte 3 kez yanıp söner.
//
//  API, önceki WS2812B sürümüyle BİREBİR aynı tutulmuştur; renk/parlaklık
//  fonksiyonları düz LED'de görsel karşılığı olmasa da protokol ve NVS
//  uyumluluğu için değerleri saklar (CMD LED / CMD BRIGHT kırılmaz).
//
//  Tüm yanıp sönmeler millis() tabanlıdır; hiçbir fonksiyon beklemez.
// =====================================================================

#include <Arduino.h>
#include "config.h"

namespace Leds {

// Pinleri çıkış yapar ve başlangıç durumunu uygular.
void begin(uint8_t brightness);

// Durumları hesaplar ve değişen LED'leri yazar. Her loop() turunda çağrılır.
void update(uint32_t now);

// Parlaklık (0..255) — PWM ile uygulanır (0 = tümü sönük sayılmaz;
// yalnızca yanan LED'lerin şiddetini belirler).
void setBrightness(uint8_t value);
uint8_t brightness();

// Aktif işletim sistemi modu (EK_OS_WIN / EK_OS_MAC) — ilgili LED yanar.
void setOsMode(uint8_t osMode);

// Combo modu (COMBO tuşuyla) açık/kapalı.
void setComboMode(bool active);

// Combo tetiklendi — çift flaş.
void flashComboFired();

// PC uygulaması bağlı mı? Bağlıyken aktif OS LED'i sabit, değilken yanıp söner.
void setLinkState(bool linked);

// HID yedek modunda combo devre dışı — COMBO LED'i hızlı yanıp söner.
void setComboBlocked(bool blocked);

// Tuş aktivitesi — düz LED sürümünde görsel karşılığı yok (uyum için durur).
void flashKeyActivity();

// HID yedek modu değişti — üç LED birlikte 3 kez yanıp söner.
void blinkWhite();

// DONANIM TESTİ: verilen LED'i (1..3; 0 = hepsi) durum mantığından
// BAĞIMSIZ olarak ~900 ms yakar. Düz LED'de renk değiştirilemediği için
// "LED testi" budur: kullanıcı hangi LED'in yandığını gözle doğrular.
void testPulse(uint8_t index);

// `CMD LED <i> <RRGGBB>`: düz LED'de renk uygulanamaz; değer yalnızca
// protokol/NVS uyumluluğu için saklanır. index 1..3.
void setBaseColor(uint8_t index, int32_t color);

// LED indeksinin (1..3) temsil ettiği renk yuvası (protokol uyumu için).
uint8_t slotForIndex(uint8_t index);

// Yuva bazlı saklama (NVS geri yükleme yolu) — görsel etkisi yoktur.
void setSlotColor(uint8_t slot, int32_t color);
int32_t slotColor(uint8_t slot);
uint32_t effectiveSlotColor(uint8_t slot);

}  // namespace Leds

#endif  // EK_LEDS_H
