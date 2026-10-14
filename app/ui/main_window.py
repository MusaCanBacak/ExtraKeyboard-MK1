# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Ana Pencere.

Uygulamanın tüm arayüzünü bir arada tutar:

* **Yan panel** — logo, OS modu göstergesi, cihaz bağlantı durumu,
  aktif profil seçici, bilgi kutusu
* **Üst çubuk** — başlık ve durum mesajı
* **Combo uyarı çubuğu** — combo modu açıkken turuncu renkte yanıp söner
* **Sekmeler** — Tuşlar · Combolar · Enkoder · LED & Cihaz · Telefon · Ayarlar
* **Alt çubuk** — "AYARLARI KAYDET" butonu

**Sürükle-bırak:** tkinterdnd2 kuruluysa pencere :class:`DnDWrapper`
karışımını alır ve Tcl ``tkdnd`` paketi kurucuda yüklenir; tuş kartlarına
dosya/klasör/uygulama/web adresi bırakılabilir. Paket yoksa uygulama
sürükle-bırak olmadan normal çalışır.

**Thread güvenliği:** :meth:`MainWindow.push_device_event` cihaz katmanının
arka plan thread'inden çağrılır. Bu metot yalnızca kilitli bir kuyruğa yazar
ve ``after(0, ...)`` ile ana thread'e geçiş yapar. Tkinter bileşenlerine
sadece ana thread'de dokunulur.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from collections import deque

import customtkinter as ctk
from tkinter import filedialog, messagebox

from app.core import platform_utils
from app.core.config import (
    COMBO_IDS,
    ENCODER_IDS,
    KEY_IDS,
    combo_id,
    parse_combo_id,
)
from app.ui import help as help_panel
from app.ui import theme
from app.ui.action_editor import open_action_editor
from app.ui.combo_matrix import ComboMatrix
from app.ui.device_panel import DevicePanel
from app.ui.encoder_panel import EncoderPanel
from app.ui.key_grid import KeyGrid

try:
    # İsteğe bağlı sürükle-bırak desteği: tkinterdnd2 import edildiği anda
    # drop_target_register / dnd_bind metodlarını tkinter tarafına enjekte
    # eder; Tcl 'tkdnd' paketini ise kök pencere sahibi __init__ içinde
    # ``_require`` ile yükler. Paket yoksa uygulama sürükle-bırak olmadan
    # normal açılır (KeyGrid kaydı kendini sessizce kapatır).
    from tkinterdnd2 import TkinterDnD as _TKDND
    _DnDMixin = _TKDND.DnDWrapper
except Exception:  # tkinterdnd2 kurulu değilse sürükle-bırak kapalı kalır.
    _TKDND = None

    class _DnDMixin:
        """tkinterdnd2 kurulu değilken kullanılan boş yer tutucu."""

#: Otomatik başlatma kayıtlarında kullanılan uygulama adı.
AUTOSTART_NAME: str = "ExtraKeyboardMK1"

#: Cihaz olay kuyruğunun güvenlik ağı olarak taranma aralığı (ms).
#: Normalde olaylar ``after(0, ...)`` ile anında işlenir; bu döngü yalnızca
#: o çağrının düştüğü (ör. olay döngüsü henüz başlamamış) durumlar içindir.
EVENT_PUMP_MS: int = 100

#: Telefon sekmesi göstergelerinin (bağlı telefon sayısı, sunucu durumu)
#: tazelenme aralığı (ms).
PHONE_POLL_MS: int = 2000

#: Tema açılır listesindeki Türkçe etiketler ve CustomTkinter karşılıkları.
THEME_LABELS: dict[str, str] = {"Koyu": "Dark", "Açık": "Light", "Sistem": "System"}
THEME_REVERSE: dict[str, str] = {v: k for k, v in THEME_LABELS.items()}

#: Enkoder slotlarının varsayılan Türkçe adları.
ENCODER_TITLES: dict[str, str] = {
    "cw": "Saat Yönü", "ccw": "Saat Yönü Tersi",
    "press": "Basış", "long": "Uzun Basış",
}


# ---------------------------------------------------------------------------
# Otomatik başlatma yardımcıları
#
# Gerçek kayıt işini çekirdek katmandaki :mod:`app.core.platform_utils` yapar;
# buradaki sarmalayıcılar yalnızca hataları yutup arayüzün çökmesini engeller.
# ---------------------------------------------------------------------------

def autostart_enabled() -> bool:
    """İşletim sisteminde otomatik başlatmanın açık olup olmadığını okur."""
    try:
        return bool(platform_utils.is_autostart_enabled())
    except Exception:
        return False


def set_autostart(enabled: bool) -> tuple[bool, str]:
    """Otomatik başlatmayı açar veya kapatır.

    Args:
        enabled: Açılsın mı.

    Returns:
        ``(başarı, mesaj)`` demeti. Mesaj kullanıcıya gösterilecek Türkçe metindir.
    """
    try:
        result = platform_utils.set_autostart(bool(enabled))
    except Exception as error:
        return False, f"Otomatik başlatma ayarlanamadı: {error}"
    if isinstance(result, tuple) and len(result) == 2:
        return bool(result[0]), str(result[1])
    return True, "Başlangıçta çalıştırma ayarı güncellendi."


# ---------------------------------------------------------------------------
# Ana pencere
# ---------------------------------------------------------------------------

