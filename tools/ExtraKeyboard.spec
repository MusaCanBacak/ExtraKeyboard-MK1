# -*- mode: python ; coding: utf-8 -*-
"""
ExtraKeyboard MK1 — PyInstaller paket tanımı (macOS .app).

AMAÇ: Kullanıcının bilgisayarına Python KURMADAN çalışan bir uygulama üretmek.
Paket kendi Python yorumlayıcısını ve Tcl/Tk 8.6'sını içinde taşır; böylece
macOS'un kendi Python 3.9'unun eski Tk 8.5.9'u devreye girmez (o sürümde
CustomTkinter widget'ları hiç çizilmez, pencere bomboş görünür).

Derleme:
    .venv/bin/pyinstaller --clean --noconfirm tools/ExtraKeyboard.spec

Çıktı: dist/ExtraKeyboard.app  (universal2 — Intel ve Apple Silicon)
"""

import os

PROJE = os.path.abspath(os.path.join(os.path.dirname(SPEC), os.pardir))

# Uygulamanın çalışma zamanında okuduğu veri dosyaları.
# varliklar/ : tepsi ve uygulama simgesi
veriler = [
    (os.path.join(PROJE, "varliklar"), "varliklar"),
]

# PyInstaller'ın statik çözümleyemediği içe aktarmalar.
# pystray ve pyautogui platform arka uçlarını çalışma zamanında seçer.
gizli = [
    "pystray._darwin",
    "PIL._tkinter_finder",
    "serial.tools.list_ports",
    "qrcode.image.pil",
    "pyperclip",
]

a = Analysis(
    [os.path.join(PROJE, "run_app.py")],
    pathex=[PROJE],
    binaries=[],
    datas=veriler,
    hiddenimports=gizli,
    hookspath=[],
    runtime_hooks=[],
    # Paketi şişiren, uygulamanın kullanmadığı ağır bağımlılıklar.
    excludes=["matplotlib", "numpy", "pandas", "scipy", "pytest", "setuptools"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ExtraKeyboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # Terminal penceresi açılmaz
    target_arch="universal2",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ExtraKeyboard",
)

app = BUNDLE(
    coll,
    name="ExtraKeyboard.app",
    # Uygulama simgesi. Dosya adi "simge.icns"tir; yanlis ad verilirse
    # PyInstaller sessizce KENDI varsayilan simgesini koyar ve uygulama
    # Finder'da/Dock'ta bos gorunur.
    icon=os.path.join(PROJE, "varliklar", "simge.icns"),
    bundle_identifier="com.bluedevelopment.extrakeyboard",
    info_plist={
        "CFBundleName": "ExtraKeyboard",
        "CFBundleDisplayName": "ExtraKeyboard MK1",
        "CFBundleShortVersionString": "3.0.0",
        "CFBundleVersion": "3.0.0",
        "NSHumanReadableCopyright": "BlueDevelopment",
        # Retina ekranlarda bulanık çizim olmaması için.
        "NSHighResolutionCapable": True,
        # Tuş eylemleri (metin yazma / kısayol) Erişilebilirlik izni ister;
        # macOS izin penceresinde bu açıklama gösterilir.
        "NSAppleEventsUsageDescription":
            "ExtraKeyboard, atadığınız tuş eylemlerini (uygulama açma, "
            "kısayol gönderme) gerçekleştirmek için diğer uygulamaları "
            "yönlendirir.",
        "LSMinimumSystemVersion": "10.15",
    },
)
