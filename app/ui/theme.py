# -*- coding: utf-8 -*-
"""
ExtraKeyboard MK1 — Arayüz Teması ve Ortak Stil Sabitleri.

Bu modül, PC uygulamasının tüm arayüz bileşenlerinin ortak kullandığı
renkleri, fontları, boşluk ölçülerini ve küçük yardımcı fonksiyonları
barındırır. Renk paleti çekirdek spesifikasyonun 8. bölümündeki
"Tema" başlığı ile birebir aynıdır:

    Koyu zeminler  : #1a1a2e  /  #16213e  /  #1e1e2e
    Açık zeminler  : #f2f3f7  /  #e6eaf3  /  #ffffff
    Vurgu renkleri : #3B8ED0  /  #2CC985  /  #FF9500  /  #E04F5F

Yüzey ve metin renkleri ``(açık, koyu)`` ikilisidir; CustomTkinter etkin
görünüm moduna göre doğru olanı seçer, böylece "Açık" tema gerçekten
çalışır. Hesap yapan kod (kontrast, animasyon) :func:`cur` ile tek dizeye
indirger. Hiçbir arayüz dosyası ham renk kodu yazmaz; hepsi buradaki
sabitleri kullanır.
"""

from __future__ import annotations

import sys

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Uygulama kimliği
# ---------------------------------------------------------------------------

APP_NAME: str = "ExtraKeyboard MK1"
APP_VERSION: str = "3.0.0"
HW_REV: str = "MK1"
VENDOR: str = "BlueDevelopment"

# ---------------------------------------------------------------------------
# Ana renk paleti (spesifikasyon bölüm 8)
# ---------------------------------------------------------------------------

# NOT: Aşağıdaki yüzey/metin renkleri ``(açık_tema, koyu_tema)`` ikilisidir.
# CustomTkinter bu biçimi doğrudan anlar ve görünüm modu değişince widget'ları
# kendiliğinden yeniden boyar; böylece "Açık" tema gerçekten çalışır.
# Vurgu renkleri (accent/success/warning/danger) marka renkleridir ve iki
# modda da aynıdır — tek dize olarak kalırlar.
# Tuple bekleyen CTk dışındaki yardımcılar (:func:`cur`) ile çözülür.

COLOR_BG: tuple[str, str] = ("#f2f3f7", "#1a1a2e")      # Uygulama zemini
COLOR_PANEL: tuple[str, str] = ("#e6eaf3", "#16213e")   # Panel kutuları
COLOR_CARD: tuple[str, str] = ("#ffffff", "#1e1e2e")    # Kart zemini
# Giriş kutusu / açılır menü zemini. Açık temada karttan (beyaz) FARKLI
# olmak zorunda; aynı olursa alanların sınırı görünmez ("çerçeve yok").
COLOR_FIELD: tuple[str, str] = ("#e9edf6", "#2b2b3d")
COLOR_HOVER: tuple[str, str] = ("#d7dded", "#3a3a4d")   # Üzerine gelince
COLOR_BORDER: tuple[str, str] = ("#c3cadb", "#33334a")  # Nötr kenarlık

COLOR_ACCENT: str = "#3B8ED0"      # Birincil vurgu (mavi)
COLOR_ACCENT_DARK: str = "#2d7ab5"  # Mavi vurgunun koyu tonu (hover)
COLOR_SUCCESS: str = "#2CC985"     # Başarı / bağlı (yeşil)
COLOR_SUCCESS_DARK: str = "#25a873"
COLOR_WARNING: str = "#FF9500"     # Uyarı / combo modu (turuncu)
COLOR_WARNING_DARK: str = "#d97e00"
COLOR_DANGER: str = "#E04F5F"      # Hata / bağlantı yok (kırmızı)
COLOR_DANGER_DARK: str = "#bd4250"