class MainWindow(ctk.CTk, _DnDMixin):
    """ExtraKeyboard MK1 yapılandırma uygulamasının ana penceresi."""

    def __init__(self, cfg, link, runner) -> None:
        """Pencereyi ve tüm sekmeleri kurar.

        Args:
            cfg: :class:`app.core.config.ConfigManager` örneği.
            link: :class:`app.core.device.DeviceLink` örneği (``None`` olabilir).
            runner: :class:`app.core.actions.ActionRunner` örneği.
        """
        super().__init__()

        # Sürükle-bırak: Tcl 'tkdnd' paketini kök pencereye yükle (İSTEĞE
        # BAĞLI). Başarısız olursa KeyGrid kayıt aşamasında sürükle-bırakı
        # sessizce kapatır; uygulama normal açılır.
        if _TKDND is not None:
            try:
                self.TkdndVersion = _TKDND._require(self)
            except Exception:
                pass

        self.cfg = cfg
        self.link = link
        self.runner = runner
        self.tray = None
        # "Gizli başlat" isteği bekliyor mu? Kararı set_tray() verir.
        self._start_min_pending = False
        #: Telefon eşlik sunucusu (:class:`app.core.mobile_server.MobileServer`).
        #: ``app.main`` pencere kurulduktan sonra :meth:`set_mobile_server`
        #: ile bağlar; kurulamadıysa ``None`` kalır.
        self.mobile_server = None

        self._pending: deque = deque()
        self._queue_lock = threading.Lock()
        self._combo_mode = False
        self._blink_on = False
        self._dirty = False
        self._status_job: str | None = None
        self._closing = False
        self._device_identity: str = ""
        self._phone_panel_ready = False
        self._phone_qr_url: str = ""
        self._phone_qr_image = None

        ui_settings = self._ui_settings()
        theme.apply_theme(ui_settings.get("theme", "Dark"))

        self.title(f"{theme.APP_NAME} v{theme.APP_VERSION}")
        self.geometry(theme.WINDOW_SIZE)
        self.minsize(*theme.WINDOW_MIN)
        self.configure(fg_color=theme.COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

        self.refresh_all()
        self._update_os_indicator()
        self._update_link_indicator()

        self._tick_blink()
        self._poll_link()
        self._pump_events()

        # macOS: Dock simgesine tıklanınca (uygulama tepsiye gizlenmişken)
        # pencere geri gelsin. Tk bu olayı ``ReopenApplication`` ile bildirir;
        # kaydedilmezse Dock tıklaması hiçbir şey yapmaz ve kullanıcı pencereyi
        # yalnızca menü çubuğu simgesinden açabilir.
        if sys.platform == "darwin":
            try:
                self.createcommand("::tk::mac::ReopenApplication",
                                   self.show_window)
            except Exception:
                pass

        # macOS Erişilebilirlik izni AÇILIŞTA BİR KEZ sorulur (eksikse).
        # Eylem sırasında hiçbir sistem penceresi tetiklenmez; izin
        # verildiyse bu diyalog hiç görünmez.
        self.after(1200, self._maybe_show_accessibility_prompt)

        # Gizli başlatma: pencere HİÇ haritalanmadan gizlenir.
        #
        # Eski davranış pencereyi önce gösterip 400 ms sonra withdraw()
        # ediyordu. macOS'ta bu, ekranda içeriği hiç çizilmemiş bir "hayalet"
        # pencere bırakıyor — kullanıcı bunu bembeyaz (koyu temada boş) bir
        # ekran olarak görüyor, üstelik tıklamalar alttaki gerçek widget'lara
        # gittiği için aynı şekilde boş diyaloglar açılıyordu. Pencereyi daha
        # görünmeden gizlemek bu durumu tamamen ortadan kaldırır.
        #
        # Son kararı set_tray() verir: tepsi simgesi yoksa pencere geri
        # getirilemeyeceği için orada yeniden görünür kılınır.
        self._start_min_pending = bool(ui_settings.get("start_minimized", False))
        if self._start_min_pending:
            try:
                self.withdraw()
            except Exception:
                self._start_min_pending = False
        else:
            # Pencere görünür açılıyor: macOS'ta ilk çizimin ekrana
            # yansımasını garantile (bkz. _pencereyi_yeniden_ciz).
            self.after(120, self._acilis_cizimi)

    # ------------------------------------------------------------------
    # Yapılandırma erişimi
    # ------------------------------------------------------------------

    def _ui_settings(self) -> dict:
        """Yapılandırmadaki ``ui`` bölümünü (canlı referans) döndürür."""
        try:
            value = self.cfg.ui_settings()
            if isinstance(value, dict):
                return value
        except Exception:
            pass
        try:
            value = self.cfg.data.get("ui", {})
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _consume_error(self) -> str:
        """Çekirdek katmanın son hatasını okur ve temizler.

        ``ConfigManager`` istisna fırlatmaz; başarısız işlemlerde
        ``last_error`` alanını doldurur. Bu yardımcı onu okuyup sıfırlar.
        """
        try:
            message = getattr(self.cfg, "last_error", None)
            if message:
                self.cfg.last_error = None
                return str(message)
        except Exception:
            pass
        return ""

    def os_key(self) -> str:
        """Aktif işletim sistemi profilini döndürür (``"windows"`` / ``"mac"``)."""
        try:
            value = self.runner.current_os_key()
            if value in ("windows", "mac"):
                return value
        except Exception:
            pass
        return "mac" if sys.platform == "darwin" else "windows"

    def get_action(self, slot: str) -> dict:
        """Aktif profildeki bir slotun eylemini döndürür."""
        try:
            action = self.cfg.get_action(self.os_key(), slot)
            if isinstance(action, dict):
                return action
        except Exception:
            pass
        return {"type": "none", "value": "", "name": ""}

    @staticmethod
    def default_slot_name(slot: str) -> str:
        """Bir slot için varsayılan Türkçe adı üretir."""
        if slot in KEY_IDS:
            return f"Tuş {slot[1:]}"
        if slot in ENCODER_TITLES:
            return ENCODER_TITLES[slot]
        if slot in COMBO_IDS:
            try:
                first, second = parse_combo_id(slot)
                return f"Combo {first}+{second}"
            except Exception:
                return slot
        return slot

    @classmethod
    def slot_title(cls, slot: str) -> str:
        """Düzenleme diyaloğunun başlığında gösterilecek okunur adı üretir."""
        if slot in KEY_IDS:
            return f"Tuş {slot[1:]}  ({slot})"
        if slot in ENCODER_TITLES:
            return f"Enkoder — {ENCODER_TITLES[slot]}"
        if slot in COMBO_IDS:
            try:
                first, second = parse_combo_id(slot)
                return f"Combo {first} + {second}"
            except Exception:
                return slot
        return slot

    # ------------------------------------------------------------------
    # Yan panel
    # ------------------------------------------------------------------

    def _build_sidebar(self) -> None:
        """Sol yan paneli oluşturur."""
        sidebar = ctk.CTkFrame(self, width=theme.SIDEBAR_WIDTH, corner_radius=0,
                               fg_color=theme.COLOR_BG)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # --- Logo ---------------------------------------------------------
        logo = ctk.CTkFrame(sidebar, fg_color=theme.COLOR_PANEL,
                            corner_radius=theme.RADIUS_CARD, height=96)
        logo.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, theme.PAD_S))
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="EXTRA", font=theme.font(24, True),
                     text_color=theme.COLOR_ACCENT).pack(pady=(14, 0))
        ctk.CTkLabel(logo, text="KEYBOARD", font=theme.font(14, True),
                     text_color=theme.COLOR_TEXT_DIM).pack()
        ctk.CTkLabel(logo, text=f"{theme.HW_REV}  ·  {theme.VENDOR}",
                     font=theme.font(10), text_color=theme.COLOR_TEXT_MUTED).pack()

        # --- OS modu göstergesi -------------------------------------------
        os_box = ctk.CTkFrame(sidebar, fg_color=theme.COLOR_PANEL,
                              corner_radius=theme.RADIUS_SMALL)
        os_box.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_XS)
        os_inner = ctk.CTkFrame(os_box, fg_color="transparent")
        os_inner.pack(fill="x", padx=theme.PAD_S, pady=theme.PAD_S)
        self._os_dot = ctk.CTkLabel(os_inner, text="●", font=theme.font(18),
                                    text_color=theme.COLOR_DISABLED, width=22)
        self._os_dot.pack(side="left")
        os_text = ctk.CTkFrame(os_inner, fg_color="transparent")
        os_text.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(os_text, text="OS MODU", font=theme.font(9, True),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(fill="x")
        self._os_label = ctk.CTkLabel(os_text, text="WINDOWS", font=theme.font(13, True),
                                      text_color=theme.COLOR_TEXT, anchor="w")
        self._os_label.pack(fill="x")

        # --- Cihaz bağlantı durumu ------------------------------------------
        link_box = ctk.CTkFrame(sidebar, fg_color=theme.COLOR_PANEL,
                                corner_radius=theme.RADIUS_SMALL)
        link_box.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_XS)
        link_inner = ctk.CTkFrame(link_box, fg_color="transparent")
        link_inner.pack(fill="x", padx=theme.PAD_S, pady=theme.PAD_S)
        self._link_dot = ctk.CTkLabel(link_inner, text="●", font=theme.font(18),
                                      text_color=theme.COLOR_DANGER, width=22)
        self._link_dot.pack(side="left")
        link_text = ctk.CTkFrame(link_inner, fg_color="transparent")
        link_text.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(link_text, text="CİHAZ", font=theme.font(9, True),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(fill="x")
        self._link_label = ctk.CTkLabel(link_text, text="Bağlı değil",
                                        font=theme.font(13, True),
                                        text_color=theme.COLOR_DANGER, anchor="w")
        self._link_label.pack(fill="x")
        self._link_port = ctk.CTkLabel(link_text, text="—", font=theme.mono(10),
                                       text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self._link_port.pack(fill="x")

        # Cihaz takılı olduğu hâlde bağlanılamadığında kullanıcının elinde
        # kalacak iki araç. Yalnızca bağlantı YOKKEN görünürler; bağlıyken
        # yer kaplamasınlar diye gizlenirler (bkz. _set_link_state).
        self._link_actions = ctk.CTkFrame(link_box, fg_color="transparent")
        self._btn_rescan = ctk.CTkButton(
            self._link_actions, text="Yeniden Tara", height=26,
            font=theme.font(11, True), corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_HOVER,
            command=self._on_rescan)
        self._btn_rescan.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self._btn_wake = ctk.CTkButton(
            self._link_actions, text="Uyandır", height=26, width=70,
            font=theme.font(11, True), corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_DISABLED, hover_color=theme.COLOR_HOVER,
            command=self._on_wake_device)
        self._btn_wake.pack(side="left", padx=(3, 0))
        self._link_actions.pack(fill="x", padx=theme.PAD_S,
                                pady=(0, theme.PAD_S))

        # --- Aktif profil ----------------------------------------------------
        profile_box = ctk.CTkFrame(sidebar, fg_color=theme.COLOR_PANEL,
                                   corner_radius=theme.RADIUS_SMALL)
        profile_box.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_XS)
        ctk.CTkLabel(profile_box, text="AKTİF PROFİL", font=theme.font(9, True),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(
            fill="x", padx=theme.PAD_S, pady=(theme.PAD_S, 0))
        self._profile_var = ctk.StringVar(value=self._active_profile_name())
        self._profile_menu = ctk.CTkOptionMenu(
            profile_box, values=self._profile_names(), variable=self._profile_var,
            command=self._on_profile_selected, height=32,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT,
            button_color=theme.COLOR_ACCENT, button_hover_color=theme.COLOR_ACCENT_DARK,
            dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT, dropdown_hover_color=theme.COLOR_HOVER,
            font=theme.font(12), dropdown_font=theme.font(12))
        self._profile_menu.pack(fill="x", padx=theme.PAD_S, pady=(4, theme.PAD_S))

        # --- Bilgi kutusu -----------------------------------------------------
        ctk.CTkLabel(sidebar, text="Bilgi", font=theme.font(13, True),
                     text_color=theme.COLOR_TEXT_DIM, anchor="w").pack(
            fill="x", padx=theme.PAD_L, pady=(theme.PAD_S, 2))
        self._info_box = ctk.CTkTextbox(sidebar, font=theme.font(11),
                                        text_color=theme.COLOR_TEXT,
                                        fg_color=theme.COLOR_PANEL,
                                        corner_radius=theme.RADIUS_SMALL,
                                        border_width=0, wrap="word")
        self._info_box.pack(fill="both", expand=True, padx=theme.PAD_M,
                            pady=(0, theme.PAD_S))
        self._info_box.configure(state="disabled")

        ctk.CTkLabel(sidebar, text=f"v{theme.APP_VERSION}", font=theme.font(10),
                     text_color=theme.COLOR_DISABLED).pack(side="bottom",
                                                           pady=(0, theme.PAD_S))

    def _update_info_box(self) -> None:
        """Yan paneldeki bilgi kutusunu aktif profile göre yeniden yazar."""
        is_mac = self.os_key() == "mac"
        modifier = "command (⌘)" if is_mac else "ctrl"
        file_hint = "• .app uygulamaları" if is_mac else "• .exe ve .lnk dosyaları"
        lines = [
            f"Aktif profil: {'macOS' if is_mac else 'Windows'}",
            "",
            "KISAYOLLAR",
            "Tuşları + ile birleştir.",
            f"• {modifier}+c   (kopyala)",
            f"• {modifier}+v   (yapıştır)",
            "",
            "UYGULAMA SEÇİMİ",
            "Gözat penceresi şunları filtreler:",
            file_hint,
            "",
            "COMBO",
            "COMBO tuşuna bir kez bas (bas-çek), ardından",
            "K1–K10 içinden iki tuşa bas. Sıra önemsiz:",
            "2+5 ile 5+2 aynı combodur.",
            "",
            "ENKODER",
            "HID modunda ses kontrolünü cihaz",
            "yapar; HOST modunda PC karar verir.",
        ]
        if self._device_identity:
            lines += ["", "CİHAZ", self._device_identity]
        try:
            self._info_box.configure(state="normal")
            self._info_box.delete("0.0", "end")
            self._info_box.insert("0.0", "\n".join(lines))
            self._info_box.configure(state="disabled")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Ana alan
    # ------------------------------------------------------------------

    def _build_main_area(self) -> None:
        """Üst çubuk, combo uyarı çubuğu, sekmeler ve kaydet butonunu oluşturur."""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=theme.PAD_M, pady=theme.PAD_M)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # --- Üst çubuk ------------------------------------------------------
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(header, text="Tuş Atama Paneli", font=theme.font(22, True),
                     text_color=theme.COLOR_TEXT).pack(side="left")
        # Durum metni uzun olabilir; sarmalanır ve genişliği sınırlanır ki
        # sola doğru büyüyüp başlığın üstüne binmesin.
        self._status_label = ctk.CTkLabel(header, text="Hazır", font=theme.font(12, True),
                                          text_color=theme.COLOR_SUCCESS,
                                          wraplength=520, justify="right",
                                          anchor="e")
        self._status_label.pack(side="right", padx=theme.PAD_S)

        # --- Combo uyarı çubuğu ----------------------------------------------
        self._combo_bar = ctk.CTkFrame(main, height=34, fg_color=theme.COLOR_WARNING,
                                       corner_radius=theme.RADIUS_SMALL)
        self._combo_bar_label = ctk.CTkLabel(
            self._combo_bar, text="COMBO MODU AKTİF — K1…K10 içinden iki tuşa bas",
            font=theme.font(13, True), text_color="#101010")
        self._combo_bar_label.pack(pady=6)
        # Başlangıçta gizli; combo modu açılınca grid'e alınır.

        # --- Sekmeler ---------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            main, corner_radius=theme.RADIUS_CARD,
            fg_color=theme.COLOR_BG,
            segmented_button_fg_color=theme.COLOR_PANEL,
            segmented_button_selected_color=theme.COLOR_ACCENT,
            segmented_button_selected_hover_color=theme.COLOR_ACCENT_DARK,
            segmented_button_unselected_color=theme.COLOR_PANEL,
            segmented_button_unselected_hover_color=theme.COLOR_HOVER,
            text_color=theme.COLOR_TEXT)
        self.tabview.grid(row=2, column=0, sticky="nsew", pady=(theme.PAD_S, theme.PAD_S))

        for name in ("Tuşlar", "Combolar", "Enkoder", "LED & Cihaz", "Telefon", "Ayarlar"):
            self.tabview.add(name)

        self._build_keys_tab(self.tabview.tab("Tuşlar"))
        self._build_combos_tab(self.tabview.tab("Combolar"))
        self._build_encoder_tab(self.tabview.tab("Enkoder"))
        self._build_device_tab(self.tabview.tab("LED & Cihaz"))
        self._build_phone_tab(self.tabview.tab("Telefon"))
        self._build_settings_tab(self.tabview.tab("Ayarlar"))

        # Her sekmenin sağ üst köşesine o sayfayı anlatan "?" düğmesi.
        for tab_adi, konu in (("Tuşlar", "tuslar"), ("Combolar", "combolar"),
                              ("Enkoder", "enkoder"), ("LED & Cihaz", "led_cihaz"),
                              ("Telefon", "telefon"), ("Ayarlar", "ayarlar")):
            help_panel.attach_help(self.tabview.tab(tab_adi), konu)

        # --- Kaydet butonu -----------------------------------------------------
        self._save_button = ctk.CTkButton(
            main, text="AYARLARI KAYDET", height=46,
            corner_radius=theme.RADIUS_CARD, fg_color=theme.COLOR_SUCCESS,
            hover_color=theme.COLOR_SUCCESS_DARK, text_color="#101010",
            font=theme.font(14, True), command=self.save_all)
        self._save_button.grid(row=3, column=0, sticky="ew")

        self._main_frame = main

    def _build_keys_tab(self, parent) -> None:
        """"Tuşlar" sekmesini oluşturur."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        ctk.CTkLabel(wrapper,
                     text="Cihazın fiziksel yerleşimi — düzenlemek için bir tuşa tıkla",
                     font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED,
                     anchor="w").pack(fill="x", pady=(0, theme.PAD_S))

        self.key_grid = KeyGrid(wrapper, self.get_action, self._edit_slot,
                                self._on_special_card, on_drop=self._on_key_drop)
        self.key_grid.pack(fill="both", expand=True)

    def _build_combos_tab(self, parent) -> None:
        """"Combolar" sekmesini oluşturur."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        self.combo_matrix = ComboMatrix(scroll, self.get_action, self._edit_slot)
        self.combo_matrix.pack(fill="both", expand=True)

    def _build_encoder_tab(self, parent) -> None:
        """"Enkoder" sekmesini oluşturur."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        self.encoder_panel = EncoderPanel(wrapper, self.get_action, self._edit_slot,
                                          self._on_encoder_mode_change)
        self.encoder_panel.pack(fill="both", expand=True)

    def _build_device_tab(self, parent) -> None:
        """"LED & Cihaz" sekmesini oluşturur."""
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        self.device_panel = DevicePanel(wrapper, self.cfg, self.link,
                                        get_os_key=self.os_key,
                                        on_status=self.set_status,
                                        on_encoder_mode=self._on_encoder_mode_change,
                                        on_dirty=lambda: self._mark_dirty(True))
        self.device_panel.pack(fill="both", expand=True)

    def _build_phone_tab(self, parent) -> None:
        """"Telefon" sekmesini oluşturur.

        Telefon eşlik sunucusunun durumunu, yerel ağ adresini, QR karekodu
        ve aç/kapat anahtarını gösterir. Sunucu nesnesi pencere kurulduktan
        sonra :meth:`set_mobile_server` ile bağlanır; o âna kadar panel
        "kullanılamıyor" durumunu gösterir.
        """
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        card = self._settings_card(
            scroll, "Telefondan İzleme",
            "Tuş atamalarını ve basılan tuşları telefonundan canlı izle. "
            "Telefonunuz bu bilgisayarla aynı Wi-Fi ağında olmalı; aşağıdaki "
            "adresi telefonun tarayıcısında aç veya QR kodu okut.")

        # --- Durum satırı: nokta + metin + bağlı telefon sayısı -------------
        status_row = ctk.CTkFrame(card, fg_color="transparent")
        status_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
        self._phone_dot = ctk.CTkLabel(status_row, text="●", font=theme.font(18),
                                       text_color=theme.COLOR_DISABLED, width=22)
        self._phone_dot.pack(side="left")
        self._phone_status_label = ctk.CTkLabel(status_row, text="Sunucu kapalı",
                                                font=theme.font(13, True),
                                                text_color=theme.COLOR_TEXT_DIM,
                                                anchor="w")
        self._phone_status_label.pack(side="left", padx=(4, 0))
        self._phone_clients_label = ctk.CTkLabel(status_row, text="Bağlı telefon: —",
                                                 font=theme.font(12),
                                                 text_color=theme.COLOR_TEXT_MUTED)
        self._phone_clients_label.pack(side="right")

        # --- Adres satırı: URL + kopyala butonu ------------------------------
        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
        self._phone_url_label = ctk.CTkLabel(url_row, text="—", font=theme.mono(13),
                                             text_color=theme.COLOR_TEXT, anchor="w")
        self._phone_url_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(url_row, text="Adresi Kopyala", height=32, width=140,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                      command=self._copy_phone_url).pack(side="right")

        # --- Aç / kapat anahtarı ---------------------------------------------
        self._phone_enabled_var = ctk.BooleanVar(
            value=bool(self._mobile_settings().get("enabled", True)))
        ctk.CTkSwitch(card, text="Telefon sunucusu açık",
                      variable=self._phone_enabled_var, command=self._on_phone_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        # --- Windows güvenlik duvarı notu ------------------------------------
        # Windows'ta sunucu ilk kez porta bağlanınca Defender Güvenlik Duvarı
        # izin penceresi açar; kullanıcı "İptal" derse veya ağ "Genel (Public)"
        # profildeyse gelen bağlantılar sessizce engellenir. Sunucu "çalışıyor"
        # görünse de telefon bağlanamaz; bu notla kullanıcıya ipucu veriyoruz.
        if sys.platform.startswith("win"):
            ctk.CTkLabel(
                card,
                text=("Windows notu: İlk açılışta Güvenlik Duvarı izin penceresi "
                      "çıkar; izin verin. Telefon bağlanamıyorsa Windows Defender "
                      "Güvenlik Duvarı'nda Python/ExtraKeyboard için özel (ev/iş) "
                      "ağlarda gelen bağlantılara izin verildiğinden ve Wi-Fi "
                      "ağının \"Genel (Public)\" profilde olmadığından emin olun."),
                font=theme.font(11), text_color=theme.COLOR_WARNING,
                anchor="w", justify="left", wraplength=780,
            ).pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        # --- QR karekod --------------------------------------------------------
        qr_card = self._settings_card(
            scroll, "QR ile Bağlan",
            "Adresi elle yazmak yerine telefonunun kamerasıyla bu kodu okut.")
        self._phone_qr_label = ctk.CTkLabel(qr_card, text="")
        self._phone_qr_hint = ctk.CTkLabel(
            qr_card, text="Sunucu açılınca QR kod burada görünür.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            anchor="w", justify="left")
        self._phone_qr_hint.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        # --- Telefona kurulum yönergesi (iPhone + Android) --------------------
        kurulum_card = self._settings_card(
            scroll, "Telefona Kurulum",
            "Sayfayı ana ekrana eklerseniz tam ekran, uygulama görünümünde açılır.")
        ctk.CTkLabel(
            kurulum_card,
            text=("  iPhone / iPad:  Adresi Safari'de açın → Paylaş (kare+ok) → "
                  "\"Ana Ekrana Ekle\".\n"
                  "  Android:  Adresi Chrome'da açın → sağ üst ⋮ menü → "
                  "\"Ana ekrana ekle\".  (Ayrı APK paketi ileride eklenecek.)\n"
                  "  Mac / PC:  Aynı adres herhangi bir tarayıcıda da açılır."),
            font=theme.font(12), text_color=theme.COLOR_TEXT_DIM,
            anchor="w", justify="left", wraplength=780,
        ).pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        self._phone_panel_ready = True
        self._refresh_phone_panel()
        self.after(PHONE_POLL_MS, self._tick_phone_panel)

    def _build_settings_tab(self, parent) -> None:
        """"Ayarlar" sekmesini oluşturur."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=theme.PAD_S, pady=theme.PAD_S)

        ui_settings = self._ui_settings()

        # --- Görünüm ---------------------------------------------------------
        appearance = self._settings_card(scroll, "Görünüm",
                                         "Uygulamanın tema tercihi.")
        row = ctk.CTkFrame(appearance, fg_color="transparent")
        row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))
        ctk.CTkLabel(row, text="Tema", font=theme.font(12),
                     text_color=theme.COLOR_TEXT_DIM).pack(side="left")
        self._theme_var = ctk.StringVar(
            value=THEME_REVERSE.get(ui_settings.get("theme", "Dark"), "Koyu"))
        ctk.CTkOptionMenu(row, values=list(THEME_LABELS.keys()),
                          variable=self._theme_var, command=self._on_theme_change,
                          width=170, height=32, corner_radius=theme.RADIUS_SMALL,
                          fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT, button_color=theme.COLOR_ACCENT,
                          button_hover_color=theme.COLOR_ACCENT_DARK,
                          dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT,
                          dropdown_hover_color=theme.COLOR_HOVER,
                          font=theme.font(12)).pack(side="right")

        # --- Davranış ---------------------------------------------------------
        behaviour = self._settings_card(
            scroll, "Davranış", "Uygulamanın açılış ve kapanış davranışı.")

        self._autostart_var = ctk.BooleanVar(value=autostart_enabled())
        ctk.CTkSwitch(behaviour, text="Bilgisayar açılışında çalıştır",
                      variable=self._autostart_var, command=self._on_autostart_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_S))

        self._tray_var = ctk.BooleanVar(value=bool(ui_settings.get("minimize_to_tray", True)))
        ctk.CTkSwitch(behaviour, text="Pencere kapatılınca sistem tepsisine küçült",
                      variable=self._tray_var, command=self._on_tray_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_S))

        self._start_min_var = ctk.BooleanVar(value=bool(ui_settings.get("start_minimized", False)))
        ctk.CTkSwitch(behaviour, text="Açılışta pencereyi gösterme (gizli başlat)",
                      variable=self._start_min_var, command=self._on_start_min_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_S))

        # Gelişmiş LED renk bölümünün görünürlüğü buradan yönetilir; kapalıyken
        # LED & Cihaz sekmesinde yalnızca parlaklık görünür (bu üründeki 3 LED
        # düz/tek renk olduğu için varsayılan KAPALI).
        self._acc_prompt_var = ctk.BooleanVar(
            value=not bool(ui_settings.get("hide_accessibility_prompt", False)))
        ctk.CTkSwitch(behaviour, text="Erişilebilirlik izni uyarısını göster (macOS)",
                      variable=self._acc_prompt_var,
                      command=self._on_acc_prompt_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_S))

        self._led_colors_var = ctk.BooleanVar(
            value=bool(ui_settings.get("show_led_colors", False)))
        ctk.CTkSwitch(behaviour, text="Gelişmiş LED renk ayarlarını göster",
                      variable=self._led_colors_var,
                      command=self._on_led_colors_toggle,
                      font=theme.font(12), progress_color=theme.COLOR_SUCCESS
                      ).pack(anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        # --- Profil yönetimi ----------------------------------------------------
        profiles = self._settings_card(
            scroll, "Profil Yönetimi",
            "Her profil, Windows ve macOS için ayrı tuş yapılandırması taşır.")

        list_row = ctk.CTkFrame(profiles, fg_color="transparent")
        list_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
        ctk.CTkLabel(list_row, text="Profil", font=theme.font(12),
                     text_color=theme.COLOR_TEXT_DIM).pack(side="left")
        self._settings_profile_var = ctk.StringVar(value=self._active_profile_name())
        self._settings_profile_menu = ctk.CTkOptionMenu(
            list_row, values=self._profile_names(),
            variable=self._settings_profile_var, command=self._on_profile_selected,
            width=220, height=32, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT, button_color=theme.COLOR_ACCENT,
            button_hover_color=theme.COLOR_ACCENT_DARK,
            dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT, dropdown_hover_color=theme.COLOR_HOVER,
            font=theme.font(12))
        self._settings_profile_menu.pack(side="right")

        name_row = ctk.CTkFrame(profiles, fg_color="transparent")
        name_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
        self._new_profile_entry = ctk.CTkEntry(
            name_row, height=34, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_FIELD, placeholder_text_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT, border_color=theme.COLOR_BORDER,
            font=theme.font(12), placeholder_text="Yeni profil adı…")
        self._new_profile_entry.pack(side="left", fill="x", expand=True)

        button_row = ctk.CTkFrame(profiles, fg_color="transparent")
        button_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))
        ctk.CTkButton(button_row, text="Ekle", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_ACCENT,
                      hover_color=theme.COLOR_ACCENT_DARK, font=theme.font(12, True),
                      command=self._add_profile
                      ).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ctk.CTkButton(button_row, text="Kopyala", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                      command=self._copy_profile
                      ).pack(side="left", expand=True, fill="x", padx=3)
        ctk.CTkButton(button_row, text="Sil", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_DANGER,
                      hover_color=theme.COLOR_DANGER_DARK, font=theme.font(12, True),
                      command=self._delete_profile
                      ).pack(side="left", expand=True, fill="x", padx=(3, 0))

        # --- Yapılandırma dosyası -------------------------------------------------
        config_card = self._settings_card(
            scroll, "Yapılandırma Dosyası",
            "Ayarlarını yedekle veya başka bir bilgisayara taşı.")

        io_row = ctk.CTkFrame(config_card, fg_color="transparent")
        io_row.pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_S))
        ctk.CTkButton(io_row, text="Dışa Aktar", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                      command=self._export_config
                      ).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ctk.CTkButton(io_row, text="İçe Aktar", height=34,
                      corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                      command=self._import_config
                      ).pack(side="left", expand=True, fill="x", padx=(3, 0))

        path_text = ""
        try:
            path_text = str(self.cfg.path)
        except Exception:
            path_text = "(bilinmiyor)"
        ctk.CTkLabel(config_card, text=f"Dosya: {path_text}", font=theme.mono(10),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w", wraplength=780,
                     justify="left").pack(fill="x", padx=theme.PAD_M,
                                          pady=(0, theme.PAD_M))

        # --- Hakkında -------------------------------------------------------------
        about = self._settings_card(scroll, "Hakkında", "")
        ctk.CTkLabel(
            about,
            text=(f"{theme.APP_NAME}  ·  uygulama v{theme.APP_VERSION}  ·  "
                  f"donanım {theme.HW_REV}\n"
                  "12 tuş · 3 LED · 1 döner enkoder. Mantık PC tarafındadır: cihaz "
                  "yalnızca hangi tuşa basıldığını bildirir, ne yapılacağına bu "
                  "uygulama karar verir."),
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            justify="left", anchor="w", wraplength=780
        ).pack(fill="x", padx=theme.PAD_M, pady=(0, theme.PAD_M))

    def _settings_card(self, parent, title: str, description: str) -> ctk.CTkFrame:
        """Ayarlar sekmesinde başlıklı bir kart çerçevesi üretir."""
        card = ctk.CTkFrame(parent, corner_radius=theme.RADIUS_CARD,
                            fg_color=theme.COLOR_CARD)
        card.pack(fill="x", pady=(0, theme.PAD_M))
        ctk.CTkLabel(card, text=title, font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(
            fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, 0))
        if description:
            ctk.CTkLabel(card, text=description, font=theme.font(11),
                         text_color=theme.COLOR_TEXT_MUTED, anchor="w",
                         justify="left", wraplength=780).pack(
                fill="x", padx=theme.PAD_M, pady=(2, theme.PAD_S))
        else:
            ctk.CTkLabel(card, text="", height=4, fg_color="transparent").pack(
                fill="x", padx=theme.PAD_M)
        return card

    # ------------------------------------------------------------------
    # Yenileme ve durum
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        """Tüm sekmeleri güncel yapılandırmadan yeniden doldurur."""
        for widget_name in ("key_grid", "combo_matrix", "encoder_panel", "device_panel"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                try:
                    widget.refresh()
                except Exception:
                    pass

        mode = self._encoder_mode()
        for widget in (getattr(self, "encoder_panel", None),
                       getattr(self, "device_panel", None),
                       getattr(self, "key_grid", None)):
            if widget is None:
                continue
            try:
                if hasattr(widget, "set_mode"):
                    widget.set_mode(mode)
                elif hasattr(widget, "set_encoder_mode"):
                    widget.set_encoder_mode(mode)
            except Exception:
                pass

        self._sync_profile_menus()
        self._update_info_box()
        self._refresh_phone_panel()
        # Bağlı telefonlar da güncel adları/profili anında görsün.
        self._publish_mobile_state()

    def set_status(self, text: str, color: str = theme.COLOR_ACCENT) -> None:
        """Üst çubuktaki durum mesajını günceller (birkaç saniye sonra silinir)."""
        mesaj = str(text or "")
        # Aşırı uzun metin iki satırı da taşırır; okunur bir sınırda kırpılır.
        if len(mesaj) > 150:
            mesaj = mesaj[:147].rstrip() + "…"
        try:
            self._status_label.configure(text=mesaj, text_color=color)
        except Exception:
            return
        if self._status_job is not None:
            try:
                self.after_cancel(self._status_job)
            except Exception:
                pass
        # Uzun/uyarı niteliğindeki mesajlar için okuma süresi uzatılır.
        sure = 8000 if len(mesaj) > 70 else 4500
        self._status_job = self.after(sure, self._clear_status)

    def _clear_status(self) -> None:
        """Durum mesajını varsayılan hâline döndürür."""
        self._status_job = None
        try:
            if self._dirty:
                self._status_label.configure(
                    text="Kaydedilmemiş değişiklik var", text_color=theme.COLOR_WARNING)
            else:
                self._status_label.configure(text="Hazır", text_color=theme.COLOR_SUCCESS)
        except Exception:
            pass

    def _mark_dirty(self, dirty: bool = True) -> None:
        """Kaydedilmemiş değişiklik durumunu işaretler ve butonu günceller.

        OTOMATİK KAYIT: her değişiklik ~1 sn içinde kendiliğinden diske
        yazılır — uygulama kapatılıp açıldığında hiçbir ayar kaybolmaz.
        KAYDET düğmesi beklemeden anında yazmak için durur.
        """
        self._dirty = dirty
        try:
            if dirty:
                self._save_button.configure(text="AYARLARI KAYDET  •",
                                            fg_color=theme.COLOR_WARNING,
                                            hover_color=theme.COLOR_WARNING_DARK)
            else:
                self._save_button.configure(text="AYARLARI KAYDET",
                                            fg_color=theme.COLOR_SUCCESS,
                                            hover_color=theme.COLOR_SUCCESS_DARK)
        except Exception:
            pass
        if dirty:
            self._schedule_autosave()

    def _schedule_autosave(self) -> None:
        """Otomatik kaydı 900 ms sonrasına planlar (art arda değişiklikte
        zamanlayıcı tazelenir; tek yazım yapılır)."""
        onceki = getattr(self, "_autosave_job", None)
        if onceki is not None:
            try:
                self.after_cancel(onceki)
            except Exception:
                pass
        try:
            self._autosave_job = self.after(900, self._autosave_now)
        except Exception:
            self._autosave_job = None

    def _autosave_now(self) -> None:
        """Bekleyen değişiklikleri sessizce diske yazar."""
        self._autosave_job = None
        if not getattr(self, "_dirty", False):
            return
        try:
            self.cfg.save()
        except Exception as hata:
            self.set_status(f"Otomatik kayıt başarısız: {hata}",
                            theme.COLOR_DANGER)
            return
        # ``ConfigManager.save()`` İSTİSNA FIRLATMAZ; başarısızlıkta yalnızca
        # ``last_error`` alanını doldurur. Bu yüzden kaydı başarılı saymadan
        # önce hatayı okuyoruz. Aksi hâlde (dizin yazılamaz, disk dolu, TCC
        # izni yok...) ``_dirty`` temizlenir, düğme yeşile döner ve çıkışta
        # uyarı da çıkmadığı için tüm oturumun ayarları sessizce kaybolur.
        failure = self._consume_error()
        if failure:
            self.set_status(failure, theme.COLOR_DANGER)
            return  # _dirty True kalır: çıkışta uyarı/yeniden deneme şansı korunur
        self._mark_dirty(False)

    def _update_os_indicator(self) -> None:
        """Yan paneldeki OS göstergesini, başlığı ve tuş ızgarasını günceller."""
        os_key = self.os_key()
        is_mac = os_key == "mac"
        color = theme.LED_OS_MAC if is_mac else theme.LED_OS_WIN
        label = "MACOS" if is_mac else "WINDOWS"
        try:
            self._os_dot.configure(text_color=color)
            self._os_label.configure(text=label)
            self.title(f"{theme.APP_NAME} v{theme.APP_VERSION} — Mod: {label}")
        except Exception:
            pass
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.set_os_mode(os_key)
            except Exception:
                pass
        self._update_info_box()

    def _update_link_indicator(self) -> None:
        """Yan paneldeki ve cihaz panelindeki bağlantı göstergelerini günceller."""
        connected = False
        port = None
        if self.link is not None:
            try:
                # DÜRÜST gösterge: port açık mı (connected) DEĞİL, cihaz gerçekten
                # YANIT VERİYOR mu (responsive = son HB taze). Port açık kalıp cihaz
                # sussa bile kullanıcıya yalan "Bağlı" gösterilmez.
                connected = bool(self.link.responsive)
                port = self.link.port_name
            except Exception:
                connected, port = False, None

        try:
            if connected:
                self._link_dot.configure(text_color=theme.COLOR_SUCCESS)
                self._link_label.configure(text="Bağlı", text_color=theme.COLOR_SUCCESS)
                self._link_port.configure(text=str(port or "—"))
                try:
                    self._link_actions.pack_forget()
                except Exception:
                    pass
            else:
                self._link_dot.configure(text_color=theme.COLOR_DANGER)
                try:
                    if not self._link_actions.winfo_ismapped():
                        self._link_actions.pack(fill="x", padx=theme.PAD_S,
                                                pady=(0, theme.PAD_S))
                except Exception:
                    pass
                self._link_label.configure(text="Bağlı değil",
                                           text_color=theme.COLOR_DANGER)
                self._link_port.configure(text="—")
        except Exception:
            pass

        panel = getattr(self, "device_panel", None)
        if panel is not None:
            try:
                panel.set_connection(connected, port)
            except Exception:
                pass
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.set_link_state(connected)
            except Exception:
                pass
        if self.tray is not None:
            try:
                self.tray.set_connected(connected)
            except Exception:
                pass

    def _poll_link(self) -> None:
        """Bağlantı durumunu düzenli aralıklarla tazeler (olay kaçsa bile doğru kalır)."""
        if self._closing:
            return
        self._update_link_indicator()
        self.after(1500, self._poll_link)

    def _tick_blink(self) -> None:
        """Combo uyarı çubuğunu yanıp söndürür."""
        if self._closing:
            return
        if self._combo_mode:
            self._blink_on = not self._blink_on
            try:
                self._combo_bar.configure(
                    fg_color=theme.COLOR_WARNING if self._blink_on else "#8a5200")
                self._combo_bar_label.configure(
                    text_color="#101010" if self._blink_on else "#F0D0A0")
            except Exception:
                pass
        self.after(theme.COMBO_BLINK_MS, self._tick_blink)

    def _set_combo_mode(self, active: bool) -> None:
        """Combo modunu açar/kapatır ve uyarı çubuğunu gösterir/gizler."""
        if active == self._combo_mode:
            return
        self._combo_mode = active
        try:
            if active:
                self._combo_bar.grid(row=1, column=0, sticky="ew",
                                     pady=(theme.PAD_S, 0))
                self._blink_on = True
                self._combo_bar.configure(fg_color=theme.COLOR_WARNING)
            else:
                self._combo_bar.grid_forget()
        except Exception:
            pass
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.set_combo_mode(active)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Slot düzenleme
    # ------------------------------------------------------------------

    def _edit_slot(self, slot: str) -> None:
        """Verilen slot için eylem düzenleme diyaloğunu açar."""
        action = dict(self.get_action(slot))
        if not (action.get("name") or "").strip():
            action["name"] = self.default_slot_name(slot)
        open_action_editor(self, slot, self.slot_title(slot), action,
                           self.os_key(), self._on_action_saved)

    def _on_action_saved(self, slot: str, action: dict) -> None:
        """Düzenleme diyaloğundan dönen eylemi yapılandırmaya yazar."""
        name = (action.get("name") or "").strip() or self.default_slot_name(slot)
        try:
            self.cfg.set_action(self.os_key(), slot, action.get("type", "none"),
                                action.get("value", ""), name)
        except Exception as error:
            self.set_status(f"Kaydedilemedi: {error}", theme.COLOR_DANGER)
            return

        if slot in KEY_IDS and getattr(self, "key_grid", None) is not None:
            self.key_grid.refresh()
        elif slot in COMBO_IDS and getattr(self, "combo_matrix", None) is not None:
            self.combo_matrix.refresh()
        elif slot in ENCODER_IDS and getattr(self, "encoder_panel", None) is not None:
            self.encoder_panel.refresh()

        self._mark_dirty(True)
        # Bağlı telefonlar yeni adı anında görsün.
        self._publish_mobile_state()

        # Enkoder slotuna eylem atandıysa ve mod HID ise: bu eylem HOST
        # moduna geçilmeden ÇALIŞMAZ. Kullanıcıyı hemen uyar.
        if slot in ENCODER_IDS and self._encoder_mode() != "host" \
                and str((action or {}).get("type", "none")) != "none":
            self.set_status(
                f"{self.slot_title(slot)} kaydedildi — ancak enkoder HID "
                "modunda çalışmaz; HOST'a geçin.", theme.COLOR_WARNING)
            return

        self.set_status(f"{self.slot_title(slot)} güncellendi — otomatik kaydedilir.", theme.COLOR_WARNING)

    def _on_key_drop(self, slot: str, action: dict) -> None:
        """Tuş kartına bırakılan dosya/klasör/uygulama/adresi slota atar.

        :class:`KeyGrid` yalnızca geçerli bir eyleme çözülen bırakmalarda
        çağırır; yapılandırmaya yazma, panelleri tazeleme ve kirli işaretleme
        :meth:`_on_action_saved` üzerinden yapılır.

        Args:
            slot: ``K1``..``K10`` arası işlev tuşu slotu.
            action: ``{"type", "value", "name"}`` eylem sözlüğü.
        """
        if slot not in KEY_IDS or not isinstance(action, dict):
            return
        self._on_action_saved(slot, dict(action))
        name = (action.get("name") or "").strip() or self.default_slot_name(slot)
        self.set_status(f"Tuş {slot[1:]}: {name} atandı (sürükle-bırak) — otomatik kaydedilir.", theme.COLOR_SUCCESS)
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.flash(slot)
            except Exception:
                pass

    def _on_special_card(self, key: str) -> None:
        """Izgaradaki ENC / COMBO / OS kartlarının tıklamalarını yönlendirir."""
        if key == "ENC":
            try:
                self.tabview.set("Enkoder")
            except Exception:
                pass
        elif key == "COMBO":
            try:
                self.tabview.set("Combolar")
            except Exception:
                pass
        elif key == "OS":
            self._toggle_os()

    def _toggle_os(self) -> None:
        """Windows ⇄ macOS profil geçişini uygular ve cihaza bildirir."""
        new_key = "mac" if self.os_key() == "windows" else "windows"
        try:
            self.runner.set_os_key(new_key)
        except Exception:
            pass
        if self.link is not None:
            try:
                self.link.set_os(new_key)
            except Exception:
                pass
        self._update_os_indicator()
        self.refresh_all()
        # Yeni profilin enkoder modu farklı olabilir; cihazı hizala.
        self._sync_device_encoder_mode()
        self.set_status(f"Profil değişti: {'macOS' if new_key == 'mac' else 'Windows'}",
                        theme.COLOR_ACCENT)

    # ------------------------------------------------------------------
    # Enkoder modu
    # ------------------------------------------------------------------

    def _encoder_mode(self) -> str:
        """Aktif profildeki enkoder modunu döndürür (``"hid"`` / ``"host"``)."""
        try:
            mode = self.cfg.encoder_mode(self.os_key())
            return "host" if str(mode).lower() == "host" else "hid"
        except Exception:
            return "hid"

    def _sync_device_encoder_mode(self) -> None:
        """Aktif profilin enkoder modunu cihaza gönderir.

        Profil veya OS değiştiğinde ``encoder.mode`` da değişebilir. Cihazın
        NVS'indeki mod ile ``config.json`` ayrışırsa enkoder hem cihazda
        (HID ses tuşu) hem PC'de (atanmış eylem) iş yapar — yani **çift
        eylem** olur. Bu yüzden her değişimde cihaz yeniden hizalanır.
        """
        if self.link is None:
            return
        try:
            self.link.set_encoder_mode(self._encoder_mode())
        except Exception:
            pass

    def _on_encoder_mode_change(self, mode: str) -> None:
        """Enkoder modu değiştiğinde yapılandırmayı, cihazı ve panelleri günceller."""
        clean = "host" if (mode or "hid").lower() == "host" else "hid"
        try:
            self.cfg.set_encoder_mode(self.os_key(), clean)
        except Exception:
            pass
        self._mark_dirty(True)   # otomatik kayıt

        if self.link is not None:
            try:
                self.link.set_encoder_mode(clean)
            except Exception:
                pass

        panel = getattr(self, "encoder_panel", None)
        if panel is not None:
            try:
                panel.set_mode(clean)
            except Exception:
                pass
        device = getattr(self, "device_panel", None)
        if device is not None:
            try:
                device.set_mode(clean)
            except Exception:
                pass
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.set_encoder_mode(clean)
            except Exception:
                pass

        self._mark_dirty(True)
        self.set_status(f"Enkoder modu: {clean.upper()}", theme.COLOR_ACCENT)

    # ------------------------------------------------------------------
    # Profil yönetimi
    # ------------------------------------------------------------------

    def _profile_names(self) -> list[str]:
        """Yapılandırmadaki profil adlarını döndürür."""
        try:
            names = self.cfg.list_profiles()
            if names:
                return [str(n) for n in names]
        except Exception:
            pass
        return ["Varsayilan"]

    def _active_profile_name(self) -> str:
        """Aktif profil adını döndürür."""
        try:
            value = self.cfg.active_profile_name()
            if value:
                return str(value)
        except Exception:
            pass
        names = self._profile_names()
        return names[0] if names else "Varsayilan"

    def _sync_profile_menus(self) -> None:
        """Yan paneldeki ve ayarlardaki profil listelerini eşitler."""
        names = self._profile_names()
        active = self._active_profile_name()
        if active not in names and names:
            active = names[0]
        for menu, variable in (
            (getattr(self, "_profile_menu", None), getattr(self, "_profile_var", None)),
            (getattr(self, "_settings_profile_menu", None),
             getattr(self, "_settings_profile_var", None)),
        ):
            if menu is None or variable is None:
                continue
            try:
                menu.configure(values=names)
                variable.set(active)
            except Exception:
                pass

    def _on_profile_selected(self, name: str) -> None:
        """Kullanıcı profil değiştirdiğinde yapılandırmayı ve arayüzü günceller."""
        if not name or name == self._active_profile_name():
            self._sync_profile_menus()
            return
        try:
            self.cfg.set_active_profile(name)
        except Exception as error:
            self.set_status(f"Profil değiştirilemedi: {error}", theme.COLOR_DANGER)
            self._sync_profile_menus()
            return
        failure = self._consume_error()
        if failure:
            self.set_status(f"Profil değiştirilemedi: {failure}", theme.COLOR_DANGER)
            self._sync_profile_menus()
            return
        self.refresh_all()
        self._update_os_indicator()
        # Yeni profilin enkoder modu farklı olabilir; cihazı hizala.
        self._sync_device_encoder_mode()
        self._mark_dirty(True)
        self.set_status(f"Aktif profil: {name}", theme.COLOR_ACCENT)

    def _add_profile(self) -> None:
        """Yeni bir boş profil ekler."""
        name = self._new_profile_entry.get().strip()
        if not name:
            self.set_status("Önce yeni profil adını yaz.", theme.COLOR_WARNING)
            return
        if name in self._profile_names():
            self.set_status("Bu adda bir profil zaten var.", theme.COLOR_WARNING)
            return
        try:
            self.cfg.add_profile(name)
        except Exception as error:
            self.set_status(f"Profil eklenemedi: {error}", theme.COLOR_DANGER)
            return
        failure = self._consume_error()
        if failure:
            self.set_status(f"Profil eklenemedi: {failure}", theme.COLOR_DANGER)
            return
        self._new_profile_entry.delete(0, "end")
        self._sync_profile_menus()
        self._mark_dirty(True)
        self.set_status(f"Profil eklendi: {name}", theme.COLOR_SUCCESS)

    def _copy_profile(self) -> None:
        """Aktif profili yeni bir adla kopyalar."""
        name = self._new_profile_entry.get().strip()
        source = self._active_profile_name()
        if not name:
            self.set_status("Kopyanın adını yaz.", theme.COLOR_WARNING)
            return
        if name in self._profile_names():
            self.set_status("Bu adda bir profil zaten var.", theme.COLOR_WARNING)
            return
        try:
            self.cfg.add_profile(name)
            failure = self._consume_error()
            if failure:
                self.set_status(f"Profil kopyalanamadı: {failure}", theme.COLOR_DANGER)
                return
            profiles = self.cfg.data.get("profiles", {})
            if source in profiles:
                # Derin kopya: iki profil aynı sözlüğü paylaşmamalı.
                profiles[name] = json.loads(json.dumps(profiles[source]))
        except Exception as error:
            self.set_status(f"Profil kopyalanamadı: {error}", theme.COLOR_DANGER)
            return
        self._new_profile_entry.delete(0, "end")
        self._sync_profile_menus()
        self._mark_dirty(True)
        self.set_status(f"'{source}' profili '{name}' adıyla kopyalandı.",
                        theme.COLOR_SUCCESS)

    def _delete_profile(self) -> None:
        """Seçili profili siler (en az bir profil kalmak zorundadır)."""
        name = self._settings_profile_var.get()
        if len(self._profile_names()) <= 1:
            self.set_status("Son profil silinemez.", theme.COLOR_WARNING)
            return
        confirmed = messagebox.askyesno(
            "Profili Sil",
            f"'{name}' profili ve içindeki tüm tuş atamaları silinecek.\nDevam edilsin mi?",
            parent=self)
        if not confirmed:
            return
        try:
            self.cfg.delete_profile(name)
        except Exception as error:
            self.set_status(f"Profil silinemedi: {error}", theme.COLOR_DANGER)
            return
        failure = self._consume_error()
        if failure:
            self.set_status(f"Profil silinemedi: {failure}", theme.COLOR_DANGER)
            return
        self._sync_profile_menus()
        self.refresh_all()
        self._mark_dirty(True)
        self.set_status(f"Profil silindi: {name}", theme.COLOR_SUCCESS)

    # ------------------------------------------------------------------
    # Ayarlar sekmesi eylemleri
    # ------------------------------------------------------------------

    def _on_theme_change(self, label: str) -> None:
        """Tema seçimini uygular ve yapılandırmaya yazar."""
        mode = THEME_LABELS.get(label, "Dark")
        applied = theme.apply_theme(mode)
        try:
            self._ui_settings()["theme"] = applied
        except Exception:
            pass
        self._mark_dirty(True)

        # Kartların rengi çalışma anında `configure` ile veriliyor (eylem
        # tipine göre kenarlık, flash sönümlemesi vb.); CTk yalnızca kendi
        # bildiği tuple renkleri otomatik günceller. Bu yüzden tema değişince
        # panelleri yeniden çizdiriyoruz ki hepsi yeni moda geçsin.
        try:
            self.refresh_all()
            self._update_os_indicator()
            self._update_link_indicator()
            # LED3 (combo) yalnızca _set_combo_mode yolundan boyanıyor ve
            # rengi çağrı anında çözülüyor; tema değişince eski modun
            # tonunda kalmasın diye burada yeniden yazdırıyoruz.
            grid = getattr(self, "key_grid", None)
            if grid is not None:
                grid.set_combo_mode(self._combo_mode)
        except Exception:
            pass

        self.set_status(f"Tema: {label}", theme.COLOR_ACCENT)

    def _on_autostart_toggle(self) -> None:
        """Otomatik başlatma anahtarını işler."""
        enabled = bool(self._autostart_var.get())
        ok, message = set_autostart(enabled)
        try:
            self.cfg.set_autostart_flag(enabled and ok)
        except Exception:
            pass
        if not ok:
            self._autostart_var.set(autostart_enabled())
        self._mark_dirty(True)
        self.set_status(message, theme.COLOR_SUCCESS if ok else theme.COLOR_DANGER)

    def _on_tray_toggle(self) -> None:
        """Tepsiye küçültme tercihini yapılandırmaya yazar."""
        value = bool(self._tray_var.get())
        try:
            self._ui_settings()["minimize_to_tray"] = value
        except Exception:
            pass
        self._mark_dirty(True)
        if value and (self.tray is None or not getattr(self.tray, "available", False)):
            self.set_status(
                "Tepsi bu ortamda kullanılamıyor; pencere kapatılınca uygulama kapanır.",
                theme.COLOR_WARNING)
        else:
            self.set_status("Tepsiye küçültme tercihi güncellendi.", theme.COLOR_ACCENT)

    def _on_acc_prompt_toggle(self) -> None:
        """Erişilebilirlik izni uyarısının gösterilip gösterilmeyeceğini ayarlar."""
        goster = bool(self._acc_prompt_var.get())
        try:
            self._ui_settings()["hide_accessibility_prompt"] = not goster
        except Exception:
            pass
        self._mark_dirty(True)
        self.set_status(
            "İzin uyarısı açılışta gösterilecek." if goster
            else "İzin uyarısı gizlendi.", theme.COLOR_ACCENT)

    def _on_led_colors_toggle(self) -> None:
        """Gelişmiş LED renk bölümünün görünürlüğünü ayarlar ve uygular."""
        value = bool(self._led_colors_var.get())
        try:
            self._ui_settings()["show_led_colors"] = value
        except Exception:
            pass
        self._mark_dirty(True)
        panel = getattr(self, "device_panel", None)
        if panel is not None:
            try:
                panel.set_color_section_visible(value)
            except Exception:
                pass
        self.set_status(
            "Gelişmiş LED renk ayarları LED & Cihaz sekmesinde görünür."
            if value else
            "Gelişmiş LED renk ayarları gizlendi.", theme.COLOR_ACCENT)

    def _on_start_min_toggle(self) -> None:
        """Gizli başlatma tercihini yapılandırmaya yazar."""
        try:
            self._ui_settings()["start_minimized"] = bool(self._start_min_var.get())
        except Exception:
            pass
        self._mark_dirty(True)
        self.set_status("Açılış tercihi güncellendi.", theme.COLOR_ACCENT)

    def _export_config(self) -> None:
        """Yapılandırmayı seçilen dosyaya kopyalar."""
        path = filedialog.asksaveasfilename(
            parent=self, title="Yapılandırmayı Dışa Aktar",
            defaultextension=".json", initialfile="extrakeyboard-config.json",
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")])
        if not path:
            return
        try:
            self.cfg.export_to(path)
        except Exception as error:
            self.set_status(f"Dışa aktarılamadı: {error}", theme.COLOR_DANGER)
            return
        failure = self._consume_error()
        if failure:
            self.set_status(failure, theme.COLOR_DANGER)
            return
        self.set_status(f"Dışa aktarıldı: {os.path.basename(path)}", theme.COLOR_SUCCESS)

    def _import_config(self) -> None:
        """Seçilen dosyadan yapılandırmayı yükler."""
        path = filedialog.askopenfilename(
            parent=self, title="Yapılandırmayı İçe Aktar",
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")])
        if not path:
            return
        confirmed = messagebox.askyesno(
            "Yapılandırmayı İçe Aktar",
            "Mevcut ayarların üzerine yazılacak.\nDevam edilsin mi?", parent=self)
        if not confirmed:
            return
        try:
            self.cfg.import_from(path)
        except Exception as error:
            self.set_status(f"İçe aktarılamadı: {error}", theme.COLOR_DANGER)
            return
        failure = self._consume_error()
        if failure:
            self.set_status(failure, theme.COLOR_DANGER)
            return
        self._reload_settings_widgets()
        self.refresh_all()
        self._update_os_indicator()
        # import_from kendisi diske yazar; kaydedilmemiş değişiklik kalmaz.
        self._mark_dirty(False)
        self.set_status(f"İçe aktarıldı: {os.path.basename(path)}", theme.COLOR_SUCCESS)

    def _reload_settings_widgets(self) -> None:
        """İçe aktarma sonrası Ayarlar sekmesindeki kontrolleri tazeler."""
        ui_settings = self._ui_settings()
        try:
            applied = theme.apply_theme(ui_settings.get("theme", "Dark"))
            self._theme_var.set(THEME_REVERSE.get(applied, "Koyu"))
            self._tray_var.set(bool(ui_settings.get("minimize_to_tray", True)))
            self._start_min_var.set(bool(ui_settings.get("start_minimized", False)))
            self._autostart_var.set(autostart_enabled())
        except Exception:
            pass

    def save_all(self) -> None:
        """Yapılandırmayı diske yazar ve cihaz ayarlarını uygular."""
        try:
            self.cfg.save()
        except Exception as error:
            self.set_status(f"Kaydedilemedi: {error}", theme.COLOR_DANGER)
            return
        failure = self._consume_error()
        if failure:
            self.set_status(failure, theme.COLOR_DANGER)
            return

        applied = False
        panel = getattr(self, "device_panel", None)
        if panel is not None:
            try:
                applied = bool(panel.apply_all_to_device())
            except Exception:
                applied = False
        if applied and self.link is not None:
            try:
                self.link.save_device_settings()
            except Exception:
                pass

        self._mark_dirty(False)
        if applied:
            self.set_status("Ayarlar kaydedildi ve cihaza uygulandı.", theme.COLOR_SUCCESS)
        else:
            self.set_status("Ayarlar kaydedildi. (Cihaz bağlı değil)", theme.COLOR_SUCCESS)

    # ------------------------------------------------------------------
    # Telefon eşlik sunucusu
    # ------------------------------------------------------------------

    def set_mobile_server(self, server) -> None:
        """Telefon eşlik sunucusunu pencereye bağlar (``app.main`` çağırır).

        Telefon sekmesi kuruluysa durum satırı, adres, QR ve anahtar
        tazelenir. Ayrıca sunucunun durum sağlayıcısı pencere verisiyle
        beslenir: OS/profil arayüzden elle değiştirilince telefon ekranı da
        aynı profili görür (cihazın son bildirdiği modla sınırlı kalmaz).

        Args:
            server: :class:`app.core.mobile_server.MobileServer` örneği
                (``None`` olabilir).
        """
        self.mobile_server = server
        if server is not None:
            try:
                server.set_state_provider(self._mobile_state_snapshot)
            except Exception:
                pass
        self._refresh_phone_panel()
        self._publish_mobile_state()

    def _mobile_settings(self) -> dict:
        """Telefon sunucusu ayarlarını yapılandırmadan savunmacı biçimde okur.

        ``ConfigManager.get_mobile_settings`` yoksa (eski yapılandırma
        katmanı) spesifikasyondaki varsayılanlara düşülür.

        Returns:
            ``{"enabled": bool, "port": int}`` sözlüğü (kopya).
        """
        getter = getattr(self.cfg, "get_mobile_settings", None)
        if callable(getter):
            try:
                settings = getter()
                if isinstance(settings, dict):
                    return settings
            except Exception:
                pass
        return {"enabled": True, "port": 8756}

    def _mobile_state_snapshot(self) -> dict:
        """Telefon arayüzüne sunulacak anlık durumu üretir.

        **HTTP thread'lerinden çağrılır**; yapılandırmaya HİÇ dokunmaz:
        ``cfg.profile()`` eksik bölümleri tamamlayabildiği (yani yazabildiği)
        için burada çağrılması güvenli değildir. Onun yerine ana thread'in
        :meth:`_rebuild_mobile_cfg_cache` ile hazırladığı hazır sözlük tek
        atomik referans okumasıyla kullanılır; yalnızca bağlantı durumu
        (basit öznitelikler) canlı okunur. Hatada ``{}`` döner.
        """
        try:
            cache = getattr(self, "_mobile_cfg_cache", None) or {}

            connected = False
            port = None
            link = self.link
            if link is not None:
                try:
                    connected = bool(link.responsive)
                    port = link.port_name
                except Exception:
                    connected, port = False, None

            return {
                "app": "ExtraKeyboard MK1",
                "profile": cache.get("profile", ""),
                "os": cache.get("os", "windows"),
                "link": connected,
                "port": port,
                "combo": bool(self._combo_mode),
                "keys": cache.get("keys", {}),
                "encoder": cache.get("encoder", {}),
            }
        except Exception:
            return {}

    def _rebuild_mobile_cfg_cache(self) -> None:
        """Yapılandırmadan türeyen telefon durumunu ANA thread'de hazırlar.

        Sonuç tek atamayla ``_mobile_cfg_cache``'e konur (atama GIL ile
        atomiktir); HTTP thread'leri yalnızca bu hazır kopyayı okur ve
        paylaşılan yapılandırma sözlüğüne asla dokunmaz.
        """
        cache: dict = {"profile": "", "os": "windows", "keys": {}, "encoder": {}}
        try:
            os_key = self.os_key()
            cache["os"] = os_key

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
            cache["keys"] = keys
            cache["encoder"] = encoder

            try:
                cache["profile"] = str(self.cfg.active_profile_name())
            except Exception:
                pass
        except Exception:
            pass
        self._mobile_cfg_cache = cache

    def _publish_mobile_state(self) -> None:
        """Bağlı telefonlara güncel durum anlık görüntüsünü yollar (varsa).

        Yayın hiçbir zaman bloklamaz; sunucu yoksa veya kapalıysa sessizce
        geçilir. Yayından önce yapılandırma önbelleği ana thread'de tazelenir
        (bkz. :meth:`_rebuild_mobile_cfg_cache`).
        """
        self._rebuild_mobile_cfg_cache()
        server = getattr(self, "mobile_server", None)
        if server is None:
            return
        try:
            server.publish_state()
        except Exception:
            pass

    def _refresh_phone_panel(self) -> None:
        """Telefon sekmesindeki durum satırını, adresi, QR'ı ve anahtarı tazeler."""
        if not getattr(self, "_phone_panel_ready", False):
            return
        server = getattr(self, "mobile_server", None)
        running = bool(getattr(server, "running", False))
        url = str(getattr(server, "url", "") or "") if running else ""

        try:
            if server is None:
                self._phone_dot.configure(text_color=theme.COLOR_DISABLED)
                self._phone_status_label.configure(
                    text="Sunucu bu oturumda kullanılamıyor",
                    text_color=theme.COLOR_TEXT_MUTED)
            elif running:
                self._phone_dot.configure(text_color=theme.COLOR_SUCCESS)
                self._phone_status_label.configure(
                    text="Sunucu çalışıyor", text_color=theme.COLOR_SUCCESS)
            else:
                last_error = str(getattr(server, "last_error", "") or "")
                self._phone_dot.configure(text_color=theme.COLOR_DISABLED)
                self._phone_status_label.configure(
                    text=("Sunucu kapalı" + (f" — {last_error}" if last_error else "")),
                    text_color=theme.COLOR_TEXT_DIM)
            self._phone_url_label.configure(text=url or "—")
        except Exception:
            pass

        try:
            self._phone_enabled_var.set(running)
        except Exception:
            pass

        self._refresh_phone_client_count()
        self._update_phone_qr(url)

    def _refresh_phone_client_count(self) -> None:
        """Bağlı telefon sayısı etiketini sunucudan okuyup günceller."""
        server = getattr(self, "mobile_server", None)
        try:
            if server is not None and bool(getattr(server, "running", False)):
                count = int(getattr(server, "client_count", 0) or 0)
                self._phone_clients_label.configure(text=f"Bağlı telefon: {count}")
            else:
                self._phone_clients_label.configure(text="Bağlı telefon: —")
        except Exception:
            pass

    def _update_phone_qr(self, url: str) -> None:
        """Verilen adres için QR karekod üretir (adres değişmediyse dokunmaz).

        ``qrcode`` paketi kurulu değilse görsel yerine kurulum ipucu gösterilir;
        uygulamanın geri kalanı etkilenmez.
        """
        if url == self._phone_qr_url:
            return
        self._phone_qr_url = url

        if not url:
            self._phone_qr_image = None
            try:
                self._phone_qr_label.pack_forget()
                self._phone_qr_hint.configure(
                    text="Sunucu açılınca QR kod burada görünür.")
                self._phone_qr_hint.pack(fill="x", padx=theme.PAD_M,
                                         pady=(0, theme.PAD_M))
            except Exception:
                pass
            return

        try:
            import qrcode
            from PIL import Image
        except ImportError:
            try:
                self._phone_qr_label.pack_forget()
                self._phone_qr_hint.configure(
                    text="QR kod için 'qrcode' paketi gerekli:  pip install qrcode\n"
                         f"Adresi elle de açabilirsin: {url}")
                self._phone_qr_hint.pack(fill="x", padx=theme.PAD_M,
                                         pady=(0, theme.PAD_M))
            except Exception:
                pass
            return

        try:
            maker = qrcode.QRCode(border=2)
            maker.add_data(url)
            maker.make(fit=True)
            image = maker.make_image(fill_color="black", back_color="white")
            pil_image = image.get_image() if hasattr(image, "get_image") else image
            pil_image = pil_image.convert("RGB").resize((220, 220), Image.NEAREST)
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image,
                                     size=(220, 220))
            # Çöp toplayıcı görseli erkenden bırakmasın diye referans tutulur.
            self._phone_qr_image = ctk_image
            self._phone_qr_hint.pack_forget()
            self._phone_qr_label.configure(image=ctk_image, text="")
            self._phone_qr_label.pack(anchor="w", padx=theme.PAD_M,
                                      pady=(0, theme.PAD_M))
        except Exception as error:
            try:
                self._phone_qr_label.pack_forget()
                self._phone_qr_hint.configure(text=f"QR üretilemedi: {error}")
                self._phone_qr_hint.pack(fill="x", padx=theme.PAD_M,
                                         pady=(0, theme.PAD_M))
            except Exception:
                pass

    def _tick_phone_panel(self) -> None:
        """Telefon sekmesi göstergelerini düzenli aralıklarla tazeler."""
        if self._closing:
            return
        try:
            self._refresh_phone_panel()
        except Exception:
            pass
        try:
            self.after(PHONE_POLL_MS, self._tick_phone_panel)
        except Exception:
            pass

    def _copy_phone_url(self) -> None:
        """Sunucu adresini panoya kopyalar (pyperclip yoksa Tk panosu)."""
        server = getattr(self, "mobile_server", None)
        url = str(getattr(server, "url", "") or "")
        if not url:
            self.set_status("Kopyalanacak adres yok — önce sunucuyu aç.",
                            theme.COLOR_WARNING)
            return
        copied = False
        try:
            import pyperclip
            pyperclip.copy(url)
            copied = True
        except Exception:
            try:
                self.clipboard_clear()
                self.clipboard_append(url)
                self.update_idletasks()
                copied = True
            except Exception:
                pass
        if copied:
            self.set_status(f"Adres panoya kopyalandı: {url}", theme.COLOR_SUCCESS)
        else:
            self.set_status("Adres panoya kopyalanamadı.", theme.COLOR_DANGER)

    def _on_phone_toggle(self) -> None:
        """Telefon sunucusu anahtarını işler: ayarı yazar, sunucuyu açar/kapatır.

        Tercih ``config.json``'a :meth:`ConfigManager.set_mobile_settings`
        ile işlenir; kalıcı olması için AYARLARI KAYDET gerekir (kirli
        işaretlenir).
        """
        enabled = bool(self._phone_enabled_var.get())

        setter = getattr(self.cfg, "set_mobile_settings", None)
        if callable(setter):
            try:
                setter(enabled=enabled)
            except Exception:
                pass

        server = getattr(self, "mobile_server", None)
        if server is None:
            self.set_status("Telefon sunucusu bu oturumda kullanılamıyor.",
                            theme.COLOR_WARNING)
            self._refresh_phone_panel()
            return

        if enabled:
            try:
                started, info = server.start()
            except Exception as error:
                started, info = False, str(error)
            if started:
                self.set_status(f"Telefon sunucusu açıldı: {info}",
                                theme.COLOR_SUCCESS)
                self._publish_mobile_state()
            else:
                self.set_status(f"Telefon sunucusu açılamadı: {info}",
                                theme.COLOR_DANGER)
        else:
            try:
                server.stop()
            except Exception:
                pass
            self.set_status("Telefon sunucusu kapatıldı.", theme.COLOR_ACCENT)

        self._mark_dirty(True)
        self._refresh_phone_panel()

    # ------------------------------------------------------------------
    # Cihaz olayları — THREAD SINIRI
    # ------------------------------------------------------------------

    def push_device_event(self, event) -> None:
        """Cihaz olayını kuyruğa alır. **Arka plan thread'inden çağrılır.**

        Bu metot hiçbir Tkinter bileşenine dokunmaz; yalnızca kilitli bir
        kuyruğa yazar ve ``after(0, ...)`` ile ana thread'i uyandırır.
        """
        with self._queue_lock:
            self._pending.append(event)
        try:
            self.after(0, self._drain_events)
        except RuntimeError:
            # Olay döngüsü henüz başlamamış ("main thread is not in main loop")
            # veya pencere kapanmış olabilir. Olay KUYRUKTA KALIR; kaybolmasın
            # diye _pump_events() bir sonraki turda işler.
            pass
        except Exception:
            pass

    def _maybe_show_accessibility_prompt(self) -> None:
        """macOS'ta Erişilebilirlik izni eksikse TEK SEFERLİK diyalog gösterir.

        İzin zaten verilmişse hiçbir şey görünmez. Kullanıcı "Daha Sonra"
        derse bu oturumda bir daha sorulmaz; metin/kısayol eylemleri
        yalnızca durum çubuğunda kibar bir yol tarifi gösterir (sistem
        penceresi eylem sırasında asla açılmaz).
        """
        try:
            if platform_utils.accessibility_granted():
                return
        except Exception:
            return
        # Kullanıcı daha önce "Bir daha sorma" dediyse hiç gösterme.
        # TEK İSTİSNA: uygulama macOS'un geçici kopyasından çalışıyorsa
        # (App Translocation) bu uyarı bastırılmaz — orada izin vermek
        # sorunu çözmez, uygulamanın taşınması gerekir ve kullanıcı bunu
        # bilmeden makro/metin eylemlerinin neden çalışmadığını anlayamaz.
        try:
            gecici_kopya = platform_utils.gecici_konumdan_mi_calisiyor()
        except Exception:
            gecici_kopya = False
        try:
            if (not gecici_kopya
                    and bool(self._ui_settings().get("hide_accessibility_prompt",
                                                     False))):
                return
        except Exception:
            pass
        if getattr(self, "_erisim_diyalogu_gosterildi", False):
            return
        # Uygulama arka planda (gizli pencereyle) başlatıldıysa hiçbir
        # diyalog açılmaz: gizli pencerenin üstünde açılan pencere macOS'ta
        # boş çizilir, üstelik arka planda başlatmayı seçen kullanıcıyı
        # ekrana zorla pencere getirerek rahatsız etmek de doğru olmaz.
        try:
            if self.wm_state() != "normal" or not self.winfo_ismapped():
                return
        except Exception:
            pass
        self._erisim_diyalogu_gosterildi = True

        try:
            win = ctk.CTkToplevel(self)
            win.title("Erişilebilirlik İzni")
            win.geometry("580x470")
            win.resizable(False, False)
            win.configure(fg_color=theme.COLOR_BG)
            win.transient(self)

            ctk.CTkLabel(win, text="Tek seferlik kurulum izni",
                         font=theme.font(17, True), text_color=theme.COLOR_TEXT,
                         anchor="w").pack(fill="x", padx=theme.PAD_L,
                                          pady=(theme.PAD_L, theme.PAD_S))
            # İznin hangi uygulamaya verileceği çalıştırma biçimine bağlıdır:
            # .app paketinde izni ExtraKeyboard'un kendisi alır; kaynak koddan
            # çalıştırıldığında ise süreci Terminal başlattığı için izin
            # Terminal'e verilmelidir.
            paketli = bool(getattr(sys, "frozen", False))
            hedef_ad = "ExtraKeyboard" if paketli else "Terminal"
            # macOS uygulamayı geçici bir kopyadan çalıştırıyorsa izin
            # vermenin faydası yok: yol her açılışta değiştiği için izin
            # ertesi açılışta kaybolur. Kullanıcıya izin adımları yerine
            # asıl çözüm (uygulamayı taşımak) anlatılır.
            gecici = False
            try:
                gecici = platform_utils.gecici_konumdan_mi_calisiyor()
            except Exception:
                pass
            ctk.CTkLabel(
                win,
                text=("ÖNCE UYGULAMAYI TAŞIYIN — izin vermek şu hâlde işe "
                      "yaramaz.\n\n"
                      "macOS, internetten indirilen uygulamayı geçici ve her "
                      "açılışta adı değişen bir kopyadan çalıştırıyor. Bu "
                      "yüzden verdiğiniz izin bir sonraki açılışta kayboluyor "
                      "ve izin hep yeniden isteniyor.\n\n"
                      "1. Bu uygulamayı kapatın.\n"
                      "2. ExtraKeyboard uygulamasını Finder'da UYGULAMALAR "
                      "klasörüne SÜRÜKLEYİN.\n"
                      "3. Uygulamayı oradan açın.\n"
                      "4. Bu pencere yeniden çıkarsa izni o zaman verin — "
                      "artık kalıcı olacaktır."
                      if gecici else
                      "Metin yazma ve kısayol gönderme eylemleri için macOS "
                      "Erişilebilirlik izni gerekir. Bu izin BİR KEZ verilir "
                      "ve kalıcıdır; uygulama bir daha sormaz.\n\n"
                      "1. Aşağıdaki düğmeyle Sistem Ayarları açılır.\n"
                      f"2. Listede {hedef_ad}'in anahtarını açın.\n"
                      "3. Bu uygulamayı kapatıp yeniden başlatın.\n\n"
                      "Komut, URL ve uygulama açma eylemleri bu izne ihtiyaç "
                      "duymaz, şimdi de çalışır."),
                font=theme.font(12), text_color=theme.COLOR_TEXT_DIM,
                anchor="w", justify="left", wraplength=540,
            ).pack(fill="x", padx=theme.PAD_L)

            # Vurgulu NOT kutusu: iznin hangi uygulamaya verileceği ve o
            # uygulama listede görünmüyorsa ne yapılacağı.
            not_kutu = ctk.CTkFrame(win, fg_color=theme.COLOR_PANEL,
                                    corner_radius=theme.RADIUS_SMALL,
                                    border_width=1,
                                    border_color=theme.COLOR_WARNING)
            not_kutu.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_S, 0))
            ctk.CTkLabel(not_kutu, text="⚠ ÖNEMLİ NOT",
                         font=theme.font(12, True),
                         text_color=theme.COLOR_WARNING, anchor="w").pack(
                fill="x", padx=theme.PAD_M, pady=(theme.PAD_S, 0))
            ctk.CTkLabel(
                not_kutu,
                text=("Uygulama şu an şuradan çalışıyor:\n"
                      "…/AppTranslocation/… (geçici kopya)\n"
                      "Alternatif çözüm: indirdiğiniz klasörde Terminal açıp "
                      "şunu çalıştırın:  xattr -cr <klasör>  — ardından "
                      "uygulamayı yeniden açın."
                      if gecici else
                      "Listede ExtraKeyboard görünmüyorsa: + düğmesine basıp "
                      "ExtraKeyboard uygulamasını seçin (Uygulamalar "
                      "klasöründen ya da uygulamayı açtığınız yerden).\n"
                      "Uygulamayı başka bir klasöre taşırsanız izni yeniden "
                      "vermeniz gerekebilir."
                      if paketli else
                      "Erişilebilirlik listesinde açılması gereken uygulama "
                      "TERMİNAL'dir — ExtraKeyboard değil (masaüstü kısayolu "
                      "listeye eklenemez; uygulamayı Terminal çalıştırır).\n"
                      "Terminal listede görünmüyorsa: Finder → İzlenceler "
                      "klasöründen Terminal'i listenin üzerine sürükleyip "
                      "bırakın; ya da + penceresinde ⌘⇧G basıp şu yolu yazın: "
                      "/System/Applications/Utilities/Terminal.app"),
                font=theme.font(11), text_color=theme.COLOR_TEXT,
                anchor="w", justify="left", wraplength=520,
            ).pack(fill="x", padx=theme.PAD_M, pady=(2, theme.PAD_S))

            satir = ctk.CTkFrame(win, fg_color="transparent")
            satir.pack(fill="x", padx=theme.PAD_L, pady=theme.PAD_L)

            def _izin_ver() -> None:
                try:
                    platform_utils.request_accessibility()
                except Exception:
                    pass
                self.set_status(
                    "Sistem Ayarları açıldı — izni verdikten sonra uygulamayı "
                    "yeniden başlatın.", theme.COLOR_WARNING)
                win.destroy()

            ctk.CTkButton(satir, text="İzin Ver (Sistem Ayarları'nı Aç)",
                          height=38, fg_color=theme.COLOR_ACCENT,
                          hover_color=theme.COLOR_ACCENT_DARK,
                          font=theme.font(13, True),
                          command=_izin_ver).pack(side="left")
            def _bir_daha_sorma() -> None:
                try:
                    self._ui_settings()["hide_accessibility_prompt"] = True
                except Exception:
                    pass
                self._mark_dirty(True)
                self.set_status(
                    "İzin uyarısı bir daha gösterilmeyecek. (Ayarlar → "
                    "Davranış'tan geri açabilirsiniz.)", theme.COLOR_ACCENT)
                win.destroy()

            ctk.CTkButton(satir, text="Daha Sonra", height=38, width=110,
                          fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                          hover_color=theme.COLOR_DANGER,
                          font=theme.font(12),
                          command=win.destroy).pack(side="right")
            ctk.CTkButton(satir, text="Bir Daha Sorma", height=38, width=140,
                          fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                          hover_color=theme.COLOR_DISABLED,
                          font=theme.font(12),
                          command=_bir_daha_sorma).pack(side="right",
                                                        padx=(0, theme.PAD_S))

            def _odakla() -> None:
                try:
                    win.lift()
                    win.focus_force()
                except Exception:
                    pass
            win.after(140, _odakla)
        except Exception:
            pass

    def _pump_events(self) -> None:
        """Kuyrukta kalmış olayları düzenli aralıklarla işler (güvenlik ağı).

        ``push_device_event`` normalde ``after(0, ...)`` ile ana thread'i
        uyandırır; o çağrı düşerse olaylar burada işlenir.
        """
        if self._closing:
            return
        try:
            if self._pending:
                self._drain_events()
        except Exception:
            pass
        try:
            self.after(EVENT_PUMP_MS, self._pump_events)
        except Exception:
            pass

    def _drain_events(self) -> None:
        """Kuyruktaki tüm olayları ana thread'de işler."""
        while True:
            with self._queue_lock:
                if not self._pending:
                    return
                event = self._pending.popleft()
            try:
                self._handle_event(event)
            except Exception:
                continue

    def _handle_event(self, event) -> None:
        """Tek bir cihaz olayını işler (yalnızca ana thread)."""
        kind = str(getattr(event, "kind", "") or "").lower()
        slot = getattr(event, "slot", None)
        raw = str(getattr(event, "raw", "") or "")
        payload = getattr(event, "payload", None)
        if not isinstance(payload, dict):
            payload = {}
        tokens = raw.split()
        upper = raw.upper()

        # Olay logu: kalp atışları ve OTOMATİK canlılık yanıtları gizlenir.
        # Uygulama saniyede bir `CMD PING` gönderdiği için (bkz.
        # device.PING_INTERVAL) bunların `ACK PING` yanıtı loglansaydı
        # gerçek olaylar (tuş, combo, enkoder) akış içinde kaybolurdu.
        # Kullanıcı "PING Gönder" düğmesine bastığında yanıt İSTENEREK
        # gösterilir (device_panel.send_ping bayrağı).
        panel = getattr(self, "device_panel", None)
        if panel is not None and kind != "hb":
            gizle = False
            if kind == "ack" and str(payload.get("command", "")).upper() == "PING":
                gizle = not getattr(panel, "_manuel_ping_bekliyor", False)
                if not gizle:
                    panel._manuel_ping_bekliyor = False
            if not gizle:
                try:
                    panel.append_event(raw or f"{kind} {slot or ''}".strip())
                except Exception:
                    pass

        if kind == "key":
            self._handle_key_event(slot, tokens, upper, payload)
        elif kind == "combo":
            self._handle_combo_event(slot, tokens, payload)
        elif kind == "mode":
            active = payload.get("combo")
            self._set_combo_mode(bool(active) if isinstance(active, bool)
                                 else "COMBO_ON" in upper)
        elif kind == "os":
            self._handle_os_event(upper, payload)
        elif kind == "enc":
            self._handle_encoder_event(slot, tokens, upper)
        elif kind == "link":
            self._update_link_indicator()
            message = payload.get("message") or raw
            if message:
                self.set_status(str(message),
                                theme.COLOR_SUCCESS if payload.get("connected")
                                else theme.COLOR_WARNING)
        elif kind == "id":
            self._handle_id_event(tokens, payload)
        elif kind == "err":
            reason = payload.get("reason") or raw
            self.set_status(f"Cihaz hatası: {reason}", theme.COLOR_DANGER)

    def _handle_key_event(self, slot, tokens: list[str], upper: str, payload: dict) -> None:
        """``EV KEY <n> DOWN|UP`` olayını işler; eylem UP kenarında çalışır."""
        key_slot = slot if isinstance(slot, str) and slot in KEY_IDS else None
        if key_slot is None and len(tokens) >= 3 and tokens[1].upper() == "KEY":
            candidate = f"K{tokens[2]}"
            if candidate in KEY_IDS:
                key_slot = candidate
        if key_slot is None:
            return

        edge = str(payload.get("edge") or payload.get("state")
                   or payload.get("action") or "").upper()
        if not edge:
            edge = "UP" if upper.endswith(" UP") else ("DOWN" if upper.endswith(" DOWN") else "")

        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.flash(key_slot)
            except Exception:
                pass

        if edge == "DOWN":
            return
        # Kenar bilgisi hiç yoksa olayı tetikleme kabul ederiz.
        self._run_slot_async(key_slot)

    def _handle_combo_event(self, slot, tokens: list[str], payload: dict) -> None:
        """``EV COMBO <a> <b>`` olayını işler."""
        cid = slot if isinstance(slot, str) and slot in COMBO_IDS else None
        if cid is None:
            first = payload.get("a")
            second = payload.get("b")
            if first is None or second is None:
                if len(tokens) >= 4 and tokens[1].upper() == "COMBO":
                    first, second = tokens[2], tokens[3]
            try:
                cid = combo_id(int(first), int(second))
            except Exception:
                cid = None
        if cid is None or cid not in COMBO_IDS:
            return

        matrix = getattr(self, "combo_matrix", None)
        if matrix is not None:
            try:
                matrix.flash(cid)
                matrix.select(cid)
            except Exception:
                pass
        self._run_slot_async(cid)

    def _handle_os_event(self, upper: str, payload: dict) -> None:
        """``EV OS WIN|MAC`` olayını işler."""
        value = str(payload.get("os") or "").upper()
        if not value:
            value = "MAC" if "MAC" in upper else ("WIN" if "WIN" in upper else "")
        if not value:
            return
        os_key = "mac" if value.startswith("MAC") else "windows"
        try:
            self.runner.set_os_key(os_key)
        except Exception:
            pass
        self._update_os_indicator()
        self.refresh_all()
        # Yeni profilin enkoder modu farklı olabilir; cihazı hizala.
        self._sync_device_encoder_mode()
        self.set_status(f"Cihaz profili değişti: {'macOS' if os_key == 'mac' else 'Windows'}",
                        theme.COLOR_ACCENT)

    def _handle_encoder_event(self, slot, tokens: list[str], upper: str) -> None:
        """``EV ENC CW|CCW|PRESS|LONG`` olayını işler."""
        enc_slot = slot if isinstance(slot, str) and slot in ENCODER_IDS else None
        if enc_slot is None:
            token = tokens[2].upper() if len(tokens) >= 3 else ""
            mapping = {"CW": "cw", "CCW": "ccw", "PRESS": "press", "LONG": "long"}
            enc_slot = mapping.get(token)
            if enc_slot is None:
                for name, value in mapping.items():
                    if upper.endswith(" " + name):
                        enc_slot = value
                        break
        if enc_slot is None:
            return

        panel = getattr(self, "encoder_panel", None)
        if panel is not None:
            try:
                panel.flash(enc_slot)
            except Exception:
                pass
        grid = getattr(self, "key_grid", None)
        if grid is not None:
            try:
                grid.flash("ENC")
            except Exception:
                pass

        # HID modunda ses kontrolünü cihaz üstlenir; PC'de eylem çalıştırmayız.
        if self._encoder_mode() == "host":
            self._run_slot_async(enc_slot)
        else:
            # Kullanıcı bu slota eylem atadıysa ama mod HID ise eylem asla
            # çalışmaz. Sessiz kalmak yerine nedenini söylüyoruz.
            try:
                eylem = self.cfg.get_action(self.os_key(), enc_slot) or {}
                if str(eylem.get("type", "none")) != "none":
                    self.set_status(
                        "Enkoder HID modunda — atadığınız eylem çalışmaz. "
                        "Enkoder sekmesinden HOST'a geçin.",
                        theme.COLOR_WARNING)
            except Exception:
                pass

    def _handle_id_event(self, tokens: list[str], payload: dict) -> None:
        """``ID <fw> <hw> <serial> <os>`` yanıtını yan panele yazar."""
        firmware = str(payload.get("fw") or "")
        hardware = str(payload.get("hw") or "")
        serial = str(payload.get("serial") or "")
        os_raw = str(payload.get("os_raw") or "")

        if firmware or hardware or serial:
            self._device_identity = (f"FW {firmware} · {hardware}\n"
                                     f"{serial} · {os_raw}").strip()
        elif len(tokens) >= 2:
            self._device_identity = " ".join(tokens[1:])
        self._update_info_box()

    def _run_slot_async(self, slot: str) -> None:
        """Slota atanmış eylemi arka plan thread'inde çalıştırır.

        Uygulama başlatmak veya kabuk komutu çalıştırmak saniyeler sürebilir;
        bu iş ana thread'de yapılırsa arayüz donar.
        """
        action = self.get_action(slot)
        if action.get("type", "none") == "none" or not (action.get("value") or "").strip():
            return

        def worker() -> None:
            try:
                result = self.runner.run(slot)
            except Exception as error:
                result = (False, str(error))
            if isinstance(result, tuple) and len(result) == 2:
                success, message = bool(result[0]), str(result[1])
            else:
                success, message = True, ""
            try:
                self.after(0, lambda: self._on_action_result(slot, success, message))
            except Exception:
                pass

        threading.Thread(target=worker, name=f"Action-{slot}", daemon=True).start()

    def _on_action_result(self, slot: str, success: bool, message: str) -> None:
        """Eylem sonucunu durum çubuğuna ve olay loguna yazar."""
        title = self.slot_title(slot)
        text = f"{title}: {message}" if message else title
        self.set_status(text, theme.COLOR_SUCCESS if success else theme.COLOR_DANGER)
        panel = getattr(self, "device_panel", None)
        if panel is not None:
            try:
                panel.append_event(f"{'OK' if success else 'HATA'} {slot} — {message}")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Pencere yönetimi
    # ------------------------------------------------------------------

    def _pencereyi_yeniden_ciz(self) -> None:
        """macOS'ta boş kalan pencere içeriğini ekrana çizdirir.

        Tk pencere içeriğini hazırlasa bile macOS pencere sunucusu ilk
        çizimi ekrana yansıtmayabilir: pencere bomboş (açık temada
        bembeyaz) görünür, ama tıklamalar alttaki gerçek widget'lara
        gittiği için uygulama çalışıyormuş gibi davranır. Uygulama arka
        planda başlatıldığında (Baslat.command ``nohup`` kullanır) ya da
        pencere açılırken başka bir uygulama öndeyse ortaya çıkar.

        Geometriye verilen bir piksellik darbe NSView'i geçersiz kılar ve
        içeriğin gerçekten çizilmesini garanti eder. Gözle görülür bir
        titreme oluşturmaz; iki adım da aynı olay döngüsü turunda biter.
        """
        try:
            self.update_idletasks()
            if sys.platform != "darwin":
                return
            gecerli = self.geometry()               # örn. "1360x848+34+64"
            boyut, ayrac, konum = gecerli.partition("+")
            genislik, _, yukseklik = boyut.partition("x")
            if not (genislik.isdigit() and yukseklik.isdigit() and ayrac):
                return
            self.geometry("%dx%s%s%s"
                          % (int(genislik) + 1, yukseklik, ayrac, konum))
            self.update_idletasks()
            self.geometry(gecerli)
            self.update_idletasks()
        except Exception:
            pass

    def _acilis_cizimi(self) -> None:
        """Açılışta pencereyi öne alır ve ilk çizimi garantiler."""
        for adim in (self.lift, self.focus_force):
            try:
                adim()
            except Exception:
                pass
        self._pencereyi_yeniden_ciz()

    def set_tray(self, tray) -> None:
        """Sistem tepsisi nesnesini pencereye bağlar.

        Gizli başlatma istendiyse asıl karar burada verilir: pencere
        ``__init__`` sırasında zaten gizlenmiştir, ama tepsi simgesi
        kullanılamıyorsa kullanıcının pencereyi geri getirecek hiçbir yolu
        kalmaz. O durumda pencere görünür kılınır (Windows'ta görev
        çubuğuna küçültülür), böylece uygulama "kayıp" olmaz.
        """
        self.tray = tray
        if not self._start_min_pending:
            return
        self._start_min_pending = False

        tray_ready = tray is not None and getattr(tray, "available", False)
        if tray_ready:
            try:
                tray.notify("Uygulama arka planda başlatıldı. "
                            "Açmak için bu simgeye tıklayın.")
            except Exception:
                pass
            return

        # Tepsi yok. macOS'ta Dock simgesi pencereyi geri getirebildiği için
        # gizli kalabilir; diğer sistemlerde görev çubuğuna küçültülür.
        if sys.platform != "darwin":
            try:
                self.deiconify()
                self.iconify()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Bağlantı kurtarma
    # ------------------------------------------------------------------

    def _on_rescan(self) -> None:
        """"Yeniden Tara" düğmesi: bağlantıyı anında baştan kurmayı dener."""
        try:
            mesaj = self.link.rescan()
        except Exception as hata:  # noqa: BLE001 - kullanıcıya anlaşılır mesaj
            self.set_status("Tarama başlatılamadı: %s" % hata,
                            theme.COLOR_DANGER)
            return
        self.set_status(mesaj, theme.COLOR_ACCENT)

    def _on_wake_device(self) -> None:
        """"Uyandır" düğmesi: karta USB'den yeniden başlatma darbesi yollar.

        Cihaz takılı görünüp el sıkışmaya yanıt vermediğinde, kabloyu fiziksel
        olarak çıkarıp takmanın yerine geçer. Kart yeniden başlayacağı için
        önce kullanıcıya sorulur.
        """
        onay = messagebox.askyesno(
            "Cihazı yeniden başlat",
            "Klavyeye yeniden başlatma darbesi gönderilecek.\n\n"
            "Bu, kabloyu çıkarıp takmakla aynı şeydir: tuş atamaları ve "
            "ayarlar SİLİNMEZ, cihaz birkaç saniye içinde geri gelir.\n\n"
            "Devam edilsin mi?",
            parent=self)
        if not onay:
            return
        try:
            mesaj = self.link.wake_device()
        except Exception as hata:  # noqa: BLE001 - kullanıcıya anlaşılır mesaj
            self.set_status("Cihaz sıfırlanamadı: %s" % hata,
                            theme.COLOR_DANGER)
            return
        self.set_status(mesaj, theme.COLOR_ACCENT)

    def show_window(self) -> None:
        """Pencereyi gizliyken geri getirir ve öne alır.

        Üç yerden çağrılır: menü çubuğu (tepsi) menüsü, macOS'ta Dock
        simgesine tıklama ve uygulama ikinci kez başlatıldığında tekil
        örnek kilidinin gönderdiği "göster" sinyali.
        """
        try:
            self.deiconify()
            # macOS'ta gizli pencere geri getirildiğinde içerik bazen
            # çizilmeden kalır (boş/beyaz pencere); çizimi burada zorlamak
            # pencerenin dolu gelmesini garantiler.
            self._pencereyi_yeniden_ciz()
            self.lift()
            self.focus_force()
            # macOS'ta arka plandaki süreç öne gelmeyebilir; kısa bir
            # "en üstte" darbesi pencereyi güvenilir biçimde öne taşır.
            if sys.platform == "darwin":
                try:
                    self.attributes("-topmost", True)
                    self.after(300, lambda: self.attributes("-topmost", False))
                except Exception:
                    pass
        except Exception:
            pass

    def ensure_visible(self) -> None:
        """Pencere gizliyse görünür kılar.

        Alt pencereler (tuş atama, combo, ayar diyalogları) gizlenmiş bir ana
        pencerenin çocuğu olarak açılırsa macOS'ta içerikleri çizilmez ve boş
        görünürler. Diyalog açan her yol önce buradan geçer.
        """
        try:
            if self.wm_state() != "normal" or not self.winfo_ismapped():
                self.show_window()
        except Exception:
            pass

    def on_close(self) -> None:
        """Pencere kapatma düğmesini işler.

        Ayarlarda "tepsiye küçült" açıksa ve tepsi kullanılabiliyorsa pencere
        gizlenir; aksi hâlde uygulama tamamen kapanır.
        """
        minimize = bool(self._ui_settings().get("minimize_to_tray", True))
        tray_ready = self.tray is not None and getattr(self.tray, "available", False)
        if minimize and tray_ready:
            self.withdraw()
            try:
                self.tray.notify("Uygulama arka planda çalışmaya devam ediyor.")
            except Exception:
                pass
            return
        self.quit_app()

    def quit_app(self) -> None:
        """Cihaz bağlantısını ve tepsiyi kapatıp uygulamadan çıkar.

        Kaydedilmemiş değişiklik varsa önce kullanıcıya sorar: değişiklikler
        yalnızca bellekte olduğu için sormadan çıkmak tüm tuş/combo/LED
        atamalarını sessizce kaybettirir.
        """
        if self._closing:
            return

        # Bekleyen otomatik kayıt varsa çıkıştan önce sessizce yaz;
        # başarılı olursa aşağıdaki soru hiç sorulmaz.
        if self._dirty:
            self._autosave_now()

        if self._dirty:
            answer = None
            try:
                # Pencere tepsiye gizlenmişse diyalog görünmez kalmasın.
                self.deiconify()
                self.lift()
            except Exception:
                pass
            try:
                answer = messagebox.askyesnocancel(
                    "Çıkış",
                    "Kaydedilmemiş değişiklikler var.\n\n"
                    "Çıkmadan önce kaydedilsin mi?\n"
                    "(Hayır = değişiklikleri at, İptal = çıkma)",
                    parent=self,
                )
            except Exception:
                answer = False   # diyalog açılamadıysa çıkışı engelleme
            if answer is None:
                return           # İptal — uygulama açık kalır
            if answer:
                try:
                    self.save_all()
                except Exception:
                    pass

        self._closing = True

        if self.link is not None:
            try:
                self.link.stop()
            except Exception:
                pass
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:
                pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
