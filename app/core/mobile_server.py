# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — telefon eşlik sunucusu (yerel HTTP + SSE yayını).

Bu modül, PC uygulamasının cihazdan aldığı olayları yerel ağdaki telefona
canlı olarak yayınlayan küçük bir HTTP sunucusu içerir:

* :class:`Broadcaster` — abone kuyruklarına **asla bloklamadan**
  (``put_nowait``) olay dağıtan yayıncı. Dolu kuyruklar sessizce atlanır;
  yavaş bir telefon, seri okuma thread'ini asla yavaşlatamaz.
* :class:`MobileServer` — ``ThreadingHTTPServer`` tabanlı sunucu.
  Daemon thread'de çalışır; uygulama kapanırken :meth:`MobileServer.stop`
  ile temiz kapanır.

Sunulan uç noktalar:

Tüm uç noktalar oturuma özel gizli jetonun altında sunulur; ``<j>``
:attr:`MobileServer.token` değeridir ve jetonsuz her istek 404 alır:

============================  ================================================
``GET /t/<j>/``               Telefon arayüzü (:data:`app.core.mobile_assets.HTML`)
``GET /t/<j>/manifest.webmanifest``  PWA manifest'i
``GET /t/<j>/sw.js``          Servis işçisi (yalnızca kurulabilirlik)
``GET /t/<j>/icon-192.png``   PIL ile üretilen "EK" ikonu (yoksa 1×1 png)
``GET /t/<j>/icon-512.png``   Aynı ikonun 512'lik hâli
``GET /t/<j>/state``          ``state_provider()`` çıktısı (JSON)
``GET /t/<j>/events``         SSE akışı: ``hello`` + ``state`` + canlı olaylar
============================  ================================================

Sunucu 0.0.0.0'da dinlediği için jeton kapısı zorunludur: aksi hâlde yerel
ağdaki herkes profil adını, tuş etiketlerini ve canlı tuş telemetrisini
okuyabilir. Ayrıca eşzamanlı SSE abonesi :data:`MAX_CLIENTS` ile sınırlıdır.

**Kritik kural:** Yayın yolu hiçbir yerde bloklamaz. Olaylar
:meth:`MobileServer.publish` ile kuyruklara ``put_nowait`` edilir; SSE
yazımı istemcinin kendi handler thread'inde yapılır. Böylece cihaz olayını
üreten seri okuma thread'i asla beklemez (beklerse 3 sn'de bağlantı düşer).

Tek başına deneme::

    python -m app.core.mobile_server
