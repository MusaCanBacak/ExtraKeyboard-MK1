"""
ExtraKeyboard MK1 — işletim sistemi yardımcıları.

Bu modül çekirdek katmanın platforma bağımlı işlerini tek yerde toplar:

* İşletim sistemi tespiti (:data:`IS_MAC`, :data:`IS_WINDOWS`, :data:`IS_LINUX`).
* Profil anahtarı çözümü (:func:`current_os_key` -> ``"windows"`` | ``"mac"``).
* Otomatik başlatma: Windows'ta ``HKCU\\...\\Run`` kayıt defteri girdisi,
  macOS'ta ``~/Library/LaunchAgents`` altında bir LaunchAgent plist dosyası.
* Dosya / klasör / bağlantı açma yardımcıları.

Modül hiçbir arayüz bileşenine bağımlı değildir ve tüm işlemler hata
durumunda istisna fırlatmak yerine ``(başarı, mesaj)`` ikilisi döndürür.
"""

from __future__ import annotations

import os
import platform
import plistlib
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

__all__ = [
    "IS_MAC",
    "IS_WINDOWS",
    "IS_LINUX",
    "OS_NAME",
    "APP_NAME",
    "AUTOSTART_LABEL",
    "current_os_key",
    "os_display_name",
    "project_root",
    "entry_script",
    "python_executable",
    "launch_arguments",
    "launch_agent_path",
    "is_autostart_enabled",
    "set_autostart",
    "shell_executable",
    "expand_path",
    "open_path",
    "open_folder",
    "open_application",
    "open_url",
    "reveal_in_file_manager",
    "run_osascript",
]

#: Çalışılan platformun ham adı (``platform.system()`` çıktısı).
OS_NAME: str = platform.system()

#: macOS üzerinde çalışıyor muyuz?
IS_MAC: bool = OS_NAME == "Darwin"

#: Windows üzerinde çalışıyor muyuz?
IS_WINDOWS: bool = OS_NAME == "Windows"

#: Linux üzerinde çalışıyor muyuz? (Resmî destek yok, geliştirme kolaylığı için.)
IS_LINUX: bool = OS_NAME == "Linux"

#: Otomatik başlatma kaydında kullanılan kısa uygulama adı.
APP_NAME: str = "ExtraKeyboard"

#: macOS LaunchAgent etiketi ve plist dosya adı.
AUTOSTART_LABEL: str = "com.bluedevelopment.extrakeyboard"

#: Windows'ta otomatik başlatma anahtarının yolu.
_WINDOWS_RUN_KEY: str = r"Software\Microsoft\Windows\CurrentVersion\Run"


def current_os_key() -> str:
    """
    Etkin işletim sistemine karşılık gelen profil anahtarını verir.

    :return: macOS'ta ``"mac"``, diğer tüm platformlarda ``"windows"``.
        (Şemada yalnızca bu iki profil vardır; Linux geliştirme ortamında
        Windows profili kullanılır.)
    """
    return "mac" if IS_MAC else "windows"


def os_display_name(os_key: str) -> str:
    """
    Profil anahtarını arayüzde gösterilecek ada çevirir.

    :param os_key: ``"windows"`` veya ``"mac"``.
    :return: ``"Windows"`` veya ``"macOS"``.
    """
    return "macOS" if str(os_key).strip().lower() == "mac" else "Windows"


