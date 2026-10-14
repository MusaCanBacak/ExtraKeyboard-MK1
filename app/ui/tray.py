# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Sistem Tepsisi Simgesi.

Uygulama penceresi kapatıldığında (ayara bağlı olarak) arka planda çalışmayı
sürdürür ve sistem tepsisinde bir simge bırakır. Simgeye tıklanarak pencere
geri getirilir veya uygulamadan çıkılır.

``pystray`` ya da ``Pillow`` kurulu değilse tepsi zarifçe devre dışı kalır;
uygulama yine de normal şekilde çalışır. Bu durumda pencere kapatma davranışı
otomatik olarak "çıkış"a döner (bkz. :meth:`TrayIcon.available`).

Tepsi menüsü geri çağırmaları **pystray'in kendi thread'inden** çağrılır.
Bu yüzden geri çağırmalar arayüze doğrudan dokunmamalı; ``after(0, ...)`` ile
ana thread'e aktarılmalıdır. Bu sorumluluk çağıran tarafındadır.
"""

from __future__ import annotations

import sys
import threading
from typing import Callable

#: macOS'ta pystray döngüsü ana thread'de çalışmak zorundadır.
IS_MAC: bool = sys.platform == "darwin"

try:  # pragma: no cover - ortama bağlı
    import pystray
    _PYSTRAY_ERROR: Exception | None = None
except Exception as _error:  # pragma: no cover
    pystray = None  # type: ignore[assignment]
    _PYSTRAY_ERROR = _error

try:  # pragma: no cover - ortama bağlı
    from PIL import Image, ImageDraw
    _PIL_ERROR: Exception | None = None
except Exception as _error:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    _PIL_ERROR = _error


#: Tepsi desteğinin bu ortamda kullanılabilir olup olmadığı.
TRAY_SUPPORTED: bool = pystray is not None and Image is not None


def dependency_error() -> str:
    """Tepsi kullanılamıyorsa sebebini Türkçe olarak açıklar."""
    if pystray is None:
        return f"pystray kütüphanesi yüklenemedi ({_PYSTRAY_ERROR})."
    if Image is None:
        return f"Pillow kütüphanesi yüklenemedi ({_PIL_ERROR})."
    return ""


def build_icon_image(connected: bool = False, size: int = 64):
    """Tepsi simgesinin görüntüsünü çizer.

    Simge, uygulamanın mavi üçgen logosudur; sağ alt köşesindeki küçük nokta
    cihaz bağlantı durumunu gösterir (yeşil = bağlı, kırmızı = bağlı değil).

    Args:
        connected: Cihaz bağlı mı.
        size: Kare simgenin kenar uzunluğu (piksel).

    Returns:
        ``PIL.Image.Image`` nesnesi; Pillow yoksa ``None``.
    """
    if Image is None or ImageDraw is None:
        return None

    background = "#101020"
    accent = "#3B8ED0"
    state_color = "#2CC985" if connected else "#E04F5F"

    image = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(image)

    # Ana logo: sol üstten inen üçgen
    draw.polygon([(0, 0), (size, 0), (0, size)], fill=accent)
    # İç boşluk — logoya derinlik verir
    inset = int(size * 0.22)
    draw.polygon([(inset, inset), (size - inset, inset), (inset, size - inset)],
                 fill=background)

    # Durum noktası
    radius = max(5, int(size * 0.13))
    center = (size - radius - 4, size - radius - 4)
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=state_color)
    return image


class TrayIcon:
    """pystray tabanlı sistem tepsisi simgesi sarmalayıcısı.

    Kütüphaneler yoksa ya da tepsi başlatılamazsa nesne sessizce
    "kullanılamaz" duruma geçer; çağıran taraf :attr:`available` ile
    kontrol edebilir.
    """

    def __init__(self, on_show: Callable[[], None], on_quit: Callable[[], None],
                 title: str = "ExtraKeyboard MK1") -> None:
        """Tepsi simgesini hazırlar (henüz başlatmaz).

        Args:
            on_show: "Ayarları Göster" seçilince çağrılır.
            on_quit: "Çıkış" seçilince çağrılır.
            title: Simgenin üzerine gelince görünen ipucu metni.
        """
        self._on_show = on_show
        self._on_quit = on_quit
        self._title = title
        self._icon = None
        self._thread: threading.Thread | None = None
        self._connected = False
        self._started = False
        self._failed = not TRAY_SUPPORTED

    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Tepsi bu ortamda kullanılabiliyor mu."""
        return TRAY_SUPPORTED and not self._failed

    @property
    def running(self) -> bool:
        """Tepsi simgesi şu anda çalışıyor mu."""
        if self._icon is None:
            return False
        if IS_MAC:
            return self._started
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Tepsi simgesini başlatır.

        Platform farkı önemlidir:

        * **macOS** — pystray'in Darwin arka ucu AppKit kullanır ve ana
          thread dışında çalıştırılamaz. Bu yüzden ``run_detached()``
          çağrılır; simge, Tkinter'ın zaten çalıştırdığı NSApplication
          döngüsüne iliştirilir. **Bu metot ana thread'den, pencere
          oluşturulduktan sonra çağrılmalıdır.**
        * **Diğer platformlar** — ``run()`` ayrı bir arka plan thread'inde
          çalıştırılır.

        Her iki yolda da hata olursa tepsi sessizce devre dışı kalır ve
        uygulama çalışmaya devam eder.

        Returns:
            Simge başlatılabildiyse ``True``.
        """
        if not self.available or self.running:
            return self.available

        try:
            menu = pystray.Menu(
                pystray.MenuItem("Ayarları Göster", self._handle_show, default=True),
                pystray.MenuItem("Çıkış", self._handle_quit),
            )
            self._icon = pystray.Icon(
                "extrakeyboard_mk1",
                build_icon_image(self._connected),
                self._tooltip(),
                menu)
        except Exception:
            self._failed = True
            self._icon = None
            return False

        if IS_MAC:
            try:
                self._icon.run_detached()
            except Exception:
                # Simge oluşturulamadı — tepsi devre dışı, uygulama etkilenmez.
                self._failed = True
                self._icon = None
                return False
            self._started = True
            return True

        self._thread = threading.Thread(target=self._run, name="TrayIcon", daemon=True)
        self._thread.start()
        self._started = True
        return True

    def _run(self) -> None:
        """pystray döngüsünü çalıştırır; hata olursa tepsiyi devre dışı bırakır."""
        icon = self._icon
        if icon is None:
            return
        try:
            icon.run()
        except Exception:
            self._failed = True
            self._icon = None
            self._started = False

    def stop(self) -> None:
        """Tepsi simgesini kapatır."""
        icon = self._icon
        self._icon = None
        self._started = False
        if icon is None:
            return
        try:
            icon.stop()
        except Exception:
            pass

    def set_connected(self, connected: bool) -> None:
        """Simgedeki durum noktasını ve ipucu metnini günceller.

        Args:
            connected: Cihaz bağlı mı.
        """
        if connected == self._connected:
            return
        self._connected = connected
        if self._icon is None:
            return
        try:
            self._icon.icon = build_icon_image(connected)
            self._icon.title = self._tooltip()
        except Exception:
            pass

    def notify(self, message: str, title: str | None = None) -> None:
        """Destekleniyorsa masaüstü bildirimi gösterir; desteklenmiyorsa yok sayar."""
        if self._icon is None:
            return
        try:
            self._icon.notify(message, title or self._title)
        except Exception:
            pass

    # ------------------------------------------------------------------

    def _tooltip(self) -> str:
        """Simge ipucu metnini üretir."""
        state = "Cihaz bağlı" if self._connected else "Cihaz bağlı değil"
        return f"{self._title} — {state}"

    def _handle_show(self, _icon=None, _item=None) -> None:
        """Menüdeki "Ayarları Göster" seçeneğini işler."""
        try:
            self._on_show()
        except Exception:
            pass

    def _handle_quit(self, _icon=None, _item=None) -> None:
        """Menüdeki "Çıkış" seçeneğini işler."""
        try:
            self._on_quit()
        except Exception:
            pass
