# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Fiziksel Tuş Izgarası.

Cihazın fiziksel yerleşimini arayüzde birebir yansıtır (tuş sayımı
SOL ALTTAN başlar)::

    SATIR 1 :  K9   K10  [COMBO]  [OS]   [ENC — enkoder]
    SATIR 2 :  K5   K6   K7       K8
    SATIR 3 :  K1   K2   K3       K4

Üst bezelde soldan sağa LED1 (Windows), LED2 (macOS), LED3 (Combo)
göstergeleri bulunur.
``K1``..``K10`` kartlarına tıklanınca eylem düzenleyici açılır; ``ENC``,
``COMBO`` ve ``OS`` kartları özel görevleri olduğu için ayrı geri çağırma
ile bildirilir.

İşlev tuşu kartları ayrıca sürükle-bırak hedefidir: üzerine dosya,
klasör, uygulama veya web adresi bırakılınca ``on_drop`` geri çağırması
tetiklenir. tkinterdnd2 kurulu değilse (veya tkdnd paketi kök pencerede
yüklenmediyse) sürükle-bırak sessizce kapalı kalır; uygulama yine açılır.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.core.config import KEY_IDS
from app.ui import dnd
from app.ui import theme

try:
    # tkinterdnd2 import edildiği anda drop_target_register / dnd_bind
    # metodlarını tkinter.BaseWidget'a enjekte eder. Tcl tarafındaki
    # "tkdnd" paketini ise kök pencere sahibi TkinterDnD.require(root)
    # ile yüklemelidir; yüklenmemişse kayıt denemesi TclError üretir ve
    # aşağıdaki kayıt kodu sürükle-bırakı sessizce devre dışı bırakır.
    from tkinterdnd2 import COPY, DND_FILES, DND_TEXT
    _DND_AVAILABLE = True
except Exception:  # tkinterdnd2 kurulu değilse sürükle-bırak kapalı kalır.
    COPY, DND_FILES, DND_TEXT = "copy", None, None
    _DND_AVAILABLE = False

#: ``K1``..``K10`` kartlarının ızgaradaki (satır, sütun) konumları.
#: Fiziksel yerleşimi aynalar (3 sıra x 4 sütun, sayım SOL ALTTAN başlar):
#:   üst sıra  : Tuş9  Tuş10  KOMBO  DEĞİŞİM(OS)   (+ enkoder 5. sütunda)
#:   orta sıra : Tuş5  Tuş6  Tuş7  Tuş8
#:   alt sıra  : Tuş1  Tuş2  Tuş3  Tuş4
KEY_POSITIONS: dict[str, tuple[int, int]] = {
    "K1": (2, 0), "K2": (2, 1), "K3": (2, 2), "K4": (2, 3),
    "K5": (1, 0), "K6": (1, 1), "K7": (1, 2), "K8": (1, 3),
    "K9": (0, 0), "K10": (0, 1),
}

CARD_WIDTH: int = 196
CARD_HEIGHT: int = 124


