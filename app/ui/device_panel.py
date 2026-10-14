# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — LED ve Cihaz Paneli.

Bu panel cihazla ilgili her şeyi tek yerde toplar:

* Genel LED parlaklığı (0–255) — standartta görünen tek LED ayarı
* Gelişmiş LED renkleri (katlanabilir, varsayılan KAPALI; yalnızca
  adreslenebilir WS2812B LED'li kartlar için anlamlıdır)
* Enkoder modu (``HID`` / ``HOST``)
* Seri port listesi, yenileme ve bağlanma
* Bağlantı durumu göstergesi
* Son 200 olayın canlı logu
* LED yakıp söndürme ve bağlantı testi butonları

Cihaz bağlı olmasa bile panel tamamen kullanılabilir; renk ve parlaklık
ayarları yapılandırmaya yazılır, cihaz bağlanınca uygulanır.
"""

from __future__ import annotations

import time
from typing import Callable

import customtkinter as ctk
from tkinter import colorchooser

from app.ui import theme


class ColorRow(ctk.CTkFrame):
    """Tek bir LED rengini seçmeye yarayan satır.

    Renk önizleme kutusu, hazır palet düğmeleri, hex giriş kutusu ve
    işletim sisteminin renk seçicisini açan bir buton içerir.
    """

    def __init__(self, master, title: str, description: str, color: str,
                 on_change: Callable[[str], None], **kwargs) -> None:
        """Renk satırını oluşturur.

        Args:
            master: Üst bileşen.
            title: Satır başlığı, örn. ``"Windows modu"``.
            description: Küçük açıklama metni.
            color: Başlangıç rengi (``#RRGGBB``).
            on_change: Renk değişince ``#RRGGBB`` ile çağrılacak geri çağırma.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._on_change = on_change
        self._color = theme.normalize_hex(color)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x")

        self._swatch = ctk.CTkFrame(head, width=30, height=30, corner_radius=8,
                                    fg_color=self._color, border_width=1,
                                    border_color=theme.COLOR_BORDER)
        self._swatch.pack(side="left")
        self._swatch.pack_propagate(False)

        text_wrap = ctk.CTkFrame(head, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True, padx=(theme.PAD_S, 0))
        ctk.CTkLabel(text_wrap, text=title, font=theme.font(12, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(text_wrap, text=description, font=theme.font(10),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(fill="x")

        self._entry = ctk.CTkEntry(head, width=98, height=30,
                                   corner_radius=theme.RADIUS_SMALL,
                                   fg_color=theme.COLOR_FIELD, placeholder_text_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT,
                                   border_color=theme.COLOR_BORDER,
                                   font=theme.mono(12))
        self._entry.insert(0, self._color)
        self._entry.pack(side="left", padx=(theme.PAD_S, 0))
        self._entry.bind("<Return>", self._apply_entry)
        self._entry.bind("<FocusOut>", self._apply_entry)

        ctk.CTkButton(head, text="Seç…", width=56, height=30,
                      corner_radius=theme.RADIUS_SMALL,
                      fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_ACCENT,
                      font=theme.font(11, True), command=self._open_chooser
                      ).pack(side="left", padx=(theme.PAD_XS, 0))

        palette = ctk.CTkFrame(self, fg_color="transparent")
        palette.pack(fill="x", pady=(theme.PAD_XS, 0))
        for preset in theme.LED_PALETTE:
            ctk.CTkButton(
                palette, text="", width=22, height=22,
                corner_radius=6, fg_color=preset, hover_color=preset,
                border_width=1, border_color=theme.COLOR_BORDER,
                command=lambda value=preset: self.set_color(value, notify=True)
            ).pack(side="left", padx=2)

    # ------------------------------------------------------------------

    def get_color(self) -> str:
        """Seçili rengi ``#RRGGBB`` biçiminde döndürür."""
        return self._color

    def set_color(self, value: str, notify: bool = False) -> None:
        """Rengi ayarlar ve isteğe bağlı olarak geri çağırmayı tetikler."""
        self._color = theme.normalize_hex(value, self._color)
        try:
            self._swatch.configure(fg_color=self._color)
            self._entry.delete(0, "end")
            self._entry.insert(0, self._color)
        except Exception:
            pass
        if notify:
            try:
                self._on_change(self._color)
            except Exception:
                pass

    def _apply_entry(self, _event=None) -> None:
        """Hex giriş kutusundaki değeri doğrular ve uygular."""
        self.set_color(self._entry.get(), notify=True)

    def _open_chooser(self) -> None:
        """İşletim sisteminin renk seçici penceresini açar."""
        try:
            chosen = colorchooser.askcolor(color=self._color,
                                           parent=self.winfo_toplevel(),
                                           title="Renk Seç")
        except Exception:
            chosen = (None, None)
        if chosen and chosen[1]:
            self.set_color(chosen[1], notify=True)


class DevicePanel(ctk.CTkFrame):
    """LED ayarları, port yönetimi, cihaz testleri ve canlı olay logu paneli."""

    def __init__(self, master, cfg, link,
                 get_os_key: Callable[[], str] | None = None,
                 on_status: Callable[[str, str], None] | None = None,
                 on_encoder_mode: Callable[[str], None] | None = None,
                 on_dirty: Callable[[], None] | None = None,
                 **kwargs) -> None:
        """Paneli kurar.

        Args:
            master: Üst bileşen.
            cfg: :class:`app.core.config.ConfigManager` örneği.
            link: :class:`app.core.device.DeviceLink` örneği.
            get_os_key: Aktif profili döndüren fonksiyon (``"windows"``/``"mac"``).
            on_status: Üst çubuğa mesaj yazmak için ``(metin, renk)`` geri çağırması.
            on_encoder_mode: Enkoder modu değişince ``"hid"``/``"host"`` ile çağrılır.
            on_dirty: Bu paneldeki bir ayar değişince çağrılır; üst pencere
                otomatik kaydı bu geri çağırma ile tetikler. Bağlanmazsa
                parlaklık/LED/enkoder değişiklikleri diske YAZILMAZ.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._cfg = cfg
        self._link = link
        self._get_os_key = get_os_key or (lambda: "windows")
        self._on_status = on_status or (lambda _text, _color: None)
        self._on_encoder_mode = on_encoder_mode or (lambda _mode: None)
        self._on_dirty = on_dirty or (lambda: None)
        self._mode_guard = False
        self._brightness_job: str | None = None
        self._manuel_ping_bekliyor: bool = False
        self._event_count = 0

        self.grid_columnconfigure(0, weight=3, uniform="devcol")
        self.grid_columnconfigure(1, weight=2, uniform="devcol")
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, theme.PAD_S))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_brightness_section(left)
        self._build_led_section(left)
        self._build_encoder_section(left)
        self._build_test_section(left)

        self._build_connection_section(right)
        self._build_port_section(right)
        self._build_log_section(right)

        # Seri port taraması yalnızca burada (bir kez) ve "Portları Yenile"
        # düğmesinde yapılır; refresh() her çağrıldığında yapılmaz.
        current_port = self._device_settings().get("port", "auto") or "auto"
        self.refresh_ports(select=current_port)
        self.refresh()

    # ------------------------------------------------------------------
    # Bölüm kurulumları
    # ------------------------------------------------------------------

    def _build_led_section(self, parent) -> None:
        """Gelişmiş LED renk ayarlarını KATLANABİLİR bir bölümde sunar.

        Bu üründe 3 adet DÜZ (tek renk) LED vardır; renkleri fiziksel
        olarak değiştirilemez. Bu yüzden renk seçicileri varsayılan olarak
        GİZLİDİR — yalnızca adreslenebilir (WS2812B) LED takılı kartlar
        için, başlığa tıklanarak açılır. Standart kullanımda görünen tek
        LED ayarı parlaklıktır.
        """
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.pack(fill="x", pady=(0, theme.PAD_M))

        # Bu bölümün görünürlüğü AYARLAR → Davranış içindeki
        # "Gelişmiş LED renk ayarlarını göster" anahtarıyla yönetilir
        # (set_color_section_visible). Varsayılan: gizli.
        self._led_adv_box = box
        ctk.CTkLabel(box, text="Gelişmiş LED renk ayarları",
                     font=theme.font(15, True), text_color=theme.COLOR_TEXT,
                     anchor="w").pack(fill="x", padx=theme.PAD_M,
                                      pady=(theme.PAD_M, 0))
        ctk.CTkLabel(
            box,
            text=("Bu üründeki 3 LED düz (tek renk) olduğu için renkleri "
                  "fiziksel olarak değişmez; aşağıdaki seçimler yalnızca "
                  "adreslenebilir (WS2812B) LED takılı kartlarda etkilidir. "
                  "Arayüz göstergeleri ise her durumda bu renkleri kullanır."),
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            anchor="w", justify="left", wraplength=700).pack(
            fill="x", padx=theme.PAD_M, pady=(2, theme.PAD_S))

        leds = self._led_settings()
        self._color_rows: dict[str, ColorRow] = {}

        definitions = (
            ("LED1 — OS Göstergesi", (
                ("os_win", "Windows modu", "OS = Windows iken yanan renk", theme.LED_OS_WIN),
                ("os_mac", "macOS modu", "OS = macOS iken yanan renk", theme.LED_OS_MAC),
            )),
            ("LED2 — Combo Göstergesi", (
                ("combo", "Combo modu açık", "K10 ile mod kilitliyken yanan renk", theme.LED_COMBO),
            )),
            ("LED3 — Bağlantı Göstergesi", (
                ("link_ok", "Uygulama bağlı", "PC uygulaması bağlıyken yanan renk", theme.LED_LINK_OK),
                ("link_err", "Bağlantı yok", "HID yedek modunda yanan renk", theme.LED_LINK_ERR),
            )),
        )

        for group_title, rows in definitions:
            group = ctk.CTkFrame(box, corner_radius=theme.RADIUS_SMALL,
                                 fg_color=theme.COLOR_PANEL)
            group.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
            ctk.CTkLabel(group, text=group_title, font=theme.font(12, True),
                         text_color=theme.COLOR_ACCENT, anchor="w").pack(
                fill="x", padx=theme.PAD_S, pady=(theme.PAD_S, theme.PAD_XS))
            for key, title, description, fallback in rows:
                row = ColorRow(group, title, description,
                               leds.get(key, fallback),
                               lambda value, k=key: self._on_color_changed(k, value))
                row.pack(fill="x", padx=theme.PAD_S, pady=(0, theme.PAD_S))
                self._color_rows[key] = row

        # Başlangıç görünürlüğü yapılandırmadan (varsayılan: gizli).
        goster = False
        try:
            goster = bool(self._cfg.ui_settings().get("show_led_colors", False))
        except Exception:
            goster = False
        self.set_color_section_visible(goster)

    # ------------------------------------------------------------------
    #  Yapılandırma / durum yardımcıları
    # ------------------------------------------------------------------

    def _led_settings(self) -> dict:
        """LED ayarları bölümünü (canlı referans) döndürür."""
        try:
            return self._cfg.led_settings()
        except Exception:
            return {}

    def _device_settings(self) -> dict:
        """Cihaz ayarları bölümünü (canlı referans) döndürür."""
        try:
            return self._cfg.device_settings()
        except Exception:
            return {}

    def _current_os_key(self) -> str:
        """Aktif profil anahtarını döndürür (``"windows"`` / ``"mac"``)."""
        try:
            value = str(self._get_os_key() or "windows").strip().lower()
        except Exception:
            return "windows"
        return "mac" if value.startswith("mac") else "windows"

    def _is_connected(self) -> bool:
        """Cihaz şu an bağlı mı?"""
        try:
            return bool(getattr(self._link, "connected", False))
        except Exception:
            return False

    def _port_name(self) -> str | None:
        """Bağlı olunan seri portun adı (yoksa ``None``)."""
        try:
            return getattr(self._link, "port_name", None)
        except Exception:
            return None

    def set_color_section_visible(self, visible: bool) -> None:
        """Gelişmiş LED renk bölümünü gösterir veya gizler.

        Ayarlar → Davranış içindeki anahtar tarafından çağrılır; panel
        kurulurken de yapılandırmadaki değere göre bir kez uygulanır.
        """
        box = getattr(self, "_led_adv_box", None)
        if box is None:
            return
        try:
            if visible:
                box.pack(fill="x", pady=(0, theme.PAD_M))
            else:
                box.pack_forget()
        except Exception:
            pass

    def _build_brightness_section(self, parent) -> None:
        """Genel parlaklık kaydırıcısını oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.pack(fill="x", pady=(0, theme.PAD_M))

        head = ctk.CTkFrame(box, fg_color="transparent")
        head.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, 0))
        ctk.CTkLabel(head, text="Durum LED'leri — Parlaklık",
                     font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT).pack(side="left")
        self._brightness_label = ctk.CTkLabel(
            head, text=str(theme.LED_DEFAULT_BRIGHTNESS), font=theme.mono(14, True),
            text_color=theme.COLOR_ACCENT)
        self._brightness_label.pack(side="right")

        self._brightness_slider = ctk.CTkSlider(
            box, from_=0, to=255, number_of_steps=255,
            command=self._on_brightness_moved,
            progress_color=theme.COLOR_ACCENT, button_color=theme.COLOR_ACCENT,
            button_hover_color=theme.COLOR_ACCENT_DARK, fg_color=theme.COLOR_FIELD)
        self._brightness_slider.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_S, 0))

        ctk.CTkLabel(box, text="0 = sönük, 255 = tam parlaklık. Önerilen değer 60.",
                     font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w").pack(fill="x", padx=theme.PAD_M,
                                      pady=(theme.PAD_XS, 0))
        ctk.CTkLabel(
            box,
            text=("LED1 Windows modunda, LED2 macOS modunda yanar (uygulama "
                  "bağlı değilken yavaş yanıp söner); LED3 combo modunu "
                  "gösterir, combo tetiklenince çift flaş yapar."),
            font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED,
            anchor="w", justify="left", wraplength=700).pack(
            fill="x", padx=theme.PAD_M, pady=(theme.PAD_XS, theme.PAD_M))

    def _build_encoder_section(self, parent) -> None:
        """Enkoder modu seçicisini oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.pack(fill="x", pady=(0, theme.PAD_M))

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_M)

        text_wrap = ctk.CTkFrame(inner, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_wrap, text="Enkoder Modu", font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(text_wrap,
                     text="HID: ses kontrolünü cihaz yapar · HOST: PC karar verir",
                     font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w").pack(fill="x", pady=(2, 0))

        self._mode_var = ctk.StringVar(value="HID")
        self._mode_switch = ctk.CTkSegmentedButton(
            inner, text_color=("#ffffff", "#DCE4EE"), values=["HID", "HOST"], variable=self._mode_var,
            command=self._on_mode_selected, font=theme.font(12, True),
            selected_color=theme.COLOR_ACCENT,
            selected_hover_color=theme.COLOR_ACCENT_DARK,
            unselected_color=("#8d97ad", "#2b2b3d"),
            unselected_hover_color=theme.COLOR_HOVER,
            height=34, width=170)
        self._mode_switch.pack(side="right", padx=(theme.PAD_M, 0))

    def _build_test_section(self, parent) -> None:
        """Cihaz test butonlarını oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.pack(fill="x", pady=(0, theme.PAD_M))

        ctk.CTkLabel(box, text="Cihazı Test Et", font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(
            fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, 0))
        ctk.CTkLabel(box, text="LED'leri kısa süre yakarak donanımı doğrula.",
                     font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w").pack(fill="x", padx=theme.PAD_M, pady=(2, theme.PAD_S))

        row1 = ctk.CTkFrame(box, fg_color="transparent")
        row1.pack(fill="x", padx=theme.PAD_M)
        for index in (1, 2, 3):
            ctk.CTkButton(
                row1, text=f"LED{index} Test", height=34,
                corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                command=lambda i=index: self.test_led(i)
            ).pack(side="left", expand=True, fill="x", padx=2)

        row2 = ctk.CTkFrame(box, fg_color="transparent")
        row2.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_S, theme.PAD_M))
        ctk.CTkButton(row2, text="Tümünü Yak", height=34,
                      corner_radius=theme.RADIUS_SMALL,
                      fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_DARK,
                      font=theme.font(12, True), command=self.test_all_leds
                      ).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(row2, text="PING Gönder", height=34,
                      corner_radius=theme.RADIUS_SMALL,
                      fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_ACCENT,
                      font=theme.font(12, True), command=self.send_ping
                      ).pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(row2, text="Cihaza Yaz (SAVE)", height=34,
                      corner_radius=theme.RADIUS_SMALL,
                      fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_DARK,
                      text_color="#101010", font=theme.font(12, True),
                      command=self.save_to_device
                      ).pack(side="left", expand=True, fill="x", padx=2)

    def _build_connection_section(self, parent) -> None:
        """Bağlantı durumu göstergesini oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.grid(row=0, column=0, sticky="ew", pady=(0, theme.PAD_M))

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_M)

        self._link_dot = ctk.CTkLabel(inner, text="●", font=theme.font(26),
                                      text_color=theme.COLOR_DANGER, width=28)
        self._link_dot.pack(side="left")

        text_wrap = ctk.CTkFrame(inner, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True, padx=(theme.PAD_S, 0))
        self._link_title = ctk.CTkLabel(text_wrap, text="Cihaz Bağlı Değil",
                                        font=theme.font(15, True),
                                        text_color=theme.COLOR_DANGER, anchor="w")
        self._link_title.pack(fill="x")
        self._link_detail = ctk.CTkLabel(
            text_wrap, text="Cihaz olmadan da tüm ayarları düzenleyebilirsin.",
            font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self._link_detail.pack(fill="x")

    def _build_port_section(self, parent) -> None:
        """Seri port seçimi ve yenileme bölümünü oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.grid(row=1, column=0, sticky="ew", pady=(0, theme.PAD_M))

        ctk.CTkLabel(box, text="Seri Port", font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(
            fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, 0))
        ctk.CTkLabel(box, text="'auto' seçiliyken cihaz VID/PID ile otomatik bulunur.",
                     font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w").pack(fill="x", padx=theme.PAD_M, pady=(2, theme.PAD_S))

        self._port_var = ctk.StringVar(value="auto")
        self._port_menu = ctk.CTkOptionMenu(
            box, values=["auto"], variable=self._port_var, height=34,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT,
            button_color=theme.COLOR_ACCENT, button_hover_color=theme.COLOR_ACCENT_DARK,
            dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT, dropdown_hover_color=theme.COLOR_HOVER,
            font=theme.mono(12), dropdown_font=theme.mono(11))
        self._port_menu.pack(fill="x", padx=theme.PAD_M)

        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_S, theme.PAD_M))
        ctk.CTkButton(row, text="Portları Yenile", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                      command=self.refresh_ports
                      ).pack(side="left", expand=True, fill="x", padx=(0, 2))
        ctk.CTkButton(row, text="Yeniden Bağlan", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_ACCENT,
                      hover_color=theme.COLOR_ACCENT_DARK, font=theme.font(12, True),
                      command=self.reconnect
                      ).pack(side="left", expand=True, fill="x", padx=(2, 0))

    def _build_log_section(self, parent) -> None:
        """Canlı olay logunu oluşturur."""
        box = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                           fg_color=theme.COLOR_CARD)
        box.grid(row=2, column=0, sticky="nsew")
        box.grid_rowconfigure(1, weight=1)
        box.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(box, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=theme.PAD_M,
                  pady=(theme.PAD_M, theme.PAD_S))
        ctk.CTkLabel(head, text="Canlı Olay Logu", font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT).pack(side="left")
        ctk.CTkButton(head, text="Temizle", width=76, height=26,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_DANGER, font=theme.font(11, True),
                      command=self.clear_log).pack(side="right")
        self._log_counter = ctk.CTkLabel(head, text="0 olay", font=theme.font(10),
                                         text_color=theme.COLOR_TEXT_MUTED)
        self._log_counter.pack(side="right", padx=theme.PAD_S)

        self._log_box = ctk.CTkTextbox(
            box, corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_BG,
            border_width=1, border_color=theme.COLOR_BORDER,
            font=theme.mono(11), text_color=theme.COLOR_TEXT_DIM, wrap="none")
        self._log_box.grid(row=1, column=0, sticky="nsew",
                           padx=theme.PAD_M, pady=(0, theme.PAD_M))
        self._log_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Paneli yapılandırma ve bağlantı durumundan yeniden doldurur."""
        leds = self._led_settings()
        for key, row in getattr(self, "_color_rows", {}).items():
            row.set_color(leds.get(key, row.get_color()))

        brightness = leds.get("brightness", theme.LED_DEFAULT_BRIGHTNESS)
        try:
            brightness = max(0, min(255, int(brightness)))
        except (TypeError, ValueError):
            brightness = theme.LED_DEFAULT_BRIGHTNESS
        self._brightness_slider.set(brightness)
        self._brightness_label.configure(text=str(brightness))

        # Port listesi burada YENİDEN TARANMAZ. refresh(), cihazdan EV OS
        # geldiğinde / profil değiştiğinde çağrılır; her seferinde
        # list_ports.comports() çalıştırmak ana thread'i onlarca milisaniye
        # bloklar (macOS'ta IOKit taraması) ve K11'e arka arkaya basınca
        # arayüz donar. Tarama yalnızca "Portları Yenile" düğmesiyle ve
        # panel ilk kurulurken yapılır.
        current_port = self._device_settings().get("port", "auto") or "auto"
        self._select_port_value(current_port)

        self.set_connection(self._is_connected(), self._port_name())

    def _select_port_value(self, port: str) -> None:
        """Port açılır listesinde verilen değeri seçer; gerekirse listeye ekler."""
        target = str(port or "auto")
        try:
            values = list(self._port_menu.cget("values") or [])
        except Exception:
            values = []
        if target not in values:
            values = values or ["auto"]
            values.append(target)
            try:
                self._port_menu.configure(values=values)
            except Exception:
                pass
        self._port_var.set(target)

    def set_mode(self, mode: str) -> None:
        """Enkoder modu düğmesini dışarıdan ayarlar (geri çağırma tetiklenmez)."""
        clean = "HOST" if (mode or "hid").lower() == "host" else "HID"
        self._mode_guard = True
        try:
            self._mode_var.set(clean)
            self._mode_switch.set(clean)
        except Exception:
            pass
        finally:
            self._mode_guard = False

    def set_connection(self, connected: bool, port: str | None) -> None:
        """Bağlantı göstergesini günceller.

        Args:
            connected: Cihaz bağlı mı.
            port: Bağlı olunan port adı (varsa).
        """
        if connected:
            self._link_dot.configure(text_color=theme.COLOR_SUCCESS)
            self._link_title.configure(text="Cihaz Bağlı", text_color=theme.COLOR_SUCCESS)
            self._link_detail.configure(
                text=f"Port: {port or 'bilinmiyor'}  ·  {theme.APP_NAME}")
        else:
            self._link_dot.configure(text_color=theme.COLOR_DANGER)
            self._link_title.configure(text="Cihaz Bağlı Değil",
                                       text_color=theme.COLOR_DANGER)
            self._link_detail.configure(
                text="Cihaz olmadan da tüm ayarları düzenleyebilirsin.")

    def append_event(self, text: str) -> None:
        """Olay logunun sonuna bir satır ekler (yalnızca ana thread'den çağır).

        Log en fazla :data:`app.ui.theme.EVENT_LOG_LIMIT` satır tutar; eski
        satırlar baştan silinir.
        """
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {text}"
        try:
            self._log_box.configure(state="normal")
            self._log_box.insert("end", line + "\n")
            total = int(self._log_box.index("end-1c").split(".")[0])
            if total > theme.EVENT_LOG_LIMIT:
                self._log_box.delete("1.0", f"{total - theme.EVENT_LOG_LIMIT + 1}.0")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
        except Exception:
            return
        self._event_count += 1
        try:
            self._log_counter.configure(text=f"{self._event_count} olay")
        except Exception:
            pass

    def clear_log(self) -> None:
        """Olay logunu tamamen temizler."""
        try:
            self._log_box.configure(state="normal")
            self._log_box.delete("0.0", "end")
            self._log_box.configure(state="disabled")
        except Exception:
            pass
        self._event_count = 0
        try:
            self._log_counter.configure(text="0 olay")
        except Exception:
            pass

    def refresh_ports(self, select: str | None = None) -> None:
        """Sistemdeki seri portları yeniden tarar ve listeyi günceller."""
        ports: list[str] = []
        try:
            found = self._link.find_ports(self._cfg) if self._link is not None else []
            ports = [str(p) for p in (found or [])]
        except Exception:
            ports = []

        values = ["auto"] + [p for p in ports if p]
        try:
            self._port_menu.configure(values=values)
        except Exception:
            pass

        target = select or self._port_var.get() or "auto"
        if target not in values:
            target = "auto"
        self._port_var.set(target)

        if select is None:
            count = len(values) - 1
            self._on_status(
                f"{count} seri port bulundu." if count else "Seri port bulunamadı.",
                theme.COLOR_ACCENT if count else theme.COLOR_WARNING)

    def reconnect(self) -> None:
        """Seçili portu yapılandırmaya yazıp bağlantıyı yeniden başlatır."""
        selected = self._port_var.get() or "auto"
        try:
            self._device_settings()["port"] = selected
        except Exception:
            pass
        self._on_dirty()   # otomatik kayıt

        if self._link is None:
            self._on_status("Cihaz katmanı kullanılamıyor.", theme.COLOR_DANGER)
            return

        try:
            self._link.stop()
        except Exception:
            pass
        try:
            self._link.start()
            self._on_status(f"Bağlantı yeniden başlatıldı ({selected}).",
                            theme.COLOR_ACCENT)
            self.append_event(f"-- Yeniden bağlanılıyor: {selected}")
        except Exception as error:
            self._on_status(f"Bağlanılamadı: {error}", theme.COLOR_DANGER)

    def send_ping(self) -> None:
        """Cihaza elle ``CMD PING`` gönderir ve yanıtı loga düşürür.

        Uygulama arka planda zaten saniyede bir canlılık sinyali gönderir;
        onların yanıtı logu doldurmasın diye gizlenir. Bu düğmeye basınca
        bayrak kalkar ve SIRADAKİ ``ACK PING`` bir kez gösterilir.
        """
        self._manuel_ping_bekliyor = True
        if self._link is None or not self._link.ping():
            self._manuel_ping_bekliyor = False
            self._on_status("PING gönderilemedi — cihaz bağlı değil.",
                            theme.COLOR_WARNING)
            return
        self.append_event("-- PING gönderildi")

    def apply_all_to_device(self) -> bool:
        """Güncel LED/parlaklık/enkoder ayarlarını cihaza uygular.

        ``MainWindow.save_all()`` bu metodu çağırır; ``True`` dönerse
        ardından ``CMD SAVE`` gönderip ayarları cihazın NVS'ine yazdırır.
        Metot eksik olduğu için çağrı AttributeError ile sessizce yutuluyor,
        NVS'e yazma hiç çalışmıyor ve durum çubuğu cihaz bağlıyken bile
        "Cihaz bağlı değil" diyordu.

        Returns:
            Ayarlar cihaza gönderilebildiyse ``True``, aksi hâlde ``False``.
        """
        if self._link is None or not self._is_connected():
            return False
        try:
            return bool(self._link.apply_settings_to_device(self._current_os_key()))
        except Exception:
            return False

    def save_to_device(self) -> None:
        """Cihaz ayarlarını kalıcı belleğe yazdırır (``CMD SAVE``).

        Önce güncel LED/parlaklık/enkoder ayarları gönderilir, ardından
        cihazdan bunları NVS'e kaydetmesi istenir; böylece ayarlar cihaz
        yeniden başlatıldığında da korunur.
        """
        if self._link is None or not self._is_connected():
            self._on_status("Cihaz bağlı değil — SAVE gönderilemedi.",
                            theme.COLOR_WARNING)
            return
        try:
            self._link.apply_settings_to_device(self._current_os_key())
        except Exception:
            pass
        try:
            ok = bool(self._link.save_device_settings())
        except Exception:
            ok = False
        if ok:
            self.append_event("-- SAVE gönderildi (cihaz NVS'e yazıyor)")
            self._on_status("Ayarlar cihaza kalıcı olarak yazıldı.",
                            theme.COLOR_SUCCESS)
        else:
            self._on_status("SAVE gönderilemedi.", theme.COLOR_WARNING)

    def test_led(self, index: int) -> None:
        """Belirtilen LED'i donanım testi olarak ~900 ms yakar.

        ``CMD LED <i> TEST`` komutu cihazda durum mantığını geçici olarak
        ezer; böylece LED2 combo modu kapalıyken de, LED1 hangi OS modunda
        olursa olsun görünür şekilde yanar.
        """
        if self._link is None or not self._link.led_test(index):
            self._on_status("Komut gönderilemedi — cihaz bağlı değil.",
                            theme.COLOR_WARNING)
            return
        self.append_event(f"-- TEST: LED{index} yakıldı (~0,9 sn)")

    def test_all_leds(self) -> None:
        """Üç LED'i birden ~900 ms yakar (donanım testi)."""
        if self._link is None or not self._link.led_test(0):
            self._on_status("Komut gönderilemedi — cihaz bağlı değil.",
                            theme.COLOR_WARNING)
            return
        self.append_event("-- TEST: Tüm LED'ler yakıldı (~0,9 sn)")

    def _send_led(self, index: int, color: str) -> bool:
        """Cihaza LED rengi gönderir; bağlantı yoksa kullanıcıyı bilgilendirir."""
        if self._link is None:
            return False
        try:
            ok = bool(self._link.set_led(index, theme.hex_to_device(color)))
        except Exception:
            ok = False
        if not ok:
            self._on_status("Komut gönderilemedi — cihaz bağlı değil.",
                            theme.COLOR_WARNING)
        return ok

    def _restore_led(self, index: int) -> None:
        """Test sonrası tek bir LED'i yapılandırmadaki rengine döndürür."""
        leds = self._led_settings()
        os_key = self._current_os_key()
        if index == 1:
            color = leds.get("os_mac" if os_key == "mac" else "os_win",
                             theme.LED_OS_MAC if os_key == "mac" else theme.LED_OS_WIN)
        elif index == 2:
            color = leds.get("combo", theme.LED_COMBO)
        else:
            color = (leds.get("link_ok", theme.LED_LINK_OK) if self._is_connected()
                     else leds.get("link_err", theme.LED_LINK_ERR))
        self._send_led(index, color)

    def _restore_all_leds(self) -> None:
        """Test sonrası üç LED'i de yapılandırmadaki renklerine döndürür."""
        for index in (1, 2, 3):
            self._restore_led(index)

    def _on_color_changed(self, key: str, color: str) -> None:
        """Renk seçimini yapılandırmaya yazar ve cihaza uygular."""
        try:
            self._led_settings()[key] = color
        except Exception:
            pass
        self._on_dirty()   # otomatik kayıt

        index_map = {"os_win": 1, "os_mac": 1, "combo": 2, "link_ok": 3, "link_err": 3}
        index = index_map.get(key)
        if index is not None and self._is_connected():
            # Yalnızca o an geçerli olan renkleri anında uygula.
            os_key = self._current_os_key()
            live = (
                (key == "os_win" and os_key == "windows")
                or (key == "os_mac" and os_key == "mac")
                or (key == "combo")
                or (key == "link_ok" and self._is_connected())
                or (key == "link_err" and not self._is_connected())
            )
            if live:
                self._send_led(index, color)
        self._on_status(f"LED rengi güncellendi: {color}", theme.COLOR_ACCENT)

    def _on_brightness_moved(self, value: float) -> None:
        """Parlaklık kaydırıcısı hareket ettiğinde etiketi ve ayarı günceller."""
        level = int(round(float(value)))
        self._brightness_label.configure(text=str(level))
        try:
            self._led_settings()["brightness"] = level
        except Exception:
            pass
        self._on_dirty()   # otomatik kayıt (yoksa açılışta eski değer döner)
        # Sürükleme sırasında cihazı komut yağmuruna tutmamak için geciktir.
        if self._brightness_job is not None:
            try:
                self.after_cancel(self._brightness_job)
            except Exception:
                pass
        self._brightness_job = self.after(220, lambda v=level: self._push_brightness(v))

    def _push_brightness(self, level: int) -> None:
        """Gecikmeli parlaklık komutunu cihaza gönderir."""
        self._brightness_job = None
        if self._link is None:
            return
        try:
            self._link.set_brightness(level)
        except Exception:
            pass

    def _on_mode_selected(self, value: str) -> None:
        """Enkoder modu değiştiğinde üst pencereye bildirir."""
        if self._mode_guard:
            return
        try:
            self._on_encoder_mode("host" if value.upper() == "HOST" else "hid")
        except Exception:
            pass
