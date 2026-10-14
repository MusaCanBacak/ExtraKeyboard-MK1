# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Combo Matrisi (üst üçgen).

``COMBO`` tuşuna bir kez basılıp (bas-çek) işlev tuşları içinden iki tuşa
basılınca cihaz ``EV COMBO <a> <b>`` gönderir ve ``a < b`` olacak şekilde
normalize eder. Bu yüzden yapılandırmada yalnızca üst üçgen anlamlıdır:
C(n, 2) benzersiz kombinasyon (n = ``KEY_COUNT``; 10 tuşta 45 combo).

Matrisin boyutu ``config.KEY_COUNT``tan türetilir:

* Satır ve sütun başlıkları ``K1``..``K<KEY_COUNT>``
* Köşegen (``i == j``) devre dışıdır — aynı tuşa iki kez basılamaz
* Alt üçgen (``i > j``) boştur — üst üçgenin aynadaki karşılığıdır
* Üst üçgen (``i < j``) tıklanabilir ve eylem tipine göre renklenir
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.core.config import COMBO_IDS, KEY_COUNT, combo_id, parse_combo_id
from app.ui import theme

CELL_WIDTH: int = 62
CELL_HEIGHT: int = 46
HEADER_WIDTH: int = 44


class ComboMatrix(ctk.CTkFrame):
    """``KEY_COUNT``×``KEY_COUNT`` üst üçgen combo matrisi ve bilgi paneli."""

    def __init__(self, master, get_action: Callable[[str], dict],
                 on_edit: Callable[[str], None], **kwargs) -> None:
        """Matrisi kurar.

        Args:
            master: Üst bileşen.
            get_action: ``C_a_b`` alıp eylem sözlüğü döndüren fonksiyon.
            on_edit: Hücreye tıklanınca ``C_a_b`` ile çağrılacak geri çağırma.
        """
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self._get_action = get_action
        self._on_edit = on_edit
        self.cells: dict[str, ctk.CTkButton] = {}
        self._base_colors: dict[str, str] = {}
        self._flash_jobs: dict[str, str] = {}
        self._selected: str | None = None

        # --- Başlık ------------------------------------------------------
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=(0, theme.PAD_S))
        ctk.CTkLabel(head, text="Kombinasyonlar", font=theme.font(16, True),
                     text_color=theme.COLOR_TEXT).pack(side="left")
        ctk.CTkLabel(head, text=f"{len(COMBO_IDS)} benzersiz combo  ·  "
                                "COMBO'ya bir kez bas, sonra iki tuşa bas",
                     font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED
                     ).pack(side="left", padx=theme.PAD_M)

        # --- Matris ------------------------------------------------------
        board = ctk.CTkFrame(self, corner_radius=theme.RADIUS_CARD,
                             fg_color=theme.COLOR_CARD)
        board.pack(fill="x", padx=2)

        grid = ctk.CTkFrame(board, fg_color="transparent")
        grid.pack(padx=theme.PAD_M, pady=theme.PAD_M)

        # Sol üst köşe (boş)
        ctk.CTkLabel(grid, text="", width=HEADER_WIDTH, height=26).grid(
            row=0, column=0, padx=2, pady=2)

        # Sütun başlıkları K1..K<KEY_COUNT> (spec bölüm 2 ve 7.1 isimlendirmesi)
        for column in range(KEY_COUNT):
            ctk.CTkLabel(grid, text=f"K{column + 1}", width=CELL_WIDTH, height=26,
                         font=theme.font(11, True), text_color=theme.COLOR_TEXT_DIM
                         ).grid(row=0, column=column + 1, padx=2, pady=2)

        for row in range(KEY_COUNT):
            # Satır başlığı K1..K<KEY_COUNT>
            ctk.CTkLabel(grid, text=f"K{row + 1}", width=HEADER_WIDTH, height=CELL_HEIGHT,
                         font=theme.font(11, True), text_color=theme.COLOR_TEXT_DIM
                         ).grid(row=row + 1, column=0, padx=2, pady=2)

            for column in range(KEY_COUNT):
                if row == column:
                    # Köşegen — devre dışı
                    ctk.CTkLabel(grid, text="—", width=CELL_WIDTH, height=CELL_HEIGHT,
                                 corner_radius=theme.RADIUS_SMALL,
                                 fg_color=theme.COLOR_EMPTY, font=theme.font(12),
                                 text_color="#333333"
                                 ).grid(row=row + 1, column=column + 1, padx=2, pady=2)
                elif row < column:
                    # Üst üçgen — tıklanabilir hücre
                    cid = combo_id(row + 1, column + 1)
                    button = ctk.CTkButton(
                        grid, text=f"{row + 1}+{column + 1}",
                        width=CELL_WIDTH, height=CELL_HEIGHT,
                        corner_radius=theme.RADIUS_SMALL,
                        fg_color=theme.COLOR_FIELD, hover_color=theme.COLOR_HOVER,
                        border_width=1, border_color=theme.COLOR_BORDER,
                        font=theme.font(11, True), text_color=theme.COLOR_TEXT_MUTED,
                        command=lambda key=cid: self._handle_click(key),
                    )
                    button.grid(row=row + 1, column=column + 1, padx=2, pady=2)
                    self.cells[cid] = button
                    self._base_colors[cid] = theme.COLOR_FIELD
                else:
                    # Alt üçgen — boş (simetrik karşılığı üst üçgende)
                    ctk.CTkLabel(grid, text="", width=CELL_WIDTH, height=CELL_HEIGHT,
                                 fg_color="transparent"
                                 ).grid(row=row + 1, column=column + 1, padx=2, pady=2)

        # --- Renk açıklaması ---------------------------------------------
        legend = ctk.CTkFrame(self, fg_color="transparent")
        legend.pack(fill="x", pady=(theme.PAD_S, 0))
        ctk.CTkLabel(legend, text="Renkler:", font=theme.font(11, True),
                     text_color=theme.COLOR_TEXT_MUTED).pack(side="left", padx=(2, theme.PAD_S))
        for type_ in ("app", "url", "shortcut", "text", "command",
                      "file", "folder", "media", "macro"):
            chip = ctk.CTkFrame(legend, fg_color="transparent")
            chip.pack(side="left", padx=5)
            ctk.CTkLabel(chip, text="●", font=theme.font(13),
                         text_color=theme.type_color(type_)).pack(side="left")
            ctk.CTkLabel(chip, text=theme.type_label(type_), font=theme.font(10),
                         text_color=theme.COLOR_TEXT_MUTED).pack(side="left", padx=(2, 0))

        # --- Seçili combo bilgi paneli ------------------------------------
        info = ctk.CTkFrame(self, corner_radius=theme.RADIUS_CARD,
                            fg_color=theme.COLOR_CARD)
        info.pack(fill="x", pady=(theme.PAD_M, 0), padx=2)

        info_inner = ctk.CTkFrame(info, fg_color="transparent")
        info_inner.pack(fill="x", padx=theme.PAD_M, pady=theme.PAD_M)

        self._info_title = ctk.CTkLabel(
            info_inner, text="Bir kombinasyon seç", font=theme.font(14, True),
            text_color=theme.COLOR_TEXT, anchor="w")
        self._info_title.pack(fill="x")

        self._info_detail = ctk.CTkLabel(
            info_inner,
            text="Üst üçgendeki hücrelerden birine tıklayarak eylem ata. "
                 "Sıra önemsizdir: 2+5 ile 5+2 aynı combodur.",
            font=theme.font(11), text_color=theme.COLOR_TEXT_MUTED,
            anchor="w", justify="left")
        self._info_detail.pack(fill="x", pady=(4, 0))

        self.refresh()

    # ------------------------------------------------------------------
    # Genel API
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Tüm hücreleri güncel yapılandırmadan yeniden renklendirir."""
        for cid, button in self.cells.items():
            try:
                action = self._get_action(cid) or {}
            except Exception:
                action = {}
            type_ = action.get("type", "none")
            value = (action.get("value") or "").strip()
            configured = type_ != "none" and bool(value)

            first, second = parse_combo_id(cid)
            if configured:
                color = theme.type_color(type_)
                self._base_colors[cid] = color
                button.configure(fg_color=color, border_color=color,
                                 text_color=theme.contrast_text(color),
                                 text=f"{first}+{second}")
            else:
                self._base_colors[cid] = theme.COLOR_FIELD
                button.configure(fg_color=theme.COLOR_FIELD,
                                 border_color=theme.COLOR_BORDER,
                                 text_color=theme.COLOR_TEXT_MUTED,
                                 text=f"{first}+{second}")

        if self._selected:
            self._update_info(self._selected)

    def flash(self, cid: str) -> None:
        """Fiziksel olarak tetiklenen combo hücresini kısa süre parlatır."""
        button = self.cells.get(cid)
        if button is None:
            return

        job = self._flash_jobs.pop(cid, None)
        if job is not None:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        try:
            button.configure(fg_color=theme.COLOR_FLASH_BORDER,
                             border_color=theme.COLOR_FLASH_BORDER,
                             text_color="#101010")
        except Exception:
            return
        self._flash_jobs[cid] = self.after(theme.FLASH_MS, lambda key=cid: self._end_flash(key))

    def _end_flash(self, cid: str) -> None:
        """Parlama bitince hücreyi normal rengine döndürür."""
        self._flash_jobs.pop(cid, None)
        button = self.cells.get(cid)
        if button is None:
            return
        base = self._base_colors.get(cid, theme.COLOR_FIELD)
        try:
            if base == theme.COLOR_FIELD:
                button.configure(fg_color=base, border_color=theme.COLOR_BORDER,
                                 text_color=theme.COLOR_TEXT_MUTED)
            else:
                button.configure(fg_color=base, border_color=base,
                                 text_color=theme.contrast_text(base))
        except Exception:
            pass

    def select(self, cid: str) -> None:
        """Bilgi panelinde verilen combonun ayrıntılarını gösterir."""
        self._selected = cid
        self._update_info(cid)

    # ------------------------------------------------------------------
    # İç mantık
    # ------------------------------------------------------------------

    def _handle_click(self, cid: str) -> None:
        """Hücre tıklamasını bilgi paneline ve düzenleyiciye yönlendirir."""
        self.select(cid)
        try:
            self._on_edit(cid)
        except Exception:
            pass

    def _update_info(self, cid: str) -> None:
        """Seçili combonun bilgi panelini günceller."""
        try:
            first, second = parse_combo_id(cid)
        except Exception:
            return
        try:
            action = self._get_action(cid) or {}
        except Exception:
            action = {}

        type_ = action.get("type", "none")
        name = (action.get("name") or "").strip() or f"Combo {first}+{second}"
        self._info_title.configure(text=f"{name}   ·   {cid}")

        if type_ == "none" or not (action.get("value") or "").strip():
            self._info_detail.configure(
                text="Bu kombinasyona henüz eylem atanmadı. "
                     "Hücreye tıklayarak düzenleyebilirsin.",
                text_color=theme.COLOR_TEXT_MUTED)
        else:
            self._info_detail.configure(
                text=f"Tip: {theme.type_label(type_)}   ·   Değer: {action.get('value')}",
                text_color=theme.COLOR_TEXT_DIM)
