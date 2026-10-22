# Lisans

ExtraKeyboard MK1'in kaynağı herkese açıktır ve **ticari olmayan** her kullanım için
serbesttir: kişisel kullanım, hobi, öğrenme, araştırma ve kâr amacı gütmeyen
kuruluşlar. Kopyalayabilir, değiştirebilir, kendiniz yapabilir ve paylaşabilirsiniz.

**Ticari kullanım için izin gerekir.** Cihazı ya da yazılımı satmak, bir ürünün veya
ücretli bir hizmetin parçası yapmak bu kapsamdadır. İzin istemek için
[GitHub'da bir konu (issue) açın](https://github.com/MusaCanBacak/ExtraKeyboard-MK1/issues).

Telif hakkı © 2026 BlueDevelopment

> Bu sayfa bir özettir. Bağlayıcı olan, aşağıda bağlantısı verilen İngilizce lisans
> metinleridir.

## Hangi lisans neye uygulanır

| Kapsam | Lisans | Metin |
|---|---|---|
| **Yazılım:** masaüstü uygulaması (`app/`), firmware (`firmware/`, `firmware-numpad/`), araçlar ve betikler (`tools/`, `dagitim/`, kökteki `.py`, `.command`, `.bat` dosyaları), Sürümler sayfasındaki derlenmiş firmware imajları ve uygulama paketleri | [PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0) | [`LICENSE.md`](LICENSE.md) |
| **Donanım tasarımı ve belgeler:** `hardware/`, `mechanical/` (OpenSCAD, DXF ve onu üreten betik dahil), `docs/`, `PIN-HARITASI.md`, `README.md`, `varliklar/` | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | [`LICENSE-CC-BY-NC-SA-4.0.txt`](LICENSE-CC-BY-NC-SA-4.0.txt) |

Tabloda sayılmayan dosyalar yazılım lisansına tabidir.

## Kısaca

**Yazılım — PolyForm Noncommercial 1.0.0**

- Ticari olmayan amaçla kullanmak, kopyalamak, değiştirmek ve dağıtmak serbesttir.
- Kişisel kullanım (hobi, öğrenme, kişisel araştırma) ile kâr amacı gütmeyen
  kuruluşların kullanımı (okul, üniversite, vakıf, kamu kurumu vb.) açıkça kapsanır.
- Dağıtırken lisans metnini ya da bağlantısını ve `LICENSE.md`'nin ilk satırındaki
  `Required Notice:` satırını birlikte verin.
- Ticari kullanım hakkı bu lisansla verilmez.

**Donanım ve belgeler — CC BY-NC-SA 4.0**

- **Atıf:** Kullandığınız ya da uyarladığınız yerde "ExtraKeyboard MK1 —
  BlueDevelopment" adını ve depo bağlantısını verin; değişiklik yaptıysanız belirtin.
- **Ticari olmayan:** Ticari amaçla kullanılamaz.
- **Aynı lisansla paylaş:** Uyarladığınız tasarım ve belgeleri aynı lisansla paylaşın.

## Üçüncü taraf bileşenler

Bu lisanslar yalnızca bu projenin kendi yazdığı kısımları kapsar. Kullanılan
bileşenler kendi lisanslarına tabidir. Derlenmiş firmware imajları ve macOS
uygulaması bunların bir kısmını içerir:

| Bileşen | Nerede | Lisans |
|---|---|---|
| Arduino-ESP32 çekirdeği | firmware | LGPL-2.1-or-later |
| ESP-IDF | firmware | Apache-2.0 |
| TinyUSB | firmware | MIT |
| Adafruit NeoPixel | firmware | LGPL-3.0 |
| Python | macOS uygulaması | PSF-2.0 |
| CustomTkinter | uygulama | paket bilgisinde CC0-1.0 / MIT |
| pyserial, pyautogui, pyperclip, qrcode, darkdetect | uygulama | BSD |
| Pillow | uygulama | MIT-CMU |
| pystray | uygulama | LGPL-3.0 |
| tkinterdnd2 | uygulama | MIT |
| PyInstaller (macOS paketini üretir) | macOS uygulaması | GPL-2.0-or-later, özel istisnayla |
| esptool | firmware yükleyicisi (ayrıca kurulur, pakete dahil değil) | GPL-2.0-or-later |

Her bileşenin bağlayıcı lisansı, kendi projesindeki lisans dosyasıdır.
