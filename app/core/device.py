"""
ExtraKeyboard MK1 — cihaz bağlantı katmanı (CDC seri, satır tabanlı ASCII).

Bu modül spec bölüm 4 (USB kimliği) ve bölüm 5 (haberleşme protokolü)
kurallarını uygular:

* Port önce **VID/PID** (``0x303A`` / ``0x82E1``) ile, bulunamazsa
  **Product** dizgesi (``ExtraKeyboard MK1``) ile aranır.
* Satır sonu ``\\n``; ``\\r`` karakterleri temizlenir; kısmi satırlar
  tamponda birikir, yalnızca ``\\n`` geldiğinde işlenir.
* **Bilinmeyen satırlar sessizce yok sayılır** (ileri uyumluluk).
* Bağlantı koparsa 1 saniyede bir yeniden bağlanmaya çalışılır.
* Canlılık ölçütü ``HB``'dir: 3000 ms boyunca kalp atışı gelmezse port
  kapatılır ve taramaya dönülür. ``CMD ID`` 1500 ms içinde yanıtlanmazsa
  o port bir tur atlanır.
* ``uptime_ms`` geriye giderse cihaz yeniden başlamış demektir; kimlik ve
  tüm cihaz ayarları yeniden gönderilir.

``on_event`` geri çağrımı **arka plan thread'inden** çağrılır. Arayüz
katmanı bu veriyi ``self.after(0, ...)`` ile ana thread'e taşımak zorundadır.

``pyserial`` kurulu değilse veya port açılamazsa uygulama çökmez; yalnızca
``kind="link"`` olayları ile durum bildirilir.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.core import config as config_module
from app.core.config import ConfigManager, combo_id

try:  # pyserial isteğe bağlıdır; yoksa uygulama çalışmaya devam eder.
    import serial  # type: ignore[import-not-found]
    from serial.tools import list_ports  # type: ignore[import-not-found]

    SERIAL_AVAILABLE = True
except Exception:  # pragma: no cover - pyserial kurulu değilse
    serial = None  # type: ignore[assignment]
    list_ports = None  # type: ignore[assignment]
    SERIAL_AVAILABLE = False

__all__ = [
    "SERIAL_AVAILABLE",
    "RECONNECT_DELAY",
    "READ_TIMEOUT",
    "HB_TIMEOUT",
    "ID_TIMEOUT",
    "DeviceEvent",
    "DeviceLink",
    "parse_line",
]

#: Bağlantı koptuğunda yeniden deneme aralığı (saniye).
RECONNECT_DELAY: float = 1.0

#: Seri porttan okuma zaman aşımı (saniye). Döngü hızını da bu belirler.
READ_TIMEOUT: float = 0.1

#: Kalp atışı (``HB``) zaman aşımı (saniye). Cihaz her 1000 ms'de bir ``HB``
#: gönderir; bu süre boyunca hiç ``HB`` gelmezse bağlantı kopmuş sayılır.
#: 3 sn ÇOK SIKIYDI: yerleşik USB CDC'de host okuması kısa süreli takılınca
#: (ya da marjinal kablo/konnektörde anlık kesinti) art arda birkaç ``HB``
#: kaçıp bağlantı gereksiz yere "düştü/bağlandı" salınımı yapıyordu. 8 sn,
#: gerçek kopmayı hâlâ makul sürede yakalarken bu kozmetik salınımı susturur.
HB_TIMEOUT: float = 8.0

#: GÖSTERGE canlılık eşiği (saniye). Port AÇIK kalsa bile son ``HB``/satır bu
#: süreden eskiyse cihaz "yanıt vermiyor" sayılır ve arayüzde "Bağlı değil"
#: gösterilir. Port KAPATILMAZ (flap yok) — bu yalnızca göstergeyi DÜRÜST tutar:
#: cihaz sussa/asılsa kullanıcıya yalan "bağlı" gösterilmez (bkz. `responsive`).
#: Cihaz saniyede bir HB attığı için 4 sn birkaç kaçırmaya tolerans verir.
RESPONSIVE_TIMEOUT: float = 4.0

#: ``CMD ID`` el sıkışma zaman aşımı (saniye). Bu süre içinde ``ID`` satırı
#: gelmezse port kapatılır ve sıradaki aday denenir.
ID_TIMEOUT: float = 3.0

#: Canlılık bildirimi aralığı (saniye). Cihaz, DTR sinyalini görmese bile
#: "son 3 sn içinde komut geldi" ölçütüyle uygulamanın bağlı olduğunu
#: anlar; bu yüzden düzenli ``CMD PING`` gönderilir (firmware ACK ile
#: yanıtlar, uygulama tarafında ek işlem gerektirmez).
PING_INTERVAL: float = 1.0

#: Kısa sessizlikte TEK SEFERLİK hızlı yeniden açma eşiği (sn).
#: 2026-09-29 ölçümü: kopmaların çoğunda (11/17) port yerinde duruyor ve
#: portu kapatıp açmak veriyi ~1 sn içinde geri getiriyor. 8 sn beklemek
#: yerine 3 sn'de bir kez denenir; sağlıklı bağlantıda HB+ACK saniyede bir
#: geldiği için 3 sn sessizlik normalde hiç oluşmaz.
FAST_REOPEN_SILENCE: float = 3.0
#: İki hızlı yeniden açma arasındaki en kısa süre (sn). Hızlı deneme işe
#: yaramazsa port bu sürede HB_TIMEOUT (8 sn) boyunca AÇIK tutulur ki
#: kartın TX bekçisi (EK_TX_STUCK_MS = 5 sn, yalnızca port açıkken sayar)
#: kendini resetleyebilsin. Her sessizlikte 3 sn'de kapatsaydık bekçi hiç
#: tetiklenemezdi (bkz. firmware config.h).
FAST_REOPEN_COOLDOWN: float = 30.0

_olay_kayitci: "logging.Logger | None" = None


def _olay_log_yolu() -> str:
    """Bağlantı olay günlüğünün yolu (platforma göre)."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Logs/ExtraKeyboard.log")
    if os.name == "nt":
        kok = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(kok, "ExtraKeyboard", "ExtraKeyboard.log")
    return os.path.expanduser("~/.extrakeyboard/ExtraKeyboard.log")


