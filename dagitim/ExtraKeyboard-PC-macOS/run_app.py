#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Giriş Noktası.

Uygulama kök dizinden şu şekilde çalıştırılır::

    python3 run_app.py

Bu dosyanın tek görevi ortamı hazırlamaktır:

1. Proje kök dizinini ``sys.path``'e ekler; böylece ``app.core`` ve ``app.ui``
   paketleri, uygulama hangi dizinden başlatılırsa başlatılsın bulunur.
2. Python sürümünü doğrular (3.9 ve üzeri yeterlidir). ``str | None`` gibi
   tip birleşimleri yalnızca ANOTASYONLARDA kullanılır ve her modülde
   ``from __future__ import annotations`` bulunduğu için çalışma zamanında
   değerlendirilmezler; bu yüzden 3.9 da desteklenir.
3. Tcl/Tk sürümünü doğrular (8.6 şart). DİKKAT: macOS'un kendi Python 3.9'u
   (``/usr/bin/python3``) YETERLİ DEĞİLDİR — tkinter'i vardır ama Tk 8.5.9 ile
   gelir ve CustomTkinter widget'ları o sürümde hiç çizilmez; uygulama
   sorunsuz açılmış gibi görünür, pencere bomboş kalır. python.org'un
   Python'u (3.9 dahil her sürümü) Tk 8.6 içerir ve uygundur.
4. Zorunlu bağımlılıkları kontrol eder ve eksik olanları Türkçe bir mesajla
   bildirir.
5. :func:`app.main.main` fonksiyonunu çağırır.

İsteğe bağlı bağımlılıklar (``pystray``, ``Pillow``, ``pyautogui``) eksik olsa
bile uygulama açılır; yalnızca ilgili özellikler devre dışı kalır.
"""

from __future__ import annotations

import os
import sys

#: Bu dosyanın bulunduğu dizin = proje kök dizini.
PROJECT_ROOT: str = os.path.dirname(os.path.abspath(__file__))

#: Uygulamanın çalışması için gereken en düşük Python sürümü.
#: 3.9 ile uçtan uca doğrulandı (tüm modüller içe aktarılıyor, selfcheck
#: 45/45 geçiyor, arayüz açılıyor). Daha eskisi f-string ve tip sözdizimi
#: nedeniyle desteklenmez. Sürüm tek başına yetmez: Tk 8.6 da gerekir —
#: bkz. :func:`_check_tk_version`.
MIN_PYTHON: tuple[int, int] = (3, 9)

#: (içe aktarma adı, pip paket adı, ne işe yaradığı) üçlüleri.
REQUIRED_PACKAGES: tuple[tuple[str, str, str], ...] = (
    ("customtkinter", "customtkinter", "arayüz bileşenleri"),
    ("serial", "pyserial", "cihazla seri haberleşme"),
)

#: Eksikliği uygulamayı durdurmayan, yalnızca özellik kapatan paketler.
OPTIONAL_PACKAGES: tuple[tuple[str, str, str], ...] = (
    ("pystray", "pystray", "sistem tepsisi simgesi"),
    ("PIL", "pillow", "tepsi simgesi görüntüsü"),
    ("pyautogui", "pyautogui", "kısayol ve metin yazma eylemleri"),
)


def _ensure_project_on_path() -> None:
    """Proje kök dizinini ``sys.path``'in başına ekler."""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def _check_python_version() -> bool:
    """Python sürümünü doğrular ve yetersizse Türkçe uyarı yazar.

    Returns:
        Sürüm yeterliyse ``True``.
    """
    if sys.version_info >= MIN_PYTHON:
        return True
    current = ".".join(str(part) for part in sys.version_info[:3])
    needed = ".".join(str(part) for part in MIN_PYTHON)
    print(f"HATA: Python {needed} veya üzeri gerekiyor, bu ortamda {current} var.",
          file=sys.stderr)
    return False