COLOR_TEXT: tuple[str, str] = ("#16213e", "#DCE4EE")        # Ana metin
COLOR_TEXT_DIM: tuple[str, str] = ("#43506b", "#bdc3c7")    # İkincil metin
COLOR_TEXT_MUTED: tuple[str, str] = ("#6b7793", "#7f8c8d")  # Silik metin
COLOR_DISABLED: tuple[str, str] = ("#9aa3b8", "#555555")    # Pasif öğe
COLOR_EMPTY: tuple[str, str] = ("#dfe3ec", "#1a1a1a")       # Devre dışı hücre

# Fiziksel tuşa basıldığında kartın 250 ms parladığı renkler
COLOR_FLASH_BG: tuple[str, str] = ("#cfe6fb", "#264a6e")
COLOR_FLASH_BORDER: tuple[str, str] = ("#3B8ED0", "#6fc3ff")

# Cihaz LED renkleri (spesifikasyon bölüm 6.4 varsayılanları)
LED_OS_WIN: str = "#1E90FF"
LED_OS_MAC: str = "#FFFFFF"
LED_COMBO: str = "#FF9500"
LED_LINK_OK: str = "#2CC985"
LED_LINK_ERR: str = "#E04F5F"
LED_DEFAULT_BRIGHTNESS: int = 60

# LED renk seçicide sunulan hazır palet
LED_PALETTE: tuple[str, ...] = (
    "#1E90FF", "#3B8ED0", "#00E5FF", "#2CC985",
    "#7DFF6B", "#FFD400", "#FF9500", "#E04F5F",
    "#FF2D95", "#9B59B6", "#FFFFFF", "#202020",
)

# ---------------------------------------------------------------------------
# Eylem tipleri — renk, Türkçe etiket ve ipucu metinleri
# ---------------------------------------------------------------------------

#: Spesifikasyon bölüm 7.2'deki 10 eylem tipinin arayüz renkleri.
TYPE_COLORS: dict[str, str] = {
    "none": "#555555",
    "app": "#2CC985",
    "url": "#3B8ED0",
    "shortcut": "#FF9500",
    "text": "#9B59B6",
    "command": "#E04F5F",
    "file": "#1ABC9C",
    "folder": "#F1C40F",
    "media": "#E67E22",
    "macro": "#7D5FFF",
}

#: Eylem tiplerinin kullanıcıya gösterilen Türkçe adları.
TYPE_LABELS: dict[str, str] = {
    "none": "Yok",
    "app": "Uygulama",
    "url": "Web Adresi",
    "shortcut": "Kısayol",
    "text": "Metin",
    "command": "Komut",
    "file": "Dosya",
    "folder": "Klasör",
    "media": "Medya",
    "macro": "Makro",
}

#: Türkçe etiketten tip anahtarına geri dönüş tablosu.
LABEL_TO_TYPE: dict[str, str] = {v: k for k, v in TYPE_LABELS.items()}

#: Medya değerlerinin Türkçe adları (spesifikasyon bölüm 7.2).
MEDIA_LABELS: dict[str, str] = {
    "volume_up": "Sesi Aç",
    "volume_down": "Sesi Kıs",
    "mute": "Sessize Al",
    "play_pause": "Oynat / Duraklat",
    "next": "Sonraki Parça",
    "prev": "Önceki Parça",
}

#: Medya Türkçe adından değere geri dönüş tablosu.
LABEL_TO_MEDIA: dict[str, str] = {v: k for k, v in MEDIA_LABELS.items()}


