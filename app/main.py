# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Uygulama Kurulumu ve Giriş Noktası.

Bu modül uygulamanın omurgasını kurar:

1. **Tekil örnek kontrolü** — 127.0.0.1:64210 portu kilit olarak kullanılır.
   Uygulama zaten çalışıyorsa yeni süreç, çalışan sürece "pencereni göster"
   sinyali gönderip sessizce kapanır.
2. :class:`app.core.config.ConfigManager` — yapılandırmayı yükler.
3. :class:`app.core.actions.ActionRunner` — eylemleri çalıştırır.
4. :class:`app.core.mobile_server.MobileServer` — telefon eşlik yayınını sunar.
5. :class:`app.core.device.DeviceLink` — seri portu arka plan thread'inde yönetir.
6. :class:`app.ui.main_window.MainWindow` — arayüzü açar.
7. :class:`app.ui.tray.TrayIcon` — varsa sistem tepsisi simgesini başlatır.

**Thread güvenliği:** ``DeviceLink`` olayları arka plan thread'inden gelir ve
önce telefon yayınına (**bloklamayan** ``put_nowait``), ardından
:meth:`MainWindow.push_device_event` metoduna verilir. O metot yalnızca
kuyruğa yazar; arayüze ana thread'de dokunulur. Aynı şekilde tepsi
menüsü geri çağırmaları da ``after(0, ...)`` ile ana thread'e aktarılır.

Cihaz bağlı olmasa bile uygulama açılır ve tüm ayarlar düzenlenebilir.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import traceback

#: Tekil örnek kilidi için kullanılan yerel port (spesifikasyon bölüm 8).
SINGLE_INSTANCE_PORT: int = 64210

#: Çalışan örneğe gönderilen "pencereyi göster" sinyali.
SHOW_SIGNAL: bytes = b"SHOW\n"


