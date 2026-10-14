// =====================================================================
//  keys.cpp — Tuş okuma, debounce ve combo durum makinesi gerçeklemesi
//  Spec bölüm 6.1, 6.2, 6.3
// =====================================================================

#include "keys.h"

namespace {

// Tek bir tuşun debounce durum makinesi
struct EkKeyState {
    bool     rawLast;       // en son okunan ham seviye (true = basılı)
    bool     stable;        // debounce sonrası kararlı seviye
    uint32_t lastEdgeMs;    // ham seviyenin son değiştiği an
    bool     downReported;  // bu tuş için EV KEY DOWN gönderildi mi
};

// Pin tablosu — işlev tuşları blok hâlinde başta (K1..K9, K12), ardından
// K10 (COMBO) ve K11 (OS) gelir; pinler spec bölüm 3.1'dekiyle aynıdır.
// YENİ TUŞ EKLERKEN: yeni EK_PIN_K13... pinini K12'den SONRA, K10'dan
// ÖNCE ekle (işlev tuşları blok hâlinde başta durmalı) ve config.h'de
// EK_FN_KEY_COUNT değerini artır. Ayrıntı: docs/09-GENISLETME.md
// DİZİNİN SIRASI = uygulamadaki tuş numarası. 9. eleman "Tuş 9", 10. eleman
// "Tuş 10", 11. COMBO, 12. OS tuşudur.
//
// Üst sıradaki dört tuşun (Tuş9, Tuş10, COMBO, OS) fiziksel bağlantısı montajda
// çaprazlanmış; canlı tuş testiyle (EV OS / EV MODE / EV COMBO olayları) gerçek
// hatlar tespit edilip burada düzeltildi:
//   Tuş 9  -> GPIO10 (EK_PIN_K11)
//   Tuş 10 -> GPIO9  (EK_PIN_K10)
//   COMBO  -> GPIO8  (EK_PIN_K9)
//   OS     -> GPIO21 (EK_PIN_K12)
// Sıra düz yazılırsa 9'a basınca OS, COMBO'ya basınca Tuş9 tetiklenir.
const uint8_t KEY_PINS[EK_KEY_COUNT] = {
    EK_PIN_K1,  EK_PIN_K2,  EK_PIN_K3,
    EK_PIN_K4,  EK_PIN_K5,  EK_PIN_K6,
    // Üst sıra BİRİME GÖRE farklı kablolanmış. Eşleme platformio.ini'deki
    // birim ortamından derleme bayrağıyla seçilir; bu dosyayı ELLE değiştirme.
#if defined(EK_KEYMAP_SWAPPED)
    // [env:e74610] — üst sıra TAKASLI: 9.tuş<->12.tuş, 10.tuş<->11.tuş
    EK_PIN_K7,  EK_PIN_K8,  EK_PIN_K12,   // <- Tuş 9  (GPIO21)
    EK_PIN_K9,  EK_PIN_K10, EK_PIN_K11    // <- Tuş 10 (GPIO8), COMBO (GPIO9), OS (GPIO10)
#else
    // [env:quad] — ORİJİNAL (6F0B98, 9A2408)
    EK_PIN_K7,  EK_PIN_K8,  EK_PIN_K11,   // <- Tuş 9  (GPIO10)
    EK_PIN_K10, EK_PIN_K9,  EK_PIN_K12    // <- Tuş 10 (GPIO9), COMBO (GPIO8), OS (GPIO21)
#endif
};

EkKeyState   g_keys[EK_KEY_COUNT];

EkComboState g_comboState  = EK_COMBO_IDLE;
uint8_t      g_comboFirst  = 0;   // 1..EK_FN_KEY_COUNT, seçilen ilk tuş
uint32_t     g_comboArmMs  = 0;   // modun açıldığı / son ilerlediği an

EkKeyEventCb   g_onKey       = nullptr;
EkComboEventCb g_onCombo     = nullptr;
EkComboModeCb  g_onComboMode = nullptr;
EkOsKeyCb      g_onOsKey     = nullptr;

uint32_t g_k11PressMs   = 0;      // K11'in basıldığı an
bool     g_k11LongFired = false;  // uzun basış olayı zaten üretildi mi

// PC uygulaması bağlı mı (main.cpp updateLinkState tarafından beslenir).
// Bağlı değilken combo olayı teslim edilemez -> çevrimdışı zaman aşımı devreye
// girer. Varsayılan true: main.cpp ilk turda gerçek değeri zaten yazar.
bool g_linked = true;

// Combo modu açılırken hâlihazırda basılı olan işlev tuşlarının
// bekleyen UP olaylarını bastırır (mod açıkken EV KEY üretilmez).
void suppressHeldFunctionKeys() {
    for (uint8_t i = 0; i < EK_FN_KEY_COUNT; i++) {
        g_keys[i].downReported = false;
    }
}

// Combo modunu kapatır ve (istenirse) COMBO_OFF bildirir.
void comboReset(bool notify) {
    if (g_comboState == EK_COMBO_IDLE) {
        return;
    }
    g_comboState = EK_COMBO_IDLE;
    g_comboFirst = 0;
    if (notify && g_onComboMode != nullptr) {
        g_onComboMode(false);
    }
}

// Combo modundayken bir işlev tuşuna BASILDIĞINDA durum makinesini ilerletir.
// Bas-çek mantığı: tuşların basılı TUTULMASI gerekmez; yalnızca DOWN
// kenarları sayılır. Aynı tuşa ikinci kez basmak yok sayılır.
void comboHandlePress(uint8_t keyNo, uint32_t now) {
    switch (g_comboState) {
        case EK_COMBO_ARMED:
            // İlk tuş seçildi; normal eylemi bastırılır, bırakılabilir.
            g_comboFirst = keyNo;
            g_comboState = EK_COMBO_ONE_HELD;
            g_comboArmMs = now;   // zaman aşımı penceresi tazelenir
            break;

        case EK_COMBO_ONE_HELD:
            if (keyNo != g_comboFirst) {
                // İkili tamamlandı; a < b normalize edilir. Mod KALICIDIR:
                // combo tetiklendikten sonra KAPANMAZ, ARMED durumuna döner
                // ve sıradaki ikili beklenir (LED yanık kalır). Moddan çıkış
                // yalnızca KOMBO tuşuna tekrar basmakla olur.
                uint8_t a = (g_comboFirst < keyNo) ? g_comboFirst : keyNo;
                uint8_t b = (g_comboFirst < keyNo) ? keyNo : g_comboFirst;
                if (g_onCombo != nullptr) {
                    g_onCombo(a, b);
                }
                g_comboFirst = 0;
                g_comboState = EK_COMBO_ARMED;
                g_comboArmMs = now;
            }
            break;

        case EK_COMBO_IDLE:
        default:
            break;
    }
}

// K10 (COMBO) tuşunun kararlı seviye değişimini işler — BAS-ÇEK (latch).
// Mod, K10'un DOWN kenarında açılır; basılı tutmak gerekmez ve bırakmak
// modu KAPATMAZ. Mod açıkken K10'a tekrar basmak iptaldir.
void handleComboKey(bool pressed, uint32_t now) {
    if (!pressed) {
        return;  // bırakış kenarının bir işlevi yok
    }
    if (g_comboState == EK_COMBO_IDLE) {
        g_comboState = EK_COMBO_ARMED;
        g_comboFirst = 0;
        g_comboArmMs = now;
        suppressHeldFunctionKeys();
        if (g_onComboMode != nullptr) {
            g_onComboMode(true);
        }
    } else {
        comboReset(true);  // ikinci K10 basışı = iptal
    }
}

// K11 (OS) tuşunun kararlı seviye değişimini işler.
void handleOsKey(bool pressed, uint32_t now) {
    if (pressed) {
        g_k11PressMs   = now;
        g_k11LongFired = false;
    } else {
        // Uzun basış zaten basılıyken tetiklendiyse bırakışta bir şey yapılmaz.
        if (!g_k11LongFired) {
            uint32_t held = now - g_k11PressMs;
            if (held < EK_OS_SHORT_PRESS_MS && g_onOsKey != nullptr) {
                g_onOsKey(false);
            }
            // 800 ms ile 3000 ms arası "kararsız bölge"dir, olay üretilmez.
        }
    }
}

// Bir işlev tuşunun (K1..K9 + K12) kararlı seviye değişimini işler.
// Combo modu açıkken DOWN kenarı durum makinesine gider ve EV KEY üretilmez;
// combo'ya katılan tuşların UP kenarı da downReported bayrağı sayesinde
// kendiliğinden bastırılır (DOWN raporlanmadıysa UP da raporlanmaz).
void handleFunctionKey(uint8_t index, bool pressed, uint32_t now) {
    uint8_t keyNo = (uint8_t)(index + 1);

    if (pressed) {
        if (g_comboState != EK_COMBO_IDLE) {
            // Combo modu açık: normal EV KEY ve HID kodu GÖNDERİLMEZ.
            comboHandlePress(keyNo, now);
        } else {
            g_keys[index].downReported = true;
            if (g_onKey != nullptr) {
                g_onKey(keyNo, true);
            }
        }
    } else {
        if (g_keys[index].downReported) {
            g_keys[index].downReported = false;
            if (g_onKey != nullptr) {
                g_onKey(keyNo, false);
            }
        }
    }
}

// Kararlı seviye değişimini ilgili tuş tipine yönlendirir.
void dispatchStableChange(uint8_t index, bool pressed, uint32_t now) {
    if (index < EK_FN_KEY_COUNT) {
        handleFunctionKey(index, pressed, now);
    } else if (index == EK_KEY_INDEX_K10) {
        handleComboKey(pressed, now);
    } else if (index == EK_KEY_INDEX_K11) {
        handleOsKey(pressed, now);
    }
}

}  // namespace

