"""
ExtraKeyboard MK1 — çekirdek (core) katman.

Bu paket arayüzden bağımsızdır ve dört modülden oluşur:

============================  ==================================================
Modül                         Görevi
============================  ==================================================
``app.core.config``           ``config.json`` şeması, sabitler, ``ConfigManager``
``app.core.device``           CDC seri bağlantısı, ``DeviceLink`` + ``DeviceEvent``
``app.core.actions``          Eylem çalıştırıcı, ``ActionRunner``
``app.core.platform_utils``   İşletim sistemi tespiti, otomatik başlatma, açma
============================  ==================================================

Alt modüller **tembel (lazy)** olarak yüklenir: ``app.core`` paketini içe
aktarmak, ``pyserial`` veya ``pyautogui`` gibi isteğe bağlı bağımlılıkları
zorlamaz. Sık kullanılan sınıflar doğrudan paket üzerinden erişilebilir::

    from app.core import ConfigManager, DeviceLink, ActionRunner
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "config",
    "device",
    "actions",
    "platform_utils",
    "ConfigManager",
    "DeviceLink",
    "DeviceEvent",
    "ActionRunner",
    "combo_id",
    "parse_combo_id",
    "SCHEMA_VERSION",
]

# İsim -> (modül adı, modül içindeki nitelik adı) eşlemesi.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "ConfigManager": ("config", "ConfigManager"),
    "combo_id": ("config", "combo_id"),
    "parse_combo_id": ("config", "parse_combo_id"),
    "SCHEMA_VERSION": ("config", "SCHEMA_VERSION"),
    "DeviceLink": ("device", "DeviceLink"),
    "DeviceEvent": ("device", "DeviceEvent"),
    "ActionRunner": ("actions", "ActionRunner"),
}

_SUBMODULES: frozenset[str] = frozenset({"config", "device", "actions", "platform_utils"})


def __getattr__(name: str) -> Any:
    """
    Paket niteliklerini tembel çözer (PEP 562).

    ``app.core.ConfigManager`` gibi bir erişim ilk kez yapıldığında ilgili alt
    modül içe aktarılır ve sonuç paket sözlüğüne yazılır.

    :param name: Erişilmek istenen nitelik adı.
    :return: Çözümlenen modül veya sınıf/fonksiyon.
    :raises AttributeError: İsim bu pakette tanımlı değilse.
    """
    import importlib

    if name in _SUBMODULES:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module

    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = importlib.import_module(f"{__name__}.{module_name}")
        value = getattr(module, attr_name)
        globals()[name] = value
        return value

    raise AttributeError(f"'{__name__}' paketinde '{name}' adında bir öğe yok")


def __dir__() -> list[str]:
    """Otomatik tamamlama için paketin sunduğu isimleri döndürür."""
    return sorted(set(__all__) | set(globals()))
