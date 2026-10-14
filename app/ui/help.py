"""
ExtraKeyboard MK1 — sayfa içi yardım panelleri.

Her sekmenin (ve eylem düzenleyicinin) sağ üst köşesine küçük bir "?"
düğmesi yerleştirilir; tıklanınca o sayfayı ve üzerindeki HER ŞEYİN ne işe
yaradığını anlatan kaydırılabilir bir bilgi penceresi açılır.

* :data:`TOPICS`      — konu anahtarı → (başlık, gövde metni)
* :func:`open_help`   — konuyu tek pencerede gösterir (tekil; ikinci çağrı
  aynı pencereyi öne getirir, üst üste pencere açılmaz)
* :func:`attach_help` — bir sekme çerçevesinin sağ üst köşesine "?" koyar
* :func:`help_button` — yerleşimini çağıranın yaptığı "?" düğmesi üretir
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme

# ---------------------------------------------------------------------------
#  Konu metinleri
# ---------------------------------------------------------------------------

_EYLEM_TIPLERI = """EYLEM TİPLERİ (tüm sekmelerde aynıdır)

•  Boş (none) — Tuşa basınca hiçbir şey olmaz.

•  URL — Adresi varsayılan tarayıcıda açar. "https://" yazmak zorunda
   değilsiniz; "bluedevelopment.com" yazarsanız başına otomatik eklenir.

•  Uygulama — Bir programı başlatır. macOS'ta "Gözat" düğmesi kurulu
   uygulamaları listeleyen aramalı bir seçici açar (yazıp filtreleyin,
   tıklayıp seçin); Windows'ta .exe veya .lnk (kısayol) dosyası seçilir.
   İpucu: uygulamayı Finder/Gezgin'den sürükleyip doğrudan tuş kartının
   üstüne bırakmak da aynı işi görür.

•  Kısayol — Tuş kombinasyonu gönderir (örn. "ctrl+c", "command+space").
   Aktif profile göre otomatik çevrilir: Windows profilinde "command"
   yazsanız bile "ctrl" basılır, macOS profilinde tersi. Not: macOS'ta
   ilk kullanımda Sistem Ayarları → Erişilebilirlik izni istenir.

•  Metin — Yazıyı, O AN ODAKTA OLAN pencereye, imlecin durduğu yere
   yazar. Yani tuşa basmadan önce hangi metin kutusuna tıkladıysanız
   metin oraya girer (Word belgesi, tarayıcı arama çubuğu, sohbet
   kutusu...). Düz İngilizce karakterler tuş tuş yazılır; Türkçe
   karakter içeren metinler pano üzerinden yapıştırılır ve eski pano
   içeriğiniz yaklaşık yarım saniye sonra geri yüklenir. Metnin sonuna
   otomatik 1 boşluk eklenir — aynı tuşa art arda basınca kelimeler
   birbirine yapışmaz.