def _check_tk_version() -> bool:
    """Tcl/Tk sürümünü doğrular; 8.6'dan eskiyse anlaşılır hata yazar.

    NEDEN AYRI BİR KONTROL: macOS'un kendi Python 3.9'u (``/usr/bin/python3``)
    2010 yapımı **Tk 8.5.9** ile gelir. Uygulama bu ortamda hatasız başlar,
    pencere açılır, tıklamalar bile çalışır — ama CustomTkinter'ın tuval
    tabanlı widget'larının hiçbiri çizilmez: kullanıcı bomboş (açık temada
    bembeyaz) bir pencere görür. Sessizce yanlış çalışmaktansa burada
    durup ne yapılacağını söylemek gerekir.

    Returns:
        Tk 8.6 veya üzeri ise ``True``.
    """
    try:
        import tkinter
        surum = float(tkinter.TkVersion)
    except Exception as hata:  # noqa: BLE001 - tkinter yoksa da anlaşılır mesaj
        print("HATA: Tcl/Tk (tkinter) kullanılamıyor:", hata, file=sys.stderr)
        print("Çözüm: python.org'dan Python kurun (Tcl/Tk dahildir).",
              file=sys.stderr)
        return False

    if surum >= 8.6:
        return True

    print(f"HATA: Bu Python'un Tcl/Tk sürümü çok eski (Tk {surum:.1f}).",
          file=sys.stderr)
    print("      Arayüz bu sürümde ÇİZİLMEZ — pencere bomboş/beyaz görünür.",
          file=sys.stderr)
    print(f"      Kullanılan Python: {sys.executable}", file=sys.stderr)
    print("", file=sys.stderr)
    print("ÇÖZÜM: Tk 8.6 içeren bir Python kurun:", file=sys.stderr)
    if sys.platform == "darwin":
        print("   1) https://www.python.org/downloads/macos/ adresinden", file=sys.stderr)
        print("      Python 3.12 (veya üstü) kurun — Tcl/Tk 8.6 dahildir.", file=sys.stderr)
        print("   2) Bu klasördeki .venv klasörünü silin.", file=sys.stderr)
        print("   3) Baslat.command dosyasına yeniden çift tıklayın.", file=sys.stderr)
        print("", file=sys.stderr)
        print("   Not: macOS'un kendi Python 3.9'u (/usr/bin/python3) Tk 8.5.9", file=sys.stderr)
        print("   ile gelir ve bu uygulama için yeterli değildir.", file=sys.stderr)
    else:
        print("   https://www.python.org adresinden güncel Python kurun,",
              file=sys.stderr)
        print("   .venv klasörünü silip başlatıcıyı yeniden çalıştırın.",
              file=sys.stderr)
    return False


def _missing_packages(packages) -> list[tuple[str, str, str]]:
    """Verilen listedeki içe aktarılamayan paketleri döndürür."""
    import importlib.util

    missing: list[tuple[str, str, str]] = []
    for module_name, pip_name, purpose in packages:
        try:
            found = importlib.util.find_spec(module_name) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            missing.append((module_name, pip_name, purpose))
    return missing


def _check_dependencies() -> bool:
    """Zorunlu bağımlılıkları kontrol eder, eksikleri Türkçe olarak bildirir.

    Returns:
        Tüm zorunlu paketler mevcutsa ``True``.
    """
    missing_required = _missing_packages(REQUIRED_PACKAGES)
    if missing_required:
        print("HATA: Uygulama için gerekli paketler eksik:", file=sys.stderr)
        for _module, pip_name, purpose in missing_required:
            print(f"  • {pip_name:<16} — {purpose}", file=sys.stderr)
        names = " ".join(pip_name for _m, pip_name, _p in missing_required)
        print("\nKurmak için:", file=sys.stderr)
        print(f"    {sys.executable} -m pip install {names}", file=sys.stderr)
        return False

    missing_optional = _missing_packages(OPTIONAL_PACKAGES)
    if missing_optional:
        print("Uyarı: bazı isteğe bağlı paketler yok, ilgili özellikler kapalı olacak:")
        for _module, pip_name, purpose in missing_optional:
            print(f"  • {pip_name:<16} — {purpose}")
    return True


def main() -> int:
    """Ortamı hazırlar ve uygulamayı başlatır.

    Returns:
        Süreç çıkış kodu (``0`` = normal kapanış).
    """
    _ensure_project_on_path()

    if not _check_python_version():
        return 2
    if not _check_tk_version():
        return 2
    if not _check_dependencies():
        return 2

    try:
        from app.main import main as run_application
    except Exception as error:  # noqa: BLE001 - kullanıcıya anlaşılır mesaj gerek
        print(f"HATA: Uygulama modülleri yüklenemedi: {error}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    return run_application(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