class SingleInstanceLock:
    """127.0.0.1 üzerindeki bir portu kilit olarak kullanan tekil örnek koruması.

    Portu bağlayabilen süreç "asıl örnek" olur ve gelen bağlantıları dinler.
    İkinci bir süreç portu bağlayamaz; bunun yerine çalışan örneğe bağlanıp
    :data:`SHOW_SIGNAL` göndererek onun penceresini öne getirir.
    """

    def __init__(self, port: int = SINGLE_INSTANCE_PORT) -> None:
        """Kilidi hazırlar (henüz bağlamaz).

        Args:
            port: Kilit olarak kullanılacak yerel TCP portu.
        """
        self.port = port
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def acquire(self) -> bool:
        """Portu bağlamayı dener.

        Returns:
            Bağlanabildiyse (bu süreç asıl örnek) ``True``, aksi hâlde ``False``.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", self.port))
            sock.listen(5)
        except OSError:
            try:
                sock.close()
            except OSError:
                pass
            return False
        self._socket = sock
        return True

    def signal_existing(self) -> bool:
        """Çalışan örneğe pencereyi gösterme sinyali gönderir.

        Returns:
            Sinyal iletilebildiyse ``True``.
        """
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.5) as client:
                client.sendall(SHOW_SIGNAL)
            return True
        except OSError:
            return False

    def serve(self, on_signal) -> None:
        """Gelen "pencereyi göster" sinyallerini arka planda dinler.

        Args:
            on_signal: Sinyal geldiğinde çağrılacak fonksiyon. **Arka plan
                thread'inden** çağrılır; arayüze doğrudan dokunmamalıdır.
        """
        if self._socket is None or self._running:
            return
        self._running = True

        def loop() -> None:
            while self._running and self._socket is not None:
                try:
                    connection, _address = self._socket.accept()
                except OSError:
                    break
                try:
                    connection.recv(64)
                except OSError:
                    pass
                finally:
                    try:
                        connection.close()
                    except OSError:
                        pass
                try:
                    on_signal()
                except Exception:
                    pass

        self._thread = threading.Thread(target=loop, name="SingleInstance", daemon=True)
        self._thread.start()

    def release(self) -> None:
        """Kilidi bırakır ve dinleyiciyi durdurur."""
        self._running = False
        sock = self._socket
        self._socket = None
        if sock is None:
            return
        try:
            sock.close()
        except OSError:
            pass


class Application:
    """Çekirdek katmanı ile arayüzü birbirine bağlayan uygulama kabuğu."""

    def __init__(self, lock: SingleInstanceLock | None = None) -> None:
        """Yapılandırmayı, cihaz bağlantısını ve pencereyi kurar.

        Args:
            lock: Tekil örnek kilidi (kapanışta serbest bırakılır).
        """
        # İçe aktarmalar burada yapılır ki eksik bağımlılık durumunda
        # kullanıcıya anlaşılır bir Türkçe mesaj gösterilebilsin.
        from app.core.actions import ActionRunner
        from app.core.config import ConfigManager
        from app.core.device import DeviceLink
        from app.ui import theme
        from app.ui.main_window import MainWindow
        from app.ui.tray import TrayIcon

        self._lock = lock
        self._theme = theme

        # 1) Yapılandırma — ConfigManager kurucusu dosyayı zaten yükler,
        #    ikinci bir load() gereksiz disk okuması/yazması demek olurdu.
        self.cfg = ConfigManager()

        # 2) Eylem çalıştırıcı
        self.runner = ActionRunner(self.cfg)

        # 3) Telefon eşlik sunucusu — cihaz olaylarını yerel ağa (SSE) yayınlar.
        #    Kurulamazsa uygulama telefonsuz çalışmaya devam eder; cihaz
        #    bağlantısından ÖNCE oluşturulur ki ilk olaydan itibaren yayın
        #    yapılabilsin. Yayın yolu asla bloklamaz (queue.put_nowait).
        self._combo_active = False
        self.mobile_server = None
        self.mobile_server_url = ""
        try:
            from app.core.mobile_server import MobileServer

            mobile_cfg = self._mobile_settings()
            eski_jeton = str(mobile_cfg.get("token", "") or "")
            self.mobile_server = MobileServer(
                state_provider=self._mobile_state,
                port=mobile_cfg.get("port", 8756),
                token=eski_jeton,
            )
            # Erişim jetonu: sunucu tüm uç noktaları ``/t/<jeton>/`` altında
            # sunar. İlk kullanımda üretilir ve yapılandırmaya yazılır ki
            # QR/adres uygulama yeniden başladığında değişmesin (telefondaki
            # kısayol çalışmaya devam etsin).
            yeni_jeton = str(getattr(self.mobile_server, "token", "") or "")
            if yeni_jeton and yeni_jeton != eski_jeton:
                try:
                    self.cfg.set_mobile_settings(token=yeni_jeton)
                    self.cfg.save()
                except Exception:
                    pass
            # Varsayılan KAPALI: sunucu yerel ağa açıldığı için kullanıcı
            # "Telefon" sekmesinden bilinçli olarak açmalıdır.
            if bool(mobile_cfg.get("enabled", False)):
                started, info = self.mobile_server.start()
                if started:
                    self.mobile_server_url = info
        except Exception:
            self.mobile_server = None

        # 4) Cihaz bağlantısı — olaylar arka plan thread'inden gelir
        self.link = DeviceLink(self.cfg, self._on_device_event)

        # 5) Ana pencere
        self.window = MainWindow(self.cfg, self.link, self.runner)
        self._set_app_icon()

        # Güvenlik: içe aktarılan yapılandırmadaki 'command'/'app' slotları
        # tuşa basılınca kod çalıştırır. ConfigManager bu kanca ile onları
        # kullanıcıya onaylatır (bkz. ConfigManager.import_confirm).
        try:
            self.cfg.import_confirm = self._confirm_risky_import
        except Exception:
            pass

        # Telefon sekmesi sunucuya `getattr(window, "mobile_server", None)`
        # ile erişir (entegrasyon sözleşmesi); varsa set_mobile_server çağrılır.
        self.window.mobile_server = self.mobile_server
        if self.mobile_server is not None and hasattr(self.window, "set_mobile_server"):
            try:
                self.window.set_mobile_server(self.mobile_server)
            except Exception:
                pass

        # 6) Sistem tepsisi (yoksa zarifçe devre dışı)
        self.tray = TrayIcon(self._tray_show, self._tray_quit, theme.APP_NAME)
        self.window.set_tray(self.tray)
        if self.tray.available:
            self.tray.start()

        # 7) Bağlantıyı başlat — cihaz yoksa uygulama yine de çalışır.
        #    ÖNEMLİ: start() burada DOĞRUDAN çağrılmaz. Arka plan thread'i
        #    Tkinter olay döngüsünden önce olay gönderirse `after(0, ...)`
        #    "main thread is not in main loop" hatası verir, olay düşer ve
        #    çağıran thread yaklaşık bir saniye bloke olur. `after(0, ...)`
        #    ile planlanan çağrı, mainloop() başlar başlamaz çalışır.
        self.window.after(0, self._start_link)

        if lock is not None:
            lock.serve(self._on_show_signal)

    def _set_app_icon(self) -> None:
        """Uygulama simgesini ayarlar: Dock/görev çubuğunda Python roketi
        yerine ExtraKeyboard'un "EK" simgesi görünür.

        Simge PNG'si başlatıcının çalıştırdığı ``tools/kisayol_olustur.py``
        tarafından ``varliklar/simge-1024.png`` olarak üretilir; dosya yoksa
        sessizce vazgeçilir (uygulama simgesiz de sorunsuz çalışır).
        """
        try:
            from app.core import platform_utils
            yol = os.path.join(str(platform_utils.project_root()),
                               "varliklar", "simge-1024.png")
        except Exception:
            return
        if not os.path.exists(yol):
            return

        # Pencere/görev çubuğu simgesi (tüm platformlar; Windows'ta görev
        # çubuğunu, macOS'ta pencere temsilini etkiler).
        try:
            import tkinter as tk
            self._app_icon_photo = tk.PhotoImage(file=yol)  # referans şart
            self.window.iconphoto(True, self._app_icon_photo)
        except Exception:
            pass

        # macOS Dock simgesi (AppKit üzerinden; pyobjc pyautogui ile gelir).
        if sys.platform == "darwin":
            try:
                from AppKit import NSApplication, NSImage
                img = NSImage.alloc().initWithContentsOfFile_(yol)
                if img:
                    NSApplication.sharedApplication().setApplicationIconImage_(img)
            except Exception:
                pass

    def _confirm_risky_import(self, riskli: list) -> bool:
        """İçe aktarılan dosyadaki komut/uygulama slotlarını onaya sunar.

        **Ana thread'den** çağrılır (Ayarlar > İçe Aktar düğmesi). Kullanıcı
        onaylamazsa :meth:`ConfigManager.import_from` mevcut ayarları
        değiştirmeden geri döner.

        Args:
            riskli: :func:`app.core.config.find_risky_actions` çıktısı.

        Returns:
            Kullanıcı "Evet" derse ``True``.
        """
        from tkinter import messagebox

        satirlar = []
        for kayit in riskli[:8]:
            deger = str(kayit.get("value", "") or "")
            if len(deger) > 90:
                deger = deger[:90] + "…"
            ad = str(kayit.get("slot_name") or kayit.get("slot") or "?")
            satirlar.append(f"• [{kayit.get('os', '')}] {ad} — "
                            f"{kayit.get('type', '')}: {deger}")
        if len(riskli) > 8:
            satirlar.append(f"… ve {len(riskli) - 8} slot daha")

        mesaj = (
            f"Bu dosya, tuşa basıldığında KOMUT ÇALIŞTIRAN {len(riskli)} slot "
            f"içeriyor.\nKomutlar sizin kullanıcı hesabınızda, pencere "
            f"açılmadan çalışır.\nDosyanın kaynağına güvenmiyorsanız İÇE "
            f"AKTARMAYIN.\n\n"
            + "\n".join(satirlar)
            + "\n\nYine de içe aktarılsın mı?"
        )
        try:
            return bool(messagebox.askyesno(
                "Güvenlik Uyarısı — İçe Aktarma", mesaj,
                icon="warning", default="no", parent=self.window))
        except Exception:
            return False

    def _start_link(self) -> None:
        """Cihaz bağlantısını başlatır (mainloop çalışmaya başladıktan sonra)."""
        try:
            self.link.start()
        except Exception as error:
            self.window.set_status(f"Cihaz bağlantısı başlatılamadı: {error}",
                                   self._theme.COLOR_DANGER)

    # ------------------------------------------------------------------
    # Telefon eşlik sunucusu yardımcıları
    # ------------------------------------------------------------------

    def _mobile_settings(self) -> dict:
        """Telefon sunucusu ayarlarını yapılandırmadan savunmacı biçimde okur.

        ``ConfigManager.get_mobile_settings`` henüz yoksa (eski yapılandırma
        katmanı) spec'teki varsayılanlara düşülür.

        Returns:
            ``{"enabled": bool, "port": int, "token": str}`` sözlüğü.
        """
        getter = getattr(self.cfg, "get_mobile_settings", None)
        if callable(getter):
            try:
                settings = getter()
                if isinstance(settings, dict):
                    return settings
            except Exception:
                pass
        # Yedek yol da KAPALI başlar: sunucu 0.0.0.0'da dinlediği için
        # kullanıcının haberi olmadan açılmamalıdır.
        return {"enabled": False, "port": 8756, "token": ""}

    def _mobile_state(self) -> dict:
        """Telefon arayüzüne sunulacak anlık durumu üretir.

        **HTTP thread'lerinden çağrılır**; yalnızca okuma yapar, Tkinter'a
        dokunmaz ve hiçbir koşulda istisna sızdırmaz (hatada ``{}`` döner).

        Returns:
            ``/state`` sözleşmesine uygun sözlük::

                {
                  "app":    "ExtraKeyboard MK1",
                  "profile": "Varsayilan",          # etkin profil adı
                  "os":     "windows" | "mac",      # cihazın son bildirdiği mod
                  "link":   bool,                   # cihaz bağlı mı
                  "port":   "COM5" | None,          # bağlı seri port
                  "combo":  bool,                   # combo modu etkin mi
                  "keys":   {"K1": {"name": str, "type": str}, ...},
                  "encoder": {"cw"|"ccw"|"press"|"long": {"name", "type"}}
                }
        """
        try:
            link = getattr(self, "link", None)
            connected = bool(getattr(link, "connected", False))
            os_key = str(getattr(link, "device_os", "") or "").strip().lower()
            if os_key not in ("windows", "mac"):
                os_key = "windows"

            keys: dict = {}
            encoder: dict = {}
            try:
                section = self.cfg.profile(os_key)
                raw_keys = section.get("keys")
                if isinstance(raw_keys, dict):
                    for slot_id, action in raw_keys.items():
                        if isinstance(action, dict):
                            keys[str(slot_id)] = {
                                "name": str(action.get("name", "") or slot_id),
                                "type": str(action.get("type", "none") or "none"),
                            }
                raw_encoder = section.get("encoder")
                if isinstance(raw_encoder, dict):
                    for slot_id in ("cw", "ccw", "press", "long"):
                        action = raw_encoder.get(slot_id)
                        if isinstance(action, dict):
                            encoder[slot_id] = {
                                "name": str(action.get("name", "") or slot_id),
                                "type": str(action.get("type", "none") or "none"),
                            }
            except Exception:
                pass

            profile_name = ""
            try:
                profile_name = str(self.cfg.active_profile_name())
            except Exception:
                pass

            return {
                "app": "ExtraKeyboard MK1",
                "profile": profile_name,
                "os": os_key,
                "link": connected,
                "port": getattr(link, "port_name", None),
                "combo": bool(getattr(self, "_combo_active", False)),
                "keys": keys,
                "encoder": encoder,
            }
        except Exception:
            return {}

    def _publish_mobile_event(self, event) -> None:
        """Cihaz olayını telefon yayınına iletir. **Arka plan thread'inden.**

        Olay ``{"kind": ..., "slot": ..., **payload}`` biçiminde düzleştirilir;
        payload anahtarları :func:`app.core.device.parse_line` çıktısıyla
        birebir aynıdır. :meth:`MobileServer.publish` yalnızca
        ``queue.put_nowait`` yapar — seri okuma thread'i asla bloklanmaz.
        """
        kind = str(getattr(event, "kind", "") or "")
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            payload = {}

        # Combo modunu izle: /state anlık görüntüsü doğru "combo" bildirsin.
        if kind == "mode":
            self._combo_active = bool(payload.get("combo", False))

        server = self.mobile_server
        if server is None:
            return
        message = {"kind": kind}
        slot = getattr(event, "slot", None)
        if slot:
            message["slot"] = str(slot)
        message.update(payload)
        server.publish(message)

    # ------------------------------------------------------------------
    # Geri çağırmalar (hepsi arka plan thread'inden gelebilir)
    # ------------------------------------------------------------------

    def _on_device_event(self, event) -> None:
        """Cihaz olayını dağıtır. **Arka plan thread'inden çağrılır.**

        Fan-out sırası: önce telefon yayınına (bloklamayan ``put_nowait``),
        sonra pencereye. :meth:`MainWindow.push_device_event` yalnızca
        kuyruğa yazıp ``after(0, ...)`` çağırdığı için burada Tkinter'a
        dokunulmaz. Yayın hatası pencere iletimini engellemez (ve tersi).
        """
        try:
            self._publish_mobile_event(event)
        except Exception:
            pass
        try:
            self.window.push_device_event(event)
        except Exception:
            pass

    def _on_show_signal(self) -> None:
        """İkinci bir örnek başlatıldığında pencereyi öne getirir."""
        try:
            self.window.after(0, self.window.show_window)
        except Exception:
            pass

    def _tray_show(self) -> None:
        """Tepsi menüsündeki "Ayarları Göster" seçeneğini ana thread'e aktarır."""
        try:
            self.window.after(0, self.window.show_window)
        except Exception:
            pass

    def _tray_quit(self) -> None:
        """Tepsi menüsündeki "Çıkış" seçeneğini ana thread'e aktarır."""
        try:
            self.window.after(0, self.window.quit_app)
        except Exception:
            pass

    # ------------------------------------------------------------------

    def run(self) -> int:
        """Tkinter olay döngüsünü çalıştırır ve kapanışta kaynakları bırakır.

        Returns:
            Süreç çıkış kodu (``0`` = normal kapanış).
        """
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
        return 0

    def shutdown(self) -> None:
        """Telefon sunucusunu, cihaz bağlantısını, tepsiyi ve kilidi kapatır."""
        for closer in (
            # Önce telefon sunucusu: abonelere veda olayı gidebilsin.
            getattr(self.mobile_server, "stop", None) if self.mobile_server is not None else None,
            getattr(self.link, "stop", None),
            getattr(self.tray, "stop", None),
            getattr(self._lock, "release", None) if self._lock is not None else None,
        ):
            if closer is None:
                continue
            try:
                closer()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    """Uygulamayı başlatır.

    Args:
        argv: Komut satırı argümanları (şu an kullanılmıyor, ileriye dönük).

    Returns:
        Süreç çıkış kodu.
    """
    _ = argv  # şimdilik kullanılmıyor

    lock = SingleInstanceLock(SINGLE_INSTANCE_PORT)
    if not lock.acquire():
        if lock.signal_existing():
            print("ExtraKeyboard MK1 zaten çalışıyor — mevcut pencere öne getirildi.")
        else:
            print(f"ExtraKeyboard MK1 zaten çalışıyor "
                  f"(port {SINGLE_INSTANCE_PORT} kullanımda).")
        return 0

    try:
        application = Application(lock)
    except ImportError as error:
        lock.release()
        print("Uygulama başlatılamadı — eksik bağımlılık:", error, file=sys.stderr)
        print("Gerekli paketleri kurmak için:", file=sys.stderr)
        print("    pip install customtkinter pyserial pyautogui pystray pillow",
              file=sys.stderr)
        return 2
    except Exception as error:
        lock.release()
        print("Uygulama başlatılamadı:", error, file=sys.stderr)
        traceback.print_exc()
        return 1

    return application.run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
