# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Sürükle-Bırak Yardımcıları.

Tuş kartlarının üzerine bırakılan dosya, klasör veya metni eylem
sözlüğüne çeviren saf yardımcı fonksiyonlar. tkdnd'nin ham bırakma
verisini ayrıştırmak (:func:`parse_drop_paths`) ve bırakılan veriden
uygun eylem tipini çıkarmak (:func:`action_from_drop`) burada yapılır;
yapılandırmaya yazma işi çağıran tarafa aittir.

Fonksiyonlar platform bağımsızdır: hem macOS (``/Applications/Safari.app``)
hem Windows (``C:\\Program Files\\uygulama.exe``) yol biçimlerini işler.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

#: Windows'ta "uygulama" sayılan dosya uzantıları.
_APP_FILE_EXTS: tuple[str, ...] = (".exe", ".lnk", ".bat", ".cmd")


def parse_drop_paths(widget, raw: str) -> list[str]:
    """tkdnd'nin bıraktığı ham yol dizgisini yol listesine çevirir.

    tkdnd birden çok dosyayı Tcl listesi olarak iletir; boşluk içeren
    yollar (özellikle Windows'ta) küme parantezi ile sarılır, örn.::

        {C:\\Program Files\\uygulama.exe} C:\\notlar.txt

    ``widget.tk.splitlist`` bu biçimi doğru ayırır; herhangi bir nedenle
    kullanılamazsa küme parantezine duyarlı yedek ayrıştırıcı devreye girer.

    Args:
        widget: ``tk`` yorumlayıcısına erişimi olan herhangi bir bileşen.
        raw: ``<<Drop>>`` olayının ``data`` alanındaki ham dizgi.

    Returns:
        Temizlenmiş yol listesi; boş girdide boş liste.
    """
    if not raw:
        return []
    try:
        parts = widget.tk.splitlist(raw)
    except Exception:
        parts = _split_braced(raw)
    return [str(part).strip() for part in parts if str(part).strip()]


def action_from_drop(veri: str, tur: str) -> dict | None:
    """Bırakılan veriden eylem sözlüğü üretir.

    Kurallar sırasıyla denenir:

    1. ``tur='text'`` ve ``http://`` / ``https://`` / ``www.`` ile
       başlıyorsa → ``url`` eylemi (ad: alan adı).
    2. ``.app`` ile biten var olan DİZİN (macOS uygulama paketi) veya
       ``.exe``/``.lnk``/``.bat``/``.cmd`` uzantılı var olan dosya
       (Windows) → ``app`` eylemi.
    3. Var olan klasör → ``folder`` eylemi.
    4. Var olan dosya → ``file`` eylemi.
    5. Hiçbiri değilse ``None`` (bırakma sessizce yok sayılır).

    Args:
        veri: Bırakılan tek yol ya da metin.
        tur: ``'files'`` (dosya bırakması) veya ``'text'`` (metin bırakması).

    Returns:
        ``{"type": ..., "value": ..., "name": ...}`` sözlüğü ya da ``None``.
    """
    text = (veri or "").strip()
    if not text:
        return None

    if tur == "text":
        lower = text.lower()
        if lower.startswith(("http://", "https://", "www.")):
            return {"type": "url", "value": text, "name": _url_name(text)}
        # URL değilse metin yine de bir yol olabilir; yol kurallarına düş.

    return _action_from_path(text)


# ---------------------------------------------------------------------------
# İç yardımcılar
# ---------------------------------------------------------------------------

def _split_braced(raw: str) -> list[str]:
    """Küme parantezli Tcl listesini elle ayırır (splitlist yedeği)."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in raw:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0:
                    parts.append("".join(current))
                    current = []
                    continue
        elif ch == " " and depth == 0:
            if current:
                parts.append("".join(current))
                current = []
            continue
        current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _url_name(url: str) -> str:
    """Web adresinden temiz görünen adı (alan adını) çıkarır."""
    candidate = url if "://" in url else "https://" + url
    try:
        host = urlparse(candidate).netloc
    except Exception:
        host = ""
    # Kullanıcı adı ve port bölümlerini at.
    host = host.split("@")[-1].split(":")[0].strip()
    if host.lower().startswith("www."):
        host = host[4:]
    return host or url


def _action_from_path(path: str) -> dict | None:
    """Bir dosya sistemi yolunu eylem sözlüğüne çevirir; eşleşme yoksa None."""
    trimmed = path.rstrip("/\\") or path
    lower = trimmed.lower()

    if lower.endswith(".app") and os.path.isdir(path):
        # macOS uygulama paketi (.app aslında bir dizindir).
        return {"type": "app", "value": path,
                "name": _clean_name(trimmed, strip_ext=True)}
    if lower.endswith(_APP_FILE_EXTS) and os.path.isfile(path):
        # Windows çalıştırılabilir / kısayol dosyaları.
        return {"type": "app", "value": path,
                "name": _clean_name(trimmed, strip_ext=True)}
    if os.path.isdir(path):
        return {"type": "folder", "value": path,
                "name": _clean_name(trimmed, strip_ext=False)}
    if os.path.isfile(path):
        return {"type": "file", "value": path,
                "name": _clean_name(trimmed, strip_ext=True)}
    return None


def _clean_name(path: str, strip_ext: bool = True) -> str:
    """Yoldan temiz görünen ad üretir: son parça, uzantısız, baş harf büyük.

    Hem ``/`` hem ``\\`` ayraçlı yolları işler; klasör adlarında uzantı
    kırpılmaz (``proje.v2`` gibi adlar bozulmasın diye).
    """
    base = os.path.basename(path.replace("\\", "/").rstrip("/")) or path
    if strip_ext:
        stem, _ext = os.path.splitext(base)
        if stem:
            base = stem
    base = base.strip()
    if not base:
        return ""
    return base[:1].upper() + base[1:]
