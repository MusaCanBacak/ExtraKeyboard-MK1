# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Ortak Eylem Düzenleme Bileşeni.

Tuşlar (``K1``..``K9``), combolar (``C_a_b``) ve enkoder slotları
(``cw``, ``ccw``, ``press``, ``long``) aynı eylem şemasını kullanır:
``{"type": ..., "value": ..., "name": ...}``.

Bu yüzden düzenleme arayüzü tek bir yerde yazılır ve her yerden çağrılır:

* :class:`ActionEditor`      — gömülebilir düzenleme paneli
* :class:`ActionEditorDialog` — modal diyalog sarmalayıcısı
* :func:`open_action_editor`  — tek satırlık kullanım kolaylığı

Eylem tipleri, medya değerleri ve şema sabitleri çekirdek yapılandırma
modülünden alınır; burada yeniden tanımlanmaz.
"""

from __future__ import annotations

import os
import sys
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog

from app.core import platform_utils
from app.core.config import ACTION_TYPES, MEDIA_VALUES
from app.ui import theme


def _ana_pencereyi_gorunur_yap(master) -> None:
    """Diyalog açılmadan önce gizli ana pencereyi geri getirir.

    Uygulama "arka planda başlat" ayarıyla açıldığında ana pencere gizlidir.
    Gizli bir pencerenin çocuğu olarak açılan ``Toplevel``'ler macOS'ta
    içerikleri hiç çizilmeden, bomboş (açık temada bembeyaz) görünür.
    Diyalogların tamamı buradan geçtiği için ana pencere önce görünür
    kılınır ve alt pencereler doğru çizilir.
    """
    try:
        kok = master.winfo_toplevel()
    except Exception:
        return
    gorunur_yap = getattr(kok, "ensure_visible", None)
    if callable(gorunur_yap):
        try:
            gorunur_yap()
        except Exception:
            pass


# Kısayol yakalarken yok sayılacak (tek başına anlam taşımayan) tuşlar
_MODIFIER_KEYSYMS: dict[str, str] = {
    "Shift_L": "shift", "Shift_R": "shift",
    "Control_L": "ctrl", "Control_R": "ctrl",
    "Alt_L": "alt", "Alt_R": "alt",
    "Option_L": "alt", "Option_R": "alt",
    "Meta_L": "meta", "Meta_R": "meta",
    "Command": "meta", "Command_L": "meta", "Command_R": "meta",
    "Super_L": "meta", "Super_R": "meta",
    "Win_L": "meta", "Win_R": "meta",
    "ISO_Level3_Shift": "alt",
    "Caps_Lock": "", "Num_Lock": "", "Scroll_Lock": "",
}

# Tkinter keysym -> kısayol metninde kullanılacak ad
_KEYSYM_ALIASES: dict[str, str] = {
    "Return": "enter", "KP_Enter": "enter", "Escape": "esc",
    "BackSpace": "backspace", "Delete": "delete", "Tab": "tab",
    "space": "space", "Up": "up", "Down": "down", "Left": "left",
    "Right": "right", "Home": "home", "End": "end",
    "Prior": "pageup", "Next": "pagedown", "Insert": "insert",
    "plus": "+", "minus": "-", "equal": "=", "comma": ",",
    "period": ".", "slash": "/", "backslash": "\\",
    "semicolon": ";", "apostrophe": "'", "grave": "`",
    "bracketleft": "[", "bracketright": "]",
}


def _canonical_modifier(name: str, os_key: str) -> str:
    """Yakalanan değiştirici tuşu, aktif profile uygun ada çevirir."""
    is_mac = (os_key or "windows").lower().startswith("mac")
    if name == "meta":
        return "command" if is_mac else "win"
    return name


def _sort_modifiers(mods: set[str], os_key: str) -> list[str]:
    """Değiştirici tuşları her zaman aynı sırayla yazmak için sıralar."""
    is_mac = (os_key or "windows").lower().startswith("mac")
    order = ["command", "ctrl", "alt", "shift"] if is_mac else ["ctrl", "win", "alt", "shift"]
    return [m for m in order if m in mods] + sorted(m for m in mods if m not in order)


class ShortcutCaptureDialog(ctk.CTkToplevel):
    """Kullanıcının tuş kombinasyonunu fiziksel olarak basarak girmesini sağlar.

    Pencere açıkken basılan değiştirici tuşlar (Shift/Ctrl/Alt/Command) takip
    edilir; değiştirici olmayan ilk tuşa basıldığında kombinasyon
    ``ctrl+shift+c`` biçiminde kurulur ve ``on_capture`` çağrılır.
    """

    def __init__(self, master, os_key: str, on_capture: Callable[[str], None]) -> None:
        """Yakalama penceresini oluşturur.

        Args:
            master: Üst pencere.
            os_key: Aktif profil (``"windows"`` / ``"mac"``).
            on_capture: Yakalanan kısayol metni ile çağrılacak geri çağırma.
        """
        _ana_pencereyi_gorunur_yap(master)
        super().__init__(master)
        self._os_key = os_key
        self._on_capture = on_capture
        self._held: set[str] = set()

        self.title("Kısayol Yakala")
        self.geometry("420x210")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)

        ctk.CTkLabel(
            self, text="Kombinasyonu şimdi bas", font=theme.font(18, True),
            text_color=theme.COLOR_TEXT,
        ).pack(pady=(22, 4))

        self._preview = ctk.CTkLabel(
            self, text="…", font=theme.mono(20, True),
            text_color=theme.COLOR_WARNING, height=48,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_CARD,
        )
        self._preview.pack(fill="x", padx=26, pady=8)

        ctk.CTkLabel(
            self,
            text="Değiştirici tuşları basılı tutup normal tuşa bas.\n"
                 "Vazgeçmek için pencereyi kapat.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED, justify="center",
        ).pack(pady=(2, 6))

        ctk.CTkButton(
            self, text="Vazgeç", width=110, height=32,
            corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_DISABLED, hover_color=theme.COLOR_HOVER,
            font=theme.font(12, True), command=self.destroy,
        ).pack(pady=(0, 14))

        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<KeyRelease>", self._on_key_release)
        self.after(120, self._grab)

    def _grab(self) -> None:
        """Pencereyi öne alır, klavye odağını ve modal kilidi kurar."""
        for step in (self.lift, self.focus_force, self.grab_set):
            try:
                step()
            except Exception:
                pass

    def _refresh_preview(self) -> None:
        """Basılı tutulan değiştiricileri canlı olarak gösterir."""
        mods = _sort_modifiers(
            {_canonical_modifier(m, self._os_key) for m in self._held if m},
            self._os_key,
        )
        self._preview.configure(text="+".join(mods) + "+…" if mods else "…")

    def _on_key_press(self, event) -> str:
        """Tuş basıldığında değiştiricileri toplar, normal tuşta yakalamayı bitirir."""
        keysym = event.keysym
        if keysym in _MODIFIER_KEYSYMS:
            name = _MODIFIER_KEYSYMS[keysym]
            if name:
                self._held.add(name)
            self._refresh_preview()
            return "break"

        key = _KEYSYM_ALIASES.get(keysym)
        if key is None:
            if len(keysym) == 1:
                key = keysym.lower()
            elif keysym.upper().startswith("F") and keysym[1:].isdigit():
                key = keysym.lower()
            elif keysym.startswith("KP_"):
                key = keysym[3:].lower()
            else:
                key = keysym.lower()

        mods = _sort_modifiers(
            {_canonical_modifier(m, self._os_key) for m in self._held if m},
            self._os_key,
        )
        combo = "+".join(mods + [key])
        self._preview.configure(text=combo, text_color=theme.COLOR_SUCCESS)
        try:
            self._on_capture(combo)
        except Exception:
            pass
        self.after(320, self.destroy)
        return "break"

    def _on_key_release(self, event) -> str:
        """Bırakılan değiştirici tuşu listeden düşürür."""
        name = _MODIFIER_KEYSYMS.get(event.keysym)
        if name:
            self._held.discard(name)
            self._refresh_preview()
        return "break"


class ActionEditor(ctk.CTkFrame):
    """Tek bir eylemi düzenleyen, her slot tipi için ortak kullanılan panel.

    Panel; ad, eylem tipi ve değer alanlarını içerir. Seçilen tipe göre
    yardımcı bileşenler değişir:

    * ``app`` / ``file`` / ``folder`` → "Gözat" dosya seçici
    * ``media``                      → hazır değer açılır listesi
    * ``shortcut``                   → "Tuşa Bas ve Yakala" butonu
    * ``macro``                      → çok satırlı adım düzenleyici + örnek
    """

    def __init__(self, master, os_key: str = "windows",
                 action: dict | None = None, show_name: bool = True, **kwargs) -> None:
        """Düzenleme panelini kurar.

        Args:
            master: Üst bileşen.
            os_key: Aktif profil anahtarı (``"windows"`` / ``"mac"``).
            action: Başlangıç eylemi; ``None`` ise boş eylem varsayılır.
            show_name: Kullanıcı adı alanı gösterilsin mi.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._os_key = (os_key or "windows").lower()
        self._show_name = show_name
        self._action = dict(action or {"type": "none", "value": "", "name": ""})

        self.grid_columnconfigure(0, weight=1)
        row = 0

        # --- Ad alanı --------------------------------------------------
        if show_name:
            ctk.CTkLabel(self, text="Görünen Ad", font=theme.font(12, True),
                         text_color=theme.COLOR_TEXT_DIM).grid(
                row=row, column=0, sticky="w", pady=(0, 2))
            row += 1
            self._name_entry = ctk.CTkEntry(
                self, height=36, corner_radius=theme.RADIUS_SMALL,
                fg_color=theme.COLOR_FIELD, placeholder_text_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT, border_color=theme.COLOR_BORDER,
                font=theme.font(13), placeholder_text="Örn: Tarayıcıyı Aç",
            )
            self._name_entry.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD_M))
            row += 1
        else:
            self._name_entry = None

        # --- Tip seçici ------------------------------------------------
        ctk.CTkLabel(self, text="Eylem Tipi", font=theme.font(12, True),
                     text_color=theme.COLOR_TEXT_DIM).grid(
            row=row, column=0, sticky="w", pady=(0, 2))
        row += 1

        type_row = ctk.CTkFrame(self, fg_color="transparent")
        type_row.grid(row=row, column=0, sticky="ew", pady=(0, theme.PAD_M))
        type_row.grid_columnconfigure(0, weight=1)
        row += 1

        self._type_var = ctk.StringVar(value=theme.type_label(self._action.get("type", "none")))
        self._type_menu = ctk.CTkOptionMenu(
            type_row,
            values=[theme.type_label(t) for t in ACTION_TYPES],
            variable=self._type_var,
            command=self._on_type_changed,
            height=36, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT, button_color=theme.COLOR_ACCENT,
            button_hover_color=theme.COLOR_ACCENT_DARK,
            dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT,
            dropdown_hover_color=theme.COLOR_HOVER,
            font=theme.font(13), dropdown_font=theme.font(12),
        )
        self._type_menu.grid(row=0, column=0, sticky="ew")

        self._type_badge = theme.make_badge(
            type_row, theme.type_label(self._action.get("type", "none")),
            theme.type_color(self._action.get("type", "none")), width=110, height=30)
        self._type_badge.grid(row=0, column=1, padx=(theme.PAD_S, 0))

        # --- Değer alanı -----------------------------------------------
        self._value_title = ctk.CTkLabel(self, text="Değer", font=theme.font(12, True),
                                         text_color=theme.COLOR_TEXT_DIM)
        self._value_title.grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1

        value_row = ctk.CTkFrame(self, fg_color="transparent")
        value_row.grid(row=row, column=0, sticky="ew")
        value_row.grid_columnconfigure(0, weight=1)
        self._value_row = value_row
        row += 1

        self._value_entry = ctk.CTkEntry(
            value_row, height=36, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_FIELD, placeholder_text_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT, border_color=theme.COLOR_BORDER,
            font=theme.font(13), placeholder_text="Değer girin…",
        )
        self._value_entry.grid(row=0, column=0, sticky="ew")

        # Tipe göre görünüp kaybolan yardımcı butonlar
        self._browse_btn = ctk.CTkButton(
            value_row, text="Gözat", width=90, height=36,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
            command=self._browse,
        )
        self._capture_btn = ctk.CTkButton(
            value_row, text="Tuşa Bas ve Yakala", width=170, height=36,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_WARNING,
            hover_color=theme.COLOR_WARNING_DARK, text_color="#101010",
            font=theme.font(12, True), command=self._capture_shortcut,
        )

        # Medya açılır listesi (değer kutusunun yerine geçer)
        self._media_var = ctk.StringVar(
            value=theme.MEDIA_LABELS.get(MEDIA_VALUES[0], MEDIA_VALUES[0]) if MEDIA_VALUES else "")
        self._media_menu = ctk.CTkOptionMenu(
            self, values=[theme.MEDIA_LABELS.get(v, v) for v in MEDIA_VALUES],
            variable=self._media_var, height=36,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_FIELD, text_color=theme.COLOR_TEXT,
            button_color=theme.COLOR_ACCENT, button_hover_color=theme.COLOR_ACCENT_DARK,
            dropdown_fg_color=theme.COLOR_CARD, dropdown_text_color=theme.COLOR_TEXT, dropdown_hover_color=theme.COLOR_HOVER,
            font=theme.font(13), dropdown_font=theme.font(12),
        )
        self._media_row = row
        row += 1

        # Makro adım düzenleyici (çok satırlı)
        self._macro_box = ctk.CTkTextbox(
            self, height=110, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_FIELD, border_color=theme.COLOR_BORDER,
            border_width=1, font=theme.mono(12), text_color=theme.COLOR_TEXT,
        )
        self._macro_row = row
        row += 1

        self._macro_help = ctk.CTkLabel(
            self, text="", font=theme.font(11), justify="left",
            text_color=theme.COLOR_TEXT_MUTED, anchor="w", wraplength=520,
        )
        self._macro_help_row = row
        row += 1

        # Makro araç düğmeleri: tuşları elle yazmak yerine yakalayıp satır
        # olarak eklemek ve hazır bekleme satırı koymak için.
        self._example_btn = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkButton(
            self._example_btn, text="Tuş Yakala → satır ekle", height=30,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_DARK, font=theme.font(11, True),
            command=self._macro_capture,
        ).pack(side="left")
        ctk.CTkButton(
            self._example_btn, text="Bekleme Ekle (500 ms)", height=30,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_ACCENT, font=theme.font(11, True),
            command=self._macro_add_wait,
        ).pack(side="left", padx=(theme.PAD_S, 0))
        ctk.CTkButton(
            self._example_btn, text="Örneği Kullan", height=30, width=120,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_ACCENT, font=theme.font(11, True),
            command=self._insert_macro_example,
        ).pack(side="left", padx=(theme.PAD_S, 0))
        self._example_row = row
        row += 1

        # --- Komut tipi için örnek komutlar paneli ----------------------
        # Aktif profile (Windows/macOS) göre en çok kullanılan komutlar
        # listelenir; satıra tıklamak komutu değer kutusuna yazar.
        self._cmd_examples = self._build_command_examples()
        self._cmd_examples_row = row
        row += 1

        # --- İpucu satırı ----------------------------------------------
        self._hint = ctk.CTkLabel(
            self, text="", font=theme.font(11), justify="left",
            text_color=theme.COLOR_TEXT_MUTED, anchor="w", wraplength=520,
        )
        self._hint.grid(row=row, column=0, sticky="ew", pady=(theme.PAD_S, 0))
        row += 1

        self.set_action(self._action)

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def set_os_key(self, os_key: str) -> None:
        """Aktif profili değiştirir; ipucu ve gözat filtreleri güncellenir."""
        self._os_key = (os_key or "windows").lower()
        self._apply_type_layout(self.current_type())

    def current_type(self) -> str:
        """Seçili eylem tipinin anahtarını döndürür."""
        return theme.LABEL_TO_TYPE.get(self._type_var.get(), "none")

    def set_action(self, action: dict | None) -> None:
        """Panele bir eylem sözlüğü yükler."""
        data = dict(action or {})
        type_ = data.get("type", "none")
        if type_ not in ACTION_TYPES:
            type_ = "none"
        value = data.get("value", "") or ""
        name = data.get("name", "") or ""

        if self._name_entry is not None:
            self._name_entry.delete(0, "end")
            self._name_entry.insert(0, name)

        self._type_var.set(theme.type_label(type_))

        self._value_entry.delete(0, "end")
        self._value_entry.insert(0, value)

        if type_ == "media":
            label = theme.MEDIA_LABELS.get(value, value)
            if value in MEDIA_VALUES:
                self._media_var.set(label)
            elif MEDIA_VALUES:
                self._media_var.set(theme.MEDIA_LABELS.get(MEDIA_VALUES[0], MEDIA_VALUES[0]))

        self._macro_box.delete("0.0", "end")
        if type_ == "macro" and value:
            self._macro_box.insert("0.0", "\n".join(p for p in value.split("|")))

        self._apply_type_layout(type_)

    def get_action(self) -> dict:
        """Paneldeki güncel değerleri eylem sözlüğü olarak döndürür.

        Returns:
            ``{"type": str, "value": str, "name": str}`` biçiminde sözlük.
        """
        type_ = self.current_type()

        if type_ == "none":
            value = ""
        elif type_ == "media":
            value = theme.LABEL_TO_MEDIA.get(self._media_var.get(), self._media_var.get())
        elif type_ == "macro":
            raw = self._macro_box.get("0.0", "end")
            steps = [line.strip() for line in raw.splitlines() if line.strip()]
            value = "|".join(steps)
        else:
            value = self._value_entry.get().strip()

        name = self._name_entry.get().strip() if self._name_entry is not None else ""
        return {"type": type_, "value": value, "name": name}

    # ------------------------------------------------------------------
    # İç mantık
    # ------------------------------------------------------------------

    def _build_command_examples(self) -> ctk.CTkFrame:
        """Aktif profile göre örnek komut listesi çerçevesini kurar.

        Windows ve macOS için ayrı listeler tutulur; satıra tıklamak
        komutu değer kutusuna yazar (kullanıcı üzerine düzenleyebilir).
        """
        is_mac = self._os_key.startswith("mac")
        ornekler = (
            (
                ('say "Merhaba"', "Metni sesli okur"),
                ("open ~/Downloads", "İndirilenler klasörünü açar"),
                ("screencapture -ci", "Ekran görüntüsünü panoya alır"),
                ("pmset displaysleepnow", "Ekranı hemen kapatır"),
                ("caffeinate -d -t 3600", "1 saat uyumayı engeller"),
                ("open -a Music", "Music uygulamasını açar"),
            ) if is_mac else (
                ("notepad", "Not Defteri'ni açar"),
                ("calc", "Hesap Makinesi'ni açar"),
                ("explorer shell:Downloads", "İndirilenler klasörünü açar"),
                ("rundll32.exe user32.dll,LockWorkStation", "Ekranı kilitler"),
                ("taskmgr", "Görev Yöneticisi'ni açar"),
                ("start https://google.com", "Adresi tarayıcıda açar"),
            )
        )

        kutu = ctk.CTkFrame(self, fg_color=theme.COLOR_PANEL,
                            corner_radius=theme.RADIUS_SMALL)
        baslik = "Örnek komutlar — macOS" if is_mac else "Örnek komutlar — Windows"
        ctk.CTkLabel(kutu, text=baslik + "  (tıkla, kutuya yazılır)",
                     font=theme.font(11, True), text_color=theme.COLOR_ACCENT,
                     anchor="w").pack(fill="x", padx=theme.PAD_S,
                                      pady=(theme.PAD_XS, 0))
        for komut, aciklama in ornekler:
            ctk.CTkButton(
                kutu, text=f"{komut}   —   {aciklama}",
                anchor="w", height=26, fg_color="transparent",
                hover_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT_DIM,
                font=theme.mono(11),
                command=lambda k=komut: self._set_value(k),
            ).pack(fill="x", padx=4, pady=0)
        ctk.CTkLabel(kutu, text="", height=2,
                     fg_color="transparent").pack()
        return kutu

    def _on_type_changed(self, _label: str) -> None:
        """Tip açılır listesi değiştiğinde yardımcı bileşenleri yeniler."""
        self._apply_type_layout(self.current_type())

    def _apply_type_layout(self, type_: str) -> None:
        """Seçili tipe göre hangi yardımcı bileşenlerin görüneceğini belirler."""
        color = theme.type_color(type_)
        self._type_badge.configure(
            text=theme.type_label(type_), fg_color=color,
            text_color=theme.contrast_text(color))

        # Önce hepsini gizle
        for widget in (self._browse_btn, self._capture_btn):
            widget.grid_forget()
        self._media_menu.grid_forget()
        self._macro_box.grid_forget()
        self._macro_help.grid_forget()
        self._example_btn.grid_forget()
        self._cmd_examples.grid_forget()
        self._value_title.grid()
        self._value_row.grid()
        self._value_entry.grid(row=0, column=0, sticky="ew")

        if type_ == "none":
            self._value_title.grid_remove()
            self._value_row.grid_remove()

        elif type_ in ("app", "file", "folder"):
            self._browse_btn.grid(row=0, column=1, padx=(theme.PAD_S, 0))
            labels = {"app": "Uygulama Seç", "file": "Dosya Seç", "folder": "Klasör Seç"}
            self._browse_btn.configure(text=labels.get(type_, "Gözat"))
            placeholders = {
                "app": "Uygulama yolu…",
                "file": "Dosya yolu…",
                "folder": "Klasör yolu…",
            }
            self._value_entry.configure(placeholder_text=placeholders.get(type_, "Değer girin…"))

        elif type_ == "shortcut":
            self._capture_btn.grid(row=0, column=1, padx=(theme.PAD_S, 0))
            is_mac = self._os_key.startswith("mac")
            self._value_entry.configure(
                placeholder_text="Örn: command+c" if is_mac else "Örn: ctrl+c")

        elif type_ == "media":
            self._value_row.grid_remove()
            self._media_menu.grid(row=self._media_row, column=0, sticky="ew")

        elif type_ == "macro":
            self._value_title.grid_remove()
            self._value_row.grid_remove()
            self._macro_box.grid(row=self._macro_row, column=0, sticky="ew")
            self._macro_help.grid(row=self._macro_help_row, column=0,
                                  sticky="ew", pady=(theme.PAD_XS, 0))
            self._example_btn.grid(row=self._example_row, column=0,
                                   sticky="w", pady=(theme.PAD_XS, 0))
            mod = "command" if self._os_key.startswith("mac") else "ctrl"
            self._macro_help.configure(
                text=(
                    "Her satır bir adımdır ve sırayla çalıştırılır.\n"
                    "• Kısayol satırı:  " + mod + "+c\n"
                    "• Bekleme satırı:  500        (milisaniye cinsinden)\n"
                    "Makro yalnızca bu iki adım tipini tanır; düz metin yazmak\n"
                    "için ayrı bir \"Metin Yaz\" eylemi kullan.\n"
                    "Kaydederken satırlar | işaretiyle birleştirilir: "
                    + mod + "+c|500|" + mod + "+v"
                )
            )

        elif type_ == "url":
            self._value_entry.configure(placeholder_text="Örn: bluedevelopment.com")
        elif type_ == "text":
            self._value_entry.configure(placeholder_text="Örn: merhaba dünya")
        elif type_ == "command":
            is_mac = self._os_key.startswith("mac")
            self._value_entry.configure(
                placeholder_text="Örn: say merhaba" if is_mac else "Örn: echo merhaba")
            self._cmd_examples.grid(row=self._cmd_examples_row, column=0,
                                    sticky="ew", pady=(theme.PAD_S, 0))

        self._hint.configure(text=theme.type_hint(type_, self._os_key))

    def _insert_macro_example(self) -> None:
        """Makro kutusuna örnek bir adım dizisi yazar."""
        mod = "command" if self._os_key.startswith("mac") else "ctrl"
        self._macro_box.delete("0.0", "end")
        self._macro_box.insert("0.0", f"{mod}+c\n500\n{mod}+v")

    def _macro_satir_ekle(self, satir: str) -> None:
        """Makro kutusunun sonuna yeni bir adım satırı ekler."""
        mevcut = self._macro_box.get("0.0", "end").rstrip("\n")
        self._macro_box.delete("0.0", "end")
        self._macro_box.insert("0.0",
                               (mevcut + "\n" if mevcut else "") + satir + "\n")

    def _macro_capture(self) -> None:
        """Tuş yakalama penceresini açar; yakalanan kısayol makroya satır
        olarak eklenir (kısayol tipindeki 'Yakala' ile aynı pencere)."""
        try:
            ShortcutCaptureDialog(self.winfo_toplevel(), self._os_key,
                                  self._macro_satir_ekle)
        except Exception:
            self._hint.configure(
                text="Tuş yakalanamadı; kombinasyonu elle satır olarak "
                     "yazabilirsin (örn. ctrl+c).",
                text_color=theme.COLOR_WARNING)

    def _macro_add_wait(self) -> None:
        """Makroya 500 ms'lik bekleme satırı ekler (süre elle düzenlenir)."""
        self._macro_satir_ekle("500")

    def _capture_shortcut(self) -> None:
        """Kısayol yakalama penceresini açar."""
        def _apply(combo: str) -> None:
            self._value_entry.delete(0, "end")
            self._value_entry.insert(0, combo)

        try:
            ShortcutCaptureDialog(self.winfo_toplevel(), self._os_key, _apply)
        except Exception:
            # Yakalama penceresi açılamazsa kullanıcı elle yazabilir.
            self._hint.configure(
                text="Kısayol yakalanamadı, kombinasyonu elle yazabilirsin. "
                     + theme.type_hint("shortcut", self._os_key),
                text_color=theme.COLOR_WARNING)

    def _browse(self) -> None:
        """Aktif tipe ve profile uygun dosya/klasör seçiciyi açar."""
        type_ = self.current_type()
        is_mac = self._os_key.startswith("mac")
        selected = ""

        try:
            if type_ == "folder":
                init_dir = os.path.expanduser("~")
                selected = filedialog.askdirectory(
                    parent=self.winfo_toplevel(),
                    title="Klasör Seç", initialdir=init_dir) or ""

            elif type_ == "app":
                if is_mac and sys.platform == "darwin":
                    # macOS'ta Tk dosya seçicisi .app paketlerini seçtirmez
                    # (klasör sayılır, soluk görünür) — yerleşik aramalı
                    # seçici açılır; sonuç geri çağırmayla yazılır.
                    AppPickerDialog(self.winfo_toplevel(), self._set_value)
                    return
                if is_mac:
                    init_dir = "/Applications" if os.path.isdir("/Applications") else os.path.expanduser("~")
                    file_types = [("Uygulamalar", "*.app"), ("Tüm Dosyalar", "*.*")]
                else:
                    init_dir = os.path.join(
                        os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
                    if not os.path.isdir(init_dir):
                        init_dir = os.path.expanduser("~")
                    file_types = [("Uygulamalar ve Kısayollar", "*.exe *.lnk"),
                                  ("Tüm Dosyalar", "*.*")]
                selected = filedialog.askopenfilename(
                    parent=self.winfo_toplevel(),
                    title="Uygulama Seç", initialdir=init_dir, filetypes=file_types) or ""

            else:  # file
                selected = filedialog.askopenfilename(
                    parent=self.winfo_toplevel(),
                    title="Dosya Seç", initialdir=os.path.expanduser("~"),
                    filetypes=[("Tüm Dosyalar", "*.*")]) or ""
        except Exception:
            selected = ""

        if selected:
            self._set_value(selected)

    def _set_value(self, selected: str) -> None:
        """Seçilen yolu değer alanına yazar (seçicilerin ortak çıkışı)."""
        if not selected:
            return
        if sys.platform.startswith("win"):
            selected = os.path.normpath(selected)
        self._value_entry.delete(0, "end")
        self._value_entry.insert(0, selected)


class AppPickerDialog(ctk.CTkToplevel):
    """macOS için yerleşik, aramalı uygulama seçici.

    Tk'nin dosya seçicisi macOS'ta ``.app`` paketlerini seçtirmediği için
    (paketler klasör sayılır ve soluk görünür) uygulama seçimi bu pencereden
    yapılır: standart klasörlerdeki uygulamalar listelenir, yazarak
    filtrelenir, tek tıkla seçilir. Listede olmayan bir uygulama için
    "Farklı konumdan seç…" düğmesi AppleScript'in yerel seçicisini açar
    (orada .app seçimi mümkündür).
    """

    _MAX_ROWS = 60  # tek seferde çizilecek satır sayısı (performans)

    def __init__(self, master, on_pick: Callable[[str], None]) -> None:
        """Pencereyi kurar ve uygulama listesini yükler.

        Args:
            master: Üst pencere.
            on_pick: Seçilen ``.app`` yolunu alacak geri çağırma.
        """
        _ana_pencereyi_gorunur_yap(master)
        super().__init__(master)
        self._on_pick = on_pick
        self._apps = platform_utils.list_installed_apps()

        # Eylem düzenleyici modal kilit (grab_set) tutar; kilidi DEVRALMAZSAK
        # bu pencere hiçbir tık/klavye olayı alamaz (donuk görünür). Açılışta
        # kilit devralınır, kapanışta önceki sahibine geri verilir.
        try:
            self._onceki_grab = self.grab_current()
        except Exception:
            self._onceki_grab = None

        self.title("Uygulama Seç")
        self.geometry("460x560")
        self.minsize(380, 420)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)

        self._search_var = ctk.StringVar()
        search = ctk.CTkEntry(self, textvariable=self._search_var,
                              placeholder_text="Ara… (örn. chrome)",
                              font=theme.font(13), height=38)
        search.pack(fill="x", padx=theme.PAD_M, pady=(theme.PAD_M, theme.PAD_S))
        search.bind("<KeyRelease>", lambda _e: self._rebuild())

        self._list = ctk.CTkScrollableFrame(self, fg_color=theme.COLOR_PANEL,
                                            corner_radius=theme.RADIUS_CARD)
        self._list.pack(fill="both", expand=True, padx=theme.PAD_M)

        alt = ctk.CTkFrame(self, fg_color="transparent")
        alt.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_S)
        ctk.CTkButton(alt, text="Farklı konumdan seç…", height=32,
                      fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_ACCENT,
                      font=theme.font(12),
                      command=self._pick_other).pack(side="left")
        ctk.CTkButton(alt, text="Vazgeç", height=32, width=90,
                      fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT, hover_color=theme.COLOR_DANGER,
                      font=theme.font(12),
                      command=self.destroy).pack(side="right")

        self._rebuild()

        # macOS'ta Toplevel'in arkada kalmaması için odak gecikmeli verilir;
        # modal kilit de burada devralınır (bkz. __init__ içindeki not).
        def _odakla() -> None:
            for step in (self.lift, self.focus_force, self.grab_set,
                         search.focus_set):
                try:
                    step()
                except Exception:
                    pass
        self.after(140, _odakla)

    def destroy(self) -> None:
        """Pencereyi kapatır ve modal kilidi önceki sahibine iade eder."""
        try:
            self.grab_release()
        except Exception:
            pass
        onceki = getattr(self, "_onceki_grab", None)
        if onceki is not None:
            try:
                if int(onceki.winfo_exists()):
                    onceki.after(60, onceki.grab_set)
            except Exception:
                pass
        super().destroy()

    def _rebuild(self) -> None:
        """Arama metnine göre listeyi yeniden çizer (en çok ``_MAX_ROWS``)."""
        for child in self._list.winfo_children():
            child.destroy()

        needle = (self._search_var.get() or "").strip().lower()
        matches = [(ad, yol) for ad, yol in self._apps
                   if needle in ad.lower()] if needle else self._apps

        for ad, yol in matches[: self._MAX_ROWS]:
            ctk.CTkButton(
                self._list, text=ad, anchor="w", height=34,
                fg_color="transparent", hover_color=theme.COLOR_HOVER,
                text_color=theme.COLOR_TEXT, font=theme.font(13),
                command=lambda p=yol: self._pick(p),
            ).pack(fill="x", padx=4, pady=1)

        kalan = len(matches) - self._MAX_ROWS
        if kalan > 0:
            ctk.CTkLabel(self._list, text=f"… ve {kalan} uygulama daha — daraltmak için arayın",
                         font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
                         ).pack(fill="x", padx=6, pady=(4, 6))
        elif not matches:
            ctk.CTkLabel(self._list, text="Eşleşen uygulama yok.",
                         font=theme.font(12), text_color=theme.COLOR_TEXT_MUTED
                         ).pack(fill="x", padx=6, pady=8)

    def _pick(self, path: str) -> None:
        """Seçimi bildirir ve pencereyi kapatır."""
        try:
            self._on_pick(path)
        finally:
            self.destroy()

    def _pick_other(self) -> None:
        """AppleScript'in yerel seçicisiyle listede olmayan bir .app seçtirir."""
        ok, cikti = platform_utils.run_osascript(
            'POSIX path of (choose file of type {"com.apple.application-bundle"} '
            'default location (path to applications folder))',
            timeout=120.0,
        )
        if ok and cikti:
            self._pick(cikti.rstrip("/"))


