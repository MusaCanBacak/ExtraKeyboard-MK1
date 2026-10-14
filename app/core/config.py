"""
ExtraKeyboard MK1 — yapılandırma katmanı (``config.json``, şema 3).

Bu modül tek doğruluk kaynağı olan ``docs/00-CEKIRDEK-SPEC.md`` bölüm 7 ve
bölüm 8'deki şemayı ve API sözleşmesini birebir uygular:

* Slot isimleri: ``K1``..``K10``, ``C_<a>_<b>`` (daima ``a < b``, 45 adet),
  enkoder için ``cw`` / ``ccw`` / ``press`` / ``long``.
* Windows ve macOS profilleri **ayrı** tutulur (``windows`` / ``mac``).
* Eylem tipleri: ``none``, ``app``, ``url``, ``shortcut``, ``text``,
  ``command``, ``file``, ``folder``, ``media``, ``macro``.

Modülün üç temel sorumluluğu vardır:

1. Varsayılan yapılandırmayı **programatik** üretmek (45 combo dâhil).
2. Eski v2 ``macro_config.json`` dosyasını yeni şemaya taşımak (migrate).
3. Diske **atomik** yazmak (``.tmp`` + ``os.replace``) ve bozuk dosyada
   çökmeden yedek alıp varsayılana düşmek.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "SCHEMA_VERSION",
    "APP_VERSION",
    "HW_REV",
    "KEY_IDS",
    "COMBO_IDS",
    "ENCODER_IDS",
    "ACTION_TYPES",
    "RISKY_ACTION_TYPES",
    "find_risky_actions",
    "MEDIA_VALUES",
    "OS_KEYS",
    "DEFAULT_PROFILE_NAME",
    "DEFAULT_MOBILE_PORT",
    "KEY_NAMES",
    "ENCODER_NAMES",
    "MEDIA_NAMES",
    "ACTION_TYPE_NAMES",
    "UI_COLORS",
    "combo_id",
    "parse_combo_id",
    "combo_name",
    "slot_display_name",
    "is_valid_slot",
    "default_config",
    "default_profile",
    "default_os_profile",
    "project_root",
    "default_config_path",
    "legacy_config_path",
    "migrate_v2_data",
    "looks_like_v2",
    "ConfigManager",
]

# ---------------------------------------------------------------------------
# 1) Sürüm ve şema sabitleri (spec bölüm 7 ve 10)
# ---------------------------------------------------------------------------

#: ``config.json`` içindeki ``schema`` alanının beklenen değeri.
#: Not: Tuş sayısı artışı gibi slot genişlemeleri şema sürümünü DEĞİŞTİRMEZ;
#: eksik slotlar ``_normalize`` yolunda varsayılanla otomatik tamamlanır,
#: bu yüzden eski dosyalar taşıma gerektirmeden kendiliğinden güncellenir.
SCHEMA_VERSION: int = 3

#: PC uygulaması sürümü.
APP_VERSION: str = "3.0.0"

#: Donanım revizyonu.
HW_REV: str = "MK1"

#: İlk çalıştırmada üretilen profilin adı (spec bölüm 7'deki JSON ile aynı).
DEFAULT_PROFILE_NAME: str = "Varsayilan"

#: İşlev tuşu sayısı (K1..K10).
KEY_COUNT: int = 10

#: Doğrudan atanabilir tuş kimlikleri: ``["K1", ..., "K10"]``.
KEY_IDS: list[str] = [f"K{i}" for i in range(1, KEY_COUNT + 1)]

#: Enkoder slot kimlikleri (spec bölüm 7.1).
ENCODER_IDS: list[str] = ["cw", "ccw", "press", "long"]

#: Desteklenen eylem tipleri (spec bölüm 7.2).
ACTION_TYPES: list[str] = [
    "none",
    "app",
    "url",
    "shortcut",
    "text",
    "command",
    "file",
    "folder",
    "media",
    "macro",
]

#: İçe aktarmada KULLANICI ONAYI gerektiren eylem tipleri.
#:
#: ``command`` doğrudan kullanıcının login kabuğunda komut çalıştırır
#: (bkz. :mod:`app.core.actions` ``_run_command`` → ``[shell, "-lc", ...]``),
#: ``app`` ise rastgele bir yürütülebilir dosyayı başlatabilir. Paylaşılan
#: bir "hazır profil" dosyası bu slotlarla gelirse ilk tuş basışında kod
#: çalışır; bu yüzden içe aktarma sessizce kabul edilmez.
RISKY_ACTION_TYPES: tuple[str, ...] = ("command", "app")

#: ``media`` tipinin kabul ettiği değerler (spec bölüm 7.2).
MEDIA_VALUES: list[str] = [
    "volume_up",
    "volume_down",
    "mute",
    "play_pause",
    "next",
    "prev",
]

#: Profil içindeki işletim sistemi bölümleri.
OS_KEYS: list[str] = ["windows", "mac"]

# ---------------------------------------------------------------------------
# 2) Cihaz kimliği (spec bölüm 4) ve LED sabitleri (spec bölüm 6.4)
# ---------------------------------------------------------------------------

#: USB satıcı kimliği (Espressif).
DEVICE_VID: str = "0x303A"

#: USB ürün kimliği.
DEVICE_PID: str = "0x82E1"

#: USB ürün dizgesi.
DEVICE_PRODUCT: str = "ExtraKeyboard MK1"

#: USB üretici dizgesi.
DEVICE_MANUFACTURER: str = "BlueDevelopment"

#: CDC seri portun açılış hızı (native USB'de önemsizdir, yine de kullanılır).
DEVICE_BAUD: int = 115200

#: LED1 — Windows modu rengi.
COLOR_OS_WIN: str = "#1E90FF"

#: LED1 — macOS modu rengi.
COLOR_OS_MAC: str = "#FFFFFF"

#: LED2 — combo modu rengi.
COLOR_COMBO: str = "#FF9500"

#: LED3 — uygulama bağlı rengi.
COLOR_LINK_OK: str = "#2CC985"

#: LED3 — bağlantı yok / HID yedek rengi.
COLOR_LINK_ERR: str = "#E04F5F"

#: Varsayılan LED parlaklığı (0-255).
DEFAULT_BRIGHTNESS: int = 60

#: Arayüz katmanının kullanacağı tema renkleri (spec bölüm 8).
UI_COLORS: dict[str, str] = {
    "bg": "#1a1a2e",
    "panel": "#16213e",
    "card": "#1e1e2e",
    "accent": "#3B8ED0",
    "success": "#2CC985",
    "warning": "#FF9500",
    "danger": "#E04F5F",
}

# ---------------------------------------------------------------------------
# 3) Combo kimlikleri — programatik üretim
# ---------------------------------------------------------------------------

_COMBO_RE: re.Pattern[str] = re.compile(r"^C_(\d+)_(\d+)$", re.IGNORECASE)


def combo_id(a: int, b: int) -> str:
    """
    İki tuş numarasından combo slot kimliği üretir.

    Kimlik daima ``a < b`` olacak biçimde normalize edilir; yani ``(5, 2)``
    ile ``(2, 5)`` aynı kimliği (``"C_2_5"``) döndürür.

    :param a: Birinci tuş numarası (1..10).
    :param b: İkinci tuş numarası (1..10).
    :return: ``"C_<a>_<b>"`` biçiminde combo kimliği.
    :raises ValueError: Numaralar 1..9 aralığı dışındaysa veya eşitse.
    """
    try:
        first = int(a)
        second = int(b)
    except (TypeError, ValueError) as exc:  # pragma: no cover - savunma amaçlı
        raise ValueError(f"Combo tuş numaraları sayı olmalı: {a!r}, {b!r}") from exc

    if first > second:
        first, second = second, first
    if first == second:
        raise ValueError(f"Combo için iki farklı tuş gerekir: {a!r} ve {b!r}")
    if not (1 <= first <= KEY_COUNT) or not (1 <= second <= KEY_COUNT):
        raise ValueError(f"Tuş numarası 1..{KEY_COUNT} aralığında olmalı: {a!r}, {b!r}")
    return f"C_{first}_{second}"


def parse_combo_id(cid: str) -> tuple[int, int]:
    """
    Combo slot kimliğini ``(a, b)`` tuş numaralarına ayrıştırır.

    :param cid: ``"C_2_5"`` biçiminde combo kimliği.
    :return: ``(2, 5)`` gibi, daima ``a < b`` olan tuş numarası ikilisi.
    :raises ValueError: Kimlik biçimi geçersizse veya numaralar aralık dışıysa.
    """
    match = _COMBO_RE.match(str(cid).strip())
    if match is None:
        raise ValueError(f"Geçersiz combo kimliği: {cid!r}")
    first = int(match.group(1))
    second = int(match.group(2))
    if first > second:
        first, second = second, first
    if first == second:
        raise ValueError(f"Combo kimliğinde iki tuş aynı olamaz: {cid!r}")
    if not (1 <= first <= KEY_COUNT) or not (1 <= second <= KEY_COUNT):
        raise ValueError(f"Combo kimliği aralık dışı: {cid!r}")
    return first, second


#: C(10,2) = 45 adet combo kimliği, küçükten büyüğe sıralı.
COMBO_IDS: list[str] = [
    combo_id(a, b) for a in range(1, KEY_COUNT + 1) for b in range(a + 1, KEY_COUNT + 1)
]

# ---------------------------------------------------------------------------
# 4) Türkçe görünen adlar
# ---------------------------------------------------------------------------

#: Tuş kimliği -> varsayılan Türkçe ad.
KEY_NAMES: dict[str, str] = {f"K{i}": f"Tuş {i}" for i in range(1, KEY_COUNT + 1)}

#: Enkoder slotu -> varsayılan Türkçe ad.
ENCODER_NAMES: dict[str, str] = {
    "cw": "Ses +",
    "ccw": "Ses −",
    "press": "Sessiz",
    "long": "Uzun basış",
}

#: Eylem tipi -> arayüzde gösterilecek Türkçe etiket.
ACTION_TYPE_NAMES: dict[str, str] = {
    "none": "Boş",
    "app": "Uygulama",
    "url": "Web adresi",
    "shortcut": "Kısayol",
    "text": "Metin yaz",
    "command": "Komut çalıştır",
    "file": "Dosya aç",
    "folder": "Klasör aç",
    "media": "Medya tuşu",
    "macro": "Makro",
}

#: Medya değeri -> arayüzde gösterilecek Türkçe etiket.
MEDIA_NAMES: dict[str, str] = {
    "volume_up": "Ses aç",
    "volume_down": "Ses kıs",
    "mute": "Sessize al",
    "play_pause": "Oynat / Duraklat",
    "next": "Sonraki parça",
    "prev": "Önceki parça",
}


def combo_name(cid: str) -> str:
    """
    Combo kimliğinden varsayılan Türkçe adı üretir.

    :param cid: ``"C_2_5"`` biçiminde combo kimliği.
    :return: ``"Combo 2+5"`` biçiminde ad.
    """
    first, second = parse_combo_id(cid)
    return f"Combo {first}+{second}"


def slot_display_name(slot: str) -> str:
    """
    Herhangi bir slot kimliği için insan tarafından okunabilir Türkçe ad verir.

    :param slot: ``"K3"``, ``"C_2_5"``, ``"cw"`` gibi slot kimliği.
    :return: Türkçe görünen ad; bilinmeyen slotlarda kimliğin kendisi.
    """
    key = str(slot).strip()
    if key in KEY_NAMES:
        return KEY_NAMES[key]
    if key in ENCODER_NAMES:
        return ENCODER_NAMES[key]
    try:
        return combo_name(key)
    except ValueError:
        return key


def find_risky_actions(config: Any) -> list[dict[str, str]]:
    """
    Bir yapılandırma sözlüğündeki "riskli" eylem slotlarını listeler.

    Riskli olanlar :data:`RISKY_ACTION_TYPES` tiplerindeki (``command`` ve
    ``app``) slotlardır; bunlar tuşa basılınca kabuk komutu çalıştırabilir
    veya rastgele bir program başlatabilir. İçe aktarma öncesi kullanıcıya
    ne kabul ettiğini göstermek için kullanılır.

    :param config: Onarılmış (normalize edilmiş) yapılandırma sözlüğü.
    :return: ``profile`` / ``os`` / ``slot`` / ``slot_name`` / ``type`` /
        ``value`` / ``name`` anahtarlı sözlüklerden oluşan liste.
    """
    bulunanlar: list[dict[str, str]] = []
    if not isinstance(config, dict):
        return bulunanlar
    profiles = config.get("profiles")
    if not isinstance(profiles, dict):
        return bulunanlar

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        for os_key in OS_KEYS:
            section = profile.get(os_key)
            if not isinstance(section, dict):
                continue
            for group in ("keys", "combos", "encoder"):
                slots = section.get(group)
                if not isinstance(slots, dict):
                    continue
                for slot_id, action in slots.items():
                    # encoder bölümündeki "mode" gibi sözlük olmayan alanlar
                    # eylem değildir; atlanır.
                    if not isinstance(action, dict):
                        continue
                    action_type = str(action.get("type", "") or "").strip().lower()
                    if action_type not in RISKY_ACTION_TYPES:
                        continue
                    bulunanlar.append({
                        "profile": str(profile_name),
                        "os": str(os_key),
                        "slot": str(slot_id),
                        "slot_name": slot_display_name(str(slot_id)),
                        "type": action_type,
                        "value": str(action.get("value", "") or ""),
                        "name": str(action.get("name", "") or ""),
                    })
    return bulunanlar


def is_valid_slot(slot: str) -> bool:
    """
    Verilen kimliğin geçerli bir slot olup olmadığını söyler.

    :param slot: Denetlenecek slot kimliği.
    :return: ``K1..K10``, 45 combodan biri veya enkoder slotuysa ``True``.
    """
    key = str(slot).strip()
    if key in KEY_IDS or key in ENCODER_IDS:
        return True
    try:
        parse_combo_id(key)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------------------
# 5) Varsayılan yapılandırma üretimi
# ---------------------------------------------------------------------------

#: Varsayılan cihaz bölümü (spec bölüm 7).
DEFAULT_DEVICE: dict[str, Any] = {
    "port": "auto",
    "vid": DEVICE_VID,
    "pid": DEVICE_PID,
    "product": DEVICE_PRODUCT,
    "baud": DEVICE_BAUD,
}

#: Varsayılan LED bölümü (spec bölüm 7).
DEFAULT_LEDS: dict[str, Any] = {
    "brightness": DEFAULT_BRIGHTNESS,
    "os_win": COLOR_OS_WIN,
    "os_mac": COLOR_OS_MAC,
    "combo": COLOR_COMBO,
    "link_ok": COLOR_LINK_OK,
    "link_err": COLOR_LINK_ERR,
}

#: Varsayılan arayüz bölümü (spec bölüm 7).
DEFAULT_UI: dict[str, Any] = {
    "theme": "Dark",
    "minimize_to_tray": True,
    "start_minimized": False,
    # LED & Cihaz sekmesindeki gelişmiş renk bölümünü göster/gizle.
    # Bu üründeki 3 LED düz (tek renk) olduğu için varsayılan KAPALI.
    "show_led_colors": False,
    # macOS Erişilebilirlik izni diyaloğu bir daha gösterilmesin mi?
    # (Kullanıcı "Bir daha sorma" derse True olur; izin verilirse diyalog
    #  zaten hiç çıkmaz.)
    "hide_accessibility_prompt": False,
}

#: Mobil ayar sunucusunun varsayılan TCP portu.
DEFAULT_MOBILE_PORT: int = 8756

#: Varsayılan mobil bölümü (telefondan ayar arayüzü sunucusu).
#:
#: ``enabled`` VARSAYILAN OLARAK KAPALI: sunucu 0.0.0.0'da dinlediği için
#: yerel ağdaki herkese görünür olur. Kullanıcı "Telefon" sekmesinden
#: bilinçli olarak açmalıdır (gizli jeton için bkz. ``token``).
#:
#: ``token`` sunucunun ürettiği erişim jetonudur; adres ``/t/<jeton>/``
#: biçimindedir. Burada saklanır ki uygulama yeniden başladığında telefondaki
#: kısayol/QR geçerliliğini korusun. Boşsa sunucu yeni bir jeton üretir.
DEFAULT_MOBILE: dict[str, Any] = {
    "enabled": False,
    "port": DEFAULT_MOBILE_PORT,
    "token": "",
}

#: Erişim jetonunda kabul edilen biçim (URL güvenli base64, 8-64 karakter).
_MOBILE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def _normalize_mobile_token(raw: Any) -> str:
    """
    Mobil erişim jetonunu doğrular.

    :param raw: Ham jeton değeri (dosyadan gelebilir).
    :return: Geçerliyse jetonun kendisi, değilse boş dizge.
    """
    aday = str(raw or "").strip()
    return aday if _MOBILE_TOKEN_RE.match(aday) else ""


def _normalize_mobile_port(raw: Any) -> int:
    """
    Mobil sunucu portunu geçerli aralığa çeker.

    :param raw: Ham port değeri (sayı olmayabilir).
    :return: 1024-65535 aralığında port; geçersizse ``DEFAULT_MOBILE_PORT``.
    """
    try:
        port = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MOBILE_PORT
    if not (1024 <= port <= 65535):
        return DEFAULT_MOBILE_PORT
    return port


def new_action(type_: str = "none", value: str = "", name: str = "") -> dict[str, str]:
    """
    Tek bir eylem sözlüğü üretir.

    :param type_: Eylem tipi; ``ACTION_TYPES`` dışındaysa ``"none"`` olur.
    :param value: Eylem değeri.
    :param name: Slotun görünen adı.
    :return: ``{"type": ..., "value": ..., "name": ...}`` sözlüğü.
    """
    action_type = str(type_).strip().lower()
    if action_type not in ACTION_TYPES:
        action_type = "none"
    return {"type": action_type, "value": str(value), "name": str(name)}


def default_key_actions() -> dict[str, dict[str, str]]:
    """K1..K10 için boş eylem sözlüğü üretir."""
    return {kid: new_action("none", "", KEY_NAMES[kid]) for kid in KEY_IDS}


def default_combo_actions() -> dict[str, dict[str, str]]:
    """45 combo için boş eylem sözlüğü üretir."""
    return {cid: new_action("none", "", combo_name(cid)) for cid in COMBO_IDS}


def default_encoder_actions() -> dict[str, Any]:
    """
    Enkoder bölümünün varsayılanını üretir.

    Spec bölüm 7'deki JSON ile birebir aynıdır: mod ``hid``, döndürme ses
    açar/kısar, basış sessize alır, uzun basış boştur.
    """
    return {
        "mode": "hid",
        "cw": new_action("media", "volume_up", ENCODER_NAMES["cw"]),
        "ccw": new_action("media", "volume_down", ENCODER_NAMES["ccw"]),
        "press": new_action("media", "mute", ENCODER_NAMES["press"]),
        "long": new_action("none", "", ENCODER_NAMES["long"]),
    }


def default_os_profile() -> dict[str, Any]:
    """Tek bir işletim sistemi bölümünün (keys + combos + encoder) varsayılanı."""
    return {
        "keys": default_key_actions(),
        "combos": default_combo_actions(),
        "encoder": default_encoder_actions(),
    }


def default_profile() -> dict[str, Any]:
    """``windows`` ve ``mac`` bölümlerini eksiksiz içeren varsayılan profil."""
    return {os_key: default_os_profile() for os_key in OS_KEYS}


def default_config() -> dict[str, Any]:
    """
    Şema 3'e uygun, eksiksiz varsayılan yapılandırmayı üretir.

    :return: ``config.json`` içeriğine karşılık gelen sözlük.
    """
    return {
        "schema": SCHEMA_VERSION,
        "app_version": APP_VERSION,
        "device": dict(DEFAULT_DEVICE),
        "active_profile": DEFAULT_PROFILE_NAME,
        "profiles": {DEFAULT_PROFILE_NAME: default_profile()},
        "leds": dict(DEFAULT_LEDS),
        "ui": dict(DEFAULT_UI),
        "mobile": dict(DEFAULT_MOBILE),
        "autostart": False,
    }


# ---------------------------------------------------------------------------
# 6) Dosya yolları
# ---------------------------------------------------------------------------


def project_root() -> Path:
    """
    Proje kök dizinini döndürür.

    Donmuş (PyInstaller ile paketlenmiş) çalıştırmada çalıştırılabilir dosyanın
    bulunduğu dizin, normal çalıştırmada ise ``app/core/config.py`` dosyasının
    iki üst dizini (``ExtraKeyboard/``) kullanılır.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Kullanıcıya ait yazılabilir veri dizinini döndürür.

    Yalnızca PAKETLENMİŞ (``.app`` / ``.exe``) çalıştırmada kullanılır:
    uygulama paketinin içi yazmaya uygun değildir — macOS'ta pakete yazmak
    kod imzasını geçersiz kılar ve uygulama güncellendiğinde içindeki her
    şey silinir. Kaynak koddan çalıştırmada eski davranış (ayarların proje
    klasöründe durması) korunur; taşınabilir kurulumun anlamı budur.
    """
    if sys.platform == "darwin":
        temel = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        temel = Path(os.environ.get("APPDATA")
                     or (Path.home() / "AppData" / "Roaming"))
    else:
        temel = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return temel / "ExtraKeyboard"


def _yapilandirma_dizini() -> Path:
    """Yapılandırma dosyalarının bulunduğu dizin (paketlenmişse kullanıcı dizini)."""
    if getattr(sys, "frozen", False):
        dizin = user_data_dir()
        try:
            dizin.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return dizin
    return project_root()


def default_config_path() -> str:
    """Yeni v3 yapılandırma dosyasının varsayılan tam yolu (``config.json``)."""
    return str(_yapilandirma_dizini() / "config.json")


def legacy_config_path() -> str:
    """Eski v2 yapılandırma dosyasının tam yolu (``macro_config.json``)."""
    return str(_yapilandirma_dizini() / "macro_config.json")


# ---------------------------------------------------------------------------
# 7) v2 -> v3 taşıma (migration)
# ---------------------------------------------------------------------------

#: Eski HID tuş adı -> yeni slot kimliği. F13..F20 sırayla K1..K8 olur,
#: K9 ve K10 boş kalır.
V2_KEY_MAP: dict[str, str] = {f"F{13 + i}": f"K{i + 1}" for i in range(8)}

#: Eski/serbest yazılmış medya değerlerini şemadaki değerlere eşler.
_MEDIA_ALIASES: dict[str, str] = {
    "volumeup": "volume_up",
    "volume+": "volume_up",
    "vol_up": "volume_up",
    "volumedown": "volume_down",
    "volume-": "volume_down",
    "vol_down": "volume_down",
    "volumemute": "mute",
    "volume_mute": "mute",
    "sessiz": "mute",
    "playpause": "play_pause",
    "play": "play_pause",
    "pause": "play_pause",
    "nexttrack": "next",
    "next_track": "next",
    "prevtrack": "prev",
    "prev_track": "prev",
    "previous": "prev",
    "previoustrack": "prev",
}


def _sanitize_action(raw: Any, fallback_name: str) -> dict[str, str]:
    """
    Ham (güvenilmeyen) bir eylem sözlüğünü şemaya uygun hâle getirir.

    :param raw: Diskten okunan ham değer; sözlük olmayabilir.
    :param fallback_name: Ad alanı boşsa kullanılacak varsayılan Türkçe ad.
    :return: ``type`` / ``value`` / ``name`` alanlarını içeren temiz sözlük.
    """
    if not isinstance(raw, dict):
        return new_action("none", "", fallback_name)

    action_type = str(raw.get("type", "none") or "none").strip().lower()
    if action_type not in ACTION_TYPES:
        action_type = "none"

    value_raw = raw.get("value", "")
    value = "" if value_raw is None else str(value_raw)

    if action_type == "media":
        normalized = value.strip().lower()
        normalized = _MEDIA_ALIASES.get(normalized, normalized)
        if normalized not in MEDIA_VALUES:
            normalized = ""
        value = normalized

    name_raw = raw.get("name", "")
    name = str(name_raw).strip() if name_raw is not None else ""
    if not name:
        name = fallback_name

    return {"type": action_type, "value": value, "name": name}


def _shortcut_to_windows(value: str) -> str:
    """
    Bir kısayol dizgesindeki ``command`` / ``cmd`` parçalarını ``ctrl`` yapar.

    Spec bölüm 7.2: Windows profilinde ``command``/``cmd`` -> ``ctrl``.

    :param value: ``"command+c"`` gibi kısayol dizgesi.
    :return: Windows profiline uygun kısayol dizgesi.
    """
    parts: list[str] = []
    for token in str(value).split("+"):
        stripped = token.strip()
        if stripped.lower() in ("command", "cmd"):
            stripped = "ctrl"
        parts.append(stripped)
    return "+".join(parts)


def _action_to_windows(action: dict[str, str]) -> dict[str, str]:
    """
    macOS'tan taşınan bir eylemi Windows profiline uyarlar.

    Yalnızca ``shortcut`` ve ``macro`` tiplerinde tuş adı çevrimi yapılır;
    diğer tipler olduğu gibi kopyalanır.

    :param action: Temizlenmiş eylem sözlüğü.
    :return: Windows profili için yeni eylem sözlüğü.
    """
    converted = dict(action)
    if converted.get("type") == "shortcut":
        converted["value"] = _shortcut_to_windows(converted.get("value", ""))
    elif converted.get("type") == "macro":
        steps: list[str] = []
        for step in str(converted.get("value", "")).split("|"):
            stripped = step.strip()
            steps.append(stripped if stripped.isdigit() else _shortcut_to_windows(step))
        converted["value"] = "|".join(steps)
    return converted


def _legacy_combo_id(raw_key: str) -> str | None:
    """
    Eski combo anahtarını yeni ``C_a_b`` kimliğine çevirir.

    Desteklenen biçimler: ``"C_1_2"``, ``"1_2"``, ``"1+2"``, ``"1-2"`` ve
    0 tabanlı indeks kullanan eski varyantlar (``"0_1"`` -> ``"C_1_2"``).
    Eski 8 tuşlu şemadaki tüm indeksler 10 tuşlu şemada da geçerlidir, bu yüzden
    ek bir kaydırma gerekmez.

    :param raw_key: Eski yapılandırmadaki combo anahtarı.
    :return: ``"C_a_b"`` kimliği veya çevrilemiyorsa ``None``.
    """
    text = str(raw_key).strip()
    numbers = re.findall(r"\d+", text)
    if len(numbers) != 2:
        return None

    first = int(numbers[0])
    second = int(numbers[1])
    # 0 tabanlı eski indeksleri 1 tabanlıya kaydır.
    if min(first, second) == 0:
        first += 1
        second += 1
    if first == second:
        return None
    if not (1 <= first <= KEY_COUNT) or not (1 <= second <= KEY_COUNT):
        return None
    return combo_id(first, second)


def looks_like_v2(raw: Any) -> bool:
    """
    Ham sözlüğün eski v2 biçiminde olup olmadığını sezgisel olarak belirler.

    :param raw: Diskten okunan ham JSON verisi.
    :return: v2 (F13..F20 düz sözlük) gibi görünüyorsa ``True``.
    """
    if not isinstance(raw, dict):
        return False
    if any(key in raw for key in V2_KEY_MAP):
        return True
    if "combine" in raw and "profiles" not in raw:
        return True
    return False


def migrate_v2_data(raw: Any) -> dict[str, Any]:
    """
    Eski v2 yapılandırmasını şema 3 sözlüğüne dönüştürür.

    Taşıma kuralları:

    * ``F13``..``F20`` -> ``K1``..``K8``; ``K9`` ve ``K10`` boş kalır.
    * ``combine`` bölümü ``C_a_b`` combo slotlarına taşınır
      (0 tabanlı eski indeksler 1 tabanlıya çevrilir).
    * v2'de işletim sistemi ayrımı olmadığı için **aynı eylemler hem
      ``mac`` hem ``windows`` profiline** yazılır; Windows kopyasında
      ``command``/``cmd`` tuşları ``ctrl``'ye çevrilir.
    * Enkoder ayarları v2'de yoktur; varsayılan (ses) değerleriyle gelir.

    :param raw: Eski yapılandırma sözlüğü.
    :return: Şema 3'e uygun, eksiksiz yeni yapılandırma sözlüğü.
    """
    config = default_config()
    if not isinstance(raw, dict):
        return config

    profile = config["profiles"][DEFAULT_PROFILE_NAME]

    # --- Tuşlar: F13..F20 -> K1..K8 ---
    for old_key, new_key in V2_KEY_MAP.items():
        source = raw.get(old_key)
        if not isinstance(source, dict):
            continue
        action = _sanitize_action(source, KEY_NAMES[new_key])
        profile["mac"]["keys"][new_key] = dict(action)
        profile["windows"]["keys"][new_key] = _action_to_windows(action)

    # --- Combolar: eski "combine" bölümü ---
    combine = raw.get("combine")
    if not isinstance(combine, dict):
        combine = raw.get("combos") if isinstance(raw.get("combos"), dict) else {}
    for old_key, source in dict(combine).items():
        new_cid = _legacy_combo_id(old_key)
        if new_cid is None or not isinstance(source, dict):
            continue
        action = _sanitize_action(source, combo_name(new_cid))
        profile["mac"]["combos"][new_cid] = dict(action)
        profile["windows"]["combos"][new_cid] = _action_to_windows(action)

    # --- Taşınabilen genel ayarlar ---
    if isinstance(raw.get("autostart"), bool):
        config["autostart"] = bool(raw["autostart"])
    elif isinstance(raw.get("startup"), bool):
        config["autostart"] = bool(raw["startup"])

    legacy_ui = raw.get("ui")
    if isinstance(legacy_ui, dict):
        for ui_key in ("theme", "minimize_to_tray", "start_minimized",
                       "show_led_colors", "hide_accessibility_prompt"):
            if ui_key in legacy_ui:
                config["ui"][ui_key] = legacy_ui[ui_key]

    return config


# ---------------------------------------------------------------------------
# 8) ConfigManager
# ---------------------------------------------------------------------------


class ConfigManager:
    """
    ``config.json`` dosyasını okuyan, onaran, taşıyan ve atomik yazan sınıf.

    Kullanım::

        cfg = ConfigManager()          # varsayılan yol: <proje kökü>/config.json
        cfg.load()                     # yoksa üretir, v2 varsa taşır
        action = cfg.get_action("mac", "K1")
        cfg.set_action("mac", "K1", "url", "bluedevelopment.com", "Site")
        cfg.save()

    Sınıf hiçbir durumda okuma/yazma hatası yüzünden istisna fırlatmaz;
    başarısız işlemler :attr:`last_error` alanına yazılır.
    """

    #: Yapılandırma dosyasının tam yolu.
    path: str

    #: Bellekteki yapılandırma sözlüğü (şema 3).
    data: dict[str, Any]

    def __init__(self, path: str | None = None) -> None:
        """
        Yöneticiyi kurar ve dosyayı hemen yükler.

        :param path: Yapılandırma dosyasının yolu. ``None`` verilirse proje
            kökündeki ``config.json`` kullanılır.
        """
        self.path = str(path) if path else default_config_path()
        self.data = default_config()
        self.last_error: str | None = None
        self._changed: bool = False
        #: İçe aktarılan dosyada kabuk komutu / uygulama başlatan slot
        #: bulunursa çağrılan onay kancası (bkz. :meth:`import_from`).
        #: ``list[dict]`` alır; ``True`` dönerse içe aktarma sürer. Arayüz
        #: katmanı (``app/main.py``) buraya modal bir diyalog bağlar. Kanca
        #: yoksa içe aktarma GÜVENLİ tarafta reddedilir.
        self.import_confirm: Callable[[list[dict[str, str]]], bool] | None = None
        try:
            self.load()
        except Exception as exc:  # pragma: no cover - savunma amaçlı
            self.last_error = f"Yapılandırma yüklenemedi: {exc}"
            self.data = default_config()

    # -- iç yardımcılar ----------------------------------------------------

    def _mark_changed(self) -> None:
        """Yapılandırmanın diske yazılması gerektiğini işaretler."""
        self._changed = True

    def _backup_broken_file(self) -> None:
        """
        Okunamayan yapılandırma dosyasını ``config.json.bak`` olarak yedekler.

        Yedekleme başarısız olursa sessizce geçilir; amaç veri kaybını
        azaltmaktır, uygulamayı durdurmak değil.
        """
        try:
            if os.path.exists(self.path):
                shutil.copy2(self.path, self.path + ".bak")
        except OSError as exc:
            self.last_error = f"Bozuk yapılandırma yedeklenemedi: {exc}"

    def _read_json(self, path: str) -> Any | None:
        """
        JSON dosyasını okur; hata durumunda ``None`` döndürür.

        :param path: Okunacak dosyanın yolu.
        :return: Ayrıştırılmış veri veya hata varsa ``None``.
        """
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.last_error = f"'{path}' okunamadı: {exc}"
            return None

    def _normalize_os_profile(self, raw: Any) -> dict[str, Any]:
        """
        Tek bir işletim sistemi bölümünü eksiksiz ve geçerli hâle getirir.

        Eksik tuş/combo/enkoder slotları varsayılanla tamamlanır, fazlalık
        (şemada olmayan) slotlar atılır.

        :param raw: Ham işletim sistemi bölümü.
        :return: Onarılmış bölüm.
        """
        section = raw if isinstance(raw, dict) else {}
        result: dict[str, Any] = {}

        raw_keys = section.get("keys") if isinstance(section.get("keys"), dict) else {}
        result["keys"] = {}
        for kid in KEY_IDS:
            if kid in raw_keys:
                result["keys"][kid] = _sanitize_action(raw_keys[kid], KEY_NAMES[kid])
            else:
                result["keys"][kid] = new_action("none", "", KEY_NAMES[kid])
                self._mark_changed()
        if len(raw_keys) != len(KEY_IDS):
            self._mark_changed()

        raw_combos = section.get("combos") if isinstance(section.get("combos"), dict) else {}
        result["combos"] = {}
        for cid in COMBO_IDS:
            if cid in raw_combos:
                result["combos"][cid] = _sanitize_action(raw_combos[cid], combo_name(cid))
            else:
                result["combos"][cid] = new_action("none", "", combo_name(cid))
                self._mark_changed()
        if len(raw_combos) != len(COMBO_IDS):
            self._mark_changed()

        raw_encoder = section.get("encoder") if isinstance(section.get("encoder"), dict) else {}
        encoder: dict[str, Any] = {}
        mode = str(raw_encoder.get("mode", "hid")).strip().lower()
        if mode not in ("hid", "host"):
            mode = "hid"
            self._mark_changed()
        encoder["mode"] = mode
        defaults = default_encoder_actions()
        for eid in ENCODER_IDS:
            if eid in raw_encoder:
                encoder[eid] = _sanitize_action(raw_encoder[eid], ENCODER_NAMES[eid])
            else:
                encoder[eid] = defaults[eid]
                self._mark_changed()
        result["encoder"] = encoder

        return result

    def _normalize_profile(self, raw: Any) -> dict[str, Any]:
        """
        Bir profilin ``windows`` ve ``mac`` bölümlerini onarır.

        :param raw: Ham profil sözlüğü.
        :return: Onarılmış profil.
        """
        section = raw if isinstance(raw, dict) else {}
        return {os_key: self._normalize_os_profile(section.get(os_key)) for os_key in OS_KEYS}

    def _normalize(self, raw: Any) -> dict[str, Any]:
        """
        Ham yapılandırmayı şema 3'e uygun, eksiksiz bir sözlüğe dönüştürür.

        Eksik veya bozuk her alan varsayılanıyla tamamlanır ve bu durumda
        yapılandırma "değişti" olarak işaretlenerek diske yazılması sağlanır.

        :param raw: Ham yapılandırma verisi.
        :return: Kullanıma hazır yapılandırma sözlüğü.
        """
        if not isinstance(raw, dict):
            self._mark_changed()
            return default_config()

        config: dict[str, Any] = {}
        config["schema"] = SCHEMA_VERSION
        if raw.get("schema") != SCHEMA_VERSION:
            self._mark_changed()

        config["app_version"] = APP_VERSION
        if raw.get("app_version") != APP_VERSION:
            self._mark_changed()

        # --- device ---
        device = dict(DEFAULT_DEVICE)
        raw_device = raw.get("device")
        if isinstance(raw_device, dict):
            for field, default_value in DEFAULT_DEVICE.items():
                if field in raw_device and raw_device[field] not in (None, ""):
                    device[field] = raw_device[field]
        else:
            self._mark_changed()
        try:
            device["baud"] = int(device.get("baud", DEVICE_BAUD))
        except (TypeError, ValueError):
            device["baud"] = DEVICE_BAUD
            self._mark_changed()
        device["port"] = str(device.get("port") or "auto")
        config["device"] = device

        # --- profiles ---
        raw_profiles = raw.get("profiles")
        profiles: dict[str, Any] = {}
        if isinstance(raw_profiles, dict) and raw_profiles:
            for name, profile_raw in raw_profiles.items():
                clean_name = str(name).strip()
                if not clean_name:
                    self._mark_changed()
                    continue
                profiles[clean_name] = self._normalize_profile(profile_raw)
        if not profiles:
            profiles = {DEFAULT_PROFILE_NAME: default_profile()}
            self._mark_changed()
        config["profiles"] = profiles

        # --- active_profile ---
        active = str(raw.get("active_profile", "") or "").strip()
        if active not in profiles:
            active = next(iter(profiles))
            self._mark_changed()
        config["active_profile"] = active

        # --- leds ---
        leds = dict(DEFAULT_LEDS)
        raw_leds = raw.get("leds")
        if isinstance(raw_leds, dict):
            for field in DEFAULT_LEDS:
                if field in raw_leds and raw_leds[field] not in (None, ""):
                    leds[field] = raw_leds[field]
        else:
            self._mark_changed()
        try:
            brightness = int(leds.get("brightness", DEFAULT_BRIGHTNESS))
        except (TypeError, ValueError):
            brightness = DEFAULT_BRIGHTNESS
            self._mark_changed()
        leds["brightness"] = max(0, min(255, brightness))
        for color_field in ("os_win", "os_mac", "combo", "link_ok", "link_err"):
            color = str(leds.get(color_field, DEFAULT_LEDS[color_field])).strip()
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
                color = str(DEFAULT_LEDS[color_field])
                self._mark_changed()
            leds[color_field] = color.upper() if color.startswith("#") else color
        config["leds"] = leds

        # --- ui ---
        ui = dict(DEFAULT_UI)
        raw_ui = raw.get("ui")
        if isinstance(raw_ui, dict):
            theme = str(raw_ui.get("theme", DEFAULT_UI["theme"])).strip() or DEFAULT_UI["theme"]
            ui["theme"] = theme
            ui["minimize_to_tray"] = bool(raw_ui.get("minimize_to_tray", DEFAULT_UI["minimize_to_tray"]))
            ui["start_minimized"] = bool(raw_ui.get("start_minimized", DEFAULT_UI["start_minimized"]))
            ui["show_led_colors"] = bool(raw_ui.get("show_led_colors", DEFAULT_UI["show_led_colors"]))
            ui["hide_accessibility_prompt"] = bool(raw_ui.get(
                "hide_accessibility_prompt", DEFAULT_UI["hide_accessibility_prompt"]))
        else:
            self._mark_changed()
        config["ui"] = ui
        # GUVENLIK: ice aktarilan dosyanin mobile bolumu (enabled/token/port)
        # KABUL EDILMEZ. Ag ayari tasinabilir profil verisi degildir; yabanci
        # bir jeton veya enabled=true sizarsa sunucu sessizce acilirdi.
        config["mobile"] = dict(DEFAULT_MOBILE)

        # --- mobile (telefondan ayar sunucusu) ---
        mobile = dict(DEFAULT_MOBILE)
        raw_mobile = raw.get("mobile")
        if isinstance(raw_mobile, dict):
            mobile["enabled"] = bool(raw_mobile.get("enabled", DEFAULT_MOBILE["enabled"]))
            mobile["token"] = _normalize_mobile_token(raw_mobile.get("token", ""))
            port = _normalize_mobile_port(raw_mobile.get("port", DEFAULT_MOBILE_PORT))
            if port != raw_mobile.get("port", DEFAULT_MOBILE_PORT):
                self._mark_changed()
            mobile["port"] = port
        else:
            self._mark_changed()
        config["mobile"] = mobile

        # --- autostart ---
        config["autostart"] = bool(raw.get("autostart", False))

        return config

    # -- genel API ---------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """
        Yapılandırmayı diskten yükler.

        Sırasıyla:

        1. ``config.json`` yoksa; **yalnızca varsayılan yol kullanılıyorsa**
           eski ``macro_config.json`` taşınır, yoksa varsayılan üretilir ve
           dosya diske yazılır.
        2. ``config.json`` bozuksa ``config.json.bak`` yedeği alınır ve
           varsayılana (veya varsa v2 taşımasına) düşülür.
        3. ``schema`` alanı 3'ten küçükse veya dosya v2 biçimindeyse taşınır.
        4. ``schema`` alanı 3'ten **büyükse** dosya daha yeni bir sürümle
           yazılmış demektir: içerik okunur ama üzerine **yazılmaz**,
           ``.newer.bak`` yedeği alınır ve :attr:`last_error` doldurulur.
        5. Sonuç her hâlükârda onarılır (eksik slotlar tamamlanır).

        :return: Yüklenmiş yapılandırma sözlüğü (``self.data`` ile aynı nesne).
        """
        self._changed = False
        raw: Any | None = None
        newer_schema = False

        if os.path.exists(self.path):
            raw = self._read_json(self.path)
            if raw is None:
                self._backup_broken_file()
                self._mark_changed()

        if raw is None:
            # Eski v2 dosyası YALNIZCA varsayılan yol kullanılıyorsa aranır.
            # Aksi hâlde (test, taşınabilir kurulum, geçici dizin) proje
            # kökündeki macro_config.json her yeni yapılandırmaya sızardı.
            legacy_raw = None
            if self._uses_default_path():
                legacy = legacy_config_path()
                legacy_raw = self._read_json(legacy) if os.path.exists(legacy) else None
            if isinstance(legacy_raw, dict) and legacy_raw:
                raw = migrate_v2_data(legacy_raw)
            else:
                raw = default_config()
            self._mark_changed()
        else:
            if looks_like_v2(raw):
                raw = migrate_v2_data(raw)
                self._mark_changed()
            else:
                schema_raw = raw.get("schema") if isinstance(raw, dict) else None
                try:
                    schema = int(schema_raw)
                except (TypeError, ValueError):
                    schema = 0
                if schema > SCHEMA_VERSION:
                    # Daha yeni bir sürümün yazdığı dosya. Şemayı geriye
                    # düşürüp ÜZERİNE YAZMAK veri kaybıdır; yalnızca okuruz.
                    newer_schema = True
                    self._backup_newer_file(schema)
                elif schema < SCHEMA_VERSION:
                    # Şema eski ama v2 imzası da yok: alanlar _normalize()
                    # tarafından tamamlanır, ayrıca bir taşıma gerekmez.
                    self._mark_changed()

        self.data = self._normalize(raw)

        if self._changed and not newer_schema:
            self.save()
        self._changed = False
        return self.data

    def _uses_default_path(self) -> bool:
        """Yönetici, proje kökündeki varsayılan ``config.json`` yolunu mu kullanıyor?"""
        try:
            return os.path.abspath(self.path) == os.path.abspath(default_config_path())
        except Exception:  # pragma: no cover - savunma amaçlı
            return False

    def _backup_newer_file(self, schema: int) -> None:
        """
        Daha yeni şemalı yapılandırmayı ``.newer.bak`` olarak yedekler ve uyarır.

        :param schema: Dosyada okunan şema numarası.
        """
        try:
            if os.path.exists(self.path):
                shutil.copy2(self.path, self.path + ".newer.bak")
        except Exception:  # noqa: BLE001 - yedekleme başarısızlığı ölümcül değil
            pass
        self.last_error = (
            f"Yapılandırma dosyası daha yeni bir sürümle yazılmış "
            f"(şema {schema} > {SCHEMA_VERSION}). Dosyanın üzerine yazılmadı; "
            f"yedeği '{os.path.basename(self.path)}.newer.bak' olarak alındı. "
            f"Uygulamayı güncellemen önerilir."
        )

    def save(self) -> None:
        """
        Yapılandırmayı **atomik** olarak diske yazar.

        Önce ``<yol>.tmp`` dosyasına yazılır, dosya diske aktarılır
        (``flush`` + ``fsync``), ardından ``os.replace`` ile hedefin üzerine
        taşınır. Böylece yazma sırasında kesinti olsa bile mevcut
        yapılandırma bozulmaz.

        Hata durumunda istisna fırlatılmaz; hata :attr:`last_error` alanına
        yazılır.
        """
        tmp_path = self.path + ".tmp"
        try:
            parent = os.path.dirname(os.path.abspath(self.path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            # GÜVENLİK: config.json mobil erişim jetonunu düz metin taşır.
            # Varsayılan 0644 (herkesin okuyabildiği) izinlerle yazılırsa, aynı
            # makinede oturum açan başka bir kullanıcı jetonu okuyup telefon
            # sunucusuna bağlanabilir. Dosya YALNIZCA sahibine okunur/yazılır
            # (0600) yapılır. Değiştirme öncesi geçici dosyada ayarlanır ki
            # nihai dosya en baştan doğru izinle görünsün.
            try:
                os.chmod(tmp_path, 0o600)
            except OSError:
                pass
            os.replace(tmp_path, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
            self.last_error = None
        except (OSError, TypeError, ValueError) as exc:
            self.last_error = f"Yapılandırma kaydedilemedi: {exc}"
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    def profile(self, os_key: str) -> dict[str, Any]:
        """
        Etkin profilin ilgili işletim sistemi bölümünü döndürür.

        :param os_key: ``"windows"`` veya ``"mac"``. Geçersiz değer verilirse
            ``"windows"`` varsayılır.
        :return: ``{"keys": ..., "combos": ..., "encoder": ...}`` sözlüğü
            (canlı referans — değişiklikler doğrudan yapılandırmaya işler).
        """
        key = str(os_key).strip().lower()
        if key not in OS_KEYS:
            key = "windows"

        profiles = self.data.setdefault("profiles", {})
        if not isinstance(profiles, dict) or not profiles:
            profiles = {DEFAULT_PROFILE_NAME: default_profile()}
            self.data["profiles"] = profiles

        active = str(self.data.get("active_profile", "") or "")
        if active not in profiles:
            active = next(iter(profiles))
            self.data["active_profile"] = active

        profile_data = profiles[active]
        if not isinstance(profile_data, dict):
            profile_data = default_profile()
            profiles[active] = profile_data

        section = profile_data.get(key)
        if not isinstance(section, dict):
            section = default_os_profile()
            profile_data[key] = section
        return section

    def get_action(self, os_key: str, slot: str) -> dict[str, Any]:
        """
        Bir slotun eylem tanımını döndürür.

        Dönen sözlük **canlı referanstır**; içeriğini değiştirdikten sonra
        :meth:`save` çağırmak yeterlidir. Yine de tercih edilen yol
        :meth:`set_action` kullanmaktır.

        :param os_key: ``"windows"`` veya ``"mac"``.
        :param slot: ``"K1"``..``"K10"``, ``"C_a_b"`` veya enkoder slotu.
        :return: ``type`` / ``value`` / ``name`` alanlarını içeren sözlük.
            Bilinmeyen slotlarda kaydedilmemiş boş bir eylem döner.
        """
        section = self.profile(os_key)
        slot_id = str(slot).strip()

        if slot_id in KEY_IDS:
            keys = section.setdefault("keys", {})
            if slot_id not in keys or not isinstance(keys[slot_id], dict):
                keys[slot_id] = new_action("none", "", KEY_NAMES[slot_id])
            return keys[slot_id]

        if slot_id in ENCODER_IDS:
            encoder = section.setdefault("encoder", default_encoder_actions())
            if slot_id not in encoder or not isinstance(encoder[slot_id], dict):
                encoder[slot_id] = default_encoder_actions()[slot_id]
            return encoder[slot_id]

        try:
            normalized_cid = combo_id(*parse_combo_id(slot_id))
        except ValueError:
            return new_action("none", "", slot_display_name(slot_id))

        combos = section.setdefault("combos", {})
        if normalized_cid not in combos or not isinstance(combos[normalized_cid], dict):
            combos[normalized_cid] = new_action("none", "", combo_name(normalized_cid))
        return combos[normalized_cid]

    def set_action(
        self,
        os_key: str,
        slot: str,
        type_: str,
        value: str,
        name: str | None = None,
    ) -> None:
        """
        Bir slotun eylemini günceller.

        Değişiklik yalnızca bellekte yapılır; kalıcı olması için :meth:`save`
        çağrılmalıdır.

        :param os_key: ``"windows"`` veya ``"mac"``.
        :param slot: Güncellenecek slot kimliği.
        :param type_: Eylem tipi; ``ACTION_TYPES`` dışındaysa ``"none"`` olur.
        :param value: Eylem değeri.
        :param name: Slotun görünen adı. ``None`` verilirse mevcut ad korunur.
        """
        action = self.get_action(os_key, slot)
        action_type = str(type_).strip().lower()
        if action_type not in ACTION_TYPES:
            action_type = "none"

        action["type"] = action_type
        action["value"] = "" if value is None else str(value)

        if name is not None:
            new_name = str(name).strip()
            action["name"] = new_name if new_name else slot_display_name(slot)
        elif not str(action.get("name", "")).strip():
            action["name"] = slot_display_name(slot)

    def led_settings(self) -> dict[str, Any]:
        """
        LED ayarları bölümünü döndürür (canlı referans).

        :return: ``brightness`` ve renk alanlarını içeren sözlük.
        """
        leds = self.data.get("leds")
        if not isinstance(leds, dict):
            leds = dict(DEFAULT_LEDS)
            self.data["leds"] = leds
        return leds

    def list_profiles(self) -> list[str]:
        """
        Tanımlı profil adlarını ekleme sırasına göre döndürür.

        :return: Profil adları listesi (en az bir öğe içerir).
        """
        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or not profiles:
            self.data["profiles"] = {DEFAULT_PROFILE_NAME: default_profile()}
            return [DEFAULT_PROFILE_NAME]
        return list(profiles.keys())

    def add_profile(self, name: str) -> None:
        """
        Yeni bir profil ekler (tüm slotlar boş, enkoder varsayılan).

        Aynı adda profil zaten varsa veya ad boşsa hiçbir şey yapılmaz.

        :param name: Yeni profilin adı.
        """
        clean = str(name).strip()
        if not clean:
            self.last_error = "Profil adı boş olamaz."
            return
        profiles = self.data.setdefault("profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
            self.data["profiles"] = profiles
        if clean in profiles:
            self.last_error = f"'{clean}' adında bir profil zaten var."
            return
        profiles[clean] = default_profile()
        self.last_error = None

    def delete_profile(self, name: str) -> None:
        """
        Bir profili siler.

        Son kalan profil silinemez. Etkin profil silinirse etkin profil
        listedeki ilk profile taşınır.

        :param name: Silinecek profilin adı.
        """
        clean = str(name).strip()
        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or clean not in profiles:
            self.last_error = f"'{clean}' adında bir profil yok."
            return
        if len(profiles) <= 1:
            self.last_error = "Son profil silinemez."
            return

        del profiles[clean]
        if str(self.data.get("active_profile", "")) == clean:
            self.data["active_profile"] = next(iter(profiles))
        self.last_error = None

    def set_active_profile(self, name: str) -> None:
        """
        Etkin profili değiştirir.

        :param name: Etkinleştirilecek profilin adı. Profil yoksa değişiklik
            yapılmaz ve :attr:`last_error` doldurulur.
        """
        clean = str(name).strip()
        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or clean not in profiles:
            self.last_error = f"'{clean}' adında bir profil yok."
            return
        self.data["active_profile"] = clean
        self.last_error = None

    def export_to(self, path: str) -> None:
        """
        Yapılandırmayı başka bir dosyaya dışa aktarır.

        :param path: Hedef dosyanın yolu.
        """
        try:
            parent = os.path.dirname(os.path.abspath(path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            # GÜVENLİK: jeton ve "mobil açık" bayrağı dışa aktarılan dosyaya
            # YAZILMAZ; aksi hâlde paylaşılan/yedeklenen dosya erişim sırrını
            # sızdırırdı. Derin kopya alınıp mobile alanı temizlenir.
            import copy as _copy
            _veri = _copy.deepcopy(self.data)
            _m = _veri.get("mobile")
            if isinstance(_m, dict):
                _m["token"] = ""
                _m["enabled"] = False
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(_veri, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            self.last_error = None
        except (OSError, TypeError, ValueError) as exc:
            self.last_error = f"Dışa aktarma başarısız: {exc}"

    def import_from(self, path: str) -> None:
        """
        Başka bir dosyadan yapılandırma içe aktarır.

        Dosya v2 biçimindeyse otomatik olarak taşınır, her hâlükârda şemaya
        göre onarılır ve başarılı olursa mevcut yapılandırma dosyasına
        kaydedilir. Hatalı dosyada mevcut yapılandırma **korunur**.

        :param path: Kaynak dosyanın yolu.
        """
        raw = self._read_json(path)
        if raw is None:
            self.last_error = f"'{path}' okunamadı veya geçerli JSON değil."
            return
        if not isinstance(raw, dict) or not raw:
            self.last_error = f"'{path}' geçerli bir yapılandırma içermiyor."
            return

        if looks_like_v2(raw):
            raw = migrate_v2_data(raw)

        onceki_changed = self._changed
        self._changed = False
        aday = self._normalize(raw)

        # GÜVENLİK: içe aktarılan dosya, ilk tuş basışında kullanıcının login
        # kabuğunda çalışacak 'command' (veya rastgele program başlatan 'app')
        # slotları taşıyabilir. "Hazır profil" diye paylaşılan bir JSON bu
        # yolla kod çalıştırabildiği için sessizce kabul edilmez; kullanıcıya
        # açıkça sorulur. Onay yoksa MEVCUT yapılandırma olduğu gibi kalır.
        riskli = find_risky_actions(aday)
        if riskli and not self._import_onayi_al(path, riskli):
            self._changed = onceki_changed
            return

        self.data = aday
        self.save()
        self._changed = False

    def _import_onayi_al(self, path: str, riskli: list[dict[str, str]]) -> bool:
        """
        Riskli slotlar için kullanıcı onayını ister.

        :param path: İçe aktarılan dosyanın yolu (hata metninde geçer).
        :param riskli: :func:`find_risky_actions` çıktısı.
        :return: İçe aktarma sürdürülebilirse ``True``.
        """
        onay = self.import_confirm
        if not callable(onay):
            # Onay soracak bir katman bağlı değil: fail-closed davranırız.
            self.last_error = (
                f"'{os.path.basename(path)}' dosyasında komut/uygulama "
                f"çalıştıran {len(riskli)} slot var. Onay alınamadığı için "
                f"içe aktarma yapılmadı; mevcut ayarlar korundu.")
            return False
        try:
            kabul = bool(onay(riskli))
        except Exception:  # noqa: BLE001 - arayüz hatası içe aktarmayı açmaz
            kabul = False
        if not kabul:
            self.last_error = ("İçe aktarma iptal edildi — komut çalıştıran "
                               "slotlar onaylanmadı, mevcut ayarlar korundu.")
        return kabul

    # -- ek yardımcılar (arayüz ve cihaz katmanı için) ----------------------

    def device_settings(self) -> dict[str, Any]:
        """
        Cihaz bölümünü döndürür (canlı referans).

        :return: ``port`` / ``vid`` / ``pid`` / ``product`` / ``baud`` sözlüğü.
        """
        device = self.data.get("device")
        if not isinstance(device, dict):
            device = dict(DEFAULT_DEVICE)
            self.data["device"] = device
        return device

    def ui_settings(self) -> dict[str, Any]:
        """
        Arayüz bölümünü döndürür (canlı referans).

        :return: ``theme`` / ``minimize_to_tray`` / ``start_minimized`` sözlüğü.
        """
        ui = self.data.get("ui")
        if not isinstance(ui, dict):
            ui = dict(DEFAULT_UI)
            self.data["ui"] = ui
        return ui

    def get_mobile_settings(self) -> dict[str, Any]:
        """
        Mobil ayar sunucusu ayarlarını döndürür.

        Port 1024-65535 aralığı dışındaysa varsayılana (8756) çekilir.

        :return: ``{"enabled": bool, "port": int}`` sözlüğü (kopya;
            değişiklik için :meth:`set_mobile_settings` kullanılmalıdır).
        """
        mobile = self.data.get("mobile")
        if not isinstance(mobile, dict):
            mobile = dict(DEFAULT_MOBILE)
            self.data["mobile"] = mobile
        return {
            "enabled": bool(mobile.get("enabled", DEFAULT_MOBILE["enabled"])),
            "port": _normalize_mobile_port(mobile.get("port", DEFAULT_MOBILE_PORT)),
            "token": _normalize_mobile_token(mobile.get("token", "")),
        }

    def set_mobile_settings(self, enabled: bool | None = None, port: int | None = None,
                            token: str | None = None) -> None:
        """
        Mobil ayar sunucusu ayarlarını günceller.

        Değişiklik bellekte yapılır ve "değişti" olarak işaretlenir; kalıcı
        olması için :meth:`save` çağrılmalıdır.

        :param enabled: Sunucu açık mı? ``None`` verilirse mevcut değer korunur.
        :param port: TCP portu; 1024-65535 aralığı dışındaysa varsayılana
            (8756) çekilir. ``None`` verilirse mevcut değer korunur.
        :param token: Sunucunun erişim jetonu (adresteki ``/t/<jeton>/``
            ön eki). ``None`` verilirse mevcut değer korunur.
        """
        mobile = self.data.get("mobile")
        if not isinstance(mobile, dict):
            mobile = dict(DEFAULT_MOBILE)
            self.data["mobile"] = mobile
        if enabled is not None:
            mobile["enabled"] = bool(enabled)
            self._mark_changed()
        if port is not None:
            mobile["port"] = _normalize_mobile_port(port)
            self._mark_changed()
        if token is not None:
            mobile["token"] = _normalize_mobile_token(token)
            self._mark_changed()

    def active_profile_name(self) -> str:
        """
        Etkin profilin adını döndürür.

        :return: Etkin profil adı.
        """
        profiles = self.list_profiles()
        active = str(self.data.get("active_profile", "") or "")
        if active not in profiles:
            active = profiles[0]
            self.data["active_profile"] = active
        return active

    def rename_profile(self, old_name: str, new_name: str) -> None:
        """
        Bir profilin adını değiştirir (sırayı koruyarak).

        :param old_name: Mevcut profil adı.
        :param new_name: Yeni profil adı.
        """
        old_clean = str(old_name).strip()
        new_clean = str(new_name).strip()
        profiles = self.data.get("profiles")
        if not isinstance(profiles, dict) or old_clean not in profiles:
            self.last_error = f"'{old_clean}' adında bir profil yok."
            return
        if not new_clean:
            self.last_error = "Profil adı boş olamaz."
            return
        if new_clean in profiles and new_clean != old_clean:
            self.last_error = f"'{new_clean}' adında bir profil zaten var."
            return

        renamed = {(new_clean if key == old_clean else key): value for key, value in profiles.items()}
        self.data["profiles"] = renamed
        if str(self.data.get("active_profile", "")) == old_clean:
            self.data["active_profile"] = new_clean
        self.last_error = None

    def encoder_mode(self, os_key: str) -> str:
        """
        Enkoder modunu döndürür.

        :param os_key: ``"windows"`` veya ``"mac"``.
        :return: ``"hid"`` (cihaz kendi ses HID'ini gönderir) veya ``"host"``.
        """
        encoder = self.profile(os_key).get("encoder")
        if not isinstance(encoder, dict):
            return "hid"
        mode = str(encoder.get("mode", "hid")).strip().lower()
        return mode if mode in ("hid", "host") else "hid"

    def set_encoder_mode(self, os_key: str, mode: str) -> None:
        """
        Enkoder modunu ayarlar.

        :param os_key: ``"windows"`` veya ``"mac"``.
        :param mode: ``"hid"`` veya ``"host"``; geçersizse ``"hid"`` yazılır.
        """
        clean = str(mode).strip().lower()
        if clean not in ("hid", "host"):
            clean = "hid"
        section = self.profile(os_key)
        encoder = section.get("encoder")
        if not isinstance(encoder, dict):
            encoder = default_encoder_actions()
            section["encoder"] = encoder
        encoder["mode"] = clean

    def autostart_enabled(self) -> bool:
        """
        Yapılandırmadaki otomatik başlatma bayrağını döndürür.

        :return: Otomatik başlatma isteniyorsa ``True``.
        """
        return bool(self.data.get("autostart", False))

    def set_autostart_flag(self, enabled: bool) -> None:
        """
        Otomatik başlatma bayrağını yazar (işletim sistemi kaydını değiştirmez).

        Gerçek kayıt işlemi için ``app.core.platform_utils.set_autostart``
        kullanılmalıdır.

        :param enabled: Yeni bayrak değeri.
        """
        self.data["autostart"] = bool(enabled)

    def reset_to_defaults(self) -> dict[str, Any]:
        """
        Tüm yapılandırmayı varsayılana döndürür ve diske yazar.

        :return: Yeni varsayılan yapılandırma sözlüğü.
        """
        self.data = default_config()
        self.save()
        return self.data
