# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Enkoder Ayarları Paneli.

EC11 döner enkoderin dört olayı yapılandırılabilir (spesifikasyon 7.1):

* ``cw``    — saat yönünde bir tık
* ``ccw``   — saat yönünün tersine bir tık
* ``press`` — enkoder butonuna kısa basış
* ``long``  — enkoder butonuna 800 ms basılı tutma

Ayrıca enkoderin çalışma modu seçilir:

* ``hid``  — cihaz doğrudan HID ses tuşu gönderir (uygulama kapalıyken de çalışır)
* ``host`` — cihaz sadece olay bildirir, ne yapılacağına PC uygulaması karar verir
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.core.config import ENCODER_IDS
from app.ui import theme

#: Enkoder slotlarının Türkçe başlıkları, açıklamaları ve sembolleri.
SLOT_META: dict[str, tuple[str, str, str]] = {
    "cw": ("Saat Yönü", "Enkoderi sağa çevir", "↻"),
    "ccw": ("Saat Yönü Tersi", "Enkoderi sola çevir", "↺"),
    "press": ("Basış", "Enkoder butonuna kısa bas", "◉"),
    "long": ("Uzun Basış", "Enkoder butonunu 800 ms basılı tut", "◎"),
}


class EncoderSlotCard(ctk.CTkFrame):
    """Tek bir enkoder olayının eylemini gösteren kart."""

    def __init__(self, master, slot: str, on_edit: Callable[[str], None], **kwargs) -> None:
        """Kartı oluşturur.

        Args:
            master: Üst bileşen.
            slot: ``cw``, ``ccw``, ``press`` veya ``long``.
            on_edit: Karta tıklanınca ``slot`` ile çağrılacak geri çağırma.
        """
        super().__init__(master, corner_radius=theme.RADIUS_CARD, border_width=2,
                         border_color=theme.COLOR_DISABLED,
                         fg_color=theme.COLOR_CARD, **kwargs)

        self.slot = slot
        self._on_edit = on_edit
        self._base_fg = theme.COLOR_CARD
        self._base_border = theme.COLOR_DISABLED
        self._flash_job: str | None = None

        title, description, glyph = SLOT_META.get(slot, (slot, "", "•"))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAD_M, pady=theme.PAD_M)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        self._knob = ctk.CTkFrame(top, width=40, height=40, corner_radius=20,
                                  fg_color=theme.COLOR_DISABLED)
        self._knob.pack(side="left")
        self._knob.pack_propagate(False)
        self._glyph = ctk.CTkLabel(self._knob, text=glyph, font=theme.font(18, True),
                                   text_color="#FFFFFF")
        self._glyph.place(relx=0.5, rely=0.5, anchor="center")

        text_wrap = ctk.CTkFrame(top, fg_color="transparent")
        text_wrap.pack(side="left", fill="x", expand=True, padx=(theme.PAD_M, 0))
        ctk.CTkLabel(text_wrap, text=title, font=theme.font(14, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(text_wrap, text=description, font=theme.font(10),
                     text_color=theme.COLOR_TEXT_MUTED, anchor="w").pack(fill="x")

        self._badge = theme.make_badge(top, "Yok", theme.COLOR_DISABLED, width=96, height=24)
        self._badge.pack(side="right", padx=(theme.PAD_S, 0))

        bottom = ctk.CTkFrame(inner, fg_color="transparent")
        bottom.pack(fill="x", pady=(theme.PAD_M, 0))

        self._name_label = ctk.CTkLabel(bottom, text="", font=theme.font(12, True),
                                        text_color=theme.COLOR_TEXT_DIM, anchor="w")
        self._name_label.pack(fill="x")

        self._value_label = ctk.CTkLabel(bottom, text="Yapılandırılmadı",
                                         font=theme.font(11),
                                         text_color=theme.COLOR_TEXT_MUTED, anchor="w")
        self._value_label.pack(fill="x", pady=(2, 0))

        ctk.CTkButton(inner, text="Düzenle", height=30,
                      corner_radius=theme.RADIUS_SMALL,
                      fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_ACCENT,
                      font=theme.font(11, True),
                      command=lambda: self._on_edit(self.slot)
                      ).pack(fill="x", pady=(theme.PAD_M, 0))

        theme.bind_click(self, lambda _event=None: self._on_edit(self.slot))

    def update_from(self, action: dict | None) -> None:
        """Kart içeriğini verilen eylem sözlüğüne göre günceller."""
        data = action or {"type": "none", "value": "", "name": ""}
        type_ = data.get("type", "none")
        color = theme.type_color(type_)
        default_name = SLOT_META.get(self.slot, (self.slot, "", ""))[0]

        self._base_border = color
        try:
            self.configure(border_color=color)
        except Exception:
            pass
        self._knob.configure(fg_color=color)
        self._glyph.configure(text_color=theme.contrast_text(color))
        self._badge.configure(text=theme.type_label(type_), fg_color=color,
                              text_color=theme.contrast_text(color))
        self._name_label.configure(
            text=theme.shorten((data.get("name") or "").strip() or default_name, 30))
        configured = type_ != "none" and bool((data.get("value") or "").strip())
        self._value_label.configure(
            text=theme.action_summary(data),
            text_color=theme.COLOR_TEXT_DIM if configured else theme.COLOR_TEXT_MUTED)

    def flash(self, duration: int = theme.FLASH_MS) -> None:
        """Enkoder olayı geldiğinde kartı kısa süre parlatır."""
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None
        try:
            self.configure(fg_color=theme.COLOR_FLASH_BG,
                           border_color=theme.COLOR_FLASH_BORDER)
        except Exception:
            return
        self._flash_job = self.after(duration, self._end_flash)

    def _end_flash(self) -> None:
        """Parlama bitince kartı normal görünümüne döndürür."""
        self._flash_job = None
        try:
            self.configure(fg_color=self._base_fg, border_color=self._base_border)
        except Exception:
            pass


class EncoderPanel(ctk.CTkFrame):
    """Enkoder modunu ve dört enkoder slotunun eylemlerini yöneten panel."""

    def __init__(self, master, get_action: Callable[[str], dict],
                 on_edit: Callable[[str], None],
                 on_mode_change: Callable[[str], None] | None = None,
                 **kwargs) -> None:
        """Paneli kurar.

        Args:
            master: Üst bileşen.
            get_action: ``slot`` alıp eylem sözlüğü döndüren fonksiyon.
            on_edit: Kart düzenlenmek istendiğinde ``slot`` ile çağrılır.
            on_mode_change: Enkoder modu değişince ``"hid"``/``"host"`` ile çağrılır.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._get_action = get_action
        self._on_edit = on_edit
        self._on_mode_change = on_mode_change or (lambda _mode: None)
        self._mode_guard = False
        self.cards: dict[str, EncoderSlotCard] = {}

        # --- Mod seçimi --------------------------------------------------
        mode_box = ctk.CTkFrame(self, corner_radius=theme.RADIUS_CARD,
                                fg_color=theme.COLOR_CARD)
        mode_box.pack(fill="x", padx=2, pady=(0, theme.PAD_M))

        mode_inner = ctk.CTkFrame(mode_box, fg_color="transparent")
        mode_inner.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_M)

        left = ctk.CTkFrame(mode_inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text="Enkoder Modu", font=theme.font(15, True),
                     text_color=theme.COLOR_TEXT, anchor="w").pack(fill="x")
        # Metin uzun olabildiği için SARMALANIR; aksi hâlde tek satırda
        # uzayıp kartın dışına/altına taşar.
        self._mode_hint = ctk.CTkLabel(
            left,
            text="HID: ses kontrolünü cihaz yapar.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            anchor="w", justify="left", wraplength=680)
        self._mode_hint.pack(fill="x", pady=(4, 0))

        self._mode_var = ctk.StringVar(value="HID")
        self._mode_switch = ctk.CTkSegmentedButton(
            mode_inner, text_color=("#ffffff", "#DCE4EE"), values=["HID", "HOST"], variable=self._mode_var,
            command=self._handle_mode_change, font=theme.font(12, True),
            selected_color=theme.COLOR_ACCENT,
            selected_hover_color=theme.COLOR_ACCENT_DARK,
            unselected_color=("#8d97ad", "#2b2b3d"),
            unselected_hover_color=theme.COLOR_HOVER,
            height=36, width=180)
        self._mode_switch.pack(side="right", padx=(theme.PAD_M, 0))

        # --- Slot kartları -----------------------------------------------
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=2)
        grid.grid_columnconfigure(0, weight=1, uniform="enccol")
        grid.grid_columnconfigure(1, weight=1, uniform="enccol")
        grid.grid_rowconfigure(0, weight=1, uniform="encrow")
        grid.grid_rowconfigure(1, weight=1, uniform="encrow")

        for index, slot in enumerate(ENCODER_IDS):
            card = EncoderSlotCard(grid, slot, self._on_edit)
            card.grid(row=index // 2, column=index % 2,
                      padx=6, pady=6, sticky="nsew")
            self.cards[slot] = card

        # --- Bilgi notu ----------------------------------------------------
        note = ctk.CTkFrame(self, corner_radius=theme.RADIUS_CARD,
                            fg_color=theme.COLOR_PANEL)
        note.pack(fill="x", padx=2, pady=(theme.PAD_M, 0))
        ctk.CTkLabel(
            note,
            text="Enkoder HID modundayken ses kontrolünü cihaz üstlenir; bu modda "
                 "buradaki eylemler PC tarafında tetiklenmez. HOST modunda ise her "
                 "enkoder olayı için aşağıdaki eylemler çalıştırılır.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            justify="left", wraplength=820, anchor="w"
        ).pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_M)

        self.refresh()

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tüm enkoder kartlarını güncel yapılandırmadan yeniden doldurur."""
        for slot, card in self.cards.items():
            try:
                card.update_from(self._get_action(slot))
            except Exception:
                card.update_from(None)

    def flash(self, slot: str) -> None:
        """Gelen enkoder olayına karşılık gelen kartı parlatır."""
        card = self.cards.get(slot)
        if card is not None:
            card.flash()

    def set_mode(self, mode: str) -> None:
        """Mod düğmesini dışarıdan (yapılandırmadan) ayarlar.

        Geri çağırma tetiklenmez; sadece görsel durum güncellenir.
        """
        clean = "HOST" if (mode or "hid").lower() == "host" else "HID"
        self._mode_guard = True
        try:
            self._mode_var.set(clean)
            self._mode_switch.set(clean)
        except Exception:
            pass
        finally:
            self._mode_guard = False
        self._update_mode_hint(clean)

    def current_mode(self) -> str:
        """Seçili enkoder modunu ``"hid"`` / ``"host"`` olarak döndürür."""
        return "host" if self._mode_var.get().upper() == "HOST" else "hid"

    # ------------------------------------------------------------------
    # İç mantık
    # ------------------------------------------------------------------

    def _update_mode_hint(self, mode_text: str) -> None:
        """Mod açıklamasını seçili moda göre günceller."""
        if mode_text.upper() == "HOST":
            self._mode_hint.configure(
                text="HOST: aşağıdaki dört slotun eylemleri çalışır.",
                text_color=theme.COLOR_SUCCESS)
        else:
            # Kullanıcının en sık takıldığı nokta: HID modunda slot eylemleri
            # ÇALIŞMAZ; cihaz kendi ses kontrolünü uygular. Bunu açıkça yaz.
            self._mode_hint.configure(
                text=("HID: ses kontrolünü cihaz yapar. Aşağıdaki slot "
                      "eylemleri ÇALIŞMAZ — HOST'a geçin."),
                text_color=theme.COLOR_WARNING)

    def _handle_mode_change(self, value: str) -> None:
        """Kullanıcı modu değiştirdiğinde cihaza ve yapılandırmaya bildirir."""
        self._update_mode_hint(value)
        if self._mode_guard:
            return
        try:
            self._on_mode_change("host" if value.upper() == "HOST" else "hid")
        except Exception:
            pass