"""

from __future__ import annotations

import io
import ipaddress
import json
import queue
import re
import secrets
import socket
import struct
import sys
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

try:  # paket içinden normal kullanım
    from app.core import mobile_assets
except ImportError:  # doğrudan "python mobile_server.py" çalıştırması
    import mobile_assets  # type: ignore[import-not-found, no-redef]

__all__ = ["Broadcaster", "MobileServer", "DEFAULT_PORT"]

#: Varsayılan sunucu portu (ayarlarda port verilmezse).
DEFAULT_PORT: int = 8756

#: Port doluysa denenecek ek port sayısı (port, port+1, …, port+9).
PORT_ATTEMPTS: int = 10

#: Abone kuyruğu kapasitesi — dolarsa yeni olaylar o istemci için atlanır.
QUEUE_CAPACITY: int = 256

#: Eşzamanlı SSE abonesi (bağlı telefon) üst sınırı. Sınır yokken yerel
#: ağdaki biri binlerce ``/events`` bağlantısı açıp her bağlantı için bir
#: thread + kuyruk yaratabiliyor; ``publish()`` tüm kuyrukları dolaştığı
#: için seri okuma thread'i saniyelerce bloklanıyor ve cihaz kalp atışı
#: (3 sn) zaman aşımına uğrayıp klavye işlevsiz kalıyordu.
MAX_CLIENTS: int = 8

#: Erişim jetonunda kabul edilen karakterler (URL güvenli base64).
_JETON_DESENI = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def _jeton_temizle(ham: Any) -> str:
    """
    Dışarıdan (yapılandırmadan) gelen jetonu doğrular.

    :param ham: Ham jeton değeri.
    :return: Geçerliyse jetonun kendisi, değilse boş dizge.
    """
    aday = str(ham or "").strip()
    return aday if _JETON_DESENI.match(aday) else ""

#: SSE canlılık yorumu (``: hb``) gönderme aralığı (saniye).
SSE_HEARTBEAT: float = 10.0


# ---------------------------------------------------------------------------
# İkon üretimi — modül yüklenirken BİR KEZ yapılır, baytlar önbelleklenir
# ---------------------------------------------------------------------------

def _yedek_png() -> bytes:
    """PIL yokken sunulacak 1×1 piksellik geçerli PNG'yi saf stdlib ile üretir."""
    def _parca(etiket: bytes, veri: bytes) -> bytes:
        govde = etiket + veri
        return (struct.pack(">I", len(veri)) + govde
                + struct.pack(">I", zlib.crc32(govde) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)  # 1×1, RGBA
    idat = zlib.compress(b"\x00" + b"\x3b\x8e\xd0\xff")   # tek piksel: #3B8ED0
    return (b"\x89PNG\r\n\x1a\n"
            + _parca(b"IHDR", ihdr) + _parca(b"IDAT", idat) + _parca(b"IEND", b""))


def _ikon_ciz(boyut: int) -> bytes:
    """
    Yuvarlak köşeli, koyu zeminli, mavi "EK" yazılı uygulama ikonunu üretir.

    :param boyut: Kare ikonun kenar uzunluğu (piksel).
    :return: PNG baytları.
    :raises Exception: PIL kurulu değilse veya çizim başarısız olursa.
    """
    from PIL import Image, ImageDraw, ImageFont  # yerelde: modül yoksa istisna

    resim = Image.new("RGBA", (boyut, boyut), (0, 0, 0, 0))
    cizim = ImageDraw.Draw(resim)
    yaricap = boyut // 5
    cizim.rounded_rectangle(
        (0, 0, boyut - 1, boyut - 1),
        radius=yaricap,
        fill=(26, 26, 26, 255),                 # arka plan #1a1a1a
        outline=(59, 142, 208, 255),            # kenarlık #3B8ED0
        width=max(2, boyut // 48),
    )

    yazi_tipi = None
    for yol in (
        "/System/Library/Fonts/Helvetica.ttc",                       # macOS
        "/System/Library/Fonts/SFNS.ttf",                            # macOS
        "C:/Windows/Fonts/arialbd.ttf",                              # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",      # Linux
    ):
        try:
            yazi_tipi = ImageFont.truetype(yol, size=int(boyut * 0.42))
            break
        except Exception:  # noqa: BLE001 - sıradaki yazı tipi denenir
            continue
    if yazi_tipi is None:
        try:
            yazi_tipi = ImageFont.load_default(size=int(boyut * 0.42))
        except TypeError:  # eski Pillow: size parametresi yok
            yazi_tipi = ImageFont.load_default()

    metin = "EK"
    kutu = cizim.textbbox((0, 0), metin, font=yazi_tipi)
    genislik = kutu[2] - kutu[0]
    yukseklik = kutu[3] - kutu[1]
    cizim.text(
        ((boyut - genislik) / 2 - kutu[0], (boyut - yukseklik) / 2 - kutu[1]),
        metin,
        font=yazi_tipi,
        fill=(59, 142, 208, 255),               # yazı #3B8ED0
    )

    tampon = io.BytesIO()
    resim.save(tampon, format="PNG")
    return tampon.getvalue()


def _ikonlari_uret() -> dict[int, bytes]:
    """192 ve 512 piksellik ikonları üretir; PIL yoksa 1×1 png'ye düşer."""
    yedek = _yedek_png()
    ikonlar: dict[int, bytes] = {}
    for boyut in (192, 512):
        try:
            ikonlar[boyut] = _ikon_ciz(boyut)
        except Exception:  # noqa: BLE001 - PIL yok veya çizim hatası
            ikonlar[boyut] = yedek
    return ikonlar


#: Önbelleklenmiş ikon baytları — modül yüklenirken bir kez üretilir.
_IKONLAR: dict[int, bytes] = _ikonlari_uret()


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def _lan_ip() -> str:
    """
    PC'nin yerel ağdaki IP adresini bulur.

    Önce "UDP connect" hilesi denenir (8.8.8.8'e paket **gönderilmez**,
    yalnızca yönlendirme tablosuna göre çıkış arabiriminin adresi öğrenilir).
    Olmazsa ``gethostbyname`` denenir; o da olmazsa ``127.0.0.1`` döner.

    :return: ``"192.168.1.34"`` gibi nokta ayrımlı IPv4 adresi.
    """
    try:
        soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            soket.connect(("8.8.8.8", 80))
            return str(soket.getsockname()[0])
        finally:
            soket.close()
    except OSError:
        pass
    try:
        adres = socket.gethostbyname(socket.gethostname())
        if adres and not adres.startswith("127."):
            return adres
    except OSError:
        pass
    return "127.0.0.1"


# ---------------------------------------------------------------------------
# Broadcaster
# ---------------------------------------------------------------------------


class Broadcaster:
    """
    Olayları abone kuyruklarına dağıtan, **asla bloklamayan** yayıncı.

    Her SSE istemcisi :meth:`subscribe` ile kendi kuyruğunu alır; sunucu
    :meth:`publish` ile olayı tüm kuyruklara ``put_nowait`` eder. Kuyruğu
    dolu (yavaş) istemciler için olay sessizce atlanır — üretici thread
    hiçbir koşulda beklemez.
    """

    def __init__(self, max_queue: int = QUEUE_CAPACITY,
                 max_clients: int = MAX_CLIENTS) -> None:
        """
        Yayıncıyı kurar.

        :param max_queue: Abone başına kuyruk kapasitesi.
        :param max_clients: Eşzamanlı abone üst sınırı (bkz. :data:`MAX_CLIENTS`).
        """
        self._lock = threading.Lock()
        self._queues: list[queue.Queue] = []
        self._max_queue = int(max_queue)
        self._max_clients = max(1, int(max_clients))

    def subscribe(self) -> queue.Queue | None:
        """
        Yeni bir abone kuyruğu oluşturup kaydeder.

        Üst sınır (:data:`MAX_CLIENTS`) dolmuşsa abonelik VERİLMEZ; çağıran
        istemciye 503 döner. Sınır olmadan yayın yolu abone sayısıyla
        doğrusal yavaşlıyor ve seri okuma thread'ini bloklayabiliyordu.

        :return: Bu aboneye özel :class:`queue.Queue` nesnesi veya sınır
            dolmuşsa ``None``.
        """
        kuyruk: queue.Queue = queue.Queue(maxsize=self._max_queue)
        with self._lock:
            if len(self._queues) >= self._max_clients:
                return None
            self._queues.append(kuyruk)
        return kuyruk

    def unsubscribe(self, kuyruk: queue.Queue) -> None:
        """
        Aboneliği sonlandırır; kuyruk zaten çıkarılmışsa sessizce geçilir.

        :param kuyruk: :meth:`subscribe` ile alınan kuyruk.
        """
        with self._lock:
            try:
                self._queues.remove(kuyruk)
            except ValueError:
                pass

    def publish(self, message: dict) -> None:
        """
        Olayı tüm abonelere dağıtır — **bloklamaz**.

        :param message: JSON'a çevrilebilir olay sözlüğü (``{"kind": ...}``).
        """
        with self._lock:
            hedefler = list(self._queues)
        for kuyruk in hedefler:
            try:
                kuyruk.put_nowait(message)
            except queue.Full:
                pass  # yavaş istemci — bu olay onun için atlanır

    @property
    def client_count(self) -> int:
        """Anlık abone (bağlı telefon) sayısı."""
        with self._lock:
            return len(self._queues)


# ---------------------------------------------------------------------------
# HTTP sunucusu ve istek işleyici
# ---------------------------------------------------------------------------


class _MobileHTTPServer(ThreadingHTTPServer):
    """Sahibine (:class:`MobileServer`) geri bağlantı taşıyan HTTP sunucusu."""

    daemon_threads = True

    # Windows'ta SO_REUSEADDR dolu porta bile bağlanmayı "başarılı" gösterir
    # ve port+1 yedeği hiç devreye girmez; bu yüzden yalnızca POSIX'te açık.
    allow_reuse_address = not sys.platform.startswith("win")

    # GÜVENLİK (uzaktan DoS): eşzamanlı bağlantı (dolayısıyla thread) üst sınırı.
    # ThreadingHTTPServer her TCP bağlantısı için bir thread açar; sınır yoksa
    # ağdaki bir saldırgan binlerce bağlantıyla thread/bellek tükenmesi
    # yaratabilir. Bu sınıra ulaşılınca yeni bağlantı ANINDA kapatılır.
    # Telefon başına birkaç bağlantı (sayfa + SSE + ikonlar) düştüğü için 24,
    # birkaç gerçek telefona rahat yeter; MAX_CLIENTS (8 SSE) zaten üstünde.
    _MAX_ESZAMANLI_BAGLANTI = 24

    def handle_error(self, request: Any, client_address: Any) -> None:
        """
        İstemci kaynaklı hataları susturur (bkz. :meth:`log_message`).

        Aksi hâlde aniden kapanan her bağlantı (telefon uykuya daldı, yerel
        ağdan gelen kaba istek seli) konsola tam bir yığın izi dökerdi.
        """

    def __init__(self, address: tuple[str, int], handler: type, owner: "MobileServer") -> None:
        """
        Sunucuyu kurar ve portu bağlar (bağlanamazsa ``OSError`` fırlatır).

        :param address: ``("0.0.0.0", port)`` biçiminde dinleme adresi.
        :param handler: İstek işleyici sınıfı.
        :param owner: Sahip :class:`MobileServer` örneği.
        """
        self.owner = owner
        self._aktif_baglanti = 0
        self._baglanti_kilidi = threading.Lock()
        super().__init__(address, handler)

    def process_request(self, request: Any, client_address: Any) -> None:
        """Eşzamanlı bağlantı sınırını uygular, sonra normal işleme devreder."""
        with self._baglanti_kilidi:
            if self._aktif_baglanti >= self._MAX_ESZAMANLI_BAGLANTI:
                asiri = True
            else:
                self._aktif_baglanti += 1
                asiri = False
        if asiri:
            # Sınır doldu: yeni bağlantıya thread AÇMADAN soketi hemen kapat.
            # close_request kullanılır (shutdown_request DEĞİL); çünkü bu bağlantı
            # için sayaç HİÇ artmadı, dolayısıyla azaltılmamalı.
            try:
                self.close_request(request)  # type: ignore[attr-defined]
            except Exception:
                try:
                    request.close()
                except Exception:
                    pass
            return
        super().process_request(request, client_address)

    def shutdown_request(self, request: Any) -> None:
        """Bağlantı kapanınca aktif sayaç azaltılır (sınır serbest kalır)."""
        try:
            super().shutdown_request(request)  # type: ignore[misc]
        finally:
            with self._baglanti_kilidi:
                if self._aktif_baglanti > 0:
                    self._aktif_baglanti -= 1


class _MobileRequestHandler(BaseHTTPRequestHandler):
    """Telefon arayüzü uç noktalarını sunan istek işleyici."""

    protocol_version = "HTTP/1.1"
    # GÜVENLİK (bilgi sızıntısı): jetonsuz bir istemciye bile dönen "Server"
    # başlığı, varsayılan olarak "ExtraKeyboardMobil/1.0 Python/3.x.y" derdi —
    # yani hedefte bu uygulamanın açık olduğunu ve TAM Python sürümünü kimlik
    # doğrulaması olmadan ele verirdi. Ad genelleştirilir, Python sürümü
    # (sys_version) tamamen kaldırılır.
    server_version = "srv"
    sys_version = ""

    # Sessizce ölen istemcide (telefon uykuda, Wi-Fi koptu, RST gelmedi)
    # gönderim tamponu dolunca flush() dakikalarca bloklanmasın diye soket
    # zaman aşımı: kalp atışı 10 sn olduğundan 30 sn canlı istemciyi etkilemez.
    timeout = 30

    # -- günlük susturma ----------------------------------------------------

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Konsolu kirletmemek için erişim günlükleri tamamen susturulur."""

    # -- yardımcılar ---------------------------------------------------------

    def _sahip(self) -> "MobileServer | None":
        """Bağlı olunan :class:`MobileServer` örneğini döndürür."""
        return getattr(self.server, "owner", None)

    def _host_yerel_mi(self) -> bool:
        """``Host`` başlığı IP ADRESİ mi (yoksa saldırgan alan adı mı)?

        GÜVENLİK (DNS rebinding): telefon, QR ile verilen doğrudan IP'ye
        bağlanır; yani meşru ``Host`` başlığı her zaman bir IP adresidir
        (``192.168.1.14:8756``) ya da ``localhost``'tur. DNS rebinding saldırısı
        ise kurbanın tarayıcısına, saldırganın kontrolündeki bir ALAN ADINI
        (``kotu.example.com``) kurbanın yerel IP'sine çözdürerek yaptırır;
        bu durumda ``Host`` başlığı bir alan adı olur. Host'un bir IP literali
        (veya localhost) olmasını şart koşmak, jeton kapısına ek olarak bu
        saldırıyı da kapatır — meşru telefonu hiç etkilemeden.

        :return: Host bir IP/localhost ise ``True``; alan adı/boş ise ``False``.
        """
        ham = self.headers.get("Host", "")
        if not ham:
            # HTTP/1.1 Host'u zorunlu kılar; yoksa meşru bir telefon değildir.
            return False
        konak = ham.rsplit(":", 1)[0].strip()
        # IPv6 köşeli parantezleri: [::1]:8756
        if konak.startswith("[") and konak.endswith("]"):
            konak = konak[1:-1]
        if konak.lower() == "localhost":
            return True
        try:
            ipaddress.ip_address(konak)
            return True
        except ValueError:
            return False

    def _gonder(self, veri: bytes, icerik_tipi: str, onbellek: bool = False) -> None:
        """
        Tek parça yanıt gönderir (``Content-Length`` ile, keep-alive uyumlu).

        :param veri: Yanıt gövdesi.
        :param icerik_tipi: ``Content-Type`` başlığı.
        :param onbellek: ``True`` ise istemcinin 1 gün önbelleklemesine izin verilir.
        """
        self.send_response(200)
        self.send_header("Content-Type", icerik_tipi)
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Cache-Control",
                         "public, max-age=86400" if onbellek else "no-store")
        self.end_headers()
        self.wfile.write(veri)

    def _bulunamadi(self) -> None:
        """404 yanıtı gönderir ve bağlantıyı KAPATIR.

        GÜVENLİK (uzaktan DoS): jetonsuz/hatalı istek bu yoldan döner. HTTP/1.1
        keep-alive açıkken bağlantı kapatılmazsa, ağdaki bir saldırgan tek bir
        soketi düzenli 404 istekleriyle süresiz açık tutup handler thread'ini
        rehin alabilir; binlerce soketle thread/bellek tükenmesi yaratabilir.
        Bağlantıyı burada kapatmak, sırrı bilmeyen istemcinin kaynak tutmasını
        engeller.
        """
        veri = "Bulunamadı".encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(veri)
        self.close_connection = True

    def _yonlendir(self, hedef: str) -> None:
        """
        302 yönlendirmesi gönderir.

        :param hedef: ``Location`` başlığına yazılacak adres.
        """
        self.send_response(302)
        self.send_header("Location", hedef)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _mesgul(self) -> None:
        """503 yanıtı gönderir (eşzamanlı telefon sınırı doldu)."""
        veri = "Çok fazla bağlı telefon var.".encode("utf-8")
        self.send_response(503)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Retry-After", "5")
        self.end_headers()
        self.wfile.write(veri)
        # Reddedilen istemci keep-alive ile thread'i meşgul etmesin.
        self.close_connection = True

    # -- ana giriş -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - http.server sözleşmesi
        """Yolu ilgili uç noktaya dağıtır; kopan istemciler sessizce yutulur."""
        try:
            yol = self.path.split("?", 1)[0]

            # GÜVENLİK — DNS rebinding kapısı (jetondan ÖNCE):
            # Host başlığı bir IP/localhost değilse (yani bir alan adıysa) istek
            # reddedilir. Meşru telefon her zaman doğrudan IP'ye bağlanır.
            if not self._host_yerel_mi():
                self._bulunamadi()
                return

            # GÜVENLİK — jeton kapısı:
            # Sunucu 0.0.0.0'da dinlediği için yerel ağdaki herkes istek
            # atabiliyor; jetonsuz hâlde /state profil adını ve tüm tuş
            # etiketlerini, /events ise canlı tuş telemetrisini herkese
            # açıyordu. Bu yüzden TÜM uç noktalar oturuma özel gizli jetonun
            # altında (``/t/<jeton>/...``) sunulur ve jetonsuz her istek 404
            # alır. Jeton sorgu dizesinde değil YOL ÖN EKİNDE taşınır; böylece
            # sayfa içindeki bağıl adresler (state, events, sw.js, ikonlar,
            # manifest) kendiliğinden doğru çözülür ve jeton korumasız hiçbir
            # yanıtta sızmaz.
            sahip = self._sahip()
            jeton = str(getattr(sahip, "token", "") or "")
            parcalar = yol.split("/", 3)
            if not jeton or len(parcalar) < 3 or parcalar[1] != "t":
                self._bulunamadi()
                return
            try:
                jeton_dogru = secrets.compare_digest(parcalar[2], jeton)
            except TypeError:  # ASCII dışı aday jeton
                jeton_dogru = False
            if not jeton_dogru:
                self._bulunamadi()
                return
            if len(parcalar) == 3:
                # "/t/<jeton>" — bağıl adreslerin doğru çözülmesi için
                # sondaki eğik çizgi şart.
                self._yonlendir("/t/" + jeton + "/")
                return
            yol = "/" + parcalar[3]

            if yol in ("/", "/index.html"):
                self._gonder(mobile_assets.HTML.encode("utf-8"),
                             "text/html; charset=utf-8")
            elif yol == "/manifest.webmanifest":
                self._gonder(mobile_assets.MANIFEST.encode("utf-8"),
                             "application/manifest+json; charset=utf-8")
            elif yol == "/sw.js":
                self._gonder(mobile_assets.SW.encode("utf-8"),
                             "text/javascript; charset=utf-8")
            elif yol in ("/icon-192.png", "/favicon.ico"):
                self._gonder(_IKONLAR[192], "image/png", onbellek=True)
            elif yol == "/icon-512.png":
                self._gonder(_IKONLAR[512], "image/png", onbellek=True)
            elif yol == "/state":
                durum = sahip._safe_state() if sahip is not None else {}
                self._gonder(json.dumps(durum, ensure_ascii=False).encode("utf-8"),
                             "application/json; charset=utf-8")
            elif yol == "/events":
                self._olaylari_akit()
            else:
                self._bulunamadi()
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
            # İstemci yanıt ortasında koptu — sessiz temizlik.
            self.close_connection = True

    # -- SSE akışı -----------------------------------------------------------

    def _sse_yaz(self, mesaj: dict) -> None:
        """
        Tek bir SSE veri çerçevesi yazar (``data: {...}\\n\\n``).

        :param mesaj: JSON'a çevrilecek olay sözlüğü.
        """
        veri = json.dumps(mesaj, ensure_ascii=False)
        self.wfile.write(("data: " + veri + "\n\n").encode("utf-8"))

    def _olaylari_akit(self) -> None:
        """
        ``/events`` SSE akışını yürütür.

        Sıra: ``retry`` ipucu → ``hello`` → anlık ``state`` görüntüsü →
        kuyruktan canlı olaylar. Her :data:`SSE_HEARTBEAT` saniyede bir
        ``: hb`` yorum satırı gönderilir ki ara kutular (proxy/NAT)
        bağlantıyı düşürmesin. İstemci kopunca abonelik sessizce silinir.
        """
        sahip = self._sahip()
        if sahip is None:
            self._bulunamadi()
            return

        # Durdurma bayrağının BU nesle ait referansı yerelde tutulur:
        # stop() sonrası yeni bir start() taze Event oluşturduğundan,
        # bloklanıp geç uyanan eski handler yeni event'i görüp dirilemez.
        durdurma = sahip._stop_event

        # Abonelik BAŞLIKLARDAN ÖNCE alınır: sınır (MAX_CLIENTS) dolmuşsa
        # 200 + akış yerine 503 dönebilelim. Sınır olmadan yerel ağdaki biri
        # binlerce /events açıp publish() yolunu (dolayısıyla seri okuma
        # thread'ini) saniyelerce bloklayabiliyordu.
        kuyruk = sahip.broadcaster.subscribe()
        if kuyruk is None:
            self._mesgul()
            return

        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            sahip._sse_kaydet(self.connection)
            self.wfile.write(b"retry: 2000\n\n")
            self._sse_yaz({"kind": "hello"})

            anlik: dict[str, Any] = {"kind": "state"}
            anlik.update(sahip._safe_state())
            self._sse_yaz(anlik)
            self.wfile.flush()

            son_atim = time.monotonic()
            while not durdurma.is_set():
                try:
                    mesaj = kuyruk.get(timeout=1.0)
                except queue.Empty:
                    mesaj = None
                if mesaj is not None:
                    self._sse_yaz(mesaj)
                    self.wfile.flush()
                simdi = time.monotonic()
                if simdi - son_atim >= SSE_HEARTBEAT:
                    self.wfile.write(b": hb\n\n")
                    self.wfile.flush()
                    son_atim = simdi
        except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
            pass  # istemci koptu (broken pipe) — normal durum, sessiz geç
        finally:
            sahip.broadcaster.unsubscribe(kuyruk)
            sahip._sse_sil(self.connection)
            self.close_connection = True


# ---------------------------------------------------------------------------
# MobileServer
# ---------------------------------------------------------------------------


class MobileServer:
    """
    Telefon eşlik sunucusunun yaşam döngüsünü yöneten sınıf.

    Örnek kullanım::

        server = MobileServer(state_provider=durum_uret, port=8756)
        ok, bilgi = server.start()      # bilgi: url veya Türkçe hata
        server.publish({"kind": "key", "number": 1, "edge": "down"})
        server.stop()

    :param state_provider: ``dict`` döndüren fonksiyon; ``/state`` ve SSE
        açılış anlık görüntüsünde kullanılır. **Herhangi bir HTTP
        thread'inden** çağrılabilir; hızlı ve istisnasız olmalıdır
        (istisnalar yutulur, ``{}`` sunulur).
    :param port: İstenen port. ``0`` verilirse boş bir port seçilir;
        doluysa ``port+1``..``port+9`` denenir.
    """

    def __init__(self,
                 state_provider: Callable[[], dict] | None = None,
                 port: int = DEFAULT_PORT,
                 token: str = "") -> None:
        """Sunucuyu kurar; port henüz açılmaz (bkz. :meth:`start`)."""
        self._state_provider = state_provider
        # Erişim jetonu: tüm uç noktalar ``/t/<jeton>/`` altında sunulur.
        # Dışarıdan geçerli bir jeton verilmezse yeni bir tane üretilir.
        # Çağıran :attr:`token` değerini saklarsa QR/adres uygulama yeniden
        # başlasa da değişmez (telefondaki kısayol çalışmaya devam eder).
        self._token: str = _jeton_temizle(token) or secrets.token_urlsafe(24)
        try:
            self._port_request = int(port)
        except (TypeError, ValueError):
            self._port_request = DEFAULT_PORT

        self.broadcaster = Broadcaster()
        self._httpd: _MobileHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        #: Açık SSE bağlantı soketleri — stop() bunları anında kapatabilsin
        #: diye handler'lar kendilerini buraya kaydeder (bkz. _sse_kaydet).
        self._sse_lock = threading.Lock()
        self._sse_sockets: set[socket.socket] = set()
        self._url: str = ""
        self.last_error: str = ""

    # -- durum bilgisi -------------------------------------------------------

    @property
    def url(self) -> str:
        """Sunucunun telefon tarafından açılacak adresi; kapalıysa boş dizge."""
        return self._url

    @property
    def token(self) -> str:
        """Erişim jetonu — adresteki ``/t/<jeton>/`` ön ekinde taşınır."""
        return self._token

    def regenerate_token(self) -> str:
        """Erişim jetonunu yenisiyle değiştirir ve yeni jetonu döndürür.

        GÜVENLİK: jeton bir kez sızarsa (paylaşılan yedek, ekran görüntüsü,
        eski dışa aktarım) o sızıntı süresiz erişim demekti. Bu metot güçlü
        yeni bir jeton (256 bit) üretir; eski jetonla kaydedilmiş telefon
        bağlantıları o an geçersiz olur. Çağıran, yeni değeri yapılandırmaya
        yazıp QR'ı yeniden gösterir. Sunucu çalışıyorken de güvenlidir: URL
        bir sonraki istekte yeni jetona göre çözülür.
        """
        self._token = secrets.token_urlsafe(24)
        # Çalışıyorsa adres yeni jetonla yeniden kurulur; kapalıyken zaten boş.
        if self._httpd is not None:
            try:
                gercek_port = self._httpd.server_address[1]
                self._url = f"http://{_lan_ip()}:{gercek_port}/t/{self._token}/"
            except Exception:
                pass
        return self._token

    @property
    def running(self) -> bool:
        """Sunucu şu anda çalışıyor mu?"""
        return self._httpd is not None

    @property
    def client_count(self) -> int:
        """Anlık bağlı telefon (SSE aboneliği) sayısı."""
        return self.broadcaster.client_count

    # -- yapılandırma ---------------------------------------------------------

    def set_state_provider(self, fn: Callable[[], dict] | None) -> None:
        """
        Durum sağlayıcıyı değiştirir.

        :param fn: ``dict`` döndüren fonksiyon veya ``None``.
        """
        self._state_provider = fn

    def _sse_kaydet(self, baglanti: socket.socket) -> None:
        """
        Açık SSE bağlantı soketini kaydeder.

        :param baglanti: Handler'ın istemci soketi (``self.connection``).
        """
        with self._sse_lock:
            self._sse_sockets.add(baglanti)

    def _sse_sil(self, baglanti: socket.socket) -> None:
        """
        SSE bağlantı kaydını siler; zaten silinmişse sessizce geçilir.

        :param baglanti: :meth:`_sse_kaydet` ile kaydedilen soket.
        """
        with self._sse_lock:
            self._sse_sockets.discard(baglanti)

    def _safe_state(self) -> dict:
        """
        Durum sağlayıcıyı güvenle çağırır; her hatada ``{}`` döner.

        JSON'a çevrilemeyen değerler de ``{}``'e düşürülür — telefon
        arayüzü asla yarım/bozuk veri almaz.
        """
        saglayici = self._state_provider
        if not callable(saglayici):
            return {}
        try:
            durum = saglayici()
        except Exception:  # noqa: BLE001 - sağlayıcı hatası yayını durdurmamalı
            return {}
        if not isinstance(durum, dict):
            return {}
        try:
            json.dumps(durum, ensure_ascii=False)
        except (TypeError, ValueError):
            return {}
        return durum

    # -- yayın ---------------------------------------------------------------

    def publish(self, message: dict) -> None:
        """
        Olayı tüm bağlı telefonlara dağıtır — **asla bloklamaz**.

        Seri okuma thread'inden güvenle çağrılabilir; yalnızca
        ``put_nowait`` yapılır, dolu kuyruklar atlanır.

        :param message: ``{"kind": ..., ...}`` biçiminde olay sözlüğü.
        """
        if not isinstance(message, dict):
            return
        self.broadcaster.publish(message)

    def publish_state(self) -> None:
        """
        Anlık durum görüntüsünü (``kind="state"``) tüm telefonlara gönderir.

        Ayarlar (tuş adı, profil, OS) değiştiğinde entegratör bunu çağırarak
        telefon ekranlarını anında tazeleyebilir.
        """
        anlik: dict[str, Any] = {"kind": "state"}
        anlik.update(self._safe_state())
        self.broadcaster.publish(anlik)

    # -- yaşam döngüsü ---------------------------------------------------------

    def start(self) -> tuple[bool, str]:
        """
        Sunucuyu daemon thread'de başlatır.

        Port doluysa ``port+1``..``port+9`` sırayla denenir; ``port=0``
        verildiyse işletim sistemi boş bir port seçer.

        :return: ``(True, url)`` veya ``(False, Türkçe hata açıklaması)``.
        """
        if self._httpd is not None:
            return True, self._url

        if self._port_request == 0:
            adaylar: list[int] = [0]
        else:
            adaylar = list(range(self._port_request,
                                 self._port_request + PORT_ATTEMPTS))

        son_hata: OSError | None = None
        for aday in adaylar:
            try:
                self._httpd = _MobileHTTPServer(("0.0.0.0", aday),
                                                _MobileRequestHandler, self)
                break
            except OSError as hata:
                son_hata = hata
                continue

        if self._httpd is None:
            if self._port_request == 0:
                self.last_error = f"Sunucu portu açılamadı: {son_hata}"
            else:
                self.last_error = (
                    f"Sunucu portu açılamadı "
                    f"({self._port_request}..{self._port_request + PORT_ATTEMPTS - 1} "
                    f"denendi): {son_hata}")
            return False, self.last_error

        gercek_port = int(self._httpd.server_address[1])
        # Her nesil KENDİ durdurma bayrağını alır (clear() değil, yeni Event):
        # önceki neslin bloklanmış SSE handler'ları eski event'i görmeye devam
        # eder ve sonraki start() onları yanlışlıkla canlandıramaz.
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            kwargs={"poll_interval": 0.5},
            name="ExtraKeyboardMobil",
            daemon=True,
        )
        self._thread.start()

        # Adres jetonu içerir; QR ve "adresi kopyala" bunu doğrudan kullanır.
        self._url = f"http://{_lan_ip()}:{gercek_port}/t/{self._token}/"
        self.last_error = ""
        return True, self._url

    def stop(self) -> None:
        """
        Sunucuyu temiz biçimde kapatır.

        Abonelere veda olayı (``kind="bye"``) gönderilir, SSE döngüleri
        durdurma bayrağıyla uyandırılır, açık SSE soketleri kapatılır
        (bloklanmış handler'lar da anında sonlanır), sunucu kapatılır ve
        dinleyici thread beklenir. Kapalı sunucuda çağrılması zararsızdır.
        """
        self._stop_event.set()
        # Abonelere veda: bekleyen SSE döngüleri hemen uyanıp kapanır.
        self.broadcaster.publish({"kind": "bye"})

        # Açık SSE soketlerini de anında sonlandır: shutdown, ölü bağlantıda
        # (ör. Wi-Fi kopmuş telefon) wfile içinde bloklanan handler'ı OSError
        # ile uyandırır; soketi kapatma işini handler'ın kendisi yapar.
        with self._sse_lock:
            baglantilar = list(self._sse_sockets)
            self._sse_sockets.clear()
        for baglanti in baglantilar:
            try:
                baglanti.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # soket zaten kapanmış olabilir — önemsiz

        httpd = self._httpd
        self._httpd = None
        if httpd is not None:
            try:
                httpd.shutdown()
            except Exception:  # noqa: BLE001 - kapanış hatası önemsiz
                pass
            try:
                httpd.server_close()
            except Exception:  # noqa: BLE001 - kapanış hatası önemsiz
                pass

        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=3.0)

        self._url = ""


# ---------------------------------------------------------------------------
# Tek başına deneme: python -m app.core.mobile_server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    def _ornek_durum() -> dict:
        """Deneme için örnek durum — gerçek uygulamada Application üretir."""
        return {
            "app": "ExtraKeyboard MK1",
            "profile": "Varsayilan",
            "os": "windows",
            "link": False,
            "port": None,
            "combo": False,
            "keys": {f"K{i}": {"name": f"Tuş {i}", "type": "none"}
                     for i in range(1, 11)},
            "encoder": {
                "cw": {"name": "Ses +", "type": "media"},
                "ccw": {"name": "Ses −", "type": "media"},
                "press": {"name": "Sessiz", "type": "media"},
                "long": {"name": "Uzun basış", "type": "none"},
            },
        }

    sunucu = MobileServer(state_provider=_ornek_durum, port=0)
    basarili, bilgi = sunucu.start()
    if not basarili:
        print("Başlatılamadı:", bilgi)
        sys.exit(1)

    print("Telefon eşlik sunucusu çalışıyor:", bilgi)
    print("Sahte olaylar yayınlanıyor…")
    sunucu.publish({"kind": "key", "slot": "K1", "number": 1,
                    "edge": "down", "pressed": True})
    sunucu.publish({"kind": "key", "slot": "K1", "number": 1,
                    "edge": "up", "pressed": False})
    time.sleep(3.0)
    print("Bağlı istemci sayısı:", sunucu.client_count)
    sunucu.stop()
    print("Sunucu kapatıldı.")
