# Bu klasör artık ikincil (opsiyonel referans)

Mekanik çizim **kendin yapılacak**. Ölçüleri buradan değil şuradan al:

### → [docs/BASIT-YAPIM.md](../docs/BASIT-YAPIM.md) §3

Orada üst plaka delik koordinatları, dikey katman yığını, gövde ölçüleri ve
3D baskı telafileri hazır tablolar hâlinde.

---

## Buradaki dosyalarla ilgili bilinen fark

Bu klasördeki `.scad` dosyaları ve `plate.dxf`, projenin **ilk (katmansız)**
tasarımına göre üretildi:

| | `.scad` dosyaları | Güncel tasarım (BASIT-YAPIM.md) |
|---|---|---|
| Gövde şekli | **düz kutu** | **önden arkaya yükselen kama, 8.04°** |
| Dış ölçü | 88.20 × 69.15 mm | **88.20 × 99.15 mm** |
| Arkada bölme | yok | **30.00 mm elektronik bölmesi** |
| Ön yükseklik | 22.00 mm | **15.00 mm** |
| Arka yükseklik | 22.00 mm | **29.00 mm** |
| İç boşluk | 18.00 mm (sabit) | **11.42 → 24.58 mm** |
| Vida | 4 adet | **6 adet** |

**İki sebep:**

1. **Yapı katmanlı hâle geldi** — delikli kart ve ESP32 artık anahtarların
   altında. Anahtar plakanın altında 9 mm, DevKit yığını 11.94 mm yer istiyor;
   ikisi tuş alanının altına sığmadığı için **arkaya 30 mm'lik anahtarsız bir
   bölme** eklendi. Plaka bu yüzden 69.15 → 99.15 mm derinleşti.
2. **Gövde ergonomi için eğimli yapıldı** (8.04°, klavye standardı 6–9°).

**Tuş yerleşimi değişmedi** (19.05 mm adım, 14.00 mm delikler) ama tuş satırları
plaka üzerinde 30 mm geriye kaydı, plaka dış ölçüsü de büyüdü.
⚠️ Bu yüzden **`plate.dxf` artık geçerli DEĞİLDİR** — güncel delik koordinatları
`docs/BASIT-YAPIM.md` §3.1'deki tablodadır.

> `case.scad` düz kutu üretir; kama gövde + bölme için yeniden yazılması gerekir.
> Kendi çizimini yapacağın için buna girmeye değmez — BASIT-YAPIM.md §3.2'deki
> iki yükseklik (15 / 29 mm) ile yandan yamuk çizmen yeterli.
> `docs/02-MEKANIK-TASARIM.md` içindeki Z-kotu tabloları da eski düz kutuya göredir.
> Karışıklığı önlemek için ya tamamen BASIT-YAPIM.md'yi izle, ya tamamen docs/02'yi.
