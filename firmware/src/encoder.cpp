// =====================================================================
//  encoder.cpp — EC11 quadrature durum tablosu çözücüsü + buton
//  Spec bölüm 6.1: "RC donanım filtresi + 4-adımlı durum tablosu çözücü.
//  EC11 tıklama başına tam bir quadrature çevrimi üretir -> 1 tık = 1 event."
// =====================================================================

#include "encoder.h"

namespace {

// ------------------------------------------------------------------
//  Durum tablosu (full-step)
//  Dinlenme (detent) konumu her iki kanalın da açık olduğu 0b11'dir;
//  pull-up'lar sayesinde iki pin de HIGH okunur. Yön biti yalnızca
//  eksiksiz bir çevrim 0b11'e döndüğünde üretilir.
//
//  Sütun indeksi (A<<1 | B) olarak üretilir; böylece A kanalı B'yi
//  öncelediğinde saat yönü elde edilir (standart EC11 davranışı).
//
//  Saat yönü çevrimi (A,B): 11 -> 01 -> 00 -> 10 -> 11  (DIR_CW)
//  Ters yön çevrimi  (A,B): 11 -> 10 -> 00 -> 01 -> 11  (DIR_CCW)
//
//  Yarım kalan veya sıçrayan hareketler tabloda başlangıca geri döner,
//  bu yüzden ne çift sayım ne de yanlış yön oluşur.
// ------------------------------------------------------------------
const uint8_t R_START     = 0x0;
const uint8_t R_CW_FINAL  = 0x1;
const uint8_t R_CW_BEGIN  = 0x2;
const uint8_t R_CW_NEXT   = 0x3;
const uint8_t R_CCW_BEGIN = 0x4;
const uint8_t R_CCW_FINAL = 0x5;
const uint8_t R_CCW_NEXT  = 0x6;

const uint8_t DIR_NONE    = 0x00;
const uint8_t DIR_CW      = 0x10;
const uint8_t DIR_CCW     = 0x20;

const uint8_t STATE_MASK  = 0x0F;
const uint8_t DIR_MASK    = 0x30;

// Satır = mevcut durum, sütun = okunan pin çifti (A<<1 | B)
const uint8_t ENC_TABLE[7][4] = {
    // R_START
    { R_START,    R_CW_BEGIN,  R_CCW_BEGIN, R_START },
    // R_CW_FINAL
    { R_CW_NEXT,  R_START,     R_CW_FINAL,  (uint8_t)(R_START | DIR_CW) },
    // R_CW_BEGIN
    { R_CW_NEXT,  R_CW_BEGIN,  R_START,     R_START },
    // R_CW_NEXT
    { R_CW_NEXT,  R_CW_BEGIN,  R_CW_FINAL,  R_START },
    // R_CCW_BEGIN
    { R_CCW_NEXT, R_START,     R_CCW_BEGIN, R_START },
    // R_CCW_FINAL
    { R_CCW_NEXT, R_CCW_FINAL, R_START,     (uint8_t)(R_START | DIR_CCW) },
    // R_CCW_NEXT
    { R_CCW_NEXT, R_CCW_FINAL, R_CCW_BEGIN, R_START }
};

uint8_t g_state = R_START;

EkEncRotateCb g_onRotate = nullptr;
EkEncButtonCb g_onButton = nullptr;

// Buton debounce durumu
bool     g_swRawLast    = false;
bool     g_swStable     = false;
uint32_t g_swLastEdgeMs = 0;
uint32_t g_swPressMs    = 0;
bool     g_swLongFired  = false;

// A ve B pinlerini okuyup tablo sütun indeksini üretir (A<<1 | B).
inline uint8_t readPinState() {
    uint8_t a = (digitalRead(EK_PIN_ENC_A) == HIGH) ? 1 : 0;
    uint8_t b = (digitalRead(EK_PIN_ENC_B) == HIGH) ? 1 : 0;
    return (uint8_t)((a << 1) | b);
}

// Enkoder butonunun kararlı seviye değişimini işler.
void handleButtonChange(bool pressed, uint32_t now) {
    if (pressed) {
        g_swPressMs   = now;
        g_swLongFired = false;
    } else {
        // Uzun basış zaten bildirildiyse bırakışta ikinci olay üretilmez.
        if (!g_swLongFired && g_onButton != nullptr) {
            g_onButton(false);
        }
    }
}

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

// A, B ve SW pinlerini dahili pull-up ile giriş yapar; çözücüyü sıfırlar.
void Enc::begin() {
    pinMode(EK_PIN_ENC_A,  INPUT_PULLUP);
    pinMode(EK_PIN_ENC_B,  INPUT_PULLUP);
    pinMode(EK_PIN_ENC_SW, INPUT_PULLUP);

    g_state = R_START;

    uint32_t now   = millis();
    bool     press = (digitalRead(EK_PIN_ENC_SW) == LOW);  // aktif LOW
    g_swRawLast    = press;
    g_swStable     = press;
    g_swLastEdgeMs = now;
    g_swPressMs    = now;
    g_swLongFired  = true;  // açılışta basılıysa olay üretme
}

// Olay geri çağırımlarını kaydeder.
void Enc::setCallbacks(EkEncRotateCb onRotate, EkEncButtonCb onButton) {
    g_onRotate = onRotate;
    g_onButton = onButton;
}

// Enkoderi ve butonunu tarar; bloklamayan, millis() tabanlıdır.
void Enc::update(uint32_t now) {
    // ---- 1) Dönme: durum tablosu ile çözümle ----
    uint8_t pinState = readPinState();
    g_state = ENC_TABLE[g_state & STATE_MASK][pinState];

    uint8_t dir = (uint8_t)(g_state & DIR_MASK);
    if (dir != DIR_NONE && g_onRotate != nullptr) {
        g_onRotate(dir == DIR_CW);
    }

    // ---- 2) Buton: 5 ms yazılım debounce ----
    bool raw = (digitalRead(EK_PIN_ENC_SW) == LOW);
    if (raw != g_swRawLast) {
        g_swRawLast    = raw;
        g_swLastEdgeMs = now;
    } else if (raw != g_swStable &&
               (uint32_t)(now - g_swLastEdgeMs) >= EK_ENC_SW_DEBOUNCE_MS) {
        g_swStable = raw;
        handleButtonChange(raw, now);
    }

    // ---- 3) Uzun basış eşiği (800 ms) — bırakmayı beklemeden bildirilir ----
    if (g_swStable && !g_swLongFired &&
        (uint32_t)(now - g_swPressMs) >= EK_ENC_LONG_PRESS_MS) {
        g_swLongFired = true;
        if (g_onButton != nullptr) {
            g_onButton(true);
        }
    }
}

// Enkoder butonunun debounce sonrası durumunu döndürür.
bool Enc::buttonPressed() {
    return g_swStable;
}