class _FlashAnimMixin:
    """Kartların paylaştığı parlama + yumuşak sönümleme animasyonu.

    ``flash()`` kartı ``FLASH_MS`` süresince parlatır, ardından
    ``FLASH_FADE_MS`` içinde ``FLASH_FADE_STEPS`` adımda taban renklere
    doğru interpolasyonla söndürür. Üst üste gelen flash çağrılarında
    önceki animasyon iptal edilir.
    """

    def _init_flash_anim(self) -> None:
        """Animasyon durum alanlarını hazırlar (``__init__`` içinde çağır)."""
        self._flash_job: str | None = None
        self._fade_job: str | None = None

    def _resting_fg(self) -> str:
        """Animasyon bitiminde dönülecek zemin rengi."""
        return self._base_fg

    def _resting_border(self) -> str:
        """Animasyon bitiminde dönülecek kenarlık rengi."""
        return self._base_border

    def _cancel_flash_anim(self) -> None:
        """Bekleyen flash/sönümleme işlerini iptal eder."""
        for attr in ("_flash_job", "_fade_job"):
            job = getattr(self, attr, None)
            if job is not None:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, attr, None)

    def flash(self, duration: int = theme.FLASH_MS) -> None:
        """Fiziksel tuşa basıldığında kartı parlatır ve yumuşakça söndürür."""
        self._cancel_flash_anim()
        try:
            self.configure(fg_color=theme.COLOR_FLASH_BG,
                           border_color=theme.COLOR_FLASH_BORDER)
        except Exception:
            return
        self._flash_job = self.after(duration, self._end_flash)

    def _end_flash(self) -> None:
        """Parlama süresi bitince sönümleme animasyonunu başlatır."""
        self._flash_job = None
        self._fade_step(1)

    def _fade_step(self, step: int) -> None:
        """Sönümlemenin tek adımını uygular ve sıradakini zamanlar."""
        self._fade_job = None
        total = max(1, theme.FLASH_FADE_STEPS)
        if step >= total:
            # SON ADIM: interpolate_hex tek bir hex DİZESİ üretir. Bu değer
            # karta yazılı kalırsa CustomTkinter tema değişiminde rengi
            # yeniden hesaplayamaz ve basılmış kartlar eski temanın
            # renginde takılı kalır (ızgara alacalı görünür). Bu yüzden
            # bitişte taban renkleri (açık, koyu) demeti hâliyle geri
            # yazıyoruz; böylece CTk mod değişiminde kendisi boyar.
            try:
                self.configure(fg_color=self._resting_fg(),
                               border_color=self._resting_border())
            except Exception:
                pass
            return
        ratio = step / float(total)
        try:
            self.configure(
                fg_color=theme.interpolate_hex(
                    theme.COLOR_FLASH_BG, self._resting_fg(), ratio),
                border_color=theme.interpolate_hex(
                    theme.COLOR_FLASH_BORDER, self._resting_border(), ratio))
        except Exception:
            return
        if step < total:
            interval = max(1, theme.FLASH_FADE_MS // total)
            self._fade_job = self.after(
                interval, lambda next_step=step + 1: self._fade_step(next_step))


class KeyCard(_FlashAnimMixin, ctk.CTkFrame):
    """Tek bir işlev tuşunu (``K1``..``K10``) temsil eden kart.

    Kart üzerinde tuş numarası dairesi, kullanıcının verdiği ad, eylem
    tipi rozeti ve değer özeti yer alır. Kartın kenarlık rengi eylem
    tipinin rengidir. Kart aynı zamanda sürükle-bırak hedefi olabilir;
    üzerine bir şey sürüklenirken kenarlık vurgu rengine döner.
    """

    def __init__(self, master, slot: str, number: int,
                 on_click: Callable[[str], None], **kwargs) -> None:
        """Kartı oluşturur.

        Args:
            master: Üst bileşen.
            slot: Slot anahtarı, örn. ``"K3"``.
            number: Kart üzerinde gösterilecek tuş numarası (1..10).
            on_click: Karta tıklanınca ``slot`` ile çağrılacak geri çağırma.
        """
        super().__init__(
            master, width=CARD_WIDTH, height=CARD_HEIGHT,
            corner_radius=theme.RADIUS_CARD, border_width=2,
            border_color=theme.COLOR_DISABLED, fg_color=theme.COLOR_CARD, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.slot = slot
        self._number = number
        self._on_click = on_click
        self._base_fg = theme.COLOR_CARD
        self._base_border = theme.COLOR_DISABLED
        self._drop_hover = False
        self._init_flash_anim()

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=9)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        self._circle = ctk.CTkFrame(top, width=34, height=34, corner_radius=17,
                                    fg_color=theme.COLOR_DISABLED)
        self._circle.pack(side="left")
        self._circle.pack_propagate(False)
        self._circle_label = ctk.CTkLabel(self._circle, text=str(number),
                                          font=theme.font(14, True), text_color="#FFFFFF")
        self._circle_label.place(relx=0.5, rely=0.5, anchor="center")

        self._badge = theme.make_badge(top, "Yok", theme.COLOR_DISABLED, width=88, height=22)
        self._badge.pack(side="right", pady=(5, 0))

        self._name_label = ctk.CTkLabel(inner, text=slot, font=theme.font(13, True),
                                        text_color=theme.COLOR_TEXT, anchor="w")
        self._name_label.pack(fill="x", pady=(9, 0))

        self._value_label = ctk.CTkLabel(inner, text="Yapılandırılmadı",
                                         font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
                                         anchor="w")
        self._value_label.pack(fill="x", pady=(2, 0))

        self._slot_label = ctk.CTkLabel(inner, text=slot, font=theme.mono(10),
                                        text_color=theme.COLOR_DISABLED, anchor="w")
        self._slot_label.pack(fill="x", side="bottom")

        theme.bind_click(self, self._handle_click)

    def _handle_click(self, _event=None) -> None:
        """Kart tıklamasını üst bileşene iletir."""
        try:
            self._on_click(self.slot)
        except Exception:
            pass

    def update_from(self, action: dict | None) -> None:
        """Kart içeriğini verilen eylem sözlüğüne göre günceller."""
        data = action or {"type": "none", "value": "", "name": ""}
        type_ = data.get("type", "none")
        color = theme.type_color(type_)
        name = (data.get("name") or "").strip() or f"Tuş {self._number}"

        self._base_border = color
        self.configure(border_color=color)
        self._circle.configure(fg_color=color)
        self._circle_label.configure(text_color=theme.contrast_text(color))
        self._badge.configure(text=theme.type_label(type_), fg_color=color,
                              text_color=theme.contrast_text(color))
        self._name_label.configure(text=theme.shorten(name, 22))

        summary = theme.action_summary(data)
        configured = type_ != "none" and bool((data.get("value") or "").strip())
        self._value_label.configure(
            text=summary,
            text_color=theme.COLOR_TEXT_DIM if configured else theme.COLOR_TEXT_MUTED)

    def set_drop_hover(self, active: bool) -> None:
        """Sürükleme kartın üzerindeyken kenarlığı vurgu rengine çevirir.

        Flash animasyonu ile yarışmaz: animasyon sürüyorsa yalnızca bayrak
        güncellenir; sönümleme zaten ``_resting_border()`` hedefine akar ve
        bayrak açıksa vurgu rengi geri gelir.
        """
        self._drop_hover = bool(active)
        if self._flash_job is None and self._fade_job is None:
            try:
                self.configure(border_color=self._resting_border())
            except Exception:
                pass

    def _resting_border(self) -> str:
        """Animasyon bitiminde dönülecek kenarlık rengi (hover öncelikli)."""
        if self._drop_hover:
            return theme.COLOR_ACCENT
        return self._base_border


class SpecialCard(_FlashAnimMixin, ctk.CTkFrame):
    """Enkoder, ``COMBO`` ve ``OS`` tuşlarını temsil eden kart.

    Bu kartlar doğrudan eylem taşımaz; görevleri sabittir. Tıklandıklarında
    ilgili sekmeye geçiş gibi işlemler için geri çağırma tetiklenir.
    """

    def __init__(self, master, key: str, title: str, subtitle: str, glyph: str,
                 color: str, on_click: Callable[[str], None], **kwargs) -> None:
        """Özel kartı oluşturur.

        Args:
            master: Üst bileşen.
            key: Kart kimliği — ``"ENC"``, ``"COMBO"`` veya ``"OS"``.
            title: Kart başlığı.
            subtitle: Açıklama satırı.
            glyph: Kartın sol tarafındaki sembol.
            color: Kartın vurgu rengi.
            on_click: Tıklandığında ``key`` ile çağrılacak geri çağırma.
        """
        super().__init__(
            master, width=CARD_WIDTH, height=CARD_HEIGHT,
            corner_radius=theme.RADIUS_CARD, border_width=2,
            border_color=color, fg_color=theme.COLOR_CARD, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.key = key
        self._on_click = on_click
        self._base_fg = theme.COLOR_CARD
        self._base_border = color
        self._init_flash_anim()

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=9)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        self._knob = ctk.CTkFrame(top, width=38, height=38, corner_radius=19,
                                  fg_color=color)
        self._knob.pack(side="left")
        self._knob.pack_propagate(False)
        self._glyph = ctk.CTkLabel(self._knob, text=glyph, font=theme.font(16, True),
                                   text_color=theme.contrast_text(color))
        self._glyph.place(relx=0.5, rely=0.5, anchor="center")

        self._title = ctk.CTkLabel(top, text=title, font=theme.font(13, True),
                                   text_color=theme.COLOR_TEXT, anchor="w")
        self._title.pack(side="left", padx=(10, 0))

        self._subtitle = ctk.CTkLabel(inner, text=subtitle, font=theme.font(11),
                                      text_color=theme.COLOR_TEXT_MUTED,
                                      anchor="w", justify="left")
        self._subtitle.pack(fill="x", pady=(10, 0))

        self._state = ctk.CTkLabel(inner, text="", font=theme.font(11, True),
                                   text_color=color, anchor="w")
        self._state.pack(fill="x", side="bottom")

        theme.bind_click(self, self._handle_click)

    def _handle_click(self, _event=None) -> None:
        """Kart tıklamasını üst bileşene iletir."""
        try:
            self._on_click(self.key)
        except Exception:
            pass

    def set_color(self, color: str) -> None:
        """Kartın vurgu rengini değiştirir (örn. OS moduna göre)."""
        self._base_border = color
        try:
            self.configure(border_color=color)
            self._knob.configure(fg_color=color)
            self._glyph.configure(text_color=theme.contrast_text(color))
            self._state.configure(text_color=color)
        except Exception:
            pass

    def set_state_text(self, text: str) -> None:
        """Kartın alt satırındaki durum metnini günceller."""
        try:
            self._state.configure(text=text)
        except Exception:
            pass

    def set_subtitle(self, text: str) -> None:
        """Kartın açıklama satırını günceller."""
        try:
            self._subtitle.configure(text=text)
        except Exception:
            pass


class KeyGrid(ctk.CTkFrame):
    """Cihazın fiziksel yerleşimini gösteren 5 sütun × 3 satır tuş ızgarası."""

    def __init__(self, master, get_action: Callable[[str], dict],
                 on_edit: Callable[[str], None],
                 on_special: Callable[[str], None] | None = None,
                 on_drop: Callable[[str, dict], None] | None = None,
                 **kwargs) -> None:
        """Izgarayı kurar.

        Args:
            master: Üst bileşen.
            get_action: ``slot`` alıp eylem sözlüğü döndüren fonksiyon.
            on_edit: ``K1``..``K10`` kartına tıklanınca çağrılır.
            on_special: ``ENC`` / ``COMBO`` / ``OS`` kartına tıklanınca çağrılır.
            on_drop: Bir işlev tuşu kartına dosya/klasör/uygulama/web adresi
                bırakılınca ``on_drop(slot_id, action_dict)`` olarak çağrılır.
                ``action_dict`` = ``{"type": "app"|"url"|"file"|"folder",
                "value": str, "name": str}``. Yapılandırmaya yazma işi
                çağıran tarafa aittir. ``None`` ise sürükle-bırak kapalıdır.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._get_action = get_action
        self._on_edit = on_edit
        self._on_special = on_special or (lambda _key: None)
        self._on_drop = on_drop
        # tkdnd kayıt denemesi ilk hatada bu bayrağı kapatır.
        self._dnd_ready = _DND_AVAILABLE and on_drop is not None
        self.cards: dict[str, KeyCard] = {}

        # --- Üst bezel: LED göstergeleri --------------------------------
        bezel = ctk.CTkFrame(self, corner_radius=theme.RADIUS_CARD,
                             fg_color=theme.COLOR_PANEL, height=54)
        bezel.pack(fill="x", padx=4, pady=(0, theme.PAD_M))
        bezel.pack_propagate(False)

        ctk.CTkLabel(bezel, text="ÜST BEZEL", font=theme.font(10, True),
                     text_color=theme.COLOR_TEXT_MUTED).pack(side="left", padx=(theme.PAD_M, 0))

        led_wrap = ctk.CTkFrame(bezel, fg_color="transparent")
        led_wrap.pack(side="left", padx=theme.PAD_L)

        self._leds: dict[int, ctk.CTkLabel] = {}
        # Düz LED donanımıyla birebir: LED1=Windows, LED2=macOS, LED3=Combo.
        # Bağlantı durumu ayrı LED değildir; aktif OS LED'i bağlıyken dolu,
        # değilken soluk gösterilir (cihazda yavaş yanıp sönmeye karşılık).
        led_titles = {1: "LED1 · Windows", 2: "LED2 · macOS", 3: "LED3 · Combo"}
        self._ui_os_mac = False
        self._ui_linked = False
        for index in (1, 2, 3):
            cell = ctk.CTkFrame(led_wrap, fg_color="transparent")
            cell.pack(side="left", padx=theme.PAD_M)
            dot = ctk.CTkLabel(cell, text="●", font=theme.font(18),
                               text_color=theme.COLOR_DISABLED, width=18)
            dot.pack(side="left")
            ctk.CTkLabel(cell, text=led_titles[index], font=theme.font(10),
                         text_color=theme.COLOR_TEXT_MUTED).pack(side="left", padx=(4, 0))
            self._leds[index] = dot

        self._layout_hint = ctk.CTkLabel(
            bezel, text="Düzenlemek için bir tuşa tıkla",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED)
        self._layout_hint.pack(side="right", padx=theme.PAD_M)

        # --- Tuş ızgarası -----------------------------------------------
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for column in range(5):
            grid.grid_columnconfigure(column, weight=1, uniform="keycol")
        for row in range(3):
            grid.grid_rowconfigure(row, weight=1, uniform="keyrow")

        for slot in KEY_IDS:
            if slot not in KEY_POSITIONS:
                continue
            row, column = KEY_POSITIONS[slot]
            number = int(slot[1:])
            card = KeyCard(grid, slot, number, self._on_edit)
            card.grid(row=row, column=column, padx=6, pady=6, sticky="nsew")
            self.cards[slot] = card

        # Özel kartlar fiziksel yerleşimi izler: üst sırada K9, K10'dan
        # SONRA KOMBO ve DEĞİŞİM(OS); enkoder ızgara dışında (5. sütun).
        self.os_card = SpecialCard(
            grid, "OS", "OS DEĞİŞTİR", "Windows ⇄ macOS\nDeğiştirmek için tıkla",
            "⇄", theme.COLOR_ACCENT, self._on_special)
        self.os_card.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")
        self.os_card.set_state_text("Mod: WINDOWS")

        self.combo_card = SpecialCard(
            grid, "COMBO", "COMBO", "Bir kez bas, sonra iki tuş seç\nCombo listesi için tıkla",
            "⊕", theme.COLOR_WARNING, self._on_special)
        self.combo_card.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
        self.combo_card.set_state_text("Combo modu kapalı")

        self.encoder_card = SpecialCard(
            grid, "ENC", "ENKODER", "Döndür: ses · Bas: sessiz\nAyarlar için tıkla",
            "●", theme.COLOR_ACCENT, self._on_special)
        self.encoder_card.grid(row=0, column=4, padx=6, pady=6, sticky="nsew")
        self.encoder_card.set_state_text("Mod: HID")

        # İşlev tuşu kartlarını sürükle-bırak hedefi yap (özel kartlar hariç).
        if self._dnd_ready:
            for slot, card in self.cards.items():
                self._register_drop_target(card, slot, card)

        self.refresh()

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tüm tuş kartlarını güncel yapılandırmadan yeniden doldurur."""
        for slot, card in self.cards.items():
            try:
                card.update_from(self._get_action(slot))
            except Exception:
                card.update_from(None)

    def flash(self, slot: str) -> None:
        """Fiziksel olarak basılan tuşun kartını parlatır.

        Args:
            slot: ``K1``..``K10``, ``COMBO``, ``OS`` veya ``ENC``.
        """
        if slot in self.cards:
            self.cards[slot].flash()
        elif slot == "COMBO":
            self.combo_card.flash()
        elif slot == "OS":
            self.os_card.flash()
        elif slot == "ENC":
            self.encoder_card.flash()

    def set_combo_mode(self, active: bool) -> None:
        """Combo modunun açık/kapalı durumunu kart üzerinde gösterir."""
        if active:
            self.combo_card.set_color(theme.COLOR_WARNING)
            self.combo_card.set_state_text("COMBO MODU AKTİF")
            self.set_led(3, theme.LED_COMBO)
        else:
            self.combo_card.set_color(theme.COLOR_WARNING)
            self.combo_card.set_state_text("Combo modu kapalı")
            self.set_led(3, theme.COLOR_DISABLED)

    def _render_os_leds(self) -> None:
        """LED1 (Windows) ve LED2 (macOS) noktalarını duruma göre boyar.

        Fiziksel davranışın aynası: aktif moda ait LED yanar; uygulama
        bağlı değilken cihazda yavaş yanıp söner — arayüzde bu, soluk
        renkle temsil edilir.
        """
        win_renk = theme.LED_OS_WIN if not self._ui_os_mac else theme.COLOR_DISABLED
        mac_renk = theme.LED_OS_MAC if self._ui_os_mac else theme.COLOR_DISABLED
        if not self._ui_linked:
            if self._ui_os_mac:
                mac_renk = theme.COLOR_TEXT_MUTED
            else:
                win_renk = theme.COLOR_TEXT_MUTED
        self.set_led(1, win_renk)
        self.set_led(2, mac_renk)

    def set_os_mode(self, os_key: str) -> None:
        """OS kartını ve Windows/macOS LED göstergelerini günceller."""
        is_mac = (os_key or "windows").lower().startswith("mac")
        self._ui_os_mac = is_mac
        color = theme.LED_OS_MAC if is_mac else theme.LED_OS_WIN
        self.os_card.set_color(color)
        self.os_card.set_state_text("Mod: MACOS" if is_mac else "Mod: WINDOWS")
        self._render_os_leds()

    def set_encoder_mode(self, mode: str) -> None:
        """Enkoder kartındaki mod bilgisini günceller (``hid`` / ``host``)."""
        clean = (mode or "hid").lower()
        self.encoder_card.set_state_text(
            "Mod: HOST" if clean == "host" else "Mod: HID")

    def set_link_state(self, connected: bool) -> None:
        """Bağlantı durumunu aktif OS LED'inin dolu/soluk hâliyle gösterir."""
        self._ui_linked = bool(connected)
        self._render_os_leds()

    def set_led(self, index: int, color: str) -> None:
        """Bezeldeki LED göstergesinin rengini ayarlar.

        Args:
            index: 1, 2 veya 3.
            color: ``#RRGGBB`` biçiminde renk.
        """
        dot = self._leds.get(index)
        if dot is None:
            return
        try:
            dot.configure(text_color=theme.normalize_hex(color, theme.COLOR_DISABLED))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # İç mantık — sürükle-bırak
    # ------------------------------------------------------------------

    def _register_drop_target(self, widget, slot: str, card: KeyCard) -> None:
        """Kartı ve tüm alt bileşenlerini bırakma hedefi yapar (recursive).

        CustomTkinter kartları iç içe çerçeve/etiketlerden oluştuğu için
        ``theme.bind_click`` ile aynı desende ağacın tamamı dolaşılır;
        bırakma hangi alt bileşene denk gelirse gelsin aynı kart yakalar.
        """
        if not self._dnd_ready:
            return
        try:
            widget.drop_target_register(DND_FILES, DND_TEXT)
            widget.dnd_bind(
                "<<DropEnter>>",
                lambda event, c=card: self._handle_drop_enter(c, event), add="+")
            widget.dnd_bind(
                "<<DropLeave>>",
                lambda event, c=card: self._handle_drop_leave(c, event), add="+")
            widget.dnd_bind(
                "<<Drop:DND_Files>>",
                lambda event, s=slot, c=card: self._handle_drop(s, c, event, "files"),
                add="+")
            widget.dnd_bind(
                "<<Drop:DND_Text>>",
                lambda event, s=slot, c=card: self._handle_drop(s, c, event, "text"),
                add="+")
        except Exception:
            # tkdnd paketi kök pencerede yüklü değil; DnD sessizce kapalı.
            self._dnd_ready = False
            return
        try:
            children = widget.winfo_children()
        except Exception:
            children = []
        for child in children:
            self._register_drop_target(child, slot, card)

    def _handle_drop_enter(self, card: KeyCard, _event):
        """Sürükleme kartın üzerine gelince vurguyu açar."""
        try:
            card.set_drop_hover(True)
        except Exception:
            pass
        return COPY

    def _handle_drop_leave(self, card: KeyCard, _event) -> None:
        """Sürükleme karttan ayrılınca vurguyu kapatır."""
        try:
            card.set_drop_hover(False)
        except Exception:
            pass

    def _handle_drop(self, slot: str, card: KeyCard, event, tur: str):
        """Bırakma olayını eyleme çevirip ``on_drop`` geri çağrısına iletir.

        Args:
            slot: Hedef kartın slot anahtarı (``K1``..``K10``).
            card: Hedef kart (vurgusu kapatılır).
            event: tkdnd bırakma olayı; ham veri ``event.data`` içindedir.
            tur: ``"files"`` veya ``"text"``.
        """
        try:
            card.set_drop_hover(False)
        except Exception:
            pass

        raw = str(getattr(event, "data", "") or "")
        if tur == "files":
            paths = dnd.parse_drop_paths(self, raw)
            veri = paths[0] if paths else ""
        else:
            veri = raw.strip()

        action = dnd.action_from_drop(veri, tur)
        if action is not None and self._on_drop is not None:
            try:
                self._on_drop(slot, action)
            except Exception:
                pass
        return COPY