def type_hint(type_: str, os_key: str) -> str:
    """Seçili eylem tipi ve aktif profile göre Türkçe ipucu metni döndürür.

    Args:
        type_: Eylem tipi (``none``, ``app``, ``url``, ...).
        os_key: Aktif profil anahtarı — ``"windows"`` veya ``"mac"``.

    Returns:
        Değer kutusunun altında gösterilecek açıklama metni.
    """
    is_mac = (os_key or "windows").lower().startswith("mac")
    mod = "command" if is_mac else "ctrl"
    hints: dict[str, str] = {
        "none": "Bu slot için hiçbir şey yapılmaz. Tuş boş kalır.",
        "app": (
            "Açılacak uygulamanın tam yolu. Örnek: /Applications/Safari.app"
            if is_mac else
            "Açılacak uygulamanın tam yolu. Örnek: C:\\Windows\\notepad.exe"
        ),
        "url": "Varsayılan tarayıcıda açılır. Şema yazmazsan başına https:// eklenir. Örnek: bluedevelopment.com",
        "shortcut": (
            f"Tuşları + ile birleştir. Örnek: {mod}+c · {mod}+shift+4"
            + ("  (macOS'ta Control ayrı bir tuştur, komut için command yaz.)" if is_mac else "")
        ),
        "text": "Yazılacak düz metin; sonuna otomatik 1 boşluk eklenir. Örnek: merhaba dünya",
        "command": (
            "Kabuk komutu çalıştırılır. Örnek: say merhaba"
            if is_mac else
            "Kabuk komutu çalıştırılır. Örnek: echo merhaba"
        ),
        "file": (
            "Varsayılan uygulamada açılacak dosya. Örnek: ~/notlar.txt"
            if is_mac else
            "Varsayılan uygulamada açılacak dosya. Örnek: C:\\Notlar\\liste.txt"
        ),
        "folder": (
            "Finder'da açılacak klasör. Örnek: ~/Downloads"
            if is_mac else
            "Explorer'da açılacak klasör. Örnek: C:\\Users\\Kullanici\\Downloads"
        ),
        "media": "Sistem medya tuşu gönderilir. Aşağıdaki listeden seç.",
        "macro": (
            "Adımları | ile ayır. Sadece sayı yazarsan o kadar milisaniye beklenir. "
            f"Örnek: {mod}+c|500|{mod}+v"
        ),
    }
    return hints.get(type_, "")


def type_color(type_: str) -> str:
    """Eylem tipine karşılık gelen rozet/kenarlık rengini döndürür."""
    return TYPE_COLORS.get(type_, COLOR_DISABLED)


def type_label(type_: str) -> str:
    """Eylem tipinin Türkçe adını döndürür."""
    return TYPE_LABELS.get(type_, type_)


# ---------------------------------------------------------------------------
# Fontlar
# ---------------------------------------------------------------------------

#: Tüm platformlarda bulunan güvenli arayüz fontu.
FONT_FAMILY: str = "Arial"

#: Olay logu ve hex girişleri için eş aralıklı font.
if sys.platform == "darwin":
    FONT_MONO_FAMILY: str = "Menlo"
elif sys.platform.startswith("win"):
    FONT_MONO_FAMILY = "Consolas"
else:
    FONT_MONO_FAMILY = "DejaVu Sans Mono"


def font(size: int = 12, bold: bool = False) -> tuple:
    """Arayüz fontu üretir.

    Args:
        size: Punto.
        bold: Kalın olsun mu.

    Returns:
        Tkinter'ın kabul ettiği ``(aile, punto[, stil])`` demeti.
    """
    return (FONT_FAMILY, size, "bold") if bold else (FONT_FAMILY, size)


def mono(size: int = 11, bold: bool = False) -> tuple:
    """Eş aralıklı (monospace) font üretir."""
    return (FONT_MONO_FAMILY, size, "bold") if bold else (FONT_MONO_FAMILY, size)


# ---------------------------------------------------------------------------
# Ölçüler
# ---------------------------------------------------------------------------

RADIUS_CARD: int = 12       #: Kart köşe yuvarlaklığı
RADIUS_SMALL: int = 8       #: Buton / giriş kutusu köşe yuvarlaklığı
RADIUS_PILL: int = 20       #: Rozet köşe yuvarlaklığı

PAD_XS: int = 4
PAD_S: int = 8
PAD_M: int = 12
PAD_L: int = 18