// ---------------------------------------------------------------------
//  Genel API
// ---------------------------------------------------------------------

// Tüm tuş pinlerini dahili pull-up ile giriş yapar ve başlangıç
// seviyelerini kararlı kabul eder (açılışta sahte olay üretilmez).
void Keys::begin() {
    uint32_t now = millis();
    for (uint8_t i = 0; i < EK_KEY_COUNT; i++) {
        pinMode(KEY_PINS[i], INPUT_PULLUP);
        bool pressed = (digitalRead(KEY_PINS[i]) == LOW);  // aktif LOW
        g_keys[i].rawLast      = pressed;
        g_keys[i].stable       = pressed;
        g_keys[i].lastEdgeMs   = now;
        g_keys[i].downReported = false;
    }
    g_comboState   = EK_COMBO_IDLE;
    g_comboFirst   = 0;
    g_comboArmMs   = now;
    g_k11PressMs   = now;
    g_k11LongFired = true;  // açılışta basılı tutuluyorsa olay üretme
}

// Olay geri çağırımlarını kaydeder.
void Keys::setCallbacks(EkKeyEventCb onKey,
                        EkComboEventCb onCombo,
                        EkComboModeCb onComboMode,
                        EkOsKeyCb onOsKey) {
    g_onKey       = onKey;
    g_onCombo     = onCombo;
    g_onComboMode = onComboMode;
    g_onOsKey     = onOsKey;
}

