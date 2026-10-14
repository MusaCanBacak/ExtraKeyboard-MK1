// =====================================================================
//  EC11 ENKODER BAGIMSIZ TEST PROGRAMI — ExtraKeyboard MK1
//
//  Yalnizca enkoderi test eder; tus, LED ve USB-HID kodu YOKTUR.
//  Pinler ana firmware ile birebir ayni (firmware/src/config.h):
//
//     EC11 A   -> GPIO11  (J1-17)
//     EC11 B   -> GPIO12  (J1-18)
//     EC11 C   -> GND     (J3-1, 3'lu tarafin ORTADAKI pini)
//     EC11 SW1 -> GPIO13  (J1-19)
//     EC11 SW2 -> GND     (J3-1)
//
//  RC filtre kartiyla da DOGRUDAN kablolamayla da calisir
//  (dahili pull-up'lar acik). Cikti: "UART" etiketli USB-C port, 115200.
//
//  NE GORMELISIN:
//    - Saga bir tik   -> tam 1 satir "CW   tik ..."
//    - Sola bir tik   -> tam 1 satir "CCW  tik ..."
//    - Butona basinca -> ">>> BUTON BASILDI", birakinca sure yazilir
//    - 5 saniyede bir [OZET] satiri: sayaclar + anlik A/B/SW seviyeleri
//
//  ARIZA IPUCLARI:
//    - Bir tikta 2+ satir       -> sicrama; "gecersiz" sayaci da artiyorsa
//                                  RC filtresi yok/yanlis demektir
//    - Hic satir gelmiyor       -> C (ortak) teli kopuk olabilir
//    - Yonler ters              -> A ile B telleri yer degistirmis
//    - SW=0 gorunuyor (basili
//      degilken)                -> SW1/SW2 kablolamasini kontrol et
// =====================================================================

#include <Arduino.h>

static const int PIN_A  = 11;   // EC11 A   (J1-17)
static const int PIN_B  = 12;   // EC11 B   (J1-18)
static const int PIN_SW = 13;   // EC11 SW1 (J1-19)

// 4 adimli durum tablosu. Indeks = (eskiDurum << 2) | yeniDurum,
// durum = (A << 1) | B, dinlenme = 0b11.
//   CW  dizisi: 11 -> 01 -> 00 -> 10 -> 11   (her adim +1)
//   CCW dizisi: 11 -> 10 -> 00 -> 01 -> 11   (her adim -1)
// Iki kanalin ayni anda degistigi gecisler gecersizdir (0) ve ayrica
// sayilir — bunlar kontak sicramasinin parmak izidir.
static const int8_t TRANS[16] = {
     0, -1, +1,  0,
    +1,  0,  0, -1,
    -1,  0,  0, +1,
     0, +1, -1,  0
};

static inline bool gecersizMi(uint8_t idx) {
    return idx == 0b0011 || idx == 0b0110 || idx == 0b1001 || idx == 0b1100;
}

// --- enkoder durumu ---
static uint8_t  durum     = 0b11;
static int8_t   acc       = 0;   // detent ici adim toplayici
static int32_t  pozisyon  = 0;   // net konum (CW +, CCW -)
static uint32_t tikCW     = 0;
static uint32_t tikCCW    = 0;
static uint32_t hamGecis  = 0;   // tum A/B kenar degisimleri
static uint32_t gecersiz  = 0;   // sicrama kaynakli gecersiz gecisler

// --- buton durumu (5 ms yazilim debounce, ana firmware ile ayni) ---
static bool     swHam       = false;
static bool     swKarali    = false;
static uint32_t swDegisim   = 0;
static uint32_t basmaAni    = 0;
static uint32_t basSayisi   = 0;
static bool     uzunVerildi = false;

static uint32_t sonOzet = 0;

static void ozetYazdir() {
    Serial.printf("[OZET] A=%d B=%d SW=%d | pozisyon=%+ld | CW=%lu CCW=%lu | ham gecis=%lu | gecersiz=%lu\r\n",
                  digitalRead(PIN_A), digitalRead(PIN_B), digitalRead(PIN_SW),
                  (long)pozisyon, (unsigned long)tikCW, (unsigned long)tikCCW,
                  (unsigned long)hamGecis, (unsigned long)gecersiz);
}