SIDEBAR_WIDTH: int = 250    #: Yan panel genişliği
WINDOW_SIZE: str = "1360x820"   #: Açılış pencere ölçüsü (5 sütunlu ızgara + yan panel)
WINDOW_MIN: tuple[int, int] = (1240, 720)  #: En küçük pencere ölçüsü (5 sütunlu ızgara)

FLASH_MS: int = 250         #: Fiziksel tuş geri bildiriminin süresi (ms)
FLASH_FADE_MS: int = 350    #: Parlamanın taban renge sönümlenme süresi (ms)
FLASH_FADE_STEPS: int = 12  #: Sönümleme animasyonunun adım sayısı
COMBO_BLINK_MS: int = 550   #: Combo uyarı çubuğunun yanıp sönme periyodu (ms)
EVENT_LOG_LIMIT: int = 200  #: Canlı olay logunda tutulan satır sayısı


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def apply_theme(mode: str = "Dark") -> str:
    """CustomTkinter genel görünümünü ayarlar.

    Args:
        mode: ``"Dark"``, ``"Light"`` veya ``"System"``.

    Returns:
        Gerçekte uygulanan mod adı.
    """
    normalized = (mode or "Dark").strip().capitalize()
    if normalized not in ("Dark", "Light", "System"):
        normalized = "Dark"
    try:
        ctk.set_appearance_mode(normalized)
        ctk.set_default_color_theme("blue")
    except Exception:
        # Tema uygulanamazsa uygulama yine de açılmalı.
        pass
    return normalized


def cur(color) -> str:
    """Renk sabitini o anki görünüm moduna göre tek dizeye indirger.

    ``(açık, koyu)`` ikilisi verilirse etkin moda uygun olanı döndürür;
    zaten dize olan renkleri olduğu gibi geçirir. CustomTkinter tuple'ı
    kendisi çözebildiği için bu yardımcı yalnızca hesap yapan kodda
    gereklidir (kontrast, interpolasyon, hex doğrulama).
    """
    if isinstance(color, (tuple, list)):
        if not color:
            return "#000000"
        try:
            koyu = str(ctk.get_appearance_mode()).lower().startswith("dark")
        except Exception:
            koyu = True
        return str(color[1] if (koyu and len(color) > 1) else color[0])
    return str(color)


def normalize_hex(value, fallback=COLOR_ACCENT) -> str:
    """Kullanıcının girdiği rengi ``#RRGGBB`` biçimine çevirir.

    ``1E90FF``, ``#1e90ff``, ``1e90ff`` gibi yazımların hepsini kabul eder.
    Geçersiz girdide ``fallback`` döndürür.
    """
    value = cur(value)
    fallback = cur(fallback)
    if not value:
        return fallback
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return fallback
    try:
        int(text, 16)
    except ValueError:
        return fallback
    return "#" + text.upper()


def hex_to_device(value: str) -> str:
    """``#1E90FF`` biçimindeki rengi cihaz protokolünün beklediği ``1E90FF``e çevirir."""
    return normalize_hex(value).lstrip("#")


def interpolate_hex(c1, c2, t: float) -> str:
    """İki ``#RRGGBB`` rengi arasında doğrusal geçiş yapar.

    Kart parlaması gibi animasyonlarda ara kareleri üretmek için kullanılır.

    Args:
        c1: Başlangıç rengi (``t = 0`` iken döner).
        c2: Bitiş rengi (``t = 1`` iken döner).
        t: 0..1 aralığında geçiş oranı; aralık dışı değerler kırpılır.

    Returns:
        ``#RRGGBB`` biçiminde ara renk.
    """
    start = normalize_hex(cur(c1), "#000000").lstrip("#")
    end = normalize_hex(cur(c2), "#000000").lstrip("#")
    ratio = 0.0 if t < 0 else 1.0 if t > 1 else float(t)
    channels = []
    for i in (0, 2, 4):
        v1 = int(start[i:i + 2], 16)
        v2 = int(end[i:i + 2], 16)
        channels.append(int(round(v1 + (v2 - v1) * ratio)))
    return "#{:02X}{:02X}{:02X}".format(*channels)


