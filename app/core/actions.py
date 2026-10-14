"""
ExtraKeyboard MK1 — eylem çalıştırma katmanı.

Spec bölüm 7.2'deki **tüm** eylem tiplerini uygular:

===========  ============================================================
``type``     Davranış
===========  ============================================================
``none``     Hiçbir şey yapmaz.
``app``      Uygulamayı başlatır (macOS ``open``, Windows ``os.startfile``).
``url``      Varsayılan tarayıcıda açar; şema yoksa ``https://`` ekler.
``shortcut`` ``pyautogui.hotkey`` ile tuş kombinasyonu gönderir.
``text``     Metni yazar; Türkçe karakterlerde pano üzerinden yapıştırır.
``command``  Kabuk komutu çalıştırır.
``file``     Dosyayı varsayılan uygulamada açar.
``folder``   Klasörü Finder / Dosya Gezgini'nde açar.
``media``    Medya/ses tuşu gönderir (macOS'ta AppleScript yedeğiyle).
``macro``    ``|`` ile ayrılmış adımlar; sayı olan adımlar ms bekleme.
===========  ============================================================

**Kısayol normalizasyonu (spec bölüm 7.2):** Windows profilinde
``command``/``cmd`` -> ``ctrl``; macOS profilinde ``ctrl`` olduğu gibi kalır.

Her eylem ``try``/``except`` ile sarılıdır ve daima ``(başarı, mesaj)``
ikilisi döndürür — hiçbir koşulda uygulamayı çökertmez.
"""

from __future__ import annotations

import re
import subprocess
import sys
import threading
import time
from typing import Any, Callable

from app.core import platform_utils
from app.core.config import (
    ACTION_TYPES,
    MEDIA_VALUES,
    ConfigManager,
    slot_display_name,
)

try:  # pyautogui isteğe bağlıdır; yoksa yalnızca tuş eylemleri devre dışı kalır.
    import pyautogui  # type: ignore[import-not-found]

    pyautogui.FAILSAFE = False
    PYAUTOGUI_AVAILABLE = True
except Exception:  # pragma: no cover - başsız ortam veya eksik paket
    pyautogui = None  # type: ignore[assignment]
    PYAUTOGUI_AVAILABLE = False

try:  # pano yedeği için
    import pyperclip  # type: ignore[import-not-found]

    PYPERCLIP_AVAILABLE = True
except Exception:  # pragma: no cover - eksik paket
    pyperclip = None  # type: ignore[assignment]
    PYPERCLIP_AVAILABLE = False

__all__ = [
    "PYAUTOGUI_AVAILABLE",
    "PYPERCLIP_AVAILABLE",
    "MAX_MACRO_DELAY_MS",
    "ActionRunner",
    "normalize_shortcut",
]

#: Makro içindeki tek bir bekleme adımının üst sınırı (ms).
MAX_MACRO_DELAY_MS: int = 10_000

#: macOS'ta enkoder/medya ile ses değiştirme adımı (0-100 ölçeğinde).
MAC_VOLUME_STEP: int = 6

#: Sayısal makro adımını tanıyan desen (``"500"``, ``"250.5"``).
_NUMBER_RE: re.Pattern[str] = re.compile(r"^\d+(?:\.\d+)?$")

#: Serbest yazılmış tuş adlarını pyautogui'nin beklediği adlara eşler.
_KEY_ALIASES: dict[str, str] = {
    # Değiştirici tuşlar
    "control": "ctrl",
    "ctl": "ctrl",
    "ctrl": "ctrl",
    "shift": "shift",
    "alt": "alt",
    "option": "alt",
    "opt": "alt",
    "altgr": "altright",
    "altright": "altright",
    "altleft": "altleft",
    "fn": "fn",
    # Yön ve gezinme
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "yukari": "up",
    "asagi": "down",
    "sol": "left",
    "sag": "right",
    "home": "home",
    "end": "end",
    "pgup": "pageup",
    "pageup": "pageup",
    "pgdn": "pagedown",
    "pgdown": "pagedown",
    "pagedown": "pagedown",
    # Düzenleme
    "esc": "esc",
    "escape": "esc",
    "enter": "enter",
    "return": "enter",
    "ret": "enter",
    "giris": "enter",
    "tab": "tab",
    "sekme": "tab",
    "space": "space",
    "spacebar": "space",
    "bosluk": "space",
    "backspace": "backspace",
    "bksp": "backspace",
    "geri": "backspace",
    "del": "delete",
    "delete": "delete",
    "sil": "delete",
    "ins": "insert",
    "insert": "insert",
    # Kilitler ve özel tuşlar
    "capslock": "capslock",
    "caps": "capslock",
    "numlock": "numlock",
    "scrolllock": "scrolllock",
    "printscreen": "printscreen",
    "prtsc": "printscreen",
    "prtscr": "printscreen",
    "menu": "apps",
    "apps": "apps",
    "pause": "pause",
    # Medya (kısayol içinde de kullanılabilir)
    "volumeup": "volumeup",
    "volumedown": "volumedown",
    "volumemute": "volumemute",
    "playpause": "playpause",
    "nexttrack": "nexttrack",
    "prevtrack": "prevtrack",
}