def project_root() -> Path:
    """
    Proje kök dizinini döndürür.

    Donmuş (paketlenmiş) çalıştırmada çalıştırılabilir dosyanın dizini,
    normal çalıştırmada ``app/core/`` dizininin iki üstü kullanılır.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller paketinde veri dosyaları (varliklar/ …) geçici bir
        # çıkarma dizinine açılır; sys._MEIPASS onu gösterir. Bu dizin SALT
        # OKUNURDUR — yazılacak dosyalar için config.user_data_dir() kullanılır.
        taban = getattr(sys, "_MEIPASS", None)
        if taban:
            return Path(taban)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def entry_script() -> Path:
    """
    Uygulamanın giriş noktası betiğinin yolunu döndürür.

    Spec bölüm 9'a göre giriş noktası proje kökündeki ``run_app.py``
    dosyasıdır. Dosya henüz yoksa da yol yine de üretilir.
    """
    return project_root() / "run_app.py"


def python_executable() -> str:
    """
    Otomatik başlatmada kullanılacak Python yorumlayıcısının yolunu verir.

    Windows'ta konsol penceresi açılmaması için ``python.exe`` yerine varsa
    ``pythonw.exe`` tercih edilir.

    :return: Yorumlayıcının tam yolu.
    """
    executable = sys.executable or "python"
    if IS_WINDOWS:
        candidate = Path(executable)
        if candidate.name.lower() == "python.exe":
            windowless = candidate.with_name("pythonw.exe")
            if windowless.exists():
                return str(windowless)
    return executable


def launch_arguments() -> list[str]:
    """
    Uygulamayı başlatmak için gereken komut satırı parçalarını üretir.

    Donmuş çalıştırmada tek parça (çalıştırılabilir dosya), normal
    çalıştırmada ``[python, run_app.py]`` döner.

    :return: ``subprocess`` ile doğrudan kullanılabilecek argüman listesi.
    """
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [python_executable(), str(entry_script())]


def _quote_windows(argument: str) -> str:
    """
    Windows kayıt defteri değeri için argümanı tırnak içine alır.

    :param argument: Tırnaklanacak argüman.
    :return: Boşluk içeriyorsa çift tırnaklı, aksi hâlde olduğu gibi.
    """
    if " " in argument and not argument.startswith('"'):
        return f'"{argument}"'
    return argument


def launch_agent_path() -> Path:
    """
    macOS LaunchAgent plist dosyasının tam yolunu döndürür.

    :return: ``~/Library/LaunchAgents/com.bluedevelopment.extrakeyboard.plist``
    """
    return Path.home() / "Library" / "LaunchAgents" / f"{AUTOSTART_LABEL}.plist"


def is_autostart_enabled() -> bool:
    """
    Otomatik başlatmanın işletim sistemi düzeyinde açık olup olmadığını verir.

    :return: Windows'ta kayıt defteri girdisi, macOS'ta plist dosyası varsa
        ``True``; diğer platformlarda daima ``False``.
    """
    if IS_WINDOWS:
        try:
            import winreg  # type: ignore[import-not-found]

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WINDOWS_RUN_KEY, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False
        except ImportError:  # pragma: no cover - Windows dışı
            return False

    if IS_MAC:
        return launch_agent_path().exists()

    return False


def _set_autostart_windows(enabled: bool) -> tuple[bool, str]:
    """
    Windows kayıt defterindeki otomatik başlatma girdisini açar/kapatır.

    :param enabled: ``True`` ise girdi yazılır, ``False`` ise silinir.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - Windows dışı
        return False, "Kayıt defteri modülü (winreg) bulunamadı."

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WINDOWS_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                command = " ".join(_quote_windows(part) for part in launch_arguments())
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                return True, "Otomatik başlatma açıldı."
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            return True, "Otomatik başlatma kapatıldı."
    except OSError as exc:
        return False, f"Kayıt defteri güncellenemedi: {exc}"