def contrast_text(bg_hex) -> str:
    """Verilen zemin rengi üzerinde okunaklı yazı rengini döndürür.

    Açık zeminlerde siyah, koyu zeminlerde beyaz döner.
    """
    clean = normalize_hex(cur(bg_hex), "#000000").lstrip("#")
    try:
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
    except ValueError:
        return "#FFFFFF"
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#000000" if luminance > 0.62 else "#FFFFFF"


def shorten(text: str, limit: int = 34) -> str:
    """Uzun metinleri kart içinde taşırmadan göstermek için kısaltır."""
    if text is None:
        return ""
    clean = str(text).replace("\n", " ").strip()
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 1)] + "…"


def action_summary(action: dict | None) -> str:
    """Bir eylem sözlüğünün kart üzerinde gösterilecek özet metnini üretir."""
    if not action:
        return "Yapılandırılmadı"
    type_ = action.get("type", "none")
    value = (action.get("value") or "").strip()
    if type_ == "none" or not value:
        return "Yapılandırılmadı"
    if type_ == "media":
        return MEDIA_LABELS.get(value, value)
    if type_ in ("app", "file", "folder"):
        # Yol uzun olabilir; sadece son parçayı göster.
        parts = value.replace("\\", "/").rstrip("/").split("/")
        tail = parts[-1] if parts else value
        return shorten(tail, 30)
    return shorten(value, 30)


def bind_click(widget, callback, cursor: str = "hand2") -> None:
    """Bir bileşene ve tüm alt bileşenlerine sol tık olayını bağlar.

    CustomTkinter kartları iç içe çerçeve/etiketlerden oluştuğu için sadece
    dış çerçeveye bağlanan tık olayı çalışmaz. Bu yardımcı, ağacın tamamını
    dolaşıp her düğüme aynı geri çağırmayı ekler.

    Args:
        widget: Kök bileşen.
        callback: ``event`` parametresi alan geri çağırma.
        cursor: Fare imleci adı; uygulanamazsa sessizce atlanır.
    """
    # CustomTkinter bileşenleri `bind()` çağrısını iç tuvale (canvas)
    # devreder; ağaç dolaşımı aynı tuvali alt bileşen olarak tekrar ziyaret
    # ettiğinde aynı geri çağırma İKİ kez bağlanır ve tek tık iki kez
    # tetiklenirdi (örn. eylem diyaloğu üst üste iki kez açılırdı). Tek bir
    # fiziksel tık için X olay zamanı (event.time) tüm kopya tetiklemelerde
    # aynıdır; ağaç başına paylaşılan bu bekçi aynı olayı bir kez geçirir.
    son_olay = {"time": None}

    def _tek_sefer(event, _cb=callback, _son=son_olay):
        zaman = getattr(event, "time", None)
        if zaman is not None and zaman == _son["time"]:
            return None
        _son["time"] = zaman
        return _cb(event)

    def _bagla(node) -> None:
        try:
            node.bind("<Button-1>", _tek_sefer, add="+")
        except Exception:
            pass
        if cursor:
            try:
                node.configure(cursor=cursor)
            except Exception:
                pass
        try:
            children = node.winfo_children()
        except Exception:
            children = []
        for child in children:
            _bagla(child)

    _bagla(widget)


def make_badge(master, text: str, color: str, width: int = 84, height: int = 22):
    """Renk kodlu küçük bir "rozet" etiketi üretir ve döndürür.

    Args:
        master: Üst bileşen.
        text: Rozet üzerindeki yazı.
        color: Rozet zemin rengi.
        width: Rozet genişliği (piksel).
        height: Rozet yüksekliği (piksel).

    Returns:
        Yerleştirilmeye hazır ``CTkLabel``.
    """
    return ctk.CTkLabel(
        master,
        text=text,
        width=width,
        height=height,
        corner_radius=RADIUS_PILL,
        fg_color=color,
        text_color=contrast_text(color),
        font=font(10, True),
    )
