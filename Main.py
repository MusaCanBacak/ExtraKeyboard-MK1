import sys
import time
import platform
import os
import subprocess
import webbrowser
import threading
import json
import traceback
import socket

import customtkinter as ctk
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import pyautogui
from tkinter import filedialog

# --- VERSİYON BİLGİSİ ---
APP_VERSION = "v2.0"

# --- SYSTEM TRAY ---
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pass

# --- WINDOWS REGISTRY (Sadece Windows için) ---
if platform.system() == "Windows":
    import winreg

# --- YAPILANDIRMA ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "macro_config.json"
IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
INITIAL_OS = None

# --- COMBINE MOD TANIMLARI ---
COMBINE_SIGNAL_CHARS = list("0123456789abcdefghijklopqrst")

COMBINE_PAIRS = []
for _i in range(8):
    for _j in range(_i + 1, 8):
        COMBINE_PAIRS.append((_i, _j))

SIGNAL_TO_COMBO = {}
for _idx, _pair in enumerate(COMBINE_PAIRS):
    SIGNAL_TO_COMBO[COMBINE_SIGNAL_CHARS[_idx]] = _pair


def combo_config_key(btn1, btn2):
    return f"C_{btn1 + 1}_{btn2 + 1}"


DEFAULT_COMBINE_CONFIG = {}
for _pair in COMBINE_PAIRS:
    _key = combo_config_key(_pair[0], _pair[1])
    DEFAULT_COMBINE_CONFIG[_key] = {
        "type": "none",
        "value": "",
        "name": f"Buton {_pair[0] + 1}+{_pair[1] + 1}"
    }

# Tip renkleri
TYPE_COLORS = {
    "url": "#3B8ED0",
    "app": "#2CC985",
    "shortcut": "#FF9500",
    "none": "#555555"
}

# --- PORT AYARI (Tek Uygulama İçin) ---
SINGLE_INSTANCE_PORT = 64209
instance_socket = None

DEFAULT_CONFIG = {
    "F13": {"type": "url", "value": "https://www.youtube.com", "name": "Buton 1"},
    "F14": {"type": "app", "value": "Spotify", "name": "Buton 2"},
    "F15": {"type": "shortcut", "value": "ctrl+c", "name": "Buton 3"},
    "F16": {"type": "shortcut", "value": "ctrl+v", "name": "Buton 4"},
    "F17": {"type": "none", "value": "", "name": "Buton 5"},
    "F18": {"type": "none", "value": "", "name": "Buton 6"},
    "F19": {"type": "none", "value": "", "name": "Buton 7"},
    "F20": {"type": "none", "value": "", "name": "Buton 8"}
}


def create_tray_icon():
    width = 64
    height = 64
    color_blue = "#3B8ED0"
    color_black = "#101010"
    image = Image.new('RGB', (width, height), color_black)
    dc = ImageDraw.Draw(image)
    dc.polygon([(0, 0), (width, 0), (0, height)], fill=color_blue)
    return image


# --- TEK UYGULAMA KONTROLÜ ---
def check_single_instance():
    global instance_socket
    instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        instance_socket.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        return True
    except socket.error:
        return False


class MacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_os = INITIAL_OS
        self.tray_icon = None
        self.is_combine_mode = False
        self.combine_widgets = {}
        self._combine_flash_id = None

        # Versiyon numarasını başlığa ekledik
        self.title(f"ESP32 Makro Klavye {APP_VERSION} - Mod: SEÇİLMEDİ")
        self.geometry("950x700")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<FocusIn>", self.on_focus_in)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.config_data = self.load_config()
        self.ui_cards = {}

        try:
            self.create_sidebar()
            self.create_main_area()
        except Exception as e:
            print(f"Arayüz Hatası: {e}")

        try:
            self.listener_thread = threading.Thread(target=self.start_listener, daemon=True)
            self.listener_thread.start()
        except:
            pass

        if IS_WINDOWS:
            self.setup_system_tray()

    # --- PENCERE YÖNETİMİ ---
    def on_closing(self):
        if IS_MAC:
            self.iconify()
        else:
            self.withdraw()

    def show_window(self):
        self.after(0, self.deiconify)
        self.after(0, self.lift)
        self.after(100, self._update_ui_for_mode)

    def on_focus_in(self, event):
        self._update_ui_for_mode()

    def quit_app(self):
        if self.tray_icon: self.tray_icon.stop()
        self.quit()
        sys.exit()

    def setup_system_tray(self):
        def tray_thread_func():
            try:
                image = create_tray_icon()
                menu = (
                    pystray.MenuItem('Ayarları Göster', lambda icon, item: self.show_window()),
                    pystray.MenuItem('Çıkış', lambda icon, item: self.quit_app())
                )
                self.tray_icon = pystray.Icon("EspMacro", image, "Makro Klavye", menu)
                self.tray_icon.run()
            except:
                pass

        t = threading.Thread(target=tray_thread_func, daemon=True)
        t.start()

    # --- ARAYÜZ ---
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#1a1a2e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Logo alanı
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="#16213e", corner_radius=12, height=80)
        logo_frame.pack(fill="x", padx=12, pady=(15, 5))
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="MAKRO", font=("Arial", 22, "bold"),
                     text_color="#3B8ED0").pack(pady=(10, 0))
        ctk.CTkLabel(logo_frame, text="KLAVYE", font=("Arial", 14),
                     text_color="#7f8c8d").pack()

        # Mod göstergesi
        self.mode_frame = ctk.CTkFrame(self.sidebar, fg_color="#16213e", corner_radius=10)
        self.mode_frame.pack(fill="x", padx=12, pady=8)
        mode_inner = ctk.CTkFrame(self.mode_frame, fg_color="transparent")
        mode_inner.pack(pady=10, padx=10)
        self.mode_dot = ctk.CTkLabel(mode_inner, text="\u25CF", font=("Arial", 18), text_color="gray", width=25)
        self.mode_dot.pack(side="left")
        self.version_lbl = ctk.CTkLabel(mode_inner, text="Mod: Bekleniyor...",
                                        font=("Arial", 13, "bold"), text_color="gray")
        self.version_lbl.pack(side="left", padx=5)

        # Bilgi kutusu
        ctk.CTkLabel(self.sidebar, text="Bilgi", font=("Arial", 14, "bold"),
                     text_color="#bdc3c7").pack(pady=(8, 2), padx=15, anchor="w")
        self.info_box = ctk.CTkTextbox(self.sidebar, font=("Arial", 12), text_color="#DCE4EE",
                                       fg_color="#16213e", corner_radius=10)
        self.info_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.update_sidebar_text()

        # Başlangıçta çalıştır switch'i
        self.startup_var = ctk.BooleanVar(value=self.check_startup_status())
        self.switch_startup = ctk.CTkSwitch(
            self.sidebar,
            text="Başlangıçta Çalıştır",
            variable=self.startup_var,
            command=self.toggle_startup,
            font=("Arial", 12, "bold"),
            progress_color="#2CC985"
        )
        self.switch_startup.pack(side="bottom", pady=(0, 15), padx=15)

        # Versiyon
        ctk.CTkLabel(self.sidebar, text=APP_VERSION, font=("Arial", 10),
                     text_color="#555").pack(side="bottom", pady=(0, 5))

    def update_sidebar_text(self):
        # 1. Metni Hazırla
        if self.current_os is None:
            # Mod Seçilmediyse
            info_text = "⚠️ MOD SEÇİLMEDİ\n\n" \
                        "Lütfen cihaz üzerindeki\n" \
                        "butona basarak işletim\n" \
                        "sistemini seçiniz.\n\n" \
                        "Işık yanınca panel\n" \
                        "aktif olacaktır."
        else:
            # Mod Seçildiyse
            if self.current_os == "Windows":
                os_name = "WINDOWS"
                cmd_key = "Ctrl"
                file_hint = "• .exe Dosyası\n• .lnk (Kısayol)"
            else:
                os_name = "MAC OS"
                cmd_key = "Command (⌘)"
                file_hint = "• .app Uygulaması"

            info_text = f"Mevcut Mod: {os_name}\n\n" \
                        f"⌨️ KISAYOLLAR\n" \
                        f"Tuşları '+' ile yazın.\n\n" \
                        f"Örnekler:\n" \
                        f"• {cmd_key}+c  (Kopyala)\n" \
                        f"• {cmd_key}+v  (Yapıştır)\n" \
                        f"• {cmd_key}+z  (Geri Al)\n\n" \
                        f"📂 UYGULAMA SEÇİMİ\n" \
                        f"'Seç' butonu şunları\nfiltreler:\n" \
                        f"{file_hint}"

        # 2. Metni Kutuya Yaz
        try:
            self.info_box.configure(state="normal")
            self.info_box.delete("0.0", "end")
            self.info_box.insert("0.0", info_text)
            self.info_box.configure(state="disabled")
        except:
            pass

    # --- OTOMATİK BAŞLATMA MANTIĞI ---
    def check_startup_status(self):
        app_name = "ESPMacroKeyboard"
        if IS_WINDOWS:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                     winreg.KEY_READ)
                winreg.QueryValueEx(key, app_name)
                key.Close()
                return True
            except WindowsError:
                return False
        elif IS_MAC:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{app_name.lower()}.plist")
            return os.path.exists(plist_path)
        return False

    def toggle_startup(self):
        state = self.startup_var.get()
        app_name = "ESPMacroKeyboard"

        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

        if IS_WINDOWS:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                if state:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except:
                        pass
                key.Close()
            except:
                pass

        elif IS_MAC:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{app_name.lower()}.plist")
            if state:
                python_exe = sys.executable
                script_file = os.path.abspath(__file__)
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_file}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
                try:
                    with open(plist_path, "w") as f:
                        f.write(plist_content)
                except:
                    pass
            else:
                if os.path.exists(plist_path): os.remove(plist_path)

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)

        # Üst başlık çubuğu
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text="Tuş Atama Paneli",
                     font=("Arial", 22, "bold")).pack(side="left")

        self.status_label = ctk.CTkLabel(header_frame, text="Lütfen Cihazdan Mod Seçin",
                                         font=("Arial", 12, "bold"), text_color="#E04F5F")
        self.status_label.pack(side="right", padx=10)

        # Combine durum çubuğu (başlangıçta gizli)
        self.combine_bar = ctk.CTkFrame(self.main_frame, height=35, fg_color="#FF9500",
                                        corner_radius=8)
        self.combine_bar_label = ctk.CTkLabel(self.combine_bar, text="COMBINE MOD: AKTİF",
                                              font=("Arial", 13, "bold"), text_color="white")
        self.combine_bar_label.pack(pady=5)

        # Sekmeler
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10,
                                      segmented_button_fg_color="#1a1a2e",
                                      segmented_button_selected_color="#3B8ED0")
        self.tabview.pack(fill="both", expand=True, pady=5)

        self.tabview.add("Butonlar")
        self.tabview.add("Combine Ayarları")

        self.create_buttons_tab(self.tabview.tab("Butonlar"))
        self.create_combine_tab(self.tabview.tab("Combine Ayarları"))

        # Kaydet butonu
        ctk.CTkButton(self.main_frame, text="AYARLARI KAYDET", command=self.save_settings,
                      height=45, fg_color="#2CC985", hover_color="#25a873",
                      text_color="black", font=("Arial", 14, "bold"),
                      corner_radius=10).pack(fill="x", pady=(5, 0))

    def create_buttons_tab(self, parent):
        self.scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, pady=5)

        self.widgets = {}
        key_list = [f"F{i}" for i in range(13, 21)]

        for idx, key in enumerate(key_list):
            if key not in self.config_data:
                self.config_data[key] = DEFAULT_CONFIG.get(key, {"type": "none", "value": "", "name": key})

            data = self.config_data[key]
            btn_type = data["type"]
            border_color = TYPE_COLORS.get(btn_type, "#555555")

            # Ana kart
            card_outer = ctk.CTkFrame(self.scroll_frame, corner_radius=12,
                                      border_width=2, border_color=border_color,
                                      fg_color="#1e1e2e")
            card_outer.pack(fill="x", pady=4, padx=5)
            self.ui_cards[key] = card_outer

            card = ctk.CTkFrame(card_outer, fg_color="transparent")
            card.pack(fill="x", padx=12, pady=10)

            # Üst satır: numara dairesi + isim + tip seçici
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x")

            # Numara dairesi
            num_circle = ctk.CTkFrame(top_row, width=36, height=36,
                                      corner_radius=18, fg_color=border_color)
            num_circle.pack(side="left")
            num_circle.pack_propagate(False)
            ctk.CTkLabel(num_circle, text=str(idx + 1), font=("Arial", 14, "bold"),
                         text_color="white").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(top_row, text=data["name"], font=("Arial", 14, "bold")
                         ).pack(side="left", padx=10)

            # Tip seçici — SegmentedButton
            seg_btn = ctk.CTkSegmentedButton(
                top_row, values=["url", "app", "shortcut", "none"],
                command=lambda c, k=key: self.on_type_change(k, c),
                font=("Arial", 11), selected_color="#3B8ED0",
                selected_hover_color="#2d7ab5",
                unselected_color="#2b2b3d", unselected_hover_color="#3a3a4d"
            )
            seg_btn.set(btn_type)
            seg_btn.pack(side="right")

            # Alt satır: değer girişi + seç butonu
            bottom_row = ctk.CTkFrame(card, fg_color="transparent")
            bottom_row.pack(fill="x", pady=(8, 0))

            entry = ctk.CTkEntry(bottom_row, placeholder_text="Değer girin...",
                                 corner_radius=8, height=35, fg_color="#2b2b3d",
                                 border_color="#3a3a4d")
            entry.insert(0, data["value"])
            entry.pack(side="left", fill="x", expand=True)

            btn_browse = ctk.CTkButton(bottom_row, text="Seç", width=50,
                                       fg_color="#3a3a4d", hover_color="#4a4a5d",
                                       corner_radius=8, height=35,
                                       command=lambda k=key: self.browse_file(k))

            if btn_type == "app":
                btn_browse.pack(side="left", padx=(8, 0))
            else:
                btn_browse.pack_forget()

            # Durum metni
            status_text = "Aktif" if btn_type != "none" and data["value"] else "Yapılandırılmadı"
            status_color = "#2CC985" if status_text == "Aktif" else "#555"
            status_lbl = ctk.CTkLabel(card, text=f"\u25CF {status_text}",
                                      font=("Arial", 10), text_color=status_color)
            status_lbl.pack(anchor="w", pady=(5, 0))

            self.widgets[key] = {
                "type": seg_btn, "value": entry, "browse": btn_browse,
                "card_outer": card_outer, "num_circle": num_circle,
                "status_lbl": status_lbl
            }

    def create_combine_tab(self, parent):
        # Açıklama
        ctk.CTkLabel(parent, text="Kombinasyonu düzenlemek için hücreye tıklayın",
                     font=("Arial", 12), text_color="#7f8c8d").pack(pady=(5, 10))

        # Grid container
        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(expand=True)

        # Başlık satırı
        ctk.CTkLabel(grid_frame, text="", width=60).grid(row=0, column=0, padx=2, pady=2)
        for j in range(8):
            ctk.CTkLabel(grid_frame, text=f"B{j + 1}", width=60,
                         font=("Arial", 11, "bold"), text_color="#bdc3c7"
                         ).grid(row=0, column=j + 1, padx=2, pady=2)

        # Başlık sütunu + hücreler
        self.grid_buttons = {}
        for i in range(8):
            ctk.CTkLabel(grid_frame, text=f"B{i + 1}", width=60,
                         font=("Arial", 11, "bold"), text_color="#bdc3c7"
                         ).grid(row=i + 1, column=0, padx=2, pady=2)
            for j in range(8):
                if i == j:
                    # Köşegen — devre dışı
                    lbl = ctk.CTkLabel(grid_frame, text="—", width=60, height=50,
                                       fg_color="#1a1a1a", corner_radius=8,
                                       font=("Arial", 12), text_color="#333")
                    lbl.grid(row=i + 1, column=j + 1, padx=2, pady=2)
                elif i < j:
                    # Üst üçgen — aktif hücre
                    c_key = combo_config_key(i, j)
                    combine_data = self.config_data.get("combine", {})
                    c_data = combine_data.get(c_key, {"type": "none", "value": "", "name": f"Buton {i+1}+{j+1}"})
                    c_type = c_data["type"]
                    cell_color = TYPE_COLORS.get(c_type, "#555555")

                    btn = ctk.CTkButton(
                        grid_frame, text=f"{i+1}+{j+1}", width=60, height=50,
                        fg_color=cell_color if c_type != "none" else "#2b2b3d",
                        hover_color="#4a4a5d", corner_radius=8,
                        font=("Arial", 11, "bold"),
                        text_color="white" if c_type != "none" else "#666",
                        command=lambda k=c_key: self.open_combine_dialog(k)
                    )
                    btn.grid(row=i + 1, column=j + 1, padx=2, pady=2)
                    self.grid_buttons[c_key] = btn
                    self.ui_cards[c_key] = btn
                else:
                    # Alt üçgen — boş
                    lbl = ctk.CTkLabel(grid_frame, text="", width=60, height=50,
                                       fg_color="transparent")
                    lbl.grid(row=i + 1, column=j + 1, padx=2, pady=2)

        # Seçili hücre bilgi paneli
        self.combine_info_frame = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=10)
        self.combine_info_frame.pack(fill="x", pady=(15, 5), padx=10)
        ctk.CTkLabel(self.combine_info_frame, text="Bir kombinasyon seçin",
                     font=("Arial", 12), text_color="#7f8c8d").pack(pady=15)

    def open_combine_dialog(self, combo_key):
        combine_data = self.config_data.get("combine", {})
        data = combine_data.get(combo_key, {"type": "none", "value": "", "name": combo_key})

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Düzenle: {data['name']}")
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # İçerik
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(content, text=data["name"], font=("Arial", 18, "bold")).pack(pady=(0, 15))

        # Tip seçici
        ctk.CTkLabel(content, text="Tip:", font=("Arial", 12, "bold"),
                     text_color="#bdc3c7").pack(anchor="w")
        type_var = ctk.StringVar(value=data["type"])
        seg = ctk.CTkSegmentedButton(content, values=["url", "app", "shortcut", "none"],
                                     variable=type_var, font=("Arial", 11),
                                     selected_color="#3B8ED0")
        seg.pack(fill="x", pady=(2, 10))

        # Değer girişi
        ctk.CTkLabel(content, text="Değer:", font=("Arial", 12, "bold"),
                     text_color="#bdc3c7").pack(anchor="w")
        val_frame = ctk.CTkFrame(content, fg_color="transparent")
        val_frame.pack(fill="x", pady=(2, 15))
        val_entry = ctk.CTkEntry(val_frame, placeholder_text="Değer girin...",
                                 corner_radius=8, height=35)
        val_entry.insert(0, data["value"])
        val_entry.pack(side="left", fill="x", expand=True)

        browse_btn = ctk.CTkButton(val_frame, text="Seç", width=50, fg_color="#3a3a4d",
                                   corner_radius=8, height=35,
                                   command=lambda: self._dialog_browse(val_entry))
        if data["type"] == "app":
            browse_btn.pack(side="left", padx=(8, 0))

        def on_type_change(val):
            if val == "app":
                browse_btn.pack(side="left", padx=(8, 0))
            else:
                browse_btn.pack_forget()

        seg.configure(command=on_type_change)

        # Butonlar
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")

        def save_and_close():
            if "combine" not in self.config_data:
                self.config_data["combine"] = {}
            self.config_data["combine"][combo_key] = {
                "type": type_var.get(),
                "value": val_entry.get(),
                "name": data["name"]
            }
            self.update_grid_cell(combo_key)
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Kaydet", fg_color="#2CC985", text_color="black",
                      hover_color="#25a873", corner_radius=8, height=38,
                      command=save_and_close).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="İptal", fg_color="#555", hover_color="#666",
                      corner_radius=8, height=38,
                      command=dialog.destroy).pack(side="left", expand=True, padx=(5, 0))

    def _dialog_browse(self, entry_widget):
        if self.current_os is None: return
        if self.current_os == "Mac":
            init_dir = "/Applications"
            f_types = [("Applications", "*.app"), ("All Files", "*.*")]
        else:
            init_dir = os.path.join(os.getenv('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
            if not os.path.exists(init_dir): init_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            f_types = [("Kısayollar ve Uygulamalar", "*.lnk;*.exe"), ("Tüm Dosyalar", "*.*")]

        filename = filedialog.askopenfilename(initialdir=init_dir, filetypes=f_types)
        if filename:
            if self.current_os == "Windows": filename = os.path.normpath(filename)
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filename)

    def update_grid_cell(self, combo_key):
        if combo_key not in self.grid_buttons: return
        btn = self.grid_buttons[combo_key]
        combine_data = self.config_data.get("combine", {})
        data = combine_data.get(combo_key, {"type": "none"})
        c_type = data["type"]
        cell_color = TYPE_COLORS.get(c_type, "#555555")

        if c_type != "none":
            btn.configure(fg_color=cell_color, text_color="white")
        else:
            btn.configure(fg_color="#2b2b3d", text_color="#666")

    def on_type_change(self, key, choice):
        if key not in self.widgets: return
        w = self.widgets[key]
        if choice == "app":
            w["browse"].pack(side="left", padx=(8, 0))
            w["value"].configure(placeholder_text="Uygulama yolu...")
        elif choice == "shortcut":
            w["browse"].pack_forget()
            if self.current_os is None:
                ph = "Önce Mod Seçin!"
            else:
                ph = "Örn: command+c" if self.current_os == "Mac" else "Örn: ctrl+c"
            w["value"].configure(placeholder_text=ph)
        elif choice == "url":
            w["browse"].pack_forget()
            w["value"].configure(placeholder_text="Örn: youtube.com")
        else:
            w["browse"].pack_forget()
            w["value"].configure(placeholder_text="")

        # Kart kenar rengini güncelle
        border_color = TYPE_COLORS.get(choice, "#555555")
        w["card_outer"].configure(border_color=border_color)
        w["num_circle"].configure(fg_color=border_color)

        # Durum metnini güncelle
        has_value = bool(w["value"].get())
        if choice != "none" and has_value:
            w["status_lbl"].configure(text="\u25CF Aktif", text_color="#2CC985")
        else:
            w["status_lbl"].configure(text="\u25CF Yapılandırılmadı", text_color="#555")

    def browse_file(self, key):
        if self.current_os is None:
            self.status_label.configure(text="Önce Mod Seçin!", text_color="#E04F5F")
            self.after(3000,
                       lambda: self.status_label.configure(text="Lütfen Cihazdan Mod Seçin", text_color="#E04F5F"))
            return

        # Doğru widget sözlüğünü bul
        if key in self.widgets:
            target_widgets = self.widgets
        elif key in self.combine_widgets:
            target_widgets = self.combine_widgets
        else:
            return

        if self.current_os == "Mac":
            init_dir = "/Applications"
            f_types = [("Applications", "*.app"), ("All Files", "*.*")]
        else:
            init_dir = os.path.join(os.getenv('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
            if not os.path.exists(init_dir): init_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            f_types = [("Kısayollar ve Uygulamalar", "*.lnk;*.exe"), ("Tüm Dosyalar", "*.*")]

        filename = filedialog.askopenfilename(initialdir=init_dir, title=f"Uygulama Seç ({self.current_os})",
                                              filetypes=f_types)
        if filename:
            if self.current_os == "Windows": filename = os.path.normpath(filename)
            target_widgets[key]["value"].delete(0, "end")
            target_widgets[key]["value"].insert(0, filename)

    def set_mode(self, new_mode):
        if self.current_os == new_mode: return
        self.current_os = new_mode
        self.after(0, self._update_ui_for_mode)

    def _update_ui_for_mode(self):
        try:
            if self.current_os is None:
                self.title(f"ESP32 Makro Klavye {APP_VERSION} - Mod: SEÇİLMEDİ")
                self.version_lbl.configure(text="Mod: SEÇİLMEDİ")
                self.mode_dot.configure(text_color="gray")
                self.status_label.configure(text="Cihaz Bekleniyor...", text_color="#E04F5F")
                self.update_sidebar_text()
                return

            self.title(f"ESP32 Makro Klavye {APP_VERSION} - Mod: {self.current_os}")
            self.update_sidebar_text()
            self.version_lbl.configure(text=f"Mod: {self.current_os}")

            # Mod dairesi rengi
            dot_color = "#3B8ED0" if self.current_os == "Windows" else "#E04F5F"
            self.mode_dot.configure(text_color=dot_color)

            color = "#3B8ED0" if self.current_os == "Windows" else "#E04F5F"
            self.status_label.configure(text=f"MOD ETKİNLEŞTİ: {self.current_os.upper()}", text_color=color)
            self.after(3000, lambda: self.status_label.configure(text="", text_color="#2CC985"))

            for key, w in self.widgets.items():
                if w["type"].get() == "shortcut":
                    ph = "Örn: command+c" if self.current_os == "Mac" else "Örn: ctrl+c"
                    w["value"].configure(placeholder_text=ph)
        except:
            pass

    def save_settings(self):
        if self.current_os is None:
            self.status_label.configure(text="KAYDEDİLEMEDİ: Mod Seçin!", text_color="#E04F5F")
            return
        try:
            # Normal butonları kaydet
            for key, w in self.widgets.items():
                self.config_data[key]["type"] = w["type"].get()
                self.config_data[key]["value"] = w["value"].get()

            # Combine ayarları zaten dialog'dan kaydediliyor,
            # sadece dosyaya yaz
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=4)
            self.status_label.configure(text="Ayarlar Başarıyla Kaydedildi!", text_color="#2CC985")
            self.after(3000, lambda: self.status_label.configure(text=""))
        except Exception as e:
            print(f"Kayıt Hatası: {e}")

    def flash_ui_row(self, key):
        """Tuşa basıldığında arayüzdeki ilgili satırı/hücreyi parlatır"""
        if key in self.ui_cards:
            card = self.ui_cards[key]
            flash_color = "#2b4b3c"
            try:
                original_color = card.cget("fg_color")
                card.configure(fg_color=flash_color)
                self.after(250, lambda c=card, o=original_color: c.configure(fg_color=o))
            except:
                pass

    def execute_action(self, key):
        if self.current_os is None: return
        self.after(0, lambda: self.flash_ui_row(key))

        if key not in self.config_data: return
        data = self.config_data[key]
        val = data["value"]
        a_type = data["type"]
        try:
            if a_type == "url":
                if not val.startswith("http"): val = "https://" + val
                webbrowser.open(val)
            elif a_type == "app":
                if self.current_os == "Mac":
                    subprocess.run(["open", val])
                else:
                    os.startfile(val)
            elif a_type == "shortcut":
                if not val: return
                keys = val.lower().split('+')
                if self.current_os == "Windows": keys = [k.replace('command', 'ctrl').replace('cmd', 'ctrl') for k in
                                                         keys]
                if keys: pyautogui.hotkey(*keys)
        except:
            pass

    def execute_combine_action(self, combo_key):
        if self.current_os is None: return
        self.after(0, lambda: self.flash_ui_row(combo_key))

        combine_data = self.config_data.get("combine", {})
        if combo_key not in combine_data: return

        data = combine_data[combo_key]
        val = data["value"]
        a_type = data["type"]

        try:
            if a_type == "url":
                if not val.startswith("http"): val = "https://" + val
                webbrowser.open(val)
            elif a_type == "app":
                if self.current_os == "Mac":
                    subprocess.run(["open", val])
                else:
                    os.startfile(val)
            elif a_type == "shortcut":
                if not val: return
                keys = val.lower().split('+')
                if self.current_os == "Windows":
                    keys = [k.replace('command', 'ctrl').replace('cmd', 'ctrl') for k in keys]
                if keys: pyautogui.hotkey(*keys)
        except:
            pass

    def set_combine_mode(self, active):
        self.is_combine_mode = active
        try:
            if active:
                self.combine_bar.pack(fill="x", pady=(5, 0), before=self.tabview)
                self._start_combine_flash()
                self.tabview.set("Combine Ayarları")
            else:
                if self._combine_flash_id:
                    self.after_cancel(self._combine_flash_id)
                    self._combine_flash_id = None
                self.combine_bar.pack_forget()
        except:
            pass

    def _start_combine_flash(self):
        self._combine_flash_visible = True
        self._flash_combine_bar()

    def _flash_combine_bar(self):
        if not self.is_combine_mode: return
        try:
            if self._combine_flash_visible:
                self.combine_bar_label.configure(text_color="white")
            else:
                self.combine_bar_label.configure(text_color="#FF9500")
            self._combine_flash_visible = not self._combine_flash_visible
            self._combine_flash_id = self.after(500, self._flash_combine_bar)
        except:
            pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for k in ["F21", "F22", "F23", "F24"]:
                        if k in data: del data[k]
                    # Combine config yoksa ekle
                    if "combine" not in data:
                        data["combine"] = {k: v.copy() for k, v in DEFAULT_COMBINE_CONFIG.items()}
                    else:
                        for pair in COMBINE_PAIRS:
                            key = combo_config_key(pair[0], pair[1])
                            if key not in data["combine"]:
                                data["combine"][key] = DEFAULT_COMBINE_CONFIG[key].copy()
                    return data
            except:
                cfg = DEFAULT_CONFIG.copy()
                cfg["combine"] = {k: v.copy() for k, v in DEFAULT_COMBINE_CONFIG.items()}
                return cfg
        cfg = DEFAULT_CONFIG.copy()
        cfg["combine"] = {k: v.copy() for k, v in DEFAULT_COMBINE_CONFIG.items()}
        return cfg

    def start_listener(self):
        current_keys = set()
        combine_chars = set(COMBINE_SIGNAL_CHARS)

        def _get_char(key):
            if hasattr(key, 'char') and key.char:
                return key.char
            if hasattr(key, 'vk'):
                if 48 <= key.vk <= 57:
                    return chr(key.vk)
                elif 65 <= key.vk <= 90:
                    return chr(key.vk + 32)
            return None

        def on_press(key):
            try:
                current_keys.add(key)
                if hasattr(key, 'char') and key.char: current_keys.add(key.char)

                is_ctrl = any(k in current_keys for k in [Key.ctrl, Key.ctrl_l, Key.ctrl_r])
                is_shift = any(k in current_keys for k in [Key.shift, Key.shift_l, Key.shift_r])
                is_alt = any(k in current_keys for k in [Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr])

                if is_ctrl and is_shift and is_alt:
                    char = _get_char(key)

                    if char:
                        # Mod sinyalleri
                        if char == 'w':
                            self.set_mode("Windows")
                            current_keys.clear()
                            return
                        if char == 'm':
                            self.set_mode("Mac")
                            current_keys.clear()
                            return
                        if char == 'n':
                            self.set_mode(None)
                            current_keys.clear()
                            return

                        # Combine mod durum sinyalleri
                        if char == 'x':
                            self.after(0, lambda: self.set_combine_mode(True))
                            current_keys.clear()
                            return
                        if char == 'y':
                            self.after(0, lambda: self.set_combine_mode(False))
                            current_keys.clear()
                            return

                        # Combine tuş sinyalleri
                        if char in combine_chars:
                            pair = SIGNAL_TO_COMBO[char]
                            c_key = combo_config_key(pair[0], pair[1])
                            self.execute_combine_action(c_key)
                            current_keys.clear()
                            return
            except:
                pass

        def on_release(key):
            try:
                if key in current_keys: current_keys.remove(key)
                if hasattr(key, 'char') and key.char in current_keys: current_keys.remove(key.char)
                if hasattr(key, 'name'):
                    k = key.name.upper()
                    if k.startswith("F") and k in self.config_data:
                        self.execute_action(k)
            except:
                pass

        with keyboard.Listener(on_press=on_press, on_release=on_release) as l:
            l.join()


if __name__ == "__main__":
    if not check_single_instance():
        print("UYGULAMA ZATEN AÇIK!")
        sys.exit()

    try:
        app = MacroApp()
        app.mainloop()
    except Exception as e:
        print(f"HATA: {e}")
        traceback.print_exc()
        input("Enter...")