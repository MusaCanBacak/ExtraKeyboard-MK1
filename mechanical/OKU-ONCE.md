# mechanical/ — baskı dosyaları

## Güncel baskı dosyaları → [`stl/`](stl/)

| Dosya | Parça |
|---|---|
| [`stl/govde.stl`](stl/govde.stl) | Eğimli gövde, dış 94.20 × 105.15 mm, ön 19 → arka 33 mm. Klavye ve numpad için aynı |
| [`stl/ust-plaka-klavye.stl`](stl/ust-plaka-klavye.stl) | Klavye üst plakası, 87.85 × 99.77 × 3.00 mm: 12 tuş + enkoder + 3 LED |
| [`stl/ust-plaka-numpad.stl`](stl/ust-plaka-numpad.stl) | Numpad üst plakası, aynı dış ölçü: 16 tuş + 2 LED |
| [`stl/enkoder-dugmesi.stl`](stl/enkoder-dugmesi.stl) | Enkoder düğmesi, ⌀20 × 7.5 mm |

Ölçüler, delik koordinatları, baskı yönü ve montaj sırası:
**[docs/BASIT-YAPIM.md](../docs/BASIT-YAPIM.md) §3 ve §6.**
Tuş başlığı dosyası yoktur; MX uyumlu herhangi bir tuş başlığı olur.

---

## Bu klasördeki `.scad` dosyaları ve `plate.dxf` — ilk tasarım

Bu dosyalar projenin **ilk** tasarımına aittir ve güncel baskı dosyalarıyla
uyumlu **değildir**. Yalnızca referans olarak bırakıldı.

| | `.scad` / `plate.dxf` | Güncel (`stl/`) |
|---|---|---|
| Tuş | 11 (3 × 3 + sağ sütunda enkoder / COMBO / OS) | **12** (4 × 3), numpad **16** |
| Gövde | düz kutu, 88.20 × 69.15 mm, 22 mm yükseklik | **kama**, dış 94.20 × 105.15 mm, ön 19 → arka 33 mm, 8° |
| Plaka | 1.50 mm | **3.00 mm**, 87.85 × 99.77 mm |
| Enkoder | tuş ızgarasında | **arka şeritte**, LED'lerin yanında |
| LED | 3 × WS2812B | **3 düz LED** (⌀3.2 pencere) + ışık bölmesi |
| Plaka tutturma | — | **4 köşe vidası** (M2), gövdedeki takozlara |

`docs/02-MEKANIK-TASARIM.md` de bu ilk tasarıma göredir.
