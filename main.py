"""
Raze AutoClick - main.py
Interfaz principal con customtkinter.
"""

import sys
import customtkinter as ctk
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from config import load_config, save_config
from clicker import AutoClicker, _mouse_button_name, _key_name

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLOR_BG      = "#1a1a2e"
COLOR_SURFACE = "#16213e"
COLOR_CARD    = "#0f3460"
COLOR_ACCENT  = "#e94560"
COLOR_GREEN   = "#00d26a"
COLOR_YELLOW  = "#f5a623"
COLOR_RED     = "#e94560"
COLOR_SUBTEXT = "#8892a4"
COLOR_BORDER  = "#1e2d45"
COLOR_TEXT    = "#e0e0e0"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_LABEL = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)
FONT_BIG   = ("Segoe UI", 18, "bold")
FONT_MONO  = ("Consolas", 13, "bold")

MOUSE_BUTTON_LABELS = {
    "mouse_left":   "Mouse Izquierdo",
    "mouse_right":  "Mouse Derecho",
    "mouse_middle": "Mouse Central",
    "mouse_x1":     "Mouse X1",
    "mouse_x2":     "Mouse X2",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self._capturing_hotkey = False
        self._capture_listeners = []

        self.clicker = AutoClicker(
            on_state_change=self._on_clicker_state_change,
            on_cps_update=self._on_cps_update,
        )
        self._apply_config_to_clicker()
        self._build_ui()
        self.clicker.start_listeners()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_config_to_clicker(self):
        self.clicker.cps              = float(self.config_data.get("cps", 10.0))
        self.clicker.click_type       = self.config_data.get("click_type", "left")
        self.clicker.mode             = self.config_data.get("mode", "toggle")
        self.clicker.hotkey           = self.config_data.get("hotkey", {"type": "keyboard", "key": "f6"})
        self.clicker.antikick_enabled = self.config_data.get("antikick", True)
        self.clicker.antikick_max     = float(self.config_data.get("antikick_max", 20))

    # ─── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.title("Raze AutoClick")
        self.geometry("480x760")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        # Encabezado
        header = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚡ Raze AutoClick",
                     font=FONT_TITLE, text_color=COLOR_ACCENT).pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(header, text="v1.1",
                     font=FONT_SMALL, text_color=COLOR_SUBTEXT).pack(side="right", padx=20, pady=15)

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Botón ACTIVAR ──────────────────────────────────────────────────────
        self.toggle_btn = ctk.CTkButton(
            main, text="ACTIVAR", font=FONT_BIG, height=70,
            corner_radius=12, fg_color=COLOR_RED, hover_color="#c73652",
            command=self._toggle_clicker,
        )
        self.toggle_btn.pack(fill="x", pady=(0, 12))

        # ── Monitor en tiempo real ──────────────────────────────────────────────
        monitor_card = self._card(main, "Monitor en Tiempo Real")
        monitor_row = ctk.CTkFrame(monitor_card, fg_color="transparent")
        monitor_row.pack(fill="x", padx=14, pady=(0, 12))

        cps_box = ctk.CTkFrame(monitor_row, fg_color=COLOR_CARD, corner_radius=8)
        cps_box.pack(side="left", expand=True, fill="x", padx=(0, 8))
        ctk.CTkLabel(cps_box, text="CPS REAL", font=FONT_SMALL, text_color=COLOR_SUBTEXT).pack(pady=(8, 0))
        self.real_cps_label = ctk.CTkLabel(cps_box, text="0.0", font=FONT_MONO, text_color=COLOR_TEXT)
        self.real_cps_label.pack(pady=(0, 8))

        prot_box = ctk.CTkFrame(monitor_row, fg_color=COLOR_CARD, corner_radius=8)
        prot_box.pack(side="right", expand=True, fill="x")
        ctk.CTkLabel(prot_box, text="ANTI-KICK", font=FONT_SMALL, text_color=COLOR_SUBTEXT).pack(pady=(8, 0))
        self.prot_label = ctk.CTkLabel(prot_box, text="● EN ESPERA", font=FONT_SMALL, text_color=COLOR_SUBTEXT)
        self.prot_label.pack(pady=(0, 8))

        # ── Anti-kick ──────────────────────────────────────────────────────────
        ak_card = self._card(main, "Protección Anti-Kick")
        ak_switch_row = ctk.CTkFrame(ak_card, fg_color="transparent")
        ak_switch_row.pack(fill="x", padx=14, pady=(0, 6))

        self.antikick_var = ctk.BooleanVar(value=self.config_data.get("antikick", True))
        ctk.CTkSwitch(
            ak_switch_row, text="Activar protección",
            variable=self.antikick_var, font=FONT_LABEL,
            progress_color=COLOR_GREEN, button_color=COLOR_TEXT,
            command=self._on_antikick_toggle,
        ).pack(side="left")

        # Campo: límite máximo de CPS
        ak_max_row = ctk.CTkFrame(ak_card, fg_color="transparent")
        ak_max_row.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(
            ak_max_row,
            text="Parar si CPS real supera:",
            font=FONT_SMALL, text_color=COLOR_SUBTEXT,
        ).pack(side="left")

        self.ak_max_entry = ctk.CTkEntry(
            ak_max_row, width=60, font=FONT_LABEL, justify="center",
            border_color=COLOR_BORDER, fg_color=COLOR_CARD,
        )
        self.ak_max_entry.insert(0, str(self.config_data.get("antikick_max", 20)))
        self.ak_max_entry.pack(side="left", padx=(8, 0))
        self.ak_max_entry.bind("<FocusOut>", self._on_ak_max_change)
        self.ak_max_entry.bind("<Return>",   self._on_ak_max_change)

        ctk.CTkLabel(
            ak_max_row, text="CPS", font=FONT_SMALL, text_color=COLOR_SUBTEXT,
        ).pack(side="left", padx=(4, 0))

        # Descripción dinámica
        self.ak_desc = ctk.CTkLabel(
            ak_card,
            text=self._ak_desc_text(),
            font=FONT_SMALL, text_color=COLOR_SUBTEXT,
        )
        self.ak_desc.pack(anchor="w", padx=14, pady=(0, 10))

        # ── CPS objetivo ───────────────────────────────────────────────────────
        cps_card = self._card(main, "CPS Objetivo")
        cps_row = ctk.CTkFrame(cps_card, fg_color="transparent")
        cps_row.pack(fill="x", padx=14, pady=(0, 10))

        self.cps_slider = ctk.CTkSlider(
            cps_row, from_=1, to=100, number_of_steps=990,
            command=self._on_slider_change,
            button_color=COLOR_ACCENT, progress_color=COLOR_ACCENT,
        )
        self.cps_slider.set(self.config_data.get("cps", 10.0))
        self.cps_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.cps_entry = ctk.CTkEntry(
            cps_row, width=70, font=FONT_LABEL, justify="center",
            border_color=COLOR_BORDER, fg_color=COLOR_CARD,
        )
        self.cps_entry.insert(0, str(self.config_data.get("cps", 10.0)))
        self.cps_entry.pack(side="right")
        self.cps_entry.bind("<FocusOut>", self._on_cps_entry_change)
        self.cps_entry.bind("<Return>",   self._on_cps_entry_change)

        # ── Tipo de clic ───────────────────────────────────────────────────────
        click_card = self._card(main, "Tipo de Clic")
        self.click_var = ctk.StringVar(value=self.config_data.get("click_type", "left"))
        click_row = ctk.CTkFrame(click_card, fg_color="transparent")
        click_row.pack(fill="x", padx=14, pady=(0, 10))
        for label, val in [("Izquierdo", "left"), ("Derecho", "right"), ("Ambos alternados", "both")]:
            ctk.CTkRadioButton(
                click_row, text=label, variable=self.click_var, value=val,
                font=FONT_LABEL, fg_color=COLOR_ACCENT, hover_color=COLOR_CARD,
                command=self._save_and_apply,
            ).pack(side="left", padx=(0, 14))

        # ── Modo ───────────────────────────────────────────────────────────────
        mode_card = self._card(main, "Modo de Activación")
        self.mode_var = ctk.StringVar(value=self.config_data.get("mode", "toggle"))
        mode_row = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=14, pady=(0, 10))
        for label, val in [("Toggle", "toggle"), ("Mantener presionado", "hold")]:
            ctk.CTkRadioButton(
                mode_row, text=label, variable=self.mode_var, value=val,
                font=FONT_LABEL, fg_color=COLOR_ACCENT, hover_color=COLOR_CARD,
                command=self._save_and_apply,
            ).pack(anchor="w", pady=2)

        # ── Hotkey ─────────────────────────────────────────────────────────────
        hk_card = self._card(main, "Tecla de Activación")
        hk_row = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk_row.pack(fill="x", padx=14, pady=(0, 10))
        self.hotkey_label = ctk.CTkLabel(
            hk_row, text=self._hotkey_display(),
            font=FONT_LABEL, text_color=COLOR_ACCENT, width=160, anchor="w",
        )
        self.hotkey_label.pack(side="left")
        self.capture_btn = ctk.CTkButton(
            hk_row, text="Asignar tecla", font=FONT_LABEL, width=130,
            fg_color=COLOR_CARD, hover_color="#1a4a7a",
            command=self._start_hotkey_capture,
        )
        self.capture_btn.pack(side="right")

        # ── Status ─────────────────────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="● Inactivo — presiona la tecla asignada para iniciar",
            font=FONT_SMALL, text_color=COLOR_SUBTEXT,
        )
        self.status_label.pack(pady=(4, 10))

    # ─── Helpers ───────────────────────────────────────────────────────────────

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        wrap = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, corner_radius=10,
                            border_width=1, border_color=COLOR_BORDER)
        wrap.pack(fill="x", pady=5)
        ctk.CTkLabel(wrap, text=title, font=FONT_LABEL,
                     text_color=COLOR_SUBTEXT).pack(anchor="w", padx=14, pady=(10, 4))
        return wrap

    def _hotkey_display(self) -> str:
        hk = self.config_data.get("hotkey", {"type": "keyboard", "key": "f6"})
        key = hk.get("key", "?")
        return MOUSE_BUTTON_LABELS.get(key, key) if hk.get("type") == "mouse" else key.upper()

    def _ak_desc_text(self) -> str:
        mx = self.clicker.antikick_max
        tgt = self.clicker.cps
        return f"Se para al llegar a {mx} CPS  →  reanuda cuando baje de {tgt} CPS"

    # ─── Anti-kick ─────────────────────────────────────────────────────────────

    def _on_antikick_toggle(self):
        enabled = self.antikick_var.get()
        self.clicker.antikick_enabled = enabled
        self.config_data["antikick"] = enabled
        save_config(self.config_data)

    def _on_ak_max_change(self, event=None):
        try:
            value = float(self.ak_max_entry.get())
            value = max(1.0, min(200.0, value))
        except ValueError:
            value = 20.0
        self.ak_max_entry.delete(0, "end")
        self.ak_max_entry.insert(0, str(value))
        self.clicker.antikick_max = value
        self.config_data["antikick_max"] = value
        self.ak_desc.configure(text=self._ak_desc_text())
        save_config(self.config_data)

    # ─── CPS ───────────────────────────────────────────────────────────────────

    def _on_slider_change(self, value):
        rounded = round(float(value), 1)
        self.cps_entry.delete(0, "end")
        self.cps_entry.insert(0, str(rounded))
        self.clicker.cps = rounded
        self.config_data["cps"] = rounded
        self.ak_desc.configure(text=self._ak_desc_text())
        save_config(self.config_data)

    def _on_cps_entry_change(self, event=None):
        try:
            value = float(self.cps_entry.get())
            value = max(0.1, min(100.0, value))
        except ValueError:
            value = 10.0
        self.cps_entry.delete(0, "end")
        self.cps_entry.insert(0, str(value))
        self.cps_slider.set(value)
        self.clicker.cps = value
        self.config_data["cps"] = value
        self.ak_desc.configure(text=self._ak_desc_text())
        save_config(self.config_data)

    # ─── Guardar y aplicar ─────────────────────────────────────────────────────

    def _save_and_apply(self):
        self.config_data["click_type"] = self.click_var.get()
        self.config_data["mode"]       = self.mode_var.get()
        self.clicker.click_type = self.config_data["click_type"]
        self.clicker.mode       = self.config_data["mode"]
        save_config(self.config_data)

    # ─── Toggle ────────────────────────────────────────────────────────────────

    def _toggle_clicker(self):
        self.clicker._set_active(not self.clicker.active)

    # ─── Callbacks del motor ───────────────────────────────────────────────────

    def _on_clicker_state_change(self, active: bool):
        self.after(0, self._update_ui_state, active)

    def _update_ui_state(self, active: bool):
        if active:
            self.toggle_btn.configure(
                text="DESACTIVAR", fg_color=COLOR_GREEN, hover_color="#00a854"
            )
            self.status_label.configure(
                text=f"● Activo — objetivo {self.clicker.cps} CPS  |  máximo {self.clicker.antikick_max} CPS",
                text_color=COLOR_GREEN,
            )
        else:
            self.toggle_btn.configure(
                text="ACTIVAR", fg_color=COLOR_RED, hover_color="#c73652"
            )
            self.status_label.configure(
                text="● Inactivo — presiona la tecla asignada para iniciar",
                text_color=COLOR_SUBTEXT,
            )
            self.real_cps_label.configure(text="0.0", text_color=COLOR_TEXT)
            self.prot_label.configure(text="● EN ESPERA", text_color=COLOR_SUBTEXT)

    def _on_cps_update(self, real_cps: float, protected: bool):
        self.after(0, self._update_monitor, real_cps, protected)

    def _update_monitor(self, real_cps: float, protected: bool):
        self.real_cps_label.configure(text=f"{real_cps:.1f}")
        if real_cps == 0.0:
            self.real_cps_label.configure(text_color=COLOR_TEXT)
            self.prot_label.configure(text="● EN ESPERA", text_color=COLOR_SUBTEXT)
        elif protected:
            # Superó el límite — pausado esperando bajar al target
            self.real_cps_label.configure(text_color=COLOR_YELLOW)
            self.prot_label.configure(text="⚠ PAUSADO", text_color=COLOR_YELLOW)
        else:
            self.real_cps_label.configure(text_color=COLOR_GREEN)
            self.prot_label.configure(text="● OK", text_color=COLOR_GREEN)

    # ─── Captura de hotkey ─────────────────────────────────────────────────────

    def _start_hotkey_capture(self):
        if self._capturing_hotkey:
            return
        self._capturing_hotkey = True
        self.clicker.stop_listeners()
        self.capture_btn.configure(text="Esperando tecla...", fg_color=COLOR_ACCENT)
        self.hotkey_label.configure(text="Pulsa cualquier tecla o botón del mouse")

        def on_key(key):
            name = _key_name(key)
            if name:
                self._finish_capture({"type": "keyboard", "key": name})
                return False

        def on_mouse(x, y, button, pressed):
            if pressed:
                self._finish_capture({"type": "mouse", "key": _mouse_button_name(button)})
                return False

        kb_l = pynput_keyboard.Listener(on_press=on_key)
        ms_l = pynput_mouse.Listener(on_click=on_mouse)
        self._capture_listeners = [kb_l, ms_l]
        kb_l.start()
        ms_l.start()

    def _finish_capture(self, hotkey: dict):
        for l in self._capture_listeners:
            try:
                l.stop()
            except Exception:
                pass
        self._capture_listeners = []
        self._capturing_hotkey = False
        self.config_data["hotkey"] = hotkey
        self.clicker.hotkey = hotkey
        save_config(self.config_data)
        self.after(0, self._after_capture)

    def _after_capture(self):
        self.capture_btn.configure(text="Asignar tecla", fg_color=COLOR_CARD)
        self.hotkey_label.configure(text=self._hotkey_display())
        self.clicker.start_listeners()

    def _on_close(self):
        self.clicker.shutdown()
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
