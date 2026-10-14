# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Arayüz Katmanı.

Bu paket, CustomTkinter ile yazılmış tüm görsel bileşenleri barındırır:

* :mod:`app.ui.theme`         — renkler, fontlar, ortak stil sabitleri
* :mod:`app.ui.main_window`   — ana pencere, sekmeler, yan panel, durum çubuğu
* :mod:`app.ui.key_grid`      — 4×3 fiziksel tuş yerleşimi
* :mod:`app.ui.combo_matrix`  — 9×9 üst üçgen combo matrisi (36 hücre)
* :mod:`app.ui.encoder_panel` — enkoder eylemleri ve modu
* :mod:`app.ui.device_panel`  — LED renkleri, port yönetimi, canlı olay logu
* :mod:`app.ui.action_editor` — tüm slotlar için ortak eylem düzenleyici
* :mod:`app.ui.tray`          — sistem tepsisi simgesi

**Önemli kural:** cihaz katmanının ``on_event`` geri çağırması arka plan
thread'inden gelir. Tkinter bileşenlerine yalnızca ana thread'den
dokunulur; geçiş her zaman ``widget.after(0, ...)`` ile yapılır.

Alt modüller doğrudan içe aktarılmalıdır (``from app.ui.theme import ...``).
Bu dosya, CustomTkinter'ı uygulama açılmadan yüklememek için hiçbir alt
modülü kendiliğinden içe aktarmaz.
"""

from __future__ import annotations

__all__ = [
    "theme",
    "main_window",
    "key_grid",
    "combo_matrix",
    "encoder_panel",
    "device_panel",
    "action_editor",
    "tray",
]