// Tüm tuşları tarar, EK_KEY_DEBOUNCE_MS (8 ms) debounce uygular ve gerekli
// olayları üretir. Süre config.h'de tek yerden ayarlanır; burada sayı yazılmaz.
// Değer 8 ms'dir çünkü Cherry MX Blue'nun click jacket'i BIRAKIŞ tarafında
// ek kontak sıçraması üretir (bkz. config.h EK_KEY_DEBOUNCE_MS gerekçesi).
// Hiçbir bekleme yapmaz; millis() tabanlıdır.
void Keys::update(uint32_t now) {
    for (uint8_t i = 0; i < EK_KEY_COUNT; i++) {
        bool raw = (digitalRead(KEY_PINS[i]) == LOW);

        if (raw != g_keys[i].rawLast) {
            // Ham seviye değişti; debounce sayacını sıfırla.
            g_keys[i].rawLast    = raw;
            g_keys[i].lastEdgeMs = now;
        } else if (raw != g_keys[i].stable &&
                   (uint32_t)(now - g_keys[i].lastEdgeMs) >= EK_KEY_DEBOUNCE_MS) {
            // Seviye EK_KEY_DEBOUNCE_MS boyunca sabit kaldı; kararlı kabul et.
            g_keys[i].stable = raw;
            dispatchStableChange(i, raw, now);
        }
    }

    // K11 basılı tutulurken uzun basış eşiğini kontrol et (bırakmayı bekleme).
    if (g_keys[EK_KEY_INDEX_K11].stable && !g_k11LongFired &&
        (uint32_t)(now - g_k11PressMs) >= EK_OS_LONG_PRESS_MS) {
        g_k11LongFired = true;
        if (g_onOsKey != nullptr) {
            g_onOsKey(true);
        }
    }

    // Combo bas-çek zaman aşımı: modda unutulursa kendiliğinden kapan.
    //
    // ESKİDEN bu blok `#if EK_COMBO_LATCH_TIMEOUT_MS > 0` ile sarılıydı ve
    // değer 0 olduğu için ön-işlemci tarafından TAMAMEN SİLİNİYORDU. Artık
    // kontrol ÇALIŞMA ZAMANINDA yapılıyor (0 = kapalı); böylece config.h'deki
    // değeri değiştirmek ek derleme mantığı gerektirmiyor.
    uint32_t latchTimeout = (uint32_t)EK_COMBO_LATCH_TIMEOUT_MS;

    // Uygulama bağlı değilken combo modu açık kalırsa 10 işlev tuşu ne EV KEY
    // ne de HID kodu üretir (handleFunctionKey her DOWN'u combo durum
    // makinesine yönlendirir) ve olayı alacak kimse olmadığı için mod süresiz
    // açık kalabilir. Bu durumda her hâlükârda kısa bir üst sınır uygula.
    if (!g_linked && (latchTimeout == 0 ||
                      latchTimeout > (uint32_t)EK_COMBO_OFFLINE_TIMEOUT_MS)) {
        latchTimeout = (uint32_t)EK_COMBO_OFFLINE_TIMEOUT_MS;
    }

    if (latchTimeout > 0 && g_comboState != EK_COMBO_IDLE &&
        (uint32_t)(now - g_comboArmMs) >= latchTimeout) {
        comboReset(true);
    }
}

// PC uygulamasının bağlı olup olmadığını kaydeder (çevrimdışı combo zaman
// aşımı bu bayrağa bakar).
void Keys::setLinked(bool linked) {
    g_linked = linked;
}

// Combo durum makinesinin anlık durumunu döndürür.
EkComboState Keys::comboState() {
    return g_comboState;
}

// Combo modu kilitli mi (ARMED veya ONE_HELD)?
bool Keys::comboModeActive() {
    return g_comboState != EK_COMBO_IDLE;
}

// Verilen indeksteki tuşun debounce sonrası durumunu döndürür.
bool Keys::isPressed(uint8_t index) {
    if (index >= EK_KEY_COUNT) {
        return false;
    }
    return g_keys[index].stable;
}