#: Windows tarafında ``win`` ailesi tuşlarının karşılığı.
_WINDOWS_META_KEYS: dict[str, str] = {
    "win": "win",
    "windows": "win",
    "super": "win",
    "meta": "win",
    "cmd": "ctrl",
    "command": "ctrl",
    "winleft": "winleft",
    "winright": "winright",
}

#: macOS tarafında ``command`` ailesi tuşlarının karşılığı.
_MAC_META_KEYS: dict[str, str] = {
    "cmd": "command",
    "command": "command",
    "win": "command",
    "windows": "command",
    "super": "command",
    "meta": "command",
    "winleft": "command",
    "winright": "command",
}

#: Windows'ta medya değerlerinin pyautogui tuş adları.
_MEDIA_KEYS: dict[str, str] = {
    "volume_up": "volumeup",
    "volume_down": "volumedown",
    "mute": "volumemute",
    "play_pause": "playpause",
    "next": "nexttrack",
    "prev": "prevtrack",
}

#: macOS'ta AppleScript ile yönetilecek taşıma (transport) komutları.
_MAC_TRANSPORT: dict[str, str] = {
    "play_pause": "playpause",
    "next": "next track",
    "prev": "previous track",
}


def _split_shortcut(value: str) -> list[str]:
    """
    Kısayol dizgesini tuş parçalarına ayırır.

    ``"ctrl++"`` gibi son parçası artı işareti olan yazımlar da doğru
    ayrıştırılır.

    :param value: ``"ctrl+shift+esc"`` biçiminde kısayol.
    :return: Küçük harfe çevrilmiş tuş parçaları listesi.
    """
    tokens = str(value).strip().lower().split("+")
    parts: list[str] = []
    for index, token in enumerate(tokens):
        stripped = token.strip()
        if stripped:
            parts.append(stripped)
        elif index > 0 and index == len(tokens) - 1 and parts:
            # "ctrl++" -> son boş parça artı tuşunun kendisidir.
            parts.append("+")
    return parts


def normalize_shortcut(value: str, os_key: str) -> tuple[list[str], str]:
    """
    Kısayol dizgesini pyautogui'nin beklediği tuş adlarına çevirir.

    Windows profilinde ``command``/``cmd`` tuşları ``ctrl``'ye dönüştürülür;
    macOS profilinde ``win``/``super``/``meta`` yazımları ``command`` kabul
    edilir ve ``ctrl`` olduğu gibi bırakılır (macOS'ta Control ayrı tuştur).

    :param value: Ham kısayol dizgesi.
    :param os_key: ``"windows"`` veya ``"mac"``.
    :return: ``(tuş listesi, hata mesajı)``. Hata yoksa mesaj boş dizgedir;
        hata varsa liste boş döner.
    """
    parts = _split_shortcut(value)
    if not parts:
        return [], "Kısayol boş."

    is_mac = str(os_key).strip().lower() == "mac"
    meta_map = _MAC_META_KEYS if is_mac else _WINDOWS_META_KEYS

    keys: list[str] = []
    for token in parts:
        if token in meta_map:
            keys.append(meta_map[token])
            continue
        if token in _KEY_ALIASES:
            keys.append(_KEY_ALIASES[token])
            continue
        if re.fullmatch(r"f([1-9]|1\d|2[0-4])", token):
            keys.append(token)
            continue
        keys.append(token)

    if PYAUTOGUI_AVAILABLE and pyautogui is not None:
        valid = set(getattr(pyautogui, "KEYBOARD_KEYS", []) or [])
        if valid:
            unknown = [key for key in keys if key not in valid]
            if unknown:
                return [], "Tanınmayan tuş adı: " + ", ".join(unknown)

    return keys, ""