def _set_autostart_mac(enabled: bool) -> tuple[bool, str]:
    """
    macOS LaunchAgent plist dosyasını oluşturur veya siler.

    Plist yazıldıktan sonra ``launchctl load -w`` ile yüklenmeye çalışılır;
    bu adım başarısız olsa bile kullanıcı bir sonraki oturum açılışında
    uygulamanın başlaması için yeterlidir.

    :param enabled: ``True`` ise plist yazılır, ``False`` ise kaldırılır.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    plist_path = launch_agent_path()

    if enabled:
        payload = {
            "Label": AUTOSTART_LABEL,
            "ProgramArguments": launch_arguments(),
            "RunAtLoad": True,
            "KeepAlive": False,
            "ProcessType": "Interactive",
            "WorkingDirectory": str(project_root()),
        }
        try:
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(plist_path, "wb") as handle:
                plistlib.dump(payload, handle)
        except OSError as exc:
            return False, f"LaunchAgent dosyası yazılamadı: {exc}"

        _launchctl(["load", "-w", str(plist_path)])
        return True, "Otomatik başlatma açıldı."

    if plist_path.exists():
        _launchctl(["unload", "-w", str(plist_path)])
        try:
            plist_path.unlink()
        except OSError as exc:
            return False, f"LaunchAgent dosyası silinemedi: {exc}"
    return True, "Otomatik başlatma kapatıldı."


def _launchctl(arguments: list[str]) -> bool:
    """
    ``launchctl`` komutunu sessizce çalıştırır.

    :param arguments: ``launchctl`` sonrası gelen argümanlar.
    :return: Komut 0 ile döndüyse ``True``.
    """
    try:
        result = subprocess.run(
            ["launchctl", *arguments],
            check=False,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def set_autostart(enabled: bool) -> tuple[bool, str]:
    """
    Otomatik başlatmayı işletim sistemi düzeyinde açar veya kapatır.

    :param enabled: ``True`` ise açılır, ``False`` ise kapatılır.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi. Desteklenmeyen platformlarda
        ``(False, ...)`` döner.
    """
    if IS_WINDOWS:
        return _set_autostart_windows(bool(enabled))
    if IS_MAC:
        return _set_autostart_mac(bool(enabled))
    return False, "Otomatik başlatma bu işletim sisteminde desteklenmiyor."


def shell_executable() -> str | None:
    """
    ``shell=True`` ile komut çalıştırırken kullanılacak kabuğu belirler.

    :return: POSIX sistemlerde kullanıcının kabuğu (``$SHELL``) veya
        ``/bin/zsh`` / ``/bin/sh``; Windows'ta ``None`` (``cmd.exe`` kullanılır).
    """
    if IS_WINDOWS:
        return None

    candidate = os.environ.get("SHELL", "").strip()
    if candidate and os.path.exists(candidate):
        return candidate
    for fallback in ("/bin/zsh", "/bin/bash", "/bin/sh"):
        if os.path.exists(fallback):
            return fallback
    return None


def expand_path(path: str) -> str:
    """
    Yol dizgesindeki ``~`` ve ortam değişkenlerini açar.

    :param path: Ham yol dizgesi (``~/Downloads``, ``%USERPROFILE%\\Desktop``).
    :return: Genişletilmiş yol.
    """
    return os.path.expandvars(os.path.expanduser(str(path).strip()))


def open_path(path: str) -> tuple[bool, str]:
    """
    Bir dosyayı varsayılan uygulamada açar.

    :param path: Açılacak dosyanın yolu.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    target = expand_path(path)
    if not target:
        return False, "Dosya yolu boş."
    if not os.path.exists(target):
        return False, f"Dosya bulunamadı: {target}"

    try:
        if IS_MAC:
            subprocess.run(["open", target], check=True, capture_output=True, timeout=15)
        elif IS_WINDOWS:
            os.startfile(target)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", target])
        return True, f"Açıldı: {os.path.basename(target)}"
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
        return False, f"Dosya açılamadı: {detail or exc}"
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Dosya açılamadı: {exc}"


def open_folder(path: str) -> tuple[bool, str]:
    """
    Bir klasörü Finder / Dosya Gezgini içinde açar.

    :param path: Açılacak klasörün yolu.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    target = expand_path(path)
    if not target:
        return False, "Klasör yolu boş."
    if not os.path.isdir(target):
        return False, f"Klasör bulunamadı: {target}"

    try:
        if IS_MAC:
            subprocess.run(["open", target], check=True, capture_output=True, timeout=15)
        elif IS_WINDOWS:
            try:
                os.startfile(target)  # type: ignore[attr-defined]
            except OSError:
                subprocess.Popen(["explorer", target])
        else:
            subprocess.Popen(["xdg-open", target])
        return True, f"Klasör açıldı: {os.path.basename(target.rstrip(os.sep)) or target}"
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
        return False, f"Klasör açılamadı: {detail or exc}"
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Klasör açılamadı: {exc}"


def open_application(value: str) -> tuple[bool, str]:
    """
    Bir uygulamayı başlatır.

    * macOS: ``.app`` paketi veya var olan bir yol ise ``open <yol>``,
      aksi hâlde uygulama adı kabul edilip ``open -a <ad>`` kullanılır.
    * Windows: ``os.startfile`` denenir, başarısız olursa doğrudan
      çalıştırma ve son çare olarak kabuk üzerinden ``start`` denenir.

    :param value: Uygulama yolu veya adı.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    raw = str(value).strip()
    if not raw:
        return False, "Uygulama yolu/adı boş."
    target = expand_path(raw)

    try:
        if IS_MAC:
            if target.endswith(".app") or os.path.exists(target):
                subprocess.run(["open", target], check=True, capture_output=True, timeout=20)
            else:
                subprocess.run(["open", "-a", raw], check=True, capture_output=True, timeout=20)
            return True, f"Uygulama başlatıldı: {os.path.basename(target.rstrip('/')) or raw}"

        if IS_WINDOWS:
            try:
                os.startfile(target)  # type: ignore[attr-defined]
                return True, f"Uygulama başlatıldı: {os.path.basename(target) or raw}"
            except OSError:
                pass
            resolved = shutil.which(raw)
            if resolved:
                subprocess.Popen([resolved])
                return True, f"Uygulama başlatıldı: {raw}"
            # GÜVENLİK (komut enjeksiyonu): eskiden `start "" "{raw}"` bir KABUK
            # dizgesine gömülüp shell=True ile çalıştırılıyordu; raw içine tırnak
            # veya `&` konursa (paylaşılan yapılandırma, telefon vb.) rastgele
            # komut çalışırdı. Kabuk hiç kullanılmaz: os.startfile zaten `start`
            # ile aynı işi (varsayılan uygulamayla açma) yapar; expand edilmemiş
            # ham ad ile son bir kez denenir, olmazsa kabuğa düşülmeden hata verilir.
            try:
                os.startfile(raw)  # type: ignore[attr-defined]
                return True, f"Uygulama başlatıldı: {raw}"
            except OSError:
                return False, f"Uygulama bulunamadı/başlatılamadı: {raw}"

        resolved = shutil.which(raw)
        if resolved:
            subprocess.Popen([resolved])
            return True, f"Uygulama başlatıldı: {raw}"
        subprocess.Popen(["xdg-open", target])
        return True, f"Uygulama başlatıldı: {raw}"
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
        return False, f"Uygulama başlatılamadı: {detail or exc}"
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Uygulama başlatılamadı: {exc}"