def _olay(mesaj: str) -> None:
    """Bağlantı olayını zaman damgasıyla kalıcı günlüğe yazar. ASLA hata atmaz.

    Neden var: kopmalar aralıklı ve birkaç saniyelik; anlık gözlemle
    yakalanamıyor. Her olayın zamanı, türü, kartın bildirdiği reset nedeni ve
    neyin düzelttiği burada birikir. Normal çalışmada hiçbir şey yazılmaz.
    """
    global _olay_kayitci
    try:
        if _olay_kayitci is None:
            yol = _olay_log_yolu()
            os.makedirs(os.path.dirname(yol), exist_ok=True)
            k = logging.getLogger("extrakeyboard.baglanti")
            k.setLevel(logging.INFO)
            k.propagate = False
            if not k.handlers:
                h = logging.handlers.RotatingFileHandler(
                    yol, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
                h.setFormatter(logging.Formatter(
                    "%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
                k.addHandler(h)
            _olay_kayitci = k
        _olay_kayitci.info(mesaj)
    except Exception:  # noqa: BLE001 - günlük hatası bağlantıyı etkilemesin
        pass

#: Tampon bu boyutu aşarsa (satır sonu hiç gelmiyorsa) temizlenir.
_MAX_BUFFER_BYTES: int = 65536

_ENC_SLOTS: dict[str, str] = {
    "CW": "cw",
    "CCW": "ccw",
    "PRESS": "press",
    "LONG": "long",
}

_HEX_COLOR_RE: re.Pattern[str] = re.compile(r"^#?[0-9A-Fa-f]{6}$")


@dataclass
class DeviceEvent:
    """
    Cihazdan gelen tek bir olayı temsil eden basit veri sınıfı.

    :ivar kind: Olay türü — ``"key"``, ``"combo"``, ``"mode"``, ``"os"``,
        ``"enc"``, ``"hb"``, ``"id"``, ``"ack"``, ``"err"`` veya ``"link"``.
    :ivar slot: İlgili slot kimliği (``"K3"``, ``"C_2_5"``, ``"cw"`` …).
        Slotu olmayan olaylarda ``None``.
    :ivar raw: Cihazdan gelen ham satır (``"link"`` olaylarında uygulama
        tarafından üretilen açıklama).
    :ivar payload: Olaya özgü ek alanlar.
    """

    kind: str
    slot: str | None = None
    raw: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


def _to_int(value: Any, default: int = 0) -> int:
    """
    ``"0x303A"``, ``"303A"``, ``12345`` gibi değerleri tam sayıya çevirir.

    :param value: Çevrilecek değer.
    :param default: Çevrilemezse döndürülecek değer.
    :return: Tam sayı karşılığı.
    """
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text, 10)
    except ValueError:
        try:
            return int(text, 16)
        except ValueError:
            return default


def parse_line(line: str) -> DeviceEvent | None:
    """
    Cihazdan gelen tek bir protokol satırını :class:`DeviceEvent` nesnesine çevirir.

    Spec bölüm 5.1'deki tüm mesajlar desteklenir. Tanınmayan satırlar için
    ``None`` döner (sessizce yok sayılır).

    :param line: ``\\r`` ve boşluklardan arındırılmış tek satır.
    :return: Ayrıştırılmış olay veya tanınmıyorsa ``None``.
    """
    raw = str(line).strip()
    if not raw:
        return None

    parts = raw.split()
    head = parts[0].upper()

    # --- HB <uptime_ms> ---
    if head == "HB":
        uptime = _to_int(parts[1], 0) if len(parts) > 1 else 0
        return DeviceEvent(kind="hb", slot=None, raw=raw, payload={"uptime_ms": uptime})

    # --- ID <fw> <hw> <serial> <os> ---
    if head == "ID":
        fields = parts[1:]
        os_raw = fields[3].upper() if len(fields) > 3 else ""
        payload: dict[str, Any] = {
            "fw": fields[0] if len(fields) > 0 else "",
            "hw": fields[1] if len(fields) > 1 else "",
            "serial": fields[2] if len(fields) > 2 else "",
            "os_raw": os_raw,
            "os": "mac" if os_raw == "MAC" else ("windows" if os_raw == "WIN" else ""),
        }
        return DeviceEvent(kind="id", slot=None, raw=raw, payload=payload)

    # --- ACK <komut> ---
    if head == "ACK":
        return DeviceEvent(
            kind="ack",
            slot=None,
            raw=raw,
            payload={"command": " ".join(parts[1:])},
        )

    # --- ERR <sebep> ---
    if head == "ERR":
        return DeviceEvent(
            kind="err",
            slot=None,
            raw=raw,
            payload={"reason": " ".join(parts[1:])},
        )

    # --- EV ... ---
    if head != "EV" or len(parts) < 2:
        return None

    topic = parts[1].upper()

    # EV KEY <n> DOWN|UP
    if topic == "KEY" and len(parts) >= 4:
        number = _to_int(parts[2], 0)
        edge = parts[3].upper()
        if not 1 <= number <= config_module.KEY_COUNT or edge not in ("DOWN", "UP"):
            return None
        return DeviceEvent(
            kind="key",
            slot=f"K{number}",
            raw=raw,
            payload={"number": number, "edge": edge.lower(), "pressed": edge == "DOWN"},
        )

    # EV COMBO <a> <b>
    if topic == "COMBO" and len(parts) >= 4:
        first = _to_int(parts[2], 0)
        second = _to_int(parts[3], 0)
        try:
            slot = combo_id(first, second)
        except ValueError:
            return None
        low, high = sorted((first, second))
        return DeviceEvent(kind="combo", slot=slot, raw=raw, payload={"a": low, "b": high})

    # EV MODE COMBO_ON|COMBO_OFF
    if topic == "MODE" and len(parts) >= 3:
        state = parts[2].upper()
        if state not in ("COMBO_ON", "COMBO_OFF"):
            return None
        active = state == "COMBO_ON"
        return DeviceEvent(
            kind="mode",
            slot=None,
            raw=raw,
            payload={"combo": active, "state": "on" if active else "off"},
        )

    # EV OS WIN|MAC
    if topic == "OS" and len(parts) >= 3:
        os_raw = parts[2].upper()
        if os_raw not in ("WIN", "MAC"):
            return None
        return DeviceEvent(
            kind="os",
            slot=None,
            raw=raw,
            payload={"os": "mac" if os_raw == "MAC" else "windows", "os_raw": os_raw},
        )

    # EV ENC CW|CCW|PRESS|LONG
    if topic == "ENC" and len(parts) >= 3:
        action = parts[2].upper()
        slot = _ENC_SLOTS.get(action)
        if slot is None:
            return None
        return DeviceEvent(kind="enc", slot=slot, raw=raw, payload={"action": slot})

    return None


class DeviceLink:
    """
    Arka plan thread'inde seri portu yönetir; cihazı otomatik bulur ve
    bağlantı koptuğunda 1 saniyede bir yeniden bağlanmayı dener.

    Örnek kullanım::

        link = DeviceLink(cfg, on_event=olayi_isle)
        link.start()                    # arka plan thread'i başlar
        link.set_led(1, "#1E90FF")      # LED1'i Windows mavisine ayarla
        link.set_brightness(60)         # varsayılan parlaklık
        link.stop()                     # uygulama kapanırken

    :param cfg: Cihaz ayarlarının okunacağı yapılandırma yöneticisi.
    :param on_event: Her olay için çağrılan geri çağrım. **Arka plan
        thread'inden** çağrılır.
    """

    def __init__(self, cfg: ConfigManager, on_event: Callable[[DeviceEvent], None]) -> None:
        """Bağlantı nesnesini kurar; port henüz açılmaz (bkz. :meth:`start`)."""
        self._cfg: ConfigManager = cfg
        self._on_event: Callable[[DeviceEvent], None] = on_event

        self._serial: Any | None = None
        self._thread: threading.Thread | None = None
        self._stop_event: threading.Event = threading.Event()
        self._write_lock: threading.Lock = threading.Lock()

        self._buffer: bytearray = bytearray()
        self._connected: bool = False
        self._last_ping_sent: float = 0.0
        self._port_name: str | None = None
        self._last_link_state: bool | None = None
        self._last_error: str = ""

        # -- canlılık ve el sıkışma durumu (bkz. docs/03-PROTOKOL.md 6.3) --
        #: Son ``HB`` / ``ID`` satırının alındığı an (``time.monotonic()``).
        self._last_hb: float = 0.0
        #: Cihazdan gelen son ``uptime_ms``; geriye giderse cihaz yeniden başlamıştır.
        self._last_uptime: int = -1
        #: Bu bağlantıda ``ID`` yanıtı alındı mı (el sıkışma tamamlandı mı).
        self._id_seen: bool = False
        #: Bu bağlantı denemesinde cihazdan ANLAMLI bir satır geldi mi?
        #: (HB, EV, ACK …) ``CMD ID`` yanıtsız kalsa bile cihazın
        #: konuştuğunu gösterir; bkz. :meth:`_handshake`.
        self._cihaz_konustu: bool = False
        #: Cihazın bildirdiği OS modu (``"windows"`` / ``"mac"``).
        self._device_os: str = ""
        #: Cihaz yeniden başladı; kimlik ve ayarlar yeniden gönderilmeli.
        self._restart_pending: bool = False
        #: ``CMD ID`` yanıtı vermediği için bir tur atlanacak portlar.
        self._skip_ports: set[str] = set()
        #: Son hızlı yeniden açmanın zamanı (bkz. FAST_REOPEN_COOLDOWN).
        self._son_hizli_acma: float = -1e9
        #: Sessizlik yüzünden yeniden bağlanıldıysa sessizliğin başladığı an;
        #: ilk satır gelince toplam kesinti süresi günlüğe yazılır.
        self._toparlanma_basi: float | None = None

    # -- yaşam döngüsü -----------------------------------------------------

    def start(self) -> None:
        """
        Arka plan dinleme thread'ini başlatır.

        Zaten çalışıyorsa hiçbir şey yapmaz. ``pyserial`` kurulu değilse
        thread başlatılmaz; bunun yerine tek bir ``kind="link"`` olayı ile
        durum bildirilir ve uygulama çalışmaya devam eder.
        """
        if self._thread is not None and self._thread.is_alive():
            return

        if not SERIAL_AVAILABLE:
            self._emit_link(
                False,
                "pyserial kurulu değil — cihaz bağlantısı devre dışı. "
                "Kurmak için: pip install pyserial",
            )
            return

        # Her nesil KENDİ durdurma bayrağını alır (clear() DEĞİL, yeni Event):
        # stop() sırasında join zaman aşımına uğrayıp hâlâ yaşayan eski bir
        # thread varsa, paylaşılan bayrağın clear()'lanması onu diriltir ve
        # aynı port üzerinde İKİ okuma döngüsü çalışırdı (tampon bölünmesi,
        # olay kaybı, birleşmiş satırlar, sürekli bağlan/kop salınımı).
        durdurma = threading.Event()
        self._stop_event = durdurma
        self._thread = threading.Thread(
            target=self._run,
            args=(durdurma,),
            name="ExtraKeyboardDeviceLink",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """
        Dinleme thread'ini temiz biçimde durdurur ve portu kapatır.

        Thread'in bitmesi en fazla birkaç yüz milisaniye sürer; ardından
        seri port kapatılır ve bağlantı durumu ``False`` yapılır.
        """
        self._stop_event.set()

        # Bloklanmış okumayı uyandır: pyserial'ın cancel_read'i port.read()
        # içinde bekleyen thread'i hemen döndürür; aksi hâlde join boşuna
        # zaman aşımına uğrar. Desteklemeyen sürücülerde sessizce geçilir.
        acik_port = self._serial
        if acik_port is not None:
            try:
                acik_port.cancel_read()
            except Exception:  # noqa: BLE001 - her sürücüde bulunmaz
                pass

        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(2.0, RECONNECT_DELAY + 1.0))
            if thread.is_alive():
                # Thread hâlâ bloklu (ör. tcdrain/read askıda). Referansı
                # KORUYORUZ: aksi hâlde bir sonraki start() ikinci bir okuma
                # döngüsü açar ve iki döngü aynı port/tampon üzerinde yarışır.
                # Thread uyanınca kendi bayrağı set olduğu için döngüden
                # çıkar; is_alive() False olunca start() yeniden çalışır.
                self._close_port("Bağlantı kapatıldı.")
                return
        self._thread = None
        self._close_port("Bağlantı kapatıldı.")

    # -- durum bilgisi -----------------------------------------------------

    @property
    def connected(self) -> bool:
        """Seri PORT açık mı (port yönetimi için; flap önlemede kullanılır).

        DİKKAT: Bu "cihaz yanıt veriyor" demek DEĞİLDİR — port açık kalsa bile
        cihaz susmuş olabilir. Arayüz göstergesi için :attr:`responsive` kullanın.
        """
        return self._connected

    @property
    def responsive(self) -> bool:
        """Cihaz GERÇEKTEN yanıt veriyor mu: port açık VE son HB/satır taze.

        Arayüz "Bağlı/Bağlı değil" göstergesi bunu kullanır. Port açık tutulup
        (flap yok, kart bozulmaz) ama cihaz :data:`RESPONSIVE_TIMEOUT` boyunca
        susarsa False döner — kullanıcıya yalan "bağlı" gösterilmez. HB tekrar
        gelince port kapatılıp açılmadan yeniden True olur.
        """
        if not self._connected:
            return False
        return (time.monotonic() - self._last_hb) < RESPONSIVE_TIMEOUT

    @property
    def port_name(self) -> str | None:
        """Bağlı olunan portun adı; bağlantı yoksa ``None``."""
        return self._port_name

    @property
    def last_error(self) -> str:
        """En son karşılaşılan bağlantı hatasının Türkçe açıklaması."""
        return self._last_error

    # -- gönderme ----------------------------------------------------------

    def send(self, line: str) -> bool:
        """
        Cihaza tek satırlık bir komut gönderir (spec bölüm 5.2).

        Satır sonu otomatik eklenir. Yazma işlemi bir kilit ile korunur,
        bu sayede birden fazla thread güvenle çağırabilir.

        :param line: ``"CMD PING"`` gibi komut satırı.
        :return: Gönderim başarılıysa ``True``.
        """
        payload = str(line).strip()
        if not payload:
            return False

        with self._write_lock:
            port = self._serial
            if port is None or not self._connected:
                return False
            try:
                # port.flush() BİLEREK KULLANILMAZ. pyserial'da flush() =
                # tcdrain(): çıktının tamamı iletilene kadar ZAMAN AŞIMSIZ
                # bekler (write_timeout onu KAPSAMAZ). send() okuyucu
                # thread'inden çağrıldığı için (her saniye CMD PING), kart tam
                # o sırada tıkanır/resetlenirse okuyucu SONSUZA DEK donuyordu:
                # ne okuyor ne yeniden bağlanıyordu; üstelik _write_lock'u
                # tuttuğu için _close_port() da kilitleniyordu. Kartın TX'i
                # dolup TX bekçisiyle resetleniyor, uygulama ise ölü kalıyordu
                # (2026-09-28 ölçüldü: kart reset=YAZILIM_RST). write() zaten
                # write_timeout ile sınırlıdır; veriyi OS kendisi gönderir.
                port.write((payload + "\n").encode("utf-8", "ignore"))
                return True
            except Exception as exc:  # pyserial çok çeşitli istisna atabilir
                # YAZMA HATASI ARTIK BAĞLANTIYI DÜŞÜRMEZ (kök-neden düzeltmesi):
                # Yerleşik USB CDC'de cihazın RX (host->cihaz) yolu ara sıra
                # birkaç saniye tıkanıyor; o sırada CMD PING yazımı write_timeout'a
                # takılıp istisna atıyor. Eskiden burada _connected=False yapılınca
                # uygulama "koptu" sanıp sürekli bağlan/kop salınımı yapıyordu —
                # OYSA cihaz canlı (HB düzenli geliyor). Gerçek kopmayı okuma tarafı
                # (port.read hatası) ve canlılık zaman aşımı (HB_TIMEOUT) zaten
                # yakalar. Bu yüzden yazma hatasında SADECE komutu atlarız;
                # bağlantı korunur, bir sonraki PING yeniden dener.
                self._last_error = f"Gönderim hatası (yok sayıldı): {exc}"
                return False

    def led_test(self, index: int) -> bool:
        """
        Donanım LED testi (``CMD LED <i> TEST``).

        Cihaz, verilen LED'i durum mantığından **bağımsız** olarak yaklaşık
        900 ms yakar; süre sonunda kendi durumuna döner. Düz (tek renk)
        LED'lerde renk değiştirilemediği için "LED testi" budur.

        :param index: LED numarası 1..3, ``0`` = hepsi.
        :return: Komut gönderildiyse ``True``.
        """
        try:
            led_index = int(index)
        except (TypeError, ValueError):
            return False
        if not 0 <= led_index <= 3:
            return False
        return self.send(f"CMD LED {led_index} TEST")

    def set_led(self, index: int, hex_color: str) -> bool:
        """
        Tek bir durum LED'inin rengini ayarlar (``CMD LED <i> <RRGGBB>``).

        :param index: LED numarası, 1..3.
        :param hex_color: ``"#1E90FF"`` veya ``"1E90FF"`` biçiminde renk.
        :return: Komut gönderildiyse ``True``.
        """
        try:
            led_index = int(index)
        except (TypeError, ValueError):
            return False
        if not 1 <= led_index <= 3:
            return False

        color = str(hex_color).strip()
        if not _HEX_COLOR_RE.match(color):
            return False
        return self.send(f"CMD LED {led_index} {color.lstrip('#').upper()}")

    def set_brightness(self, value: int) -> bool:
        """
        Genel LED parlaklığını ayarlar (``CMD LED BRIGHT <0-255>``).

        :param value: 0..255 aralığına kırpılan parlaklık değeri.
        :return: Komut gönderildiyse ``True``.
        """
        try:
            level = int(value)
        except (TypeError, ValueError):
            return False
        level = max(0, min(255, level))
        return self.send(f"CMD LED BRIGHT {level}")

    def set_os(self, os_key: str) -> bool:
        """
        Cihazın işletim sistemi modunu PC'den zorlar (``CMD OS WIN|MAC``).

        :param os_key: ``"windows"`` veya ``"mac"``.
        :return: Komut gönderildiyse ``True``.
        """
        key = str(os_key).strip().lower()
        if key == "mac":
            return self.send("CMD OS MAC")
        if key == "windows":
            return self.send("CMD OS WIN")
        return False

    def set_encoder_mode(self, mode: str) -> bool:
        """
        Enkoder modunu ayarlar (``CMD ENC MODE HID|HOST``).

        :param mode: ``"hid"`` (cihaz HID ses gönderir) veya ``"host"``
            (kararı PC verir).
        :return: Komut gönderildiyse ``True``.
        """
        value = str(mode).strip().lower()
        if value not in ("hid", "host"):
            return False
        return self.send(f"CMD ENC MODE {value.upper()}")

    def set_hid_fallback(self, enabled: bool) -> bool:
        """
        HID yedek modunu açar/kapatır (``CMD HIDFB ON|OFF``).

        :param enabled: ``True`` ise açılır.
        :return: Komut gönderildiyse ``True``.
        """
        return self.send(f"CMD HIDFB {'ON' if enabled else 'OFF'}")

    def request_id(self) -> bool:
        """Cihazdan kimlik bilgisi ister (``CMD ID``)."""
        return self.send("CMD ID")

    def ping(self) -> bool:
        """Cihaza canlılık testi gönderir (``CMD PING``)."""
        return self.send("CMD PING")

    def save_device_settings(self) -> bool:
        """Cihaz ayarlarının kalıcı belleğe (NVS) yazılmasını ister (``CMD SAVE``)."""
        return self.send("CMD SAVE")

    @property
    def device_os(self) -> str:
        """Cihazın son bildirdiği OS modu (``"windows"`` / ``"mac"``); bilinmiyorsa ``""``."""
        return self._device_os

    def apply_settings_to_device(self, os_key: str | None = None) -> bool:
        """
        Yapılandırmadaki cihaz ayarlarını el sıkışma sırasına göre gönderir.

        Sıra docs/03-PROTOKOL.md bölüm 4.a ile birebir aynıdır::

            CMD LED BRIGHT <parlaklık>
            CMD LED 1 <os_win | os_mac>
            CMD LED 2 <combo>
            CMD LED 3 <link_ok>
            CMD ENC MODE <HID | HOST>

        ``CMD LED`` cihazda ilgili durumun **temel rengini** günceller; durum
        mantığı (combo flaşı, bağlantı rengi) çalışmaya devam eder.

        Bağlantı kurulduktan sonra bir kez çağrılır; böylece cihazın NVS'inde
        duran enkoder modu ile ``config.json`` asla ayrışmaz — ayrışırsa
        enkoder hem cihazda hem PC'de iş yapar (çift eylem).

        :param os_key: Kullanılacak profil (``"windows"`` / ``"mac"``).
            ``None`` verilirse cihazın bildirdiği OS modu kullanılır.
        :return: Tüm komutlar gönderilebildiyse ``True``.
        """
        key = str(os_key or self._device_os or "windows").strip().lower()
        if key not in ("windows", "mac"):
            key = "windows"

        try:
            leds = dict(self._cfg.led_settings())
        except Exception:  # pragma: no cover - savunma amaçlı
            leds = {}

        ok = self.set_brightness(
            int(leds.get("brightness", config_module.DEFAULT_BRIGHTNESS) or 0))

        os_color = leds.get("os_mac" if key == "mac" else "os_win",
                            config_module.COLOR_OS_MAC if key == "mac"
                            else config_module.COLOR_OS_WIN)
        ok = self.set_led(1, str(os_color)) and ok
        ok = self.set_led(2, str(leds.get("combo", config_module.COLOR_COMBO))) and ok
        ok = self.set_led(3, str(leds.get("link_ok", config_module.COLOR_LINK_OK))) and ok

        try:
            mode = str(self._cfg.encoder_mode(key))
        except Exception:  # pragma: no cover - savunma amaçlı
            mode = "hid"
        ok = self.set_encoder_mode(mode) and ok
        return ok

    # -- port bulma --------------------------------------------------------

    @staticmethod
    def find_ports(cfg: ConfigManager | None = None) -> list[str]:
        """
        Cihaza ait olabilecek seri portları öncelik sırasıyla listeler.

        Sıra:

        1. Yapılandırmada ``port`` alanı ``"auto"`` değilse yalnızca o port.
        2. VID/PID eşleşmesi (``0x303A`` / ``0x82E1``).
        3. Ürün dizgesinde ``ExtraKeyboard`` geçen portlar.
        4. Üretici dizgesinde ``BlueDevelopment`` geçen portlar.
        5. Espressif VID'li (``0x303A``) diğer portlar — Arduino IDE ile
           derlenen firmware özel PID/ürün adını AYARLAYAMAZ (TinyUSB,
           ``setup()`` çağrılmadan başlar) ve varsayılan ``0x303A:0x1001``
           kimliğiyle numaralanır. Bu adaylar en sona konur; gerçek cihaz
           olup olmadıklarına zaten ``CMD ID`` el sıkışması karar verir,
           yanıt vermeyen port atlanır.

        :param cfg: Cihaz ayarlarının okunacağı yapılandırma yöneticisi.
            ``None`` verilirse spec'teki varsayılanlar kullanılır.
        :return: Port adlarından oluşan liste (boş olabilir).
        """
        if not SERIAL_AVAILABLE or list_ports is None:
            return []

        device_cfg: dict[str, Any] = {}
        if cfg is not None:
            try:
                device_cfg = dict(cfg.device_settings())
            except Exception:  # pragma: no cover - savunma amaçlı
                device_cfg = {}

        configured_port = str(device_cfg.get("port", "auto") or "auto").strip()
        if configured_port and configured_port.lower() != "auto":
            return [configured_port]

        target_vid = _to_int(device_cfg.get("vid", config_module.DEVICE_VID), 0x303A)
        target_pid = _to_int(device_cfg.get("pid", config_module.DEVICE_PID), 0x82E1)
        product_hint = str(device_cfg.get("product", config_module.DEVICE_PRODUCT) or "")
        # "ExtraKeyboard MK1" -> "extrakeyboard" (ilk kelime yeterlidir)
        product_needle = product_hint.split()[0].lower() if product_hint.split() else "extrakeyboard"
        manufacturer_needle = config_module.DEVICE_MANUFACTURER.lower()

        by_ids: list[str] = []
        by_product: list[str] = []
        by_manufacturer: list[str] = []
        by_vendor: list[str] = []

        try:
            candidates = list(list_ports.comports())
        except Exception:  # pragma: no cover - platform hataları
            return []

        for port_info in candidates:
            device_name = getattr(port_info, "device", None)
            if not device_name:
                continue

            product = str(getattr(port_info, "product", "") or "")
            description = str(getattr(port_info, "description", "") or "")
            serial_no = str(getattr(port_info, "serial_number", "") or "")

            # ROM İNDİRME PORTUNU ASLA ADAY YAPMA.
            # ESP32-S3'ün ROM USB-Serial-JTAG'i, firmware ile AYNI VID:PID'i
            # (0x303A:0x1001) kullanır — ölçüldü: firmware'deki USB_PID=0x82E1
            # ayarı işlemiyor, kart firmware'de de 0x1001 ile numaralanıyor.
            # Bu yüzden VID/PID ayırt edemez; iki güvenilir işaret vardır:
            #   - ürün adı: ROM "USB JTAG/serial debug unit", firmware
            #     "ExtraKeyboard MK1"
            #   - seri no: ROM MAC'i İKİ NOKTALI verir ("A0:85:E3:E7:46:10"),
            #     firmware iki noktasız ("A085E3E74610"). Windows'ta ürün adı
            #     gelmeyebildiği için bu ikinci işaret yedektir.
            # Bu porta bağlanmak ZARARLIDIR: orada DTR/RTS doğrudan EN ve
            # IO0(BOOT) hatlarına bağlıdır; uygulama portu her açtığında kartı
            # yeniden indirme moduna resetler ve kart firmware'e HİÇ dönemez
            # (2026-09-28 ölçüldü: uygulama açıkken kart indirme modunda kaldı,
            # uygulama kapanınca ilk resette firmware'e döndü).
            if ("jtag" in product.lower() or "jtag" in description.lower()
                    or ":" in serial_no):
                continue

            vid = getattr(port_info, "vid", None)
            pid = getattr(port_info, "pid", None)
            if vid == target_vid and pid == target_pid:
                by_ids.append(device_name)
                continue

            if product_needle in product.lower() or product_needle in description.lower():
                by_product.append(device_name)
                continue

            manufacturer = str(getattr(port_info, "manufacturer", "") or "")
            if manufacturer_needle and manufacturer_needle in manufacturer.lower():
                by_manufacturer.append(device_name)
                continue

            # Espressif VID'li ama PID'i farklı port: Arduino IDE derlemesi
            # olabilir (docstring madde 5). El sıkışma dogrulayacagi icin
            # aday listesinin SONUNA eklenir.
            if vid == target_vid:
                by_vendor.append(device_name)

        ordered: list[str] = []
        for group in (by_ids, by_product, by_manufacturer, by_vendor):
            for name in group:
                if name not in ordered:
                    ordered.append(name)
        return ordered

    # -- iç işleyiş --------------------------------------------------------

    def rescan(self) -> str:
        """Bağlantıyı hemen baştan kurmayı dener (kullanıcı isteğiyle).

        Arka plan döngüsü zaten saniyede bir deneme yapar; bu metot beklemeyi
        kesip taramayı ANINDA tetikler ve önceki turda "yanıt vermedi" diye
        işaretlenmiş portları da yeniden aday yapar. Cihaz takılı olduğu hâlde
        bağlanamıyorsa kullanıcının ilk başvuracağı yol budur.

        :return: Kullanıcıya gösterilecek kısa durum metni.
        """
        self._skip_ports.clear()
        if self._serial is not None:
            self._close_port("Yeniden tarama istendi.")
        adaylar = self.find_ports(self._cfg)
        if not adaylar:
            return ("Tarama yapıldı: bilgisayar USB'de hiçbir aday port "
                    "görmüyor. Kabloyu kartın \"USB\" konnektörüne, veri "
                    "kablosuyla ve doğrudan bilgisayara takın.")
        return "Tarama başladı — %d aday port deneniyor…" % len(adaylar)

    def wake_device(self) -> str:
        """Cihaza USB hatlarından yeniden başlatma darbesi gönderir.

        Kabloyu çıkarıp takmanın yazılımsal karşılığıdır. Firmware ``CMD ID``
        ve ``HB`` üretmeyi bırakmışsa (uygulama cihazı takılı gördüğü hâlde
        el sıkışamıyorsa) tek çözüm karta reset attırmaktır.

        ESP32-S3'ün yerleşik USB CDC'sinde reset, RTS hattının yükselip
        DTR'nin düşük tutulmasıyla tetiklenir. 1200 baud'a HİÇ inilmez;
        o hız kartı yükleme moduna (bootloader) sokar ve klavye çalışmaz
        hâle gelirdi.

        :return: Kullanıcıya gösterilecek kısa durum metni.
        """
        if serial is None:
            return "pyserial kurulu değil — cihaz sıfırlanamıyor."

        adaylar = self.find_ports(self._cfg)
        if not adaylar:
            return "Sıfırlanacak cihaz bulunamadı (USB'de aday port yok)."

        hedef = self._port_name or adaylar[0]
        self._close_port("Cihaz yeniden başlatılıyor.")

        try:
            port = serial.Serial()
            port.port = hedef
            port.baudrate = _to_int(
                dict(self._cfg.device_settings()).get("baud", config_module.DEVICE_BAUD),
                config_module.DEVICE_BAUD)
            port.dtr = False      # EN hattı serbest
            port.rts = True       # reset darbesi
            port.open()
            time.sleep(0.12)
            port.rts = False      # karta çalış izni
            time.sleep(0.05)
            port.close()
        except Exception as exc:  # noqa: BLE001 - kullanıcıya anlaşılır mesaj
            return "Cihaz sıfırlanamadı: %s" % exc

        self._skip_ports.clear()
        return ("Cihaza yeniden başlatma darbesi gönderildi (%s). "
                "Birkaç saniye içinde yeniden bağlanmalı." % hedef)

    def _emit(self, event: DeviceEvent) -> None:
        """
        Olayı geri çağrıma iletir; geri çağrımdaki hatalar thread'i öldürmez.

        :param event: İletilecek olay.
        """
        try:
            self._on_event(event)
        except Exception:  # noqa: BLE001 - arayüz hatası bağlantıyı düşürmemeli
            pass

    def _emit_link(self, connected: bool, message: str) -> None:
        """
        Bağlantı durumu olayı üretir (yalnızca durum değiştiğinde).

        :param connected: Yeni bağlantı durumu.
        :param message: Türkçe açıklama.
        """
        if self._last_link_state == connected:
            return
        self._last_link_state = connected
        self._emit(
            DeviceEvent(
                kind="link",
                slot=None,
                raw=message,
                payload={
                    "connected": connected,
                    "port": self._port_name,
                    "message": message,
                },
            )
        )

    def _close_port(self, reason: str) -> None:
        """
        Açık portu kapatır ve bağlantı durumunu günceller.

        :param reason: Bağlantı olayında bildirilecek Türkçe sebep.
        """
        was_connected = self._connected
        with self._write_lock:
            port = self._serial
            self._serial = None
            self._connected = False
        if port is not None:
            # Bekleyen çıktıyı ATIP kapat. macOS'ta tty close() gönderilmemiş
            # veri varsa boşalmasını bekleyebilir; kart resetlenmişse bu veri
            # hiç boşalmaz ve kapatma asılı kalır. reset_output_buffer() =
            # tcflush(TCOFLUSH): beklemez, yalnızca kuyruğu siler.
            try:
                port.reset_output_buffer()
            except Exception:  # noqa: BLE001 - port zaten ölü olabilir
                pass
            try:
                port.close()
            except Exception:  # noqa: BLE001 - kapatma hatası önemsiz
                pass
        self._buffer.clear()
        self._id_seen = False
        self._last_uptime = -1
        self._restart_pending = False
        if was_connected:
            self._emit_link(False, reason)
        self._port_name = None

    def _try_connect(self) -> bool:
        """
        Aday portları sırayla deneyerek bağlantı kurmaya çalışır.

        :return: Bağlantı kurulduysa ``True``.
        """
        if serial is None:
            return False

        device_cfg: dict[str, Any] = {}
        try:
            device_cfg = dict(self._cfg.device_settings())
        except Exception:  # pragma: no cover - savunma amaçlı
            device_cfg = {}
        baud = _to_int(device_cfg.get("baud", config_module.DEVICE_BAUD), config_module.DEVICE_BAUD)

        candidates = self.find_ports(self._cfg)
        if not candidates:
            # Aday port hiç yoksa cihaz işletim sistemine bile görünmüyor
            # demektir; bu, uygulamanın çözebileceği bir durum değildir.
            # Kullanıcıya sırayla bakması gereken yeri söyleriz.
            self._last_error = (
                "Cihaz bulunamadı — bilgisayar kartı USB'de hiç görmüyor. "
                "Sırayla kontrol edin: (1) kablo kartın \"USB\" yazan "
                "konnektöründe mi, (2) kablo VERİ kablosu mu (şarj-only "
                "kablolar görünmez), (3) hub yerine doğrudan bilgisayara "
                "takın, (4) karttaki kırmızı güç LED'i yanıyor mu."
            )
            self._emit_link(False, self._last_error)
            self._skip_ports.clear()
            return False

        # Bir önceki turda CMD ID'yi yanıtlamayan portlar bu tur atlanır.
        skipped = [name for name in candidates if name in self._skip_ports]
        usable = [name for name in candidates if name not in self._skip_ports]
        self._skip_ports.clear()
        if not usable:
            usable = skipped   # başka aday yoksa atlananları yine de dene

        for port_name in usable:
            if self._stop_event.is_set():
                return False
            try:
                # KRİTİK — DTR/RTS sırası:
                # pyserial, ``Serial(port=...)`` ile açarken DTR **ve** RTS
                # hatlarını birlikte yükseltir. ESP32-S3'ün yerleşik USB
                # CDC'sinde bu kombinasyon donanımsal RESET tetikler: cihaz
                # yeniden başlar, USB'den düşer ve "bağlantı yok" görünür.
                # Bu yüzden port önce KAPALI oluşturulur, hatlar güvenli
                # duruma ayarlanır (RTS düşük kalır), sonra açılır.
                # DTR yüksek olmalıdır: firmware bunu "PC uygulaması bağlı"
                # göstergesi olarak okur (spec 5.3, Protocol::hostDtr).
                port = serial.Serial()
                port.port = port_name
                port.baudrate = baud
                port.timeout = READ_TIMEOUT
                # write_timeout = 4 sn: cihazın RX yolu ara sıra ~3 sn tıkanıyor.
                # KISA timeout (0.5) yazmayı BAŞARISIZ yapıyordu; başarısız yazma
                # kartın USB'sini bozup kartı susturuyordu. Yeterince uzun timeout
                # ile yazma tıkanma boyunca BEKLEYİP tamamlanır (başarısız olmaz) —
                # kararlı 60 sn monitör de bloklamalı yazma kullanıyordu. Yazma
                # bittikten sonra okuma döngüsü devam eder; HB toleransı 8 sn.
                port.write_timeout = 4.0
                try:
                    # Hatlar port AÇILMADAN önce nihai değerlerine ayarlanır
                    # ve açıldıktan sonra BİR DAHA DEĞİŞTİRİLMEZ.
                    #   DTR yüksek : firmware "uygulama bağlı" sayar (spec 5.3)
                    #   RTS düşük  : DTR/RTS geçiş kombinasyonu ESP32-S3'te
                    #                donanımsal reset/bootloader tetikler
                    # Açıldıktan sonra DTR'yi değiştirmek (0->1 geçişi bile)
                    # cihazı düşürdüğü ölçüldü; bu yüzden dokunulmaz.
                    port.dtr = True
                    port.rts = False
                except Exception:
                    pass
                port.open()
            except Exception as exc:  # pyserial SerialException ve OSError
                self._last_error = f"'{port_name}' açılamadı: {exc}"
                continue

            try:
                port.reset_input_buffer()
                port.reset_output_buffer()
            except Exception:  # noqa: BLE001 - bazı sürücüler desteklemez
                pass

            with self._write_lock:
                self._serial = port
                self._connected = True
            self._port_name = port_name
            self._buffer.clear()
            self._last_error = ""
            self._id_seen = False
            self._last_uptime = -1
            self._restart_pending = False
            self._last_hb = time.monotonic()

            # El sıkışma (EN İYİ ÇABA): CMD ID gönder, kısa süre ID/HB bekle.
            # BAŞARISIZ OLSA BİLE portu KAPATMA. find_ports zaten VID/PID/ürün
            # ile bu cihazı seçti; el sıkışma anlık takılsa bile portu kapatıp
            # yeniden açmak ESP32-S3'ün yerleşik USB'sini bozup kartı susturuyor
            # (bu, "bağlandı/düştü" salınımının ASIL nedeniydi). Bağlantıyı kabul
            # et; read loop portu TUTAR ve HB geldikçe cihaz kendiliğinden
            # doğrulanır. Port fiziksel kaybolmadıkça (kablo çıkmadıkça) bir daha
            # kapat/aç yapılmaz.
            id_ok = self._handshake(port)

            self._emit_link(True, f"Cihaz bağlandı: {port_name}")
            _olay(f"BAGLANDI {os.path.basename(port_name)} "
                  f"kimlik={'var' if id_ok else 'YOK'}")
            # LED renkleri, parlaklık ve enkoder modunu gönder. Cihaz yanıt
            # verdiyse hemen; sessizse write_timeout ile sınırlı kalır (kart
            # sağlıklıyken <1 ms sürer).
            if id_ok:
                self.apply_settings_to_device()
            return True

        self._emit_link(False, self._last_error or "Cihaz portu açılamadı.")
        return False

    def _handshake(self, port: Any) -> bool:
        """
        ``CMD ID`` gönderip ``ID ...`` yanıtını :data:`ID_TIMEOUT` kadar bekler.

        Bekleme sırasında gelen satırlar normal yoldan ayrıştırılır ve olay
        olarak yayınlanır; hiçbir veri kaybolmaz.

        :param port: Açık seri port nesnesi.
        :return: Kimlik yanıtı alındıysa ``True``.
        """
        self._cihaz_konustu = False
        # CMD ID gönder (EN İYİ ÇABA). Yazma başarısız olsa BİLE el sıkışmayı
        # İPTAL ETME: yerleşik USB CDC'de portu açtıktan hemen sonra host->cihaz
        # (RX) yönü bir an hazır olmayabilir ve CMD ID yazımı write_timeout'a
        # takılabilir. Cihazın HB'si (cihaz->host) ise akmaya devam eder;
        # aşağıdaki döngü bir HB görürse (_cihaz_konustu) bağlantı kabul edilir.
        # ESKİ DAVRANIŞ (return False) HATALIYDI: açılıştan sonraki ilk yazma
        # takıldığında el sıkışma başarısız olup uygulama portu saniyede bir
        # aç/kapa (flap) yapıyordu; bu aç/kapa DTR/RTS geçişleri ESP32-S3'ün
        # yerleşik USB'sini bozup kartı susturuyordu (kısır döngü).
        self.request_id()

        # İstek bir kez kaybolabilir (cihaz o an meşgulse, USB tamponu
        # doluysa). Süre dolmadan bir kez daha sorulur.
        tekrar_soruldu = False

        deadline = time.monotonic() + ID_TIMEOUT
        while not self._id_seen and time.monotonic() < deadline:
            if self._stop_event.is_set():
                return False
            try:
                waiting = 0
                try:
                    waiting = int(port.in_waiting)
                except Exception:  # noqa: BLE001 - bazı sürücülerde yok
                    waiting = 0
                chunk = port.read(waiting if waiting > 0 else 1)
            except Exception as exc:  # SerialException, OSError…
                self._last_error = f"Bağlantı koptu: {exc}"
                return False
            if chunk:
                self._feed(chunk)
            elif not tekrar_soruldu and time.monotonic() > deadline - ID_TIMEOUT / 2:
                tekrar_soruldu = True
                self.request_id()

        if self._id_seen:
            return True

        # KİMLİK GELMEDİ, AMA CİHAZ KONUŞUYOR:
        # Firmware sürekli ``HB`` yayınlar. Kimlik yanıtı kaybolmuş olsa
        # bile bu satırlar geliyorsa karşıda çalışan bir cihaz vardır ve
        # bağlantıyı reddetmek yanlış olur — kullanıcı, cihaz takılı
        # olmasına rağmen "bağlı değil" görür ve kabloyu çıkarıp takmak
        # zorunda kalır. Bağlantı kabul edilir; kimlik arka planda yeniden
        # istenir ve ``ID`` geldiğinde bilgiler kendiliğinden dolar.
        if self._cihaz_konustu:
            self.request_id()
            return True

        return False

    def _feed(self, chunk: bytes) -> None:
        """
        Porttan gelen ham baytları tampona ekler ve tam satırları işler.

        Kısmi satırlar tamponda bekletilir; yalnızca ``\\n`` görüldüğünde
        satır tamamlanmış sayılır. ``\\r`` karakterleri temizlenir.

        :param chunk: Porttan okunan ham baytlar.
        """
        self._buffer.extend(chunk)

        if len(self._buffer) > _MAX_BUFFER_BYTES and self._buffer.find(b"\n") < 0:
            # Satır sonu HİÇ gelmiyorsa çöp veri birikmesin. İçinde tam satır
            # varsa tampon silinmez; aşağıdaki döngü önce onları işler.
            self._buffer.clear()
            return

        while True:
            newline_index = self._buffer.find(b"\n")
            if newline_index < 0:
                break
            raw_line = bytes(self._buffer[:newline_index])
            del self._buffer[: newline_index + 1]

            text = raw_line.decode("utf-8", "replace").replace("\r", "").strip()
            if not text:
                continue
            if text.startswith("DBG"):
                # Cihazın tanılama satırı (örn. "DBG BOOT reset=3(YAZILIM_RST)").
                # Protokol olayı değildir; eskiden sessizce atılıyordu. Kart her
                # resetten sonra nedenini bildirir -> kalıcı günlüğe al.
                _olay(f"cihaz: {text}")
            event = parse_line(text)
            if event is not None:
                self._note_event(event)
                self._emit(event)

        # Tam satırlar işlendikten sonra kalan kısmi satır makul boyutta olmalı.
        if len(self._buffer) > _MAX_BUFFER_BYTES:
            self._buffer.clear()

    def _note_event(self, event: DeviceEvent) -> None:
        """
        Canlılık sayaçlarını günceller (yalnızca arka plan thread'inden).

        * ``HB`` ve ``ID`` satırları "son yaşam belirtisi" zamanını tazeler.
        * ``uptime_ms`` küçülürse cihaz yeniden başlamıştır: kimlik ve tüm
          ayarlar yeniden gönderilecek şekilde işaretlenir.

        :param event: Ayrıştırılmış olay.
        """
        kind = str(getattr(event, "kind", "") or "")
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            payload = {}

        # Ayrıştırılabilen her satır, karşı tarafta ÇALIŞAN bir firmware
        # olduğunu kanıtlar. El sıkışma bunu yedek ölçüt olarak kullanır.
        self._cihaz_konustu = True

        # Sessizlik yüzünden yeniden bağlanıldıysa: toplam kesintiyi kaydet.
        if self._toparlanma_basi is not None:
            _olay(f"TOPARLANDI: veri {time.monotonic() - self._toparlanma_basi:.1f}"
                  f" sn sonra geri geldi")
            self._toparlanma_basi = None

        # CANLILIK — KRİTİK: ayrıştırılabilen HER satır cihazın yaşadığını
        # kanıtlar, yalnızca HB değil. Eskiden yalnızca HB/ID _last_hb'yi
        # tazeliyordu; uygulama saniyede bir CMD PING yollayıp ACK PING alsa
        # BİLE bu ACK canlılık sayılmıyordu. Bu yüzden yerleşik USB CDC'de HB
        # satırı bir an düşünce (TX FIFO anlık dolması, host okumasının kısa
        # takılması) 3 sn içinde bağlantı boş yere "koptu" sanılıp sürekli
        # bağlan/kop salınımı oluyordu — tüm birimlerde. Artık ACK/EV/ERR
        # dahil her satır sayacı tazeler: uygulamanın kendi PING'ine gelen
        # ACK gidiş-dönüşü tek başına bağlantıyı ayakta tutmaya yeter.
        self._last_hb = time.monotonic()

        if kind == "hb":
            self._last_hb = time.monotonic()
            uptime = _to_int(payload.get("uptime_ms", 0), 0)
            if self._last_uptime >= 0 and uptime < self._last_uptime:
                # Sayaç geriye gitti → cihaz yeniden başladı (docs/03 6.3).
                self._restart_pending = True
            self._last_uptime = uptime
        elif kind == "id":
            self._last_hb = time.monotonic()
            self._id_seen = True
            os_value = str(payload.get("os", "") or "").strip().lower()
            if os_value in ("windows", "mac"):
                self._device_os = os_value
        elif kind == "os":
            os_value = str(payload.get("os", "") or "").strip().lower()
            if os_value in ("windows", "mac"):
                self._device_os = os_value

    def _port_present(self) -> bool:
        """Bağlı portun /dev düğümü hâlâ var mı (kablo fiziksel olarak takılı mı).

        Kısa süreli okuma hatalarını (kart ara sıra birkaç sn tıkanır) gerçek
        kopmadan ayırmak için kullanılır.

        DİKKAT — tek başına YETERLİ DEĞİLDİR: kart resetlendiğinde macOS aygıt
        düğümünü AYNI ADLA geri getirir, yani bu fonksiyon True döner ama elimizdeki
        tanıtıcı ÖLÜDÜR. Bu yüzden _run() ayrıca HB sessizliğine bakar ve
        HB_TIMEOUT aşılınca port varken bile yeniden bağlanır. (Eskiden "port
        varsa asla kapatma" kuralı vardı; DTR/RTS->bootloader sorunu firmware'de
        enableReboot(false) ile çözülünce o kural gereksiz ve zararlı hâle geldi.)
        """
        p = self._port_name
        if not p:
            return False
        try:
            return os.path.exists(p)
        except Exception:  # noqa: BLE001 - emin değilsek "var" say (gereksiz kopma yapma)
            return True

    def _run(self, durdurma: threading.Event | None = None) -> None:
        """
        Arka plan thread'inin ana döngüsü.

        :param durdurma: Bu nesle ait durdurma bayrağı (bkz. :meth:`start`).
            Yerelde tutulur ki sonraki bir ``start()`` bu thread'i
            yanlışlıkla diriltemesin.

        Bağlantı yoksa kurmaya çalışır, varsa porttan okur. Her hata
        durumunda port kapatılır ve :data:`RECONNECT_DELAY` kadar beklenip
        yeniden denenir. Ayrıca her turda ``HB`` zaman aşımı denetlenir;
        port açık kalsa bile cihaz susmuşsa bağlantı kopmuş sayılır.
        """
        # Bayrak yerelde tutulur; self._stop_event yeni bir nesle geçebilir.
        if durdurma is None:
            durdurma = self._stop_event

        while not durdurma.is_set():
            if self._serial is None:
                if not self._try_connect():
                    durdurma.wait(RECONNECT_DELAY)
                continue

            port = self._serial
            try:
                waiting = 0
                try:
                    waiting = int(port.in_waiting)
                except Exception:  # noqa: BLE001 - bazı sürücülerde yok
                    waiting = 0
                chunk = port.read(waiting if waiting > 0 else 1)
            except Exception as exc:  # SerialException, OSError, TypeError…
                # GEÇİCİ OKUMA HATASI: port /dev'de HÂLÂ varsa (kablo takılı)
                # bağlantıyı KAPATMA. Kapat/aç döngüsü bu kartların yerleşik
                # USB'sini bozup kartı susturuyor (izolasyon testi: tek bağlantı
                # tutulunca kart 60 sn stabil, hiç susmadı). Sadece kısa bekleyip
                # AYNI port üzerinde devam et. Yalnızca port düğümü KAYBOLDUYSA
                # (kablo çıktı) gerçek kopma say ve kapat.
                #
                # 2026-09-28 DÜZELTMESİ: bu dal eskiden port /dev'de durduğu
                # sürece KOŞULSUZ `continue` ediyordu. Kart resetlenince (TX/
                # loop bekçisi) macOS aygıt düğümünü AYNI ADLA geri getirir;
                # eski tanıtıcıdan okuma sonsuza dek hata verir ve "port var"
                # kontrolü bunu ayırt edemez -> uygulama bir daha ASLA
                # bağlanamıyordu. Artık yalnızca cihaz YAKIN ZAMANDA konuştuysa
                # (HB_TIMEOUT içinde) geçici sayılır; aksi hâlde yeniden bağlanılır.
                sessiz = time.monotonic() - self._last_hb
                if self._port_present() and sessiz <= HB_TIMEOUT:
                    self._last_error = f"Geçici okuma hatası (yok sayıldı): {exc}"
                    durdurma.wait(0.3)
                    continue
                if self._toparlanma_basi is None:
                    self._toparlanma_basi = self._last_hb
                _olay(f"OKUMA HATASI ({sessiz:.1f} sn sessiz, port "
                      f"{'var' if self._port_present() else 'YOK'}): {exc} "
                      f"-> yeniden baglanma")
                self._last_error = f"Bağlantı yenileniyor: {exc}"
                self._close_port(self._last_error)
                durdurma.wait(RECONNECT_DELAY)
                continue

            if chunk:
                self._feed(chunk)
            elif not self._connected and not self._port_present():
                # Bağlantı yalnızca port fiziksel kaybolduysa yenilenir.
                self._close_port(self._last_error or "Bağlantı koptu.")
                durdurma.wait(RECONNECT_DELAY)
                continue

            # Canlılık bildirimi: cihaz DTR'yi göremese bile taze komut
            # görsün diye saniyede bir PING yollanır (bkz. PING_INTERVAL).
            if self._connected:
                simdi = time.monotonic()
                if simdi - self._last_ping_sent >= PING_INTERVAL:
                    self._last_ping_sent = simdi
                    try:
                        self.ping()
                    except Exception:
                        pass

            # Cihaz yeniden başladıysa kimliği ve ayarları yeniden gönder.
            if self._restart_pending and self._connected:
                self._restart_pending = False
                self._id_seen = False
                self.request_id()
                self.apply_settings_to_device()

            # Sessiz kopma denetimi: HB_TIMEOUT boyunca hiçbir satır gelmezse
            # portu KAPATIP YENİDEN AÇ — port /dev'de dursa BİLE.
            #
            # Eskiden "port /dev'de varsa asla kapatma" kuralı vardı; çünkü
            # kapat/aç'taki DTR/RTS geçişleri kartı bootloader'a atıyordu. O
            # sorun firmware'de kökten çözüldü (enableReboot(false)); ayrıca bu
            # uygulama RTS'i hiç yükseltmediği için eski firmware'de de 4 adımlı
            # dizi tamamlanamaz. Buna karşılık o kural, kart resetlenince
            # (düğüm aynı adla geri gelir) uygulamayı ölü tanıtıcıda SONSUZA DEK
            # bekletiyordu. Bu bir flap DEĞİLDİR: en fazla HB_TIMEOUT'ta bir,
            # yalnızca cihaz gerçekten sustuğunda tek bir yeniden bağlanmadır.
            #
            # İKİ KADEME (2026-09-29): önce FAST_REOPEN_SILENCE'ta bir kez hızlı
            # dene (port yerindeyken takılmaların çoğunu anında çözüyor); işe
            # yaramazsa FAST_REOPEN_COOLDOWN boyunca hızlı deneme yapılmaz ve
            # port HB_TIMEOUT kadar açık tutulur -> kartın TX bekçisi çalışabilir.
            if self._connected:
                simdi = time.monotonic()
                sessiz = simdi - self._last_hb
                if (sessiz > FAST_REOPEN_SILENCE
                        and simdi - self._son_hizli_acma >= FAST_REOPEN_COOLDOWN):
                    self._son_hizli_acma = simdi
                    if self._toparlanma_basi is None:
                        self._toparlanma_basi = self._last_hb
                    _olay(f"SESSIZLIK {sessiz:.1f} sn (port "
                          f"{'var' if self._port_present() else 'YOK'}) "
                          f"-> HIZLI yeniden acma")
                    self._last_error = "Cihaz sustu — hızlı yeniden bağlanma."
                    self._close_port(self._last_error)
                    # RECONNECT_DELAY beklenmez: bir sonraki turda hemen açılır.
                elif sessiz > HB_TIMEOUT:
                    if self._toparlanma_basi is None:
                        self._toparlanma_basi = self._last_hb
                    _olay(f"SESSIZLIK {sessiz:.1f} sn (port "
                          f"{'var' if self._port_present() else 'YOK'}) "
                          f"-> normal yeniden baglanma")
                    self._last_error = "Cihaz yanıt vermiyor — yeniden bağlanılıyor."
                    self._close_port(self._last_error)
                    durdurma.wait(RECONNECT_DELAY)

        # Yalnızca hâlâ geçerli nesil isek portu kapat: geç uyanan eski bir
        # thread, yeni neslin açtığı portu kapatmamalı.
        if durdurma is self._stop_event:
            self._close_port("Bağlantı kapatıldı.")
