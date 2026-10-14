#ifndef EK_ENCODER_H
#define EK_ENCODER_H

// =====================================================================
//  encoder — EC11 döner enkoder çözücüsü + buton
//  Spec bölüm 3.1 (pinler), 3.4 (RC debounce), 6.1 (durum tablosu)
//
//  Çözücü 4 adımlı (full-step) quadrature geçiş tablosudur:
//  tablo yalnızca eksiksiz bir tık tamamlandığında yön üretir, bu yüzden
//  bir tık = tam olarak bir olay olur; kontak sıçraması ve yarım
//  hareketler yön üretmeden elenir.
// =====================================================================

#include <Arduino.h>
#include "config.h"

// Enkoder bir tık döndü. cw=true -> saat yönü (EV ENC CW).
typedef void (*EkEncRotateCb)(bool cw);

// Enkoder butonu olayı. longPress=false -> EV ENC PRESS, true -> EV ENC LONG.
typedef void (*EkEncButtonCb)(bool longPress);

namespace Enc {

// A/B/SW pinlerini INPUT_PULLUP yapar ve çözücüyü başlangıç konumuna alır.
void begin();

// Olay geri çağırımlarını kaydeder. Her ikisi de nullptr olabilir.
void setCallbacks(EkEncRotateCb onRotate, EkEncButtonCb onButton);

// Bloklamayan güncelleme; her loop() turunda çağrılmalıdır.
void update(uint32_t now);

// Enkoder butonu (debounce sonrası) basılı mı?
bool buttonPressed();

}  // namespace Enc

#endif  // EK_ENCODER_H