#: Açık olan tek eylem diyaloğu (tekillik koruması ``open_action_editor``'da).
_ACTIVE_DIALOG: "ActionEditorDialog | None" = None


class ActionEditorDialog(ctk.CTkToplevel):
    """:class:`ActionEditor` panelini modal bir pencerede sunar.

    Kaydet'e basıldığında ``on_save`` geri çağırması, düzenlenmiş eylem
    sözlüğü ile çağrılır. İptal edilirse hiçbir şey çağrılmaz.
    """

    def __init__(self, master, slot: str, slot_title: str, action: dict | None,
                 os_key: str, on_save: Callable[[str, dict], None]) -> None:
        """Diyaloğu oluşturur ve ekranın ortasına yerleştirir.

        Args:
            master: Üst pencere.
            slot: Slot anahtarı (``"K3"``, ``"C_2_5"``, ``"cw"`` …).
            slot_title: Başlıkta gösterilecek okunur ad.
            action: Düzenlenecek eylem.
            os_key: Aktif profil (``"windows"`` / ``"mac"``).
            on_save: ``(slot, action)`` ile çağrılacak geri çağırma.
        """
        _ana_pencereyi_gorunur_yap(master)
        super().__init__(master)
        self._slot = slot
        self._on_save = on_save

        self.title(f"Düzenle — {slot_title}")
        self.geometry("580x620")
        self.minsize(520, 560)
        self.configure(fg_color=theme.COLOR_BG)
        self.transient(master)

        header = ctk.CTkFrame(self, fg_color=theme.COLOR_PANEL,
                              corner_radius=theme.RADIUS_CARD)
        header.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_S))
        ctk.CTkLabel(header, text=slot_title, font=theme.font(19, True),
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=theme.PAD_M,
                                                       pady=(theme.PAD_M, 0))

        # Sağ üstte "?" — tüm eylem tiplerini anlatan yardım panelini açar.
        # Yerel import: app.ui.help yalnızca theme'e bağımlıdır, döngü oluşmaz.
        from app.ui import help as help_panel
        try:
            help_panel.help_button(header, "eylem_editoru").place(
                relx=1.0, y=8, x=-8, anchor="ne")
        except Exception:
            pass
        profile_text = "macOS profili" if (os_key or "").lower().startswith("mac") else "Windows profili"
        ctk.CTkLabel(header, text=f"Slot: {slot}   ·   {profile_text}",
                     font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED).pack(
            anchor="w", padx=theme.PAD_M, pady=(0, theme.PAD_M))

        body = ctk.CTkScrollableFrame(self, fg_color=theme.COLOR_CARD,
                                      corner_radius=theme.RADIUS_CARD)
        body.pack(fill="both", expand=True, padx=theme.PAD_L, pady=theme.PAD_S)

        self.editor = ActionEditor(body, os_key=os_key, action=action)
        self.editor.pack(fill="both", expand=True, padx=theme.PAD_M, pady=theme.PAD_M)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_S, theme.PAD_L))

        ctk.CTkButton(
            footer, text="Kaydet", height=40, corner_radius=theme.RADIUS_SMALL,
            fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_DARK,
            text_color="#101010", font=theme.font(13, True), command=self._save,
        ).pack(side="left", expand=True, fill="x", padx=(0, theme.PAD_XS))

        ctk.CTkButton(
            footer, text="Temizle", height=40, width=110,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
            hover_color=theme.COLOR_DANGER, font=theme.font(13, True),
            command=self._clear,
        ).pack(side="left", padx=theme.PAD_XS)

        ctk.CTkButton(
            footer, text="İptal", height=40, width=110,
            corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_DISABLED,
            hover_color=theme.COLOR_HOVER, font=theme.font(13, True),
            command=self.destroy,
        ).pack(side="left", padx=(theme.PAD_XS, 0))

        self.after(140, self._grab)

    def _grab(self) -> None:
        """Pencereyi öne alır ve modal kilidi kurar (macOS için gecikmeli)."""
        for step in (self.lift, self.focus_force, self.grab_set):
            try:
                step()
            except Exception:
                pass

    def _clear(self) -> None:
        """Eylemi ``none`` tipine döndürür (slotu boşaltır)."""
        current = self.editor.get_action()
        self.editor.set_action({"type": "none", "value": "", "name": current.get("name", "")})

    def _save(self) -> None:
        """Düzenlenen eylemi geri çağırma ile üst pencereye iletir."""
        action = self.editor.get_action()
        try:
            self._on_save(self._slot, action)
        finally:
            self.destroy()


