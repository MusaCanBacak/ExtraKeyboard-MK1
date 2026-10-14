"""
ExtraKeyboard MK1 — PC uygulaması paketi.

Bu paket iki katmandan oluşur:

* ``app.core``  — arayüzden tamamen bağımsız çekirdek katman
  (yapılandırma, cihaz bağlantısı, eylem çalıştırıcı, platform yardımcıları).
* ``app.ui``    — CustomTkinter tabanlı kullanıcı arayüzü katmanı.

Çekirdek katman hiçbir arayüz modülünü içe aktarmaz; bu sayede uygulama
başsız (headless) olarak da çalıştırılabilir ve test edilebilir.

Sürüm bilgileri ``docs/00-CEKIRDEK-SPEC.md`` bölüm 10 ile birebir aynıdır.
"""

from __future__ import annotations

__all__ = ["APP_VERSION", "FW_VERSION", "HW_REV", "APP_NAME", "APP_TITLE"]

#: PC uygulamasının sürümü (spec bölüm 10).
APP_VERSION: str = "3.0.0"

#: Uyumlu olduğumuz firmware sürümü (spec bölüm 10).
FW_VERSION: str = "3.0.0"

#: Donanım revizyonu (spec bölüm 10).
HW_REV: str = "MK1"

#: Kısa uygulama adı — otomatik başlatma kaydı ve tepsi simgesi için kullanılır.
APP_NAME: str = "ExtraKeyboard"

#: Pencere başlıklarında gösterilen tam ad.
APP_TITLE: str = "ExtraKeyboard MK1"
