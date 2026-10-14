// =====================================================================
//  leds.cpp — NUMPAD varyantı: 2 düz LED'in durum makinesi
//
//  LED0 (GPIO42) = Windows göstergesi (Windows modunda sabit yanar)
//  LED1 (GPIO41) = macOS göstergesi   (macOS modunda sabit yanar)
//  Birbirini dışlar: her an yalnızca biri yanar -> aktif OS her bakışta belli.
//  Tuş basışında flaş YOK. Mod değişiminde (0+Enter kombosu) iki LED birlikte
//  3 kez yanıp söner (blinkWhite). Bağlantı LED'i YOK — bu cihazın eş
//  uygulaması olmadığından "bağlı/değil" göstergesi anlamsızdı.
//
//  Yazım stratejisi: her update() turunda LED'lerin OLMASI GEREKEN seviyesi
//  hesaplanır; yalnızca DEĞİŞEN LED'e yazılır (LEDC PWM). Hiçbir yerde beklenmez.
// =====================================================================

#include "leds.h"

namespace {

constexpr uint32_t WHITE_BLINK_MS = EK_LED_WHITE_BLINK_MS; // 120 ms
constexpr uint32_t TEST_PULSE_MS  = 900;

// NUMPAD: 2 LED. GPIO42 = Windows, GPIO41 = macOS.
const uint8_t PINS[EK_LED_COUNT] = { EK_PIN_LED_MAC, EK_PIN_LED_COMBO };

// LEDC (donanımsal PWM) kanalları — LED başına bir kanal.
// 5 kHz / 8 bit: gözle titreme görülmez, çözünürlük 0..255 ile birebir.
const uint8_t  LEDC_KANAL[EK_LED_COUNT] = { 0, 1 };
constexpr uint32_t LEDC_FREQ = 5000;
constexpr uint8_t  LEDC_COZUNURLUK = 8;

uint8_t  g_brightness = EK_LED_DEFAULT_BRIGHTNESS;
uint8_t  g_osMode     = EK_OS_WIN;
bool     g_linked     = false;   // yalnızca slot API tarafından okunur

// blinkWhite: iki LED birlikte 3 kez (mod değişti geri bildirimi)
uint32_t g_whiteUntil = 0;

// testPulse: donanım testi — maskedeki LED'ler süre boyunca yanar
uint32_t g_testUntil  = 0;
uint8_t  g_testMask   = 0;   // bit0=LED0, bit1=LED1

// Son yazılan PWM seviyeleri (gereksiz yazımı önlemek için)
int16_t  g_yazili[EK_LED_COUNT] = { -1, -1 };

// Protokol/NVS uyumu için saklanan renkler (bu varyantta görsel etkisi yok)
int32_t  g_slotColor[EK_LED_SLOT_COUNT] = { -1, -1, -1, -1, -1 };

uint32_t varsayilanRenk(uint8_t slot) {
    switch (slot) {
        case EK_LED_SLOT_OS_WIN:   return EK_COLOR_OS_WIN;
        case EK_LED_SLOT_OS_MAC:   return EK_COLOR_OS_MAC;
        case EK_LED_SLOT_COMBO:    return EK_COLOR_COMBO;
        case EK_LED_SLOT_LINK_OK:  return EK_COLOR_LINK_OK;
        case EK_LED_SLOT_LINK_ERR: return EK_COLOR_LINK_ERR;
        default:                   return EK_COLOR_OFF;
    }
}

// Bir LED'i istenen mantıksal duruma getirir. Parlaklık çipin KENDİ donanımsal
// PWM birimiyle (LEDC) uygulanır. 0 = sönük, g_brightness = yanık (0..255).
void yaz(uint8_t index, bool yanik) {
    int16_t seviye = yanik ? (int16_t)g_brightness : (int16_t)0;
    if (seviye == g_yazili[index]) {
        return;
    }
    g_yazili[index] = seviye;
    ledcWrite(LEDC_KANAL[index], (uint32_t)seviye);
}

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

void Leds::begin(uint8_t brightness) {
    g_brightness = brightness;
    for (uint8_t i = 0; i < EK_LED_COUNT; i++) {
        ledcSetup(LEDC_KANAL[i], LEDC_FREQ, LEDC_COZUNURLUK);
        ledcAttachPin(PINS[i], LEDC_KANAL[i]);
        ledcWrite(LEDC_KANAL[i], 0);
        g_yazili[i] = -1;      // ilk update() kesin yazsın
    }
    update(millis());
}

void Leds::update(uint32_t now) {
    // NUMPAD: iki LED yalnızca OS modunu gösterir (birbirini dışlar).
    bool winMode = (g_osMode != EK_OS_MAC);
    bool led0 = winMode;    // GPIO42 = Windows göstergesi
    bool led1 = !winMode;   // GPIO41 = macOS göstergesi

    // Mod değişim geri bildirimi: iki LED birlikte yanıp söner (blinkWhite).
    if (g_whiteUntil != 0) {
        if (now >= g_whiteUntil) {
            g_whiteUntil = 0;
        } else {
            bool on = (((g_whiteUntil - now) / WHITE_BLINK_MS) % 2) == 0;
            led0 = on;
            led1 = on;
        }
    }

    // Donanım testi (CMD LED i TEST) durum mantığını EZER: bit0->LED0, bit1->LED1.
    if (g_testUntil != 0) {
        if (now >= g_testUntil) {
            g_testUntil = 0;
            g_testMask = 0;
        } else {
            led0 = (g_testMask & 0x01) != 0;
            led1 = (g_testMask & 0x02) != 0;
        }
    }

    yaz(0, led0);
    yaz(1, led1);
}

void Leds::setBrightness(uint8_t value) {
    g_brightness = value;
    for (uint8_t i = 0; i < EK_LED_COUNT; i++) {
        g_yazili[i] = -1;   // yeni parlaklık bir sonraki update()'te uygulanır
    }
}

uint8_t Leds::brightness() {
    return g_brightness;
}

void Leds::setOsMode(uint8_t osMode) {
    g_osMode = (osMode == EK_OS_MAC) ? EK_OS_MAC : EK_OS_WIN;
}

// NUMPAD'de combo modu / combo LED'i yok — bu setter'lar yalnızca protokol
// arayüzü aynı kalsın diye tutulur (görsel etkisi yoktur).
void Leds::setComboMode(bool active) {
    (void)active;
}

void Leds::flashComboFired() {
    // NUMPAD: combo tetik flaşı yok.
}

void Leds::setLinkState(bool linked) {
    g_linked = linked;   // yalnızca slotForIndex() için (renk yuvası seçimi)
}

void Leds::setComboBlocked(bool blocked) {
    (void)blocked;
}

void Leds::flashKeyActivity() {
    // NUMPAD: tuş aktivite flaşı YOK (kullanıcı isteği) — bilinçli boş.
}

void Leds::blinkWhite() {
    g_whiteUntil = millis() + 6 * WHITE_BLINK_MS;   // iki LED birlikte 3 kez
}

void Leds::testPulse(uint8_t index) {
    if (index == 0) {
        g_testMask = 0x03;              // iki LED
    } else if (index >= 1 && index <= EK_LED_COUNT) {
        g_testMask = (uint8_t)(1u << (index - 1));
    } else {
        return;                          // geçersiz indeks — sessizce yok say
    }
    g_testUntil = millis() + TEST_PULSE_MS;
}

// ---------------------------------------------------------------------
//  Renk API'si — protokol/NVS uyumluluğu (bu varyantta görsel etkisi yok)
// ---------------------------------------------------------------------

uint8_t Leds::slotForIndex(uint8_t index) {
    switch (index) {
        case 1: return (g_osMode == EK_OS_MAC) ? EK_LED_SLOT_OS_MAC
                                               : EK_LED_SLOT_OS_WIN;
        case 2: return EK_LED_SLOT_COMBO;
        case 3: return g_linked ? EK_LED_SLOT_LINK_OK : EK_LED_SLOT_LINK_ERR;
        default: return EK_LED_SLOT_NONE;
    }
}

void Leds::setBaseColor(uint8_t index, int32_t color) {
    uint8_t slot = slotForIndex(index);
    if (slot != EK_LED_SLOT_NONE) {
        setSlotColor(slot, color);
    }
}

void Leds::setSlotColor(uint8_t slot, int32_t color) {
    if (slot >= EK_LED_SLOT_COUNT) {
        return;
    }
    if (color >= 0 && (uint32_t)color > 0xFFFFFFUL) {
        color = (int32_t)(color & 0xFFFFFF);
    }
    g_slotColor[slot] = color;
}

int32_t Leds::slotColor(uint8_t slot) {
    if (slot >= EK_LED_SLOT_COUNT) {
        return -1;
    }
    return g_slotColor[slot];
}

uint32_t Leds::effectiveSlotColor(uint8_t slot) {
    if (slot >= EK_LED_SLOT_COUNT) {
        return EK_COLOR_OFF;
    }
    int32_t ozel = g_slotColor[slot];
    return ozel >= 0 ? (uint32_t)ozel : varsayilanRenk(slot);
}
