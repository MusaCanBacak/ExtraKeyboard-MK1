// =====================================================================
//  leds.cpp — 3 düz LED'in durum makinesi (leds.h'deki sözleşme)
//
//  Yazım stratejisi: her update() turunda üç LED'in OLMASI GEREKEN
//  seviyesi hesaplanır; yalnızca DEĞİŞEN LED'e yazılır (analogWrite,
//  parlaklık PWM'i). Hiçbir yerde beklenmez.
// =====================================================================

#include "leds.h"

namespace {

// Yanıp sönme zamanlamaları
constexpr uint32_t LINK_BLINK_MS    = 500;  // bağlantı yok: yavaş
constexpr uint32_t BLOCKED_BLINK_MS = EK_LED_RED_BLINK_MS;   // 250 ms
constexpr uint32_t FIRED_FLASH_MS   = EK_LED_COMBO_FLASH_MS; // 150 ms
constexpr uint32_t WHITE_BLINK_MS   = EK_LED_WHITE_BLINK_MS; // 120 ms

const uint8_t PINS[3] = { EK_PIN_LED_WIN, EK_PIN_LED_MAC, EK_PIN_LED_COMBO };

// LEDC (donanımsal PWM) kanalları — LED başına bir kanal.
// 5 kHz / 8 bit: gözle titreme görülmez, çözünürlük 0..255 ile birebir.
const uint8_t  LEDC_KANAL[3] = { 0, 1, 2 };
constexpr uint32_t LEDC_FREQ = 5000;
constexpr uint8_t  LEDC_COZUNURLUK = 8;

uint8_t  g_brightness   = EK_LED_DEFAULT_BRIGHTNESS;
uint8_t  g_osMode       = EK_OS_WIN;
bool     g_comboMode    = false;
bool     g_linked       = false;
bool     g_comboBlocked = false;

// flashComboFired: çift flaş (yan-yan-söner-yan-söner deseni)
uint32_t g_firedUntil   = 0;   // 0 = etkin değil; 4 dilimli pencere sonu

// blinkWhite: üç LED birlikte 3 kez
uint32_t g_whiteUntil   = 0;   // 0 = etkin değil; 6 yarı-periyotluk pencere

// testPulse: donanım testi — maskedeki LED'ler süre boyunca yanar
uint32_t g_testUntil    = 0;   // 0 = etkin değil
uint8_t  g_testMask     = 0;   // bit0=LED1, bit1=LED2, bit2=LED3
constexpr uint32_t TEST_PULSE_MS = 900;

// Son yazılan PWM seviyeleri (gereksiz yazımı önlemek için)
int16_t  g_yazili[3] = { -1, -1, -1 };

// Protokol/NVS uyumu için saklanan renkler (görsel etkisi yok)
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

// Bir LED'i istenen mantıksal duruma getirir. Parlaklık, çipin KENDİ
// donanımsal PWM birimiyle (LEDC) uygulanır; kanallar begin() içinde elle
// kurulur. `analogWrite` sarmalayıcısı Arduino sürümüne göre davranış
// değiştirebildiği için doğrudan LEDC API'si kullanılır — böylece
// parlaklık her çekirdek sürümünde çalışır. NeoPixel/RMT ile ilgisi yoktur.
// 0 = sönük, g_brightness = yanık seviyesi (0..255).
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
    for (uint8_t i = 0; i < 3; i++) {
        // LEDC kanalını kur ve pini bu kanala bağla (PWM ile parlaklık).
        ledcSetup(LEDC_KANAL[i], LEDC_FREQ, LEDC_COZUNURLUK);
        ledcAttachPin(PINS[i], LEDC_KANAL[i]);
        ledcWrite(LEDC_KANAL[i], 0);
        g_yazili[i] = -1;      // ilk update() kesin yazsın
    }
    update(millis());
}