def open_action_editor(master, slot: str, slot_title: str, action: dict | None,
                       os_key: str, on_save: Callable[[str, dict], None]) -> ActionEditorDialog:
    """Eylem düzenleme diyaloğunu açar ve nesnesini döndürür.

    Args:
        master: Üst pencere.
        slot: Slot anahtarı (``"K3"``, ``"C_2_5"``, ``"cw"`` …).
        slot_title: Başlıkta gösterilecek okunur ad.
        action: Düzenlenecek eylem sözlüğü.
        os_key: Aktif profil anahtarı.
        on_save: ``(slot, action)`` ile çağrılacak geri çağırma.

    Returns:
        Oluşturulan (veya öne getirilen mevcut) :class:`ActionEditorDialog`
        örneği.
    """
    global _ACTIVE_DIALOG

    # Tekillik koruması: bir düzenleme diyaloğu zaten açıksa ikinci bir
    # pencere üst üste AÇILMAZ. Aynı slot için olan istek mevcut pencereyi
    # öne getirir; farklı slot istenirse eski pencere kapatılıp yenisi açılır.
    mevcut = _ACTIVE_DIALOG
    if mevcut is not None:
        try:
            if int(mevcut.winfo_exists()):
                if getattr(mevcut, "_slot", None) == slot:
                    mevcut.lift()
                    mevcut.focus_force()
                    return mevcut
                mevcut.destroy()
        except Exception:
            pass
        _ACTIVE_DIALOG = None

    _ACTIVE_DIALOG = ActionEditorDialog(master, slot, slot_title, action,
                                        os_key, on_save)
    return _ACTIVE_DIALOG