class ActionRunner:
    """
    Bir slota atanmış eylemi çalıştıran sınıf.

    Etkin profil anahtarı (``"windows"`` / ``"mac"``) çalışma zamanında
    tutulur; cihazdan ``EV OS`` olayı geldiğinde arayüz katmanı
    :meth:`set_os_key` ile bunu günceller.

    :param cfg: Eylemlerin okunacağı yapılandırma yöneticisi.
    """

    def __init__(self, cfg: ConfigManager) -> None:
        """Çalıştırıcıyı kurar; işletim sistemi anahtarı platformdan belirlenir."""
        self._cfg: ConfigManager = cfg
        self._os_key: str = platform_utils.current_os_key()
        self._lock: threading.Lock = threading.Lock()
        self.last_result: tuple[bool, str] = (True, "Henüz eylem çalıştırılmadı.")

        #: Tip -> işleyici eşlemesi (spec bölüm 7.2'deki tüm tipler).
        self._handlers: dict[str, Callable[[str], tuple[bool, str]]] = {
            "none": self._run_none,
            "app": self._run_app,
            "url": self._run_url,
            "shortcut": self._run_shortcut,
            "text": self._run_text,
            "command": self._run_command,
            "file": self._run_file,
            "folder": self._run_folder,
            "media": self._run_media,
            "macro": self._run_macro,
        }

    # -- işletim sistemi anahtarı -----------------------------------------

    def current_os_key(self) -> str:
        """
        Eylemlerin okunduğu etkin profil anahtarını döndürür.

        :return: ``"windows"`` veya ``"mac"``.
        """
        return self._os_key

    def set_os_key(self, os_key: str) -> None:
        """
        Etkin profil anahtarını değiştirir.

        Geçersiz bir değer verilirse mevcut anahtar korunur.

        :param os_key: ``"windows"`` veya ``"mac"``.
        """
        key = str(os_key).strip().lower()
        if key in ("windows", "mac"):
            self._os_key = key

    # -- genel çalıştırma --------------------------------------------------

    def run(self, slot: str) -> tuple[bool, str]:
        """
        Bir slota atanmış eylemi çalıştırır.

        :param slot: ``"K1"``..``"K9"``, ``"C_a_b"`` veya enkoder slotu.
        :return: ``(başarı, Türkçe mesaj)`` ikilisi.
        """
        slot_id = str(slot).strip()
        try:
            action = self._cfg.get_action(self._os_key, slot_id)
        except Exception as exc:  # noqa: BLE001 - yapılandırma hatası çökertmemeli
            result = (False, f"'{slot_id}' okunamadı: {exc}")
            self.last_result = result
            return result

        success, message = self.run_action(action)
        if not success:
            message = f"{slot_display_name(slot_id)}: {message}"
        self.last_result = (success, message)
        return success, message

    def run_action(self, action: dict[str, Any]) -> tuple[bool, str]:
        """
        Verilen eylem sözlüğünü çalıştırır.

        :param action: ``type`` / ``value`` / ``name`` alanlarını içeren sözlük.
        :return: ``(başarı, Türkçe mesaj)`` ikilisi.
        """
        if not isinstance(action, dict):
            return False, "Geçersiz eylem tanımı."

        action_type = str(action.get("type", "none") or "none").strip().lower()
        value = action.get("value", "")
        value = "" if value is None else str(value)

        if action_type not in ACTION_TYPES:
            return False, f"Bilinmeyen eylem tipi: {action_type}"

        handler = self._handlers.get(action_type)
        if handler is None:  # pragma: no cover - _handlers tüm tipleri kapsar
            return False, f"'{action_type}' için işleyici tanımlı değil."

        try:
            return handler(value)
        except Exception as exc:  # noqa: BLE001 - hiçbir eylem uygulamayı çökertmez
            return False, f"Eylem çalıştırılamadı ({action_type}): {exc}"

    # -- tip işleyicileri --------------------------------------------------

    def _run_none(self, value: str) -> tuple[bool, str]:
        """``none`` tipi: hiçbir şey yapmaz."""
        return True, "Bu slota eylem atanmamış."

    def _run_app(self, value: str) -> tuple[bool, str]:
        """``app`` tipi: uygulamayı başlatır."""
        if not value.strip():
            return False, "Uygulama yolu boş."
        return platform_utils.open_application(value)

    def _run_url(self, value: str) -> tuple[bool, str]:
        """``url`` tipi: adresi varsayılan tarayıcıda açar."""
        if not value.strip():
            return False, "Web adresi boş."
        return platform_utils.open_url(value)

    # -- macOS Erişilebilirlik denetimi ---------------------------------
    # macOS, izin verilmemiş bir uygulamadan gelen klavye olaylarını
    # SESSİZCE yok sayar: pyautogui hata bile fırlatmaz, metin/kısayol
    # "hiçbir şey olmuyor" gibi görünür. İzin İSTEME işi yalnızca uygulama
    # AÇILIŞINDA, bir kez yapılır (MainWindow'daki tek seferlik diyalog);
    # burada eylem sırasında hiçbir sistem penceresi tetiklenmez, yalnızca
    # durum çubuğu için yol tarifi döndürülür.
    def _macos_event_izni(self) -> tuple[bool, str]:
        """(izin_var, yol_tarifi) döndürür; macOS dışında hep (True, "").

        Yol tarifi çalıştırma biçimine göre değişir — yanlış hedefe izin
        vermek en sık yaşanan çıkmazdır:

        * ``.app`` paketi geçici kopyadan çalışıyorsa (App Translocation)
          izin vermek İŞE YARAMAZ; uygulamanın taşınması gerekir.
        * ``.app`` paketinde izni ExtraKeyboard'ın kendisi alır.
        * Kaynak koddan çalıştırıldığında süreci Terminal başlattığı için
          izin Terminal'e verilir.
        """
        if platform_utils.accessibility_granted():
            return True, ""

        try:
            if platform_utils.gecici_konumdan_mi_calisiyor():
                return False, (
                    "İzin vermek şu hâlde işe yaramaz: uygulama macOS'un "
                    "her açılışta değişen geçici kopyasından çalışıyor. "
                    "ExtraKeyboard'ı Uygulamalar klasörüne taşıyıp oradan "
                    "açın; izin ancak o zaman kalıcı olur.")
        except Exception:
            pass

        if getattr(sys, "frozen", False):
            return False, (
                "Erişilebilirlik izni gerekli: Sistem Ayarları → Gizlilik ve "
                "Güvenlik → Erişilebilirlik listesinde EXTRAKEYBOARD'ın "
                "anahtarını açın (Terminal'e vermeyin — bu sürümde izni "
                "uygulamanın kendisi alır), sonra uygulamayı yeniden "
                "başlatın.")

        return False, (
            "Erişilebilirlik izni gerekli: Sistem Ayarları → Gizlilik ve "
            "Güvenlik → Erişilebilirlik listesinde TERMİNAL'in anahtarını "
            "açın (kaynak koddan çalıştırırken izin ExtraKeyboard'a değil, "
            "onu çalıştıran Terminal'e verilir), sonra uygulamayı masaüstü "
            "kısayolundan yeniden başlatın.")

    def _run_shortcut(self, value: str) -> tuple[bool, str]:
        """``shortcut`` tipi: tuş kombinasyonu gönderir."""
        if not value.strip():
            return False, "Kısayol boş."
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return False, "pyautogui kurulu değil — kısayol gönderilemiyor."
        izin, tarif = self._macos_event_izni()
        if not izin:
            return False, tarif

        keys, error = normalize_shortcut(value, self._os_key)
        if error:
            return False, error

        try:
            pyautogui.hotkey(*keys)
        except Exception as exc:  # noqa: BLE001
            return False, f"Kısayol gönderilemedi: {exc}"
        return True, "Kısayol gönderildi: " + "+".join(keys)

    def _run_text(self, value: str) -> tuple[bool, str]:
        """
        ``text`` tipi: metni yazar.

        ``pyautogui.write`` yalnızca ASCII karakterleri yazabildiği için
        Türkçe karakter (ç ğ ı ö ş ü İ) içeren metinler **pano üzerinden**
        yapıştırılır; eski pano içeriği sonrasında geri yüklenir.
        """
        if not value:
            return False, "Yazılacak metin boş."
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return False, "pyautogui kurulu değil — metin yazılamıyor."
        izin, tarif = self._macos_event_izni()
        if not izin:
            return False, tarif

        # Metnin sonuna 1 boşluk eklenir: aynı tuşa art arda basıldığında
        # metinler birbirine yapışmaz. Metin zaten boşluk/satır sonuyla
        # bitiyorsa ikinci bir boşluk eklenmez.
        if not value.endswith((" ", "\n", "\t")):
            value = value + " "

        if value.isascii():
            try:
                pyautogui.write(value, interval=0.01)
                return True, "Metin yazıldı."
            except Exception as exc:  # noqa: BLE001
                return False, f"Metin yazılamadı: {exc}"

        return self._paste_text(value)

    def _run_command(self, value: str) -> tuple[bool, str]:
        """``command`` tipi: kabuk komutunu arka planda çalıştırır.

        Komut pencere GÖSTERMEDEN çalışır. POSIX'te login kabuğu (``-l``)
        kullanılır ki kullanıcının PATH'i (Homebrew vb.) geçerli olsun —
        aksi hâlde "komut bulunamadı" hataları sessizce kayboluyordu.
        Hemen (0.4 sn içinde) hata koduyla biten komutlar kullanıcıya
        bildirilir; uzun sürenler arka planda devam eder.
        """
        command = value.strip()
        if not command:
            return False, "Çalıştırılacak komut boş."

        try:
            if platform_utils.IS_WINDOWS:
                proc = subprocess.Popen(command, shell=True)
            else:
                shell = platform_utils.shell_executable() or "/bin/sh"
                proc = subprocess.Popen([shell, "-lc", command])
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            return False, f"Komut çalıştırılamadı: {exc}"

        # Anında patlayan komutu yakala (ör. yazım hatası, bulunamayan araç).
        time.sleep(0.4)
        kod = proc.poll()
        if kod is not None and kod != 0:
            return False, (f"Komut hata koduyla bitti ({kod}): {command} — "
                           "komut penceresiz çalışır; çıktı görmek için "
                           "'open -a Terminal' benzeri kullanın.")
        return True, f"Komut çalıştırıldı: {command}"

    def _run_file(self, value: str) -> tuple[bool, str]:
        """``file`` tipi: dosyayı varsayılan uygulamada açar."""
        if not value.strip():
            return False, "Dosya yolu boş."
        return platform_utils.open_path(value)

    def _run_folder(self, value: str) -> tuple[bool, str]:
        """``folder`` tipi: klasörü dosya yöneticisinde açar."""
        if not value.strip():
            return False, "Klasör yolu boş."
        return platform_utils.open_folder(value)

    def _run_media(self, value: str) -> tuple[bool, str]:
        """
        ``media`` tipi: ses ve oynatma tuşlarını gönderir.

        Windows'ta pyautogui'nin medya tuşları kullanılır. macOS'ta pyautogui
        medya tuşlarını desteklemediği için ses işlemleri AppleScript
        (``set volume output volume ...``) ile, oynat/ileri/geri komutları
        çalışan bir müzik uygulaması (Spotify veya Music) üzerinden yapılır.
        """
        media = value.strip().lower()
        if media not in MEDIA_VALUES:
            return False, f"Bilinmeyen medya değeri: {value}"

        if platform_utils.IS_MAC:
            return self._run_media_mac(media)

        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return False, "pyautogui kurulu değil — medya tuşu gönderilemiyor."

        key_name = _MEDIA_KEYS[media]
        try:
            pyautogui.press(key_name)
        except Exception as exc:  # noqa: BLE001
            return False, f"Medya tuşu gönderilemedi: {exc}"
        return True, f"Medya komutu gönderildi: {media}"

    def _run_macro(self, value: str) -> tuple[bool, str]:
        """
        ``macro`` tipi: ``|`` ile ayrılmış adımları sırayla uygular.

        Sayı olan adımlar milisaniye cinsinden bekleme, diğerleri kısayol
        olarak yorumlanır. Örnek: ``ctrl+c|500|ctrl+v``.
        """
        raw_steps = [step.strip() for step in str(value).split("|")]
        steps = [step for step in raw_steps if step]
        if not steps:
            return False, "Makro boş."

        executed = 0
        for index, step in enumerate(steps, start=1):
            if _NUMBER_RE.match(step):
                delay_ms = min(float(step), float(MAX_MACRO_DELAY_MS))
                time.sleep(delay_ms / 1000.0)
                executed += 1
                continue

            success, message = self._run_shortcut(step)
            if not success:
                return False, f"Makro {index}. adımda durdu ({step}): {message}"
            executed += 1

        return True, f"Makro tamamlandı ({executed} adım)."

    # -- yardımcılar -------------------------------------------------------

    def _paste_text(self, value: str) -> tuple[bool, str]:
        """
        Metni pano üzerinden yapıştırır (Türkçe karakter yedeği).

        Eski pano içeriği okunur, metin panoya konur, yapıştırma kısayolu
        gönderilir ve kısa bir gecikmeden sonra eski içerik geri yüklenir.

        :param value: Yapıştırılacak metin.
        :return: ``(başarı, Türkçe mesaj)`` ikilisi.
        """
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return False, "pyautogui kurulu değil — metin yapıştırılamıyor."

        previous = self._clipboard_get()
        if not self._clipboard_set(value):
            return False, "Pano kullanılamıyor — Türkçe metin yazılamadı."

        paste_keys = ["command", "v"] if platform_utils.IS_MAC else ["ctrl", "v"]
        try:
            time.sleep(0.05)
            pyautogui.hotkey(*paste_keys)
        except Exception as exc:  # noqa: BLE001
            return False, f"Yapıştırma kısayolu gönderilemedi: {exc}"
        finally:
            if previous is not None:
                self._restore_clipboard_later(previous)

        return True, "Metin pano üzerinden yapıştırıldı."

    def _restore_clipboard_later(self, previous: str) -> None:
        """
        Eski pano içeriğini kısa bir gecikmeden sonra geri yükler.

        Geri yükleme ayrı bir thread'de yapılır; yapıştırma işleminin
        tamamlanmasını beklemek için 0.4 saniye gecikme uygulanır.

        :param previous: Geri yüklenecek eski pano metni.
        """

        def worker() -> None:
            """Gecikmeli geri yükleme görevini yürütür."""
            time.sleep(0.4)
            self._clipboard_set(previous)

        thread = threading.Thread(target=worker, name="ExtraKeyboardClipboard", daemon=True)
        thread.start()

    def _clipboard_get(self) -> str | None:
        """
        Pano içeriğini okur.

        :return: Pano metni; okunamazsa ``None``.
        """
        if PYPERCLIP_AVAILABLE and pyperclip is not None:
            try:
                return str(pyperclip.paste())
            except Exception:  # noqa: BLE001 - pano erişimi başarısız olabilir
                pass

        try:
            if platform_utils.IS_MAC:
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout
            elif platform_utils.IS_WINDOWS:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                if result.returncode == 0:
                    return result.stdout.rstrip("\r\n")
        except (OSError, subprocess.SubprocessError):
            return None
        return None

    def _clipboard_set(self, text: str) -> bool:
        """
        Panoya metin yazar.

        :param text: Panoya konacak metin.
        :return: Başarılıysa ``True``.
        """
        if PYPERCLIP_AVAILABLE and pyperclip is not None:
            try:
                pyperclip.copy(text)
                return True
            except Exception:  # noqa: BLE001 - platform yedeğine düş
                pass

        try:
            if platform_utils.IS_MAC:
                process = subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
                return process.returncode == 0
            if platform_utils.IS_WINDOWS:
                process = subprocess.run(["clip"], input=text, text=True, timeout=5)
                return process.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False
        return False

    def _mac_volume(self) -> tuple[int, bool] | None:
        """
        macOS'ta güncel çıkış ses seviyesini ve sessiz durumunu okur.

        :return: ``(0-100 arası seviye, sessiz mi)`` ikilisi; okunamazsa ``None``.
        """
        success, output = platform_utils.run_osascript(
            'set s to (get volume settings)\n'
            'return (output volume of s as text) & "," & (output muted of s as text)'
        )
        if not success or "," not in output:
            return None
        level_text, muted_text = output.split(",", 1)
        try:
            level = int(float(level_text.strip()))
        except ValueError:
            return None
        muted = muted_text.strip().lower() in ("true", "yes", "1")
        return max(0, min(100, level)), muted

    def _run_media_mac(self, media: str) -> tuple[bool, str]:
        """
        macOS'ta medya eylemini AppleScript ile uygular.

        Ses açma/kısma/sessize alma sistem genelinde çalışır. Oynat/ileri/geri
        komutları için çalışan bir müzik uygulaması (Spotify, ardından Music)
        aranır; hiçbiri çalışmıyorsa bilgilendirici bir hata döner.

        :param media: ``MEDIA_VALUES`` içindeki değerlerden biri.
        :return: ``(başarı, Türkçe mesaj)`` ikilisi.
        """
        if media in ("volume_up", "volume_down"):
            state = self._mac_volume()
            if state is None:
                return False, "Ses seviyesi okunamadı (AppleScript hatası)."
            level, _muted = state
            step = MAC_VOLUME_STEP if media == "volume_up" else -MAC_VOLUME_STEP
            new_level = max(0, min(100, level + step))
            success, message = platform_utils.run_osascript(
                f"set volume output volume {new_level} without output muted"
            )
            if not success:
                return False, f"Ses ayarlanamadı: {message}"
            return True, f"Ses seviyesi: %{new_level}"

        if media == "mute":
            success, message = platform_utils.run_osascript(
                "set volume output muted not (output muted of (get volume settings))"
            )
            if not success:
                return False, f"Sessize alınamadı: {message}"
            return True, "Sessiz durumu değiştirildi."

        # Oynat/duraklat ve parça geçişi: GERÇEK sistem medya tuşu basılır
        # (klavyedeki F8/F9 ile birebir aynı olay). Böylece o an medya çalan
        # HER uygulama kontrol edilir — Music, Spotify, tarayıcıdaki YouTube…
        # Erişilebilirlik izni gerektirir (metin/kısayolla aynı izin).
        NX_KODLAR = {"play_pause": 16, "next": 19, "prev": 20}
        kod = NX_KODLAR.get(media)
        if kod is None:  # pragma: no cover - MEDIA_VALUES tam kapsanıyor
            return False, f"Desteklenmeyen medya komutu: {media}"

        basari, mesaj = self._mac_medya_tusu(kod)
        if basari:
            adlar = {"play_pause": "Oynat/Duraklat", "next": "Sonraki parça",
                     "prev": "Önceki parça"}
            return True, f"Medya tuşu gönderildi: {adlar.get(media, media)}"

        # Sistem tuşu basılamadıysa (ör. izin yok) eski yönteme düşülür:
        # çalışan Spotify/Music doğrudan hedeflenir (izin gerektirmez).
        command = _MAC_TRANSPORT.get(media)
        if command is not None:
            for app_name in ("Spotify", "Music"):
                running, output = platform_utils.run_osascript(
                    f'tell application "System Events" to return (name of processes) contains "{app_name}"'
                )
                if not running or output.strip().lower() != "true":
                    continue
                success, message = platform_utils.run_osascript(
                    f'tell application "{app_name}" to {command}'
                )
                if success:
                    return True, f"{app_name}: {media}"
                return False, f"{app_name} komutu başarısız: {message}"

        return False, mesaj

    def _mac_medya_tusu(self, tus_kodu: int) -> tuple[bool, str]:
        """macOS'a donanımsal medya tuşu olayı basar (NSSystemDefined).

        :param tus_kodu: NX tuş kodu — 16=çal/duraklat, 19=ileri, 20=geri.
        :return: ``(başarı, mesaj)``; izin yoksa yol tarifi döner.
        """
        izin, tarif = self._macos_event_izni()
        if not izin:
            return False, tarif
        try:
            import Quartz
            from AppKit import NSEvent

            def bas(asagi: bool) -> None:
                bayrak = 0xA00 if asagi else 0xB00
                data1 = (tus_kodu << 16) | ((0x0A if asagi else 0x0B) << 8)
                olay = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                    14, (0, 0), bayrak, 0, 0, None, 8, data1, -1)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, olay.CGEvent())

            bas(True)
            bas(False)
            return True, "Medya tuşu gönderildi."
        except Exception as exc:  # noqa: BLE001
            return False, f"Medya tuşu gönderilemedi: {exc}"
