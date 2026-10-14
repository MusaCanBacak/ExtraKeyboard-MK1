# Genişletme Rehberi — Tuş Sayısını Artırma

Tasarım 9 işlev tuşu + K10 (combo) + K11 (OS) ile gelir ama **tuş sayısı
tek noktadan artırılabilir** şekilde kurulmuştur. Yeni bir işlev tuşu (K12,
K13, …) eklemek için dokunulacak yerler ve sınırlar bu dosyadadır.

---

## 1. Sınırlar — önce bunu oku

| Sınır | Değer | Sebep |
|---|---|---|
| İşlev tuşu üst sınırı | **11** (K1..K11 işlev + K10/K11 özel) | HID yedek modu F13–F24 aralığını kullanır: işlev tuşları F13'ten başlar, OS tuşu en sona biner. 11'i aşarsan `config.h` derlemeyi `#error` ile keser |
| Boş ve güvenli GPIO'lar | **1, 2, 21, 39, 40, 41, 42, 47** | Aşağıdaki tabloya bak |
| Dikkatli kullanılacak | 38, 48 | Bazı DevKitC-1 revizyonlarında **dahili RGB LED** bu pinlerdedir (v1.0→48, v1.1→38). LED'li pini tuşa bağlarsan tuş çalışır ama karttaki LED anlamsız yanar |
| Kesinlikle yasak | 0, 3, 19, 20, 26–37, 43–46 | Strapping / USB / flash / PSRAM / UART (spec §3.2) |

Combo sayısı kendiliğinden büyür: n işlev tuşu → C(n,2) combo
(10 tuş → 45, 11 tuş → 55). Protokol zaten geneldir (`EV KEY <n>`,
`EV COMBO <a> <b>`), mesaj formatı değişmez.

---

## 2. Dokunulacak 4 yer

Örnek: **K12'yi GPIO21'e** eklemek.

### 2.1 `firmware/src/config.h` — pin tanımı + sayı

```c
#define EK_PIN_K11       10
#define EK_PIN_K12       21          // YENİ işlev tuşu
...
#define EK_FN_KEY_COUNT   10         // 9 -> 10
```

K10/K11 indeksleri ve `EK_KEY_COUNT` buradan **otomatik türetilir**,
onlara dokunma.

### 2.2 `firmware/src/keys.cpp` — pin tablosu

`KEY_PINS` dizisinde yeni pini **K9'dan sonra, K10'dan önce** ekle
(işlev tuşları blok hâlinde başta durmalı):

```c
    EK_PIN_K7,  EK_PIN_K8,  EK_PIN_K9,
    EK_PIN_K12,                        // YENİ
    EK_PIN_K10, EK_PIN_K11
```

### 2.3 `app/core/config.py` — tuş sayısı

```python
KEY_COUNT: int = 10        # 9 -> 10
```

`KEY_IDS`, `COMBO_IDS`, isimler ve doğrulamalar bu sabitten türetilir.
Mevcut `config.json` ilk açılışta yeni slotlarla kendiliğinden tamamlanır.

### 2.4 `app/ui/key_grid.py` — yerleşim tablosu

`KEY_POSITIONS` sözlüğüne yeni tuşun ızgara konumunu ekle, örn.:

```python
"K12": (0, 4),    # satır 0, sütun 4 (enkoderin sağına yeni sütun)
```

Combo matrisi ve diğer ekranlar `KEY_COUNT`'tan türediği için kendiliğinden
büyür.

---

## 3. Mekanik tarafı unutma

- Plakada yeni tuş için **14.00 mm kare delik** (adım 19.05 korunmalı).
- Yeni sütun eklersen plaka genişliği sütun başına **+19.05** büyür;
  gövde dış ölçüsü de aynı miktar büyür (duvarlar plakanın dışında).
- Tuş, elektronik bölmesinin üzerine TAŞMAMALI (bölmede anahtar payı yok).

## 4. Doğrulama

1. Firmware'i derle-yükle; seri monitörde yeni tuşun `EV KEY <n>` ürettiğini gör.
2. PC'de `.venv/bin/python tools/selfcheck.py` çalıştır — tuş/combo sayıları
   yeni değere göre denetlenir.
3. Uygulamada Tuşlar sekmesinde yeni kartın göründüğünü ve atanabildiğini doğrula.