void setup() {
    pinMode(PIN_A,  INPUT_PULLUP);
    pinMode(PIN_B,  INPUT_PULLUP);
    pinMode(PIN_SW, INPUT_PULLUP);

    Serial.begin(115200);
    delay(600);

    Serial.println();
    Serial.println("=================================================");
    Serial.println("   EC11 ENKODER TESTI  (ExtraKeyboard MK1)");
    Serial.println("=================================================");
    Serial.println("Beklenen kablolama:");
    Serial.println("   A   -> GPIO11 (J1-17)     C  -> GND (J3-1)");
    Serial.println("   B   -> GPIO12 (J1-18)     SW2-> GND (J3-1)");
    Serial.println("   SW1 -> GPIO13 (J1-19)");
    Serial.println();

    int a  = digitalRead(PIN_A);
    int b  = digitalRead(PIN_B);
    int sw = digitalRead(PIN_SW);
    Serial.printf("Acilis seviyeleri: A=%d B=%d SW=%d\r\n", a, b, sw);
    if (a == 1 && b == 1) {
        Serial.println("   OK: dinlenme konumu (A=1 B=1) dogru.");
    } else {
        Serial.println("   NOT: enkoder iki tik arasinda durmus olabilir (normal).");
        Serial.println("        Bir tik cevirince A=1 B=1'e donmuyorsa A/B/C tellerine bak.");
    }
    if (sw == 0) {
        Serial.println("   UYARI: buton BASILI gorunuyor. Basili degilse SW1/SW2 tellerine bak.");
    }
    Serial.println();
    Serial.println("Simdi cevir ve bas. Her tik TAM 1 satir uretmeli.");
    Serial.println("-------------------------------------------------");

    durum    = (uint8_t)((a << 1) | b);
    swHam    = swKarali = (sw == LOW);
    sonOzet  = millis();
}

void loop() {
    uint32_t simdi = millis();

    // ---- enkoder A/B: 4 adimli durum tablosu cozucu ----
    uint8_t s = (uint8_t)((digitalRead(PIN_A) << 1) | digitalRead(PIN_B));
    if (s != durum) {
        uint8_t idx = (uint8_t)((durum << 2) | s);
        hamGecis++;
        if (gecersizMi(idx)) {
            gecersiz++;             // iki kanal ayni anda degisti -> sicrama izi
        } else {
            acc += TRANS[idx];
        }
        durum = s;

        if (s == 0b11) {            // dinlenme konumuna donuldu -> detent tamam
            if (acc >= 3) {
                pozisyon++; tikCW++;
                Serial.printf("CW   tik #%-4lu | pozisyon %+ld\r\n",
                              (unsigned long)tikCW, (long)pozisyon);
            } else if (acc <= -3) {
                pozisyon--; tikCCW++;
                Serial.printf("CCW  tik #%-4lu | pozisyon %+ld\r\n",
                              (unsigned long)tikCCW, (long)pozisyon);
            }
            acc = 0;
        }
    }

    // ---- buton: 5 ms yazilim debounce ----
    bool ham = (digitalRead(PIN_SW) == LOW);
    if (ham != swHam) {
        swHam     = ham;
        swDegisim = simdi;
    }
    if ((simdi - swDegisim) >= 5 && swKarali != swHam) {
        swKarali = swHam;
        if (swKarali) {
            basmaAni    = simdi;
            uzunVerildi = false;
            basSayisi++;
            Serial.printf(">>> BUTON BASILDI  (#%lu)\r\n", (unsigned long)basSayisi);
        } else {
            Serial.printf(">>> BUTON BIRAKILDI (%lu ms basili kaldi)\r\n",
                          (unsigned long)(simdi - basmaAni));
        }
    }
    if (swKarali && !uzunVerildi && (simdi - basmaAni) >= 800) {
        uzunVerildi = true;
        Serial.println(">>> UZUN BASIS esigi gecildi (800 ms)");
    }

    // ---- 5 saniyede bir ozet ----
    if (simdi - sonOzet >= 5000) {
        sonOzet = simdi;
        ozetYazdir();
    }
}