void Leds::update(uint32_t now) {
    // --- OS LED'leri (Windows / macOS) --------------------------------
    bool osYanik = true;
    if (!g_linked) {
        // Bağlantı yok: aktif OS LED'i yavaş yanıp söner.
        osYanik = ((now / LINK_BLINK_MS) % 2) == 0;
    }
    bool winYanik = (g_osMode == EK_OS_WIN) && osYanik;
    bool macYanik = (g_osMode == EK_OS_MAC) && osYanik;

    // --- COMBO LED'i ---------------------------------------------------
    bool comboYanik = g_comboMode;
    if (g_comboBlocked) {
        comboYanik = ((now / BLOCKED_BLINK_MS) % 2) == 0;
    }
    if (g_firedUntil != 0) {
        if (now >= g_firedUntil) {
            g_firedUntil = 0;
        } else {
            // Çift flaş: [yan][sön][yan][sön] dilimleri
            uint32_t kalan = g_firedUntil - now;
            uint32_t dilim = (4 * FIRED_FLASH_MS - kalan) / FIRED_FLASH_MS;
            comboYanik = (dilim % 2) == 0;
        }
    }

    // --- HID yedek bildirimi: üçü birlikte yanıp söner ------------------
    if (g_whiteUntil != 0) {
        if (now >= g_whiteUntil) {
            g_whiteUntil = 0;
        } else {
            uint32_t kalan = g_whiteUntil - now;
            uint32_t dilim = (6 * WHITE_BLINK_MS - kalan) / WHITE_BLINK_MS;
            bool hepYanik = (dilim % 2) == 0;
            winYanik = macYanik = comboYanik = hepYanik;
        }
    }

    // --- donanım testi: durum mantığını EZER (en yüksek öncelik) ---
    if (g_testUntil != 0) {
        if (now >= g_testUntil) {
            g_testUntil = 0;
            g_testMask = 0;
        } else {
            winYanik   = (g_testMask & 0x01) != 0;
            macYanik   = (g_testMask & 0x02) != 0;
            comboYanik = (g_testMask & 0x04) != 0;
        }
    }

    yaz(0, winYanik);
    yaz(1, macYanik);
    yaz(2, comboYanik);
}

void Leds::setBrightness(uint8_t value) {
    // 0 = TAMAMEN SÖNÜK (yuvarlama yok): arayüzdeki "0 = sönük" ifadesiyle
    // birebir aynı davranış.
    g_brightness = value;
    for (uint8_t i = 0; i < 3; i++) {
        g_yazili[i] = -1;   // yeni parlaklık bir sonraki update()'te uygulanır
    }
}

uint8_t Leds::brightness() {
    return g_brightness;
}

void Leds::setOsMode(uint8_t osMode) {
    g_osMode = (osMode == EK_OS_MAC) ? EK_OS_MAC : EK_OS_WIN;
}

void Leds::setComboMode(bool active) {
    g_comboMode = active;
}

void Leds::flashComboFired() {
    g_firedUntil = millis() + 4 * FIRED_FLASH_MS;
}

void Leds::setLinkState(bool linked) {
    g_linked = linked;
}

void Leds::setComboBlocked(bool blocked) {
    g_comboBlocked = blocked;
}

void Leds::flashKeyActivity() {
    // Düz LED sürümünde ayrı bir aktivite göstergesi yok (bilinçli boş).
}

void Leds::blinkWhite() {
    g_whiteUntil = millis() + 6 * WHITE_BLINK_MS;
}

void Leds::testPulse(uint8_t index) {
    if (index == 0) {
        g_testMask = 0x07;              // hepsi
    } else if (index >= 1 && index <= 3) {
        g_testMask = (uint8_t)(1u << (index - 1));
    } else {
        return;                          // geçersiz indeks — sessizce yok say
    }
    g_testUntil = millis() + TEST_PULSE_MS;
}

// ---------------------------------------------------------------------
//  Renk API'si — protokol/NVS uyumluluğu (görsel etkisi yok)
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