•  Komut — Terminal/komut satırı komutu çalıştırır (macOS'ta zsh,
   Windows'ta cmd). Örn: "open ~/Downloads" veya "notepad".

•  Dosya / Klasör — Seçilen dosyayı varsayılan uygulamasında,
   klasörü dosya yöneticisinde açar.

•  Medya — Ses/medya denetimi: ses aç/kıs, sessiz, çal/duraklat,
   sonraki/önceki parça. macOS'ta çal/duraklat ve parça geçişi GERÇEK
   sistem medya tuşu olarak basılır (klavyedeki F8 gibi) — o an medya
   çalan her uygulamayı kontrol eder; Erişilebilirlik izni gerektirir.

•  Makro — adımları sırayla oynatır: her satır bir kısayol ya da
   milisaniye cinsinden bekleme süresidir. Elle yazmak zorunda
   değilsiniz: "Tuş Yakala" düğmesi basılan kombinasyonu satır olarak
   ekler, "Bekleme Ekle" hazır 500 ms satırı koyar (süreyi düzenleyin).
   Örn: command+c → 500 → command+v  (kopyala, bekle, yapıştır)."""

TOPICS: dict[str, tuple[str, str]] = {
    "tuslar": (
        "Tuşlar Sekmesi",
        """Bu sayfa klavyenizin 10 işlev tuşunu ve 3 özel kartı gösterir.
Yerleşim, cihazın fiziksel düzeniyle birebir aynıdır: sayım SOL ALTTAN
başlar (sol alt = Tuş 1), en üst solda DEĞİŞİM ve KOMBO tuşları durur,
enkoder sağ üsttedir.

TUŞ KARTLARI (K1–K10)
•  Karta tıklayın → eylem düzenleyici açılır; tuşa ne yapacağını atarsınız.
•  SÜRÜKLE-BIRAK: Bir uygulamayı (Finder'dan .app, Windows'ta .exe/.lnk),
   bir dosyayı, klasörü veya tarayıcıdan bir adresi doğrudan kartın üstüne
   bırakın — uygun eylem otomatik atanır.
•  Cihazda tuşa bastığınızda buradaki kart kısa bir mavi parlamayla yanar;
   eylem, tuş BIRAKILDIĞINDA çalışır.
•  Kart üzerindeki renkli rozet eylemin tipini gösterir.

ÖZEL KARTLAR (atanamaz — cihazın kendi tuşlarıdır)
•  OS DEĞİŞTİR: Cihazdaki son tuş. Windows ⇄ macOS profili arasında geçiş
   yapar; Windows modunda LED1, macOS modunda LED2 yanar. Karta tıklamak
   da aynı geçişi yapar.
•  COMBO: Cihazdaki sondan ikinci tuş. Basınca combo modu açılır (LED3
   yanar); ardından bastığınız İKİ işlev tuşunun kombinasyonuna atanmış
   eylem çalışır. Ayrıntı için Combolar sekmesine bakın.
•  ENKODER: Döndürme ve basma davranışı Enkoder sekmesinden yönetilir.

""" + _EYLEM_TIPLERI,
    ),
    "combolar": (
        "Combolar Sekmesi",
        """Combo = iki işlev tuşunun birlikte kullanımı. 10 tuştan 2'li
seçimle toplam 45 kombinasyon vardır ve her birine ayrı eylem atanır.

NASIL KULLANILIR (cihazda)
1. KOMBO tuşuna bir kez basın → combo modu açılır, LED3 yanar.
   (Tuşu basılı tutmanıza gerek yok; mod kilitlenir.)
2. Sırayla iki işlev tuşuna basın (örn. Tuş 2 ve Tuş 5).
3. O çifte atanmış eylem çalışır, LED3 çift flaş yapar.
Sıra önemsizdir: 2+5 ile 5+2 aynı combodur. Combo modu açıkken tuşların
tekli eylemleri ÇALIŞMAZ. Mod KALICIDIR: combo tetiklendikten sonra da
açık kalır, art arda istediğiniz kadar combo yapabilirsiniz; kapatmak
için KOMBO tuşuna tekrar basın.

BU SAYFADA
•  Matristeki her hücre bir çifttir; tıklayıp eylem atarsınız.
•  Cihazda combo tetiklenince ilgili hücre kısa süre parlar.
•  Eylem tipleri Tuşlar sekmesindekiyle aynıdır (kartın "?" yardımına bakın).""",
    ),
    "enkoder": (
        "Enkoder Sekmesi",
        """Enkoder, klavyenin sağ üstündeki çevrilebilir/basılabilir düğmedir.
İki çalışma modu vardır:

•  HID modu (varsayılan): Ses denetimi CİHAZIN KENDİSİ tarafından yapılır —
   çevirince ses açılır/kısılır, basınca sessize alınır. Bu mod PC
   uygulaması kapalıyken bile çalışır.
   ⚠ ÖNEMLİ: Bu moddayken aşağıdaki dört slota atadığınız eylemler
   ÇALIŞMAZ. Kısa basış her zaman "sessize al" yapar, uzun basış ise
   hiçbir şey yapmaz (cihaz olayı bildirir ama uygulama HID modunda
   eylem çalıştırmaz). Kendi eylemlerinizi kullanmak için HOST'a geçin.

•  HOST modu: Ne olacağına bu uygulama karar verir. Dört slota ayrı eylem
   atarsınız:
     – Sağa çevirme (cw)
     – Sola çevirme (ccw)
     – Kısa basış (press)
     – Uzun basış (long, 800 ms ve üzeri basılı tutma)

Mod değişikliği bu sayfadan yapılır ve cihaza anında gönderilir.
Cihazda enkoder kullanıldığında ilgili slot kartı kısa süre parlar.
Eylem tipleri Tuşlar sekmesindekiyle aynıdır.""",
    ),
    "led_cihaz": (
        "LED & Cihaz Sekmesi",
        """Cihazın üç durum LED'ini ve bağlantı ayarlarını yönetir.

LED'LERİN ANLAMI (bu üründe 3 ayrı DÜZ/tek renk LED vardır)
•  LED1 — WINDOWS: Windows modundayken yanar.
•  LED2 — MACOS: macOS modundayken yanar.
   Aktif olan OS LED'i, PC uygulaması BAĞLIYKEN sabit yanar;
   uygulama yokken YAVAŞ YANIP SÖNER (bağlantı göstergesi budur;
   cihaz o sırada HID yedek modunda F13–F22/F23 gönderir).
•  LED3 — COMBO: combo modu açıkken yanar, combo tetiklenince çift
   flaş yapar; HID yedek modunda combo kullanılamazken hızlı yanıp
   söner. HID yedek modu açılıp kapanınca üç LED birlikte 3 kez
   yanıp söner.

BU SAYFADA
•  PARLAKLIK: standartta görünen tek LED ayarıdır ve düz LED'lerde de
   çalışır (çekirdeğin kendi donanımsal PWM'i ile; harici kütüphane yok).
   0 = sönük, 255 = tam; önerilen 60.
•  "Gelişmiş LED renk ayarları" başlığı varsayılan olarak KAPALIDIR;
   tıklayınca açılır. Renk seçimleri yalnızca adreslenebilir (WS2812B)
   LED takılı kartlarda fiziksel etki yapar — bu üründeki düz LED'lerin
   rengi kendi rengidir. Arayüz göstergeleri seçilen renkleri kullanır.
•  Seri port seçimi: "Otomatik" cihazı kendisi bulur. Gerekirse
   listeden belirli bir port seçin.
•  Cihaz kimliği (firmware sürümü, seri numara) burada görünür.""",
    ),
    "telefon": (
        "Telefon Sekmesi",
        """Telefonunuzu klavyenin CANLI GÖSTERGE PANELİ yapar: klavyede
basılan her tuş, telefonun ekranındaki kopyasında anında parlar; enkoder
yönü, combo modu, Windows/macOS modu ve bağlantı durumu da canlı izlenir.
Telefon yalnızca İZLER — telefondan komut gönderilmez.

KURULUM
1. Telefon ile bu bilgisayar AYNI Wi-Fi ağında olmalı.
2. "Telefon sunucusu açık" anahtarını açın.
3. Telefonun kamerasıyla QR kodu okutun veya adresi tarayıcıya yazın.

ANA EKRANA EKLEME (uygulama gibi görünür)
•  iPhone/iPad: Adresi SAFARİ'de açın → Paylaş düğmesi (kare+ok) →
   "Ana Ekrana Ekle". Tam ekran, uygulama görünümünde açılır.
•  Android: Adresi Chrome'da açın → sağ üst ⋮ menü → "Ana ekrana ekle".
   (Ayrı bir APK paketi ileride eklenecek; şimdilik bu yöntem kullanılır.)
•  Mac/PC tarayıcısından da aynı adres açılabilir.

SORUN GİDERME
•  Telefon bağlanamıyorsa: iki cihazın da aynı ağda olduğunu doğrulayın;
   Windows'ta Güvenlik Duvarı'nın Python/ExtraKeyboard'a özel ağlarda izin
   verdiğinden emin olun; macOS ilk açılışta "gelen bağlantı" izni sorar.
•  "Bağlı telefon" sayacı, o an sayfayı açık tutan cihaz sayısıdır.""",
    ),
    "ayarlar": (
        "Ayarlar Sekmesi",
        """Uygulamanın genel davranışı ve profil yönetimi.

GENEL
•  Tema — Arayüz rengi (koyu/açık/sistem).
•  Bilgisayar açılışında çalıştır — Uygulama oturum açılınca kendiliğinden
   başlar.
•  Pencere kapatılınca tepsiye küçült — Kapat düğmesi uygulamayı
   sonlandırmaz, sistem tepsisine/menü çubuğuna indirir.
•  Gizli başlat — Açılışta pencere gösterilmez, yalnızca tepside durur.

PROFİL YÖNETİMİ
Profil = tüm tuş/combo/enkoder atamalarının tam bir kopyası (hem Windows
hem macOS bölümleriyle). Örn. "Oyun", "Tasarım", "Ofis" profilleri
oluşturup aralarında geçiş yapabilirsiniz.
•  Ekle / Kopyala / Sil — Profil oluşturur, çoğaltır, kaldırır.
•  Dışa Aktar / İçe Aktar — Profili dosya olarak yedekleyin veya başka
   bilgisayara taşıyın (Mac ⇄ Windows arası taşınabilir; kısayollar
   profil bölümlerine göre otomatik uyarlanır).
•  v2 Yapılandırmasını İçe Aktar — Eski sürüm (F13–F20 tabanlı) ayar
   dosyasını yeni düzene çevirir.

Alttaki "Dosya:" satırı, ayarların diskte tutulduğu config.json yolunu
gösterir.""",
    ),
    "eylem_editoru": (
        "Eylem Düzenleyici",
        """Bir slota (tuş, combo, enkoder yönü) ne yapacağını atadığınız
penceredir.

ALANLAR
•  Tip — Eylemin türü (aşağıda tek tek açıklanmıştır).
•  Değer — Tipin ayrıntısı: adres, dosya yolu, kısayol, metin, komut…
•  Gözat — Uygulama/dosya/klasör tiplerinde dosya seçici açar.
•  Ad — Kart üzerinde görünen kısa etiket; boş bırakılırsa kendiliğinden
   üretilir.

Kaydet ile atama aktif profile yazılır; pencereyi kapatırsanız hiçbir şey
değişmez. Aynı slot için pencere zaten açıksa ikinci bir kopya açılmaz.

""" + _EYLEM_TIPLERI,
    ),
}

# ---------------------------------------------------------------------------
#  Pencere ve düğme
# ---------------------------------------------------------------------------

#: Açık olan tek yardım penceresi (tekillik koruması).
_ACTIVE: ctk.CTkToplevel | None = None


def open_help(master, topic: str) -> None:
    """Konu penceresini açar; zaten açıksa aynı pencereyi öne getirir.

    Args:
        master: Üst pencere (herhangi bir widget olabilir; kökü kullanılır).
        topic: :data:`TOPICS` içindeki konu anahtarı.
    """
    global _ACTIVE

    title, body = TOPICS.get(topic, ("Yardım", "Bu sayfa için açıklama bulunamadı."))

    mevcut = _ACTIVE
    if mevcut is not None:
        try:
            if int(mevcut.winfo_exists()):
                # Aynı pencereyi yeni konuyla güncelle ve öne getir.
                mevcut.title(f"Yardım — {title}")
                mevcut._help_title.configure(text=title)          # type: ignore[attr-defined]
                box = mevcut._help_box                            # type: ignore[attr-defined]
                box.configure(state="normal")
                box.delete("1.0", "end")
                box.insert("1.0", body)
                box.configure(state="disabled")
                mevcut.lift()
                mevcut.focus_force()
                return
        except Exception:
            pass
        _ACTIVE = None

    # Ana pencere "arka planda başlat" ayarıyla gizliyse alt pencereler
    # macOS'ta içerikleri çizilmeden boş açılır; önce görünür kılınır.
    try:
        _gorunur = getattr(master.winfo_toplevel(), "ensure_visible", None)
        if callable(_gorunur):
            _gorunur()
    except Exception:
        pass

    win = ctk.CTkToplevel(master)
    win.title(f"Yardım — {title}")
    win.geometry("620x640")
    win.minsize(480, 420)
    win.configure(fg_color=theme.COLOR_BG)
    try:
        win.transient(master.winfo_toplevel())
    except Exception:
        pass

    # Eylem düzenleyici gibi modal kilit (grab_set) tutan bir pencereden
    # açıldıysa kilit DEVRALINMALI; yoksa bu pencere tık/klavye alamaz.
    # Normal sekmelerden açılınca kilit yoktur ve alınmaz (ana pencere
    # kullanılabilir kalır).
    try:
        onceki_grab = win.grab_current()
    except Exception:
        onceki_grab = None

    def _kapat() -> None:
        try:
            win.grab_release()
        except Exception:
            pass
        if onceki_grab is not None:
            try:
                if int(onceki_grab.winfo_exists()):
                    onceki_grab.after(60, onceki_grab.grab_set)
            except Exception:
                pass
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _kapat)

    baslik = ctk.CTkLabel(win, text=title, font=theme.font(18, True),
                          text_color=theme.COLOR_TEXT, anchor="w")
    baslik.pack(fill="x", padx=theme.PAD_L, pady=(theme.PAD_L, theme.PAD_S))

    box = ctk.CTkTextbox(win, fg_color=theme.COLOR_PANEL,
                         text_color=theme.COLOR_TEXT, font=theme.font(13),
                         corner_radius=theme.RADIUS_CARD, wrap="word")
    box.pack(fill="both", expand=True, padx=theme.PAD_L, pady=(0, theme.PAD_S))
    box.insert("1.0", body)
    box.configure(state="disabled")

    ctk.CTkButton(win, text="Kapat", height=34, width=120,
                  corner_radius=theme.RADIUS_SMALL, fg_color=theme.COLOR_HOVER, text_color=theme.COLOR_TEXT,
                  hover_color=theme.COLOR_ACCENT, font=theme.font(12, True),
                  command=_kapat).pack(pady=(0, theme.PAD_L))

    # open_help ikinci kez çağrıldığında içerik güncellemesi için saklanır.
    win._help_title = baslik   # type: ignore[attr-defined]
    win._help_box = box        # type: ignore[attr-defined]

    # macOS'ta Toplevel'in arkada kalmaması için odak gecikmeli verilir
    # (action_editor ile aynı desen); modal bağlamda kilit de devralınır.
    def _odakla() -> None:
        try:
            win.lift()
            win.focus_force()
            if onceki_grab is not None:
                win.grab_set()
        except Exception:
            pass
    win.after(140, _odakla)

    _ACTIVE = win


def help_button(master, topic: str, size: int = 26) -> ctk.CTkButton:
    """Yerleşimi çağırana bırakılmış küçük yuvarlak "?" düğmesi üretir.

    Args:
        master: Düğmenin ekleneceği üst bileşen.
        topic: Tıklanınca açılacak konu anahtarı.
        size: Kenar uzunluğu (piksel).

    Returns:
        Paketlenmeye/yerleştirilmeye hazır ``CTkButton``.
    """
    return ctk.CTkButton(
        master, text="?", width=size, height=size,
        corner_radius=size // 2, font=theme.font(13, True),
        fg_color=theme.COLOR_HOVER, hover_color=theme.COLOR_ACCENT,
        text_color=theme.COLOR_TEXT,
        command=lambda: open_help(master, topic))


def attach_help(tab_frame, topic: str) -> None:
    """Bir sekme çerçevesinin sağ üst köşesine "?" düğmesi yerleştirir.

    ``place`` kullanıldığı için sekmenin kendi ``pack``/``grid`` düzenine
    karışmaz; düğme içerik üzerinde yüzer.

    Args:
        tab_frame: ``tabview.tab("...")`` çerçevesi.
        topic: :data:`TOPICS` içindeki konu anahtarı.
    """
    try:
        btn = help_button(tab_frame, topic)
        btn.place(relx=1.0, y=4, x=-4, anchor="ne")
        try:
            btn.lift()
        except Exception:
            pass
    except Exception:
        # Yardım düğmesi hiçbir koşulda uygulamayı düşürmemeli.
        pass