def open_url(url: str) -> tuple[bool, str]:
    """
    Bir web adresini varsayılan tarayıcıda açar.

    Şema (``http://`` / ``https://``) yoksa ``https://`` eklenir.

    :param url: Açılacak adres.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    raw = str(url).strip()
    if not raw:
        return False, "Adres boş."
    if "://" not in raw and not raw.lower().startswith("mailto:"):
        raw = "https://" + raw.lstrip("/")

    # GÜVENLİK — şema allowlist'i:
    # Bir adres eylemi yalnızca web/e-posta açmalıdır. Denetim öncesi bu değer
    # doğrudan işletim sistemi başlatıcısına (webbrowser.open) iletiliyordu;
    # böylece paylaşılan/içe aktarılan bir yapılandırmadaki ``file:///...``
    # yerel dosyaları açar, ``smb://`` / ``vnc://`` / özel şemalar ise ilgili
    # istemciyi tetikleyebilir (yerel dosya sızıntısı / istenmeyen bağlantı).
    # Yalnızca http, https ve mailto şemalarına izin verilir.
    sema = raw.split(":", 1)[0].lower() if ":" in raw else ""
    if sema not in ("http", "https", "mailto"):
        return False, (f"Güvenlik: yalnızca http/https/mailto adresleri "
                       f"açılabilir. Engellenen şema: '{sema or '?'}://…'")

    try:
        if webbrowser.open(raw):
            return True, f"Tarayıcıda açıldı: {raw}"
        return False, f"Tarayıcı açılamadı: {raw}"
    except (OSError, webbrowser.Error) as exc:
        return False, f"Tarayıcı açılamadı: {exc}"


def reveal_in_file_manager(path: str) -> tuple[bool, str]:
    """
    Bir dosyayı Finder / Dosya Gezgini içinde seçili hâlde gösterir.

    :param path: Gösterilecek dosyanın yolu.
    :return: ``(başarı, Türkçe mesaj)`` ikilisi.
    """
    target = expand_path(path)
    if not os.path.exists(target):
        return False, f"Yol bulunamadı: {target}"

    try:
        if IS_MAC:
            subprocess.run(["open", "-R", target], check=True, capture_output=True, timeout=15)
        elif IS_WINDOWS:
            subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(target) or target])
        return True, "Dosya konumu açıldı."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Dosya konumu açılamadı: {exc}"


def run_osascript(script: str, timeout: float = 8.0) -> tuple[bool, str]:
    """
    macOS'ta bir AppleScript parçasını çalıştırır.

    :param script: Çalıştırılacak AppleScript metni.
    :param timeout: Saniye cinsinden zaman aşımı.
    :return: ``(başarı, çıktı veya hata mesajı)`` ikilisi.
    """
    if not IS_MAC:
        return False, "AppleScript yalnızca macOS'ta çalışır."

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"AppleScript çalıştırılamadı: {exc}"

    if result.returncode != 0:
        return False, (result.stderr or "AppleScript hatası").strip()
    return True, (result.stdout or "").strip()


def list_installed_apps() -> list[tuple[str, str]]:
    """
    Kurulu macOS uygulamalarını ``(görünen ad, .app yolu)`` olarak listeler.

    Tk'nin dosya seçicisi macOS'ta ``.app`` paketlerini (aslında birer
    klasör oldukları için) çoğu sürümde seçtirmez; uygulama seçimi bu
    listeden beslenen yerleşik seçiciyle yapılır. Standart klasörler
    taranır, alt klasörlere (örn. ``/Applications/Utilities``) bir seviye
    inilir. Aynı ada sahip uygulamalarda ilk bulunan yol korunur.

    :return: Ada göre sıralı ``(ad, yol)`` listesi; macOS dışında boş liste.
    """
    if not IS_MAC:
        return []

    roots = (
        "/Applications",
        "/System/Applications",
        os.path.expanduser("~/Applications"),
    )
    found: dict[str, str] = {}

    def _scan(folder: str, depth: int) -> None:
        try:
            entries = os.scandir(folder)
        except OSError:
            return
        with entries:
            for entry in entries:
                try:
                    if entry.name.endswith(".app") and entry.is_dir():
                        found.setdefault(entry.name[:-4], entry.path)
                    elif depth > 0 and entry.is_dir() and not entry.name.startswith("."):
                        _scan(entry.path, depth - 1)
                except OSError:
                    continue

    for root in roots:
        _scan(root, 1)

    return sorted(found.items(), key=lambda item: item[0].lower())


def accessibility_granted() -> bool:
    """
    macOS Erişilebilirlik (klavye olayı basma) izni verilmiş mi?

    Metin ve kısayol eylemleri bu izne bağlıdır; izin yokken macOS
    olayları SESSİZCE yok sayar. macOS dışında her zaman ``True``.
    """
    if not IS_MAC:
        return True
    try:
        from Quartz import CGPreflightPostEventAccess
        return bool(CGPreflightPostEventAccess())
    except Exception:
        return True


def gecici_konumdan_mi_calisiyor() -> bool:
    """Uygulama macOS'un "App Translocation" kopyasından mı çalışıyor?

    İnternetten indirilmiş (karantina damgalı) bir ``.app`` ilk kez
    açıldığında macOS onu rastgele adlı, salt okunur, geçici bir konuma
    kopyalayıp ORADAN çalıştırır::

        /private/var/folders/…/AppTranslocation/<her-seferinde-farklı>/d/…

    Bunun görünen sonucu şudur: Erişilebilirlik izni verilir, uygulama
    çalışır; ama bir sonraki açılışta yol değiştiği için macOS uygulamayı
    tanımaz ve izin YİNE İSTENİR. Kullanıcıya "izin verdim ama hep soruyor,
    makro/metin çalışmıyor" gibi görünür.

    Çözüm izni tekrar vermek değil, translocation'ı sonlandırmaktır:
    karantina damgasını silmek (``xattr -cr``) veya ``.app``'i Finder'da
    başka bir klasöre (örneğin Uygulamalar) taşımak.

    :return: Geçici kopyadan çalışılıyorsa ``True``.
    """
    if not IS_MAC or not getattr(sys, "frozen", False):
        return False
    try:
        return "/AppTranslocation/" in os.path.abspath(sys.executable)
    except Exception:
        return False


def request_accessibility() -> None:
    """
    Erişilebilirlik izni akışını başlatır (yalnızca macOS).

    İki adım birden: sistem izin isteği tetiklenir VE Sistem Ayarları'nın
    doğrudan Erişilebilirlik bölmesi açılır (istek daha önce reddedildiyse
    macOS pencereyi bir daha göstermez; bölmeyi açmak her koşulda çalışır).
    """
    if not IS_MAC:
        return
    try:
        from Quartz import CGRequestPostEventAccess
        CGRequestPostEventAccess()
    except Exception:
        pass
    try:
        subprocess.Popen([
            "open",
            "x-apple.systempreferences:com.apple.preference.security"
            "?Privacy_Accessibility",
        ])
    except Exception:
        pass
