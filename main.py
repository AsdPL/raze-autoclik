"""
Raze AutoClick - main.py
Interfaz principal con customtkinter.
"""

import sys
import threading
import customtkinter as ctk
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from config import load_config, save_config
from clicker import AutoClicker, _mouse_button_name, _key_name

# ─── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ─── Paleta ────────────────────────────────────────────────────────────────────
COLOR_BG        = "#1a1a2e"
COLOR_SURFACE   = "#16213e"
COLOR_CARD      = "#0f3460"
COLOR_ACCENT    = "#e94560"
COLOR_GREEN     = "#00d26a"
COLOR_RED       = "#e94560"
COLOR_TEXT      = "#e0e0e0"
COLOR_SUBTEXT   = "#8892a4"
COLOR_BORDER    = "#1e2d45"

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_LABEL  = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 10)
FONT_BTN    = ("Segoe UI", 14, "bold")
FONT_BIG    = ("Segoe UI", 18, "bold")

# ─── Etiquetas para botones de mouse ───────────────────────────────────────────
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

        self.clicker = AutoClicker(on_state_change=self._on_clicker_state_change)
        self._apply_config_to_clicker()

        self._build_ui()
        self.clicker.start_listeners()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── Aplicar config al motor ────────────────────────────────────────────────

    def _apply_config_to_clicker(self):
        self.clicker.cps        = float(self.config_data.get("cps", 10.0))
        self.clicker.click_type = self.config_data.get("click_type", "left")
        self.clicker.mode       = self.config_data.get("mode", "toggle")
        self.clicker.hotkey     = self.config_data.get("hotkey", {"type": "keyboard", "key": "f6"})

    # ─── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.title("Raze AutoClick")
        self.geometry("480x640")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Intentar poner ícono si existe
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
        ctk.CTkLabel(header, text="v1.0",
                     font=FONT_SMALL, text_color=COLOR_SUBTEXT).pack(side="right", padx=20, pady=15)

        # Contenedor principal
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Botón ACTIVAR / DESACTIVAR ──────────────────────────────────────────
        self.toggle_btn = ctk.CTkButton(
            main,
            text="ACTIVAR",
            font=FONT_BIG,
            height=70,
            corner_radius=12,
            fg_color=COLOR_RED,
            hover_color="#c73652",
            command=self._toggle_clicker,
        )
        self.toggle_btn.pack(fill="x", pady=(0, 14))

        # ── CPS ────────────────────────────────────────────────────────────────
        cps_card = self._card(main, "Velocidad (CPS — Clics Por Segundo)")
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
        click_options = ctk.CTkFrame(click_card, fg_color="transparent")
        click_options.pack(fill="x", padx=14, pady=(0, 10))

        for label, val in [("Izquierdo", "left"), ("Derecho", "right"), ("Ambos alternados", "both")]:
            rb = ctk.CTkRadioButton(
                click_options, text=label, variable=self.click_var,
                value=val, font=FONT_LABEL,
                fg_color=COLOR_ACCENT, hover_color=COLOR_CARD,
                command=self._save_and_apply,
            )
            rb.pack(side="left", padx=(0, 16))

        # ── Modo ───────────────────────────────────────────────────────────────
        mode_card = self._card(main, "Modo de Activación")
        self.mode_var = ctk.StringVar(value=self.config_data.get("mode", "toggle"))
        mode_options = ctk.CTkFrame(mode_card, fg_color="transparent")
        mode_options.pack(fill="x", padx=14, pady=(0, 10))

        for label, val in [("Toggle (pulsa para activar/desactivar)", "toggle"),
                            ("Mantener presionado", "hold")]:
            rb = ctk.CTkRadioButton(
                mode_options, text=label, variable=self.mode_var,
                value=val, font=FONT_LABEL,
                fg_color=COLOR_ACCENT, hover_color=COLOR_CARD,
                command=self._save_and_apply,
            )
            rb.pack(anchor="w", pady=2)

        # ── Hotkey ─────────────────────────────────────────────────────────────
        hk_card = self._card(main, "Tecla de Activación")
        hk_inner = ctk.CTkFrame(hk_card, fg_color="transparent")
        hk_inner.pack(fill="x", padx=14, pady=(0, 10))

        self.hotkey_label = ctk.CTkLabel(
            hk_inner, text=self._hotkey_display(),
            font=FONT_LABEL, text_color=COLOR_ACCENT,
            width=160, anchor="w",
        )
        self.hotkey_label.pack(side="left")

        self.capture_btn = ctk.CTkButton(
            hk_inner, text="Asignar tecla",
            font=FONT_LABEL, width=130,
            fg_color=COLOR_CARD, hover_color="#1a4a7a",
            command=self._start_hotkey_capture,
        )
        self.capture_btn.pack(side="right")

        # ── Status bar ─────────────────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="● Inactivo — presiona la tecla asignada para iniciar",
            font=FONT_SMALL, text_color=COLOR_SUBTEXT,
        )
        self.status_label.pack(pady=(4, 10))

    # ─── Helpers UI ────────────────────────────────────────────────────────────

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        wrap = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        wrap.pack(fill="x", pady=6)
        ctk.CTkLabel(wrap, text=title, font=FONT_LABEL, text_color=COLOR_SUBTEXT).pack(anchor="w", padx=14, pady=(10, 4))
        return wrap

    def _hotkey_display(self) -> str:
        hk = self.config_data.get("hotkey", {"type": "keyboard", "key": "f6"})
        key = hk.get("key", "?")
        if hk.get("type") == "mouse":
            return MOUSE_BUTTON_LABELS.get(key, key)
        return key.upper()

    # ─── Eventos de CPS ────────────────────────────────────────────────────────

    def _on_slider_change(self, value):
        rounded = round(float(value), 1)
        self.cps_entry.delete(0, "end")
        self.cps_entry.insert(0, str(rounded))
        self.config_data["cps"] = rounded
        self.clicker.cps = rounded
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
        self.config_data["cps"] = value
        self.clicker.cps = value
        save_config(self.config_data)

    # ─── Guardar y aplicar ─────────────────────────────────────────────────────

    def _save_and_apply(self):
        self.config_data["click_type"] = self.click_var.get()
        self.config_data["mode"]       = self.mode_var.get()
        self.clicker.click_type = self.config_data["click_type"]
        self.clicker.mode       = self.config_data["mode"]
        save_config(self.config_data)

    # ─── Toggle desde botón ────────────────────────────────────────────────────

    def _toggle_clicker(self):
        new_state = not self.clicker.active
        if new_state:
            self.clicker._stop_event.clear()
            import threading as _t
            self.clicker.active = False  # forzar que _set_active lo active
        self.clicker._set_active(new_state)

    # ─── Callback del motor ────────────────────────────────────────────────────

    def _on_clicker_state_change(self, active: bool):
        # Ejecutar en el hilo de la UI (after seguro en tkinter)
        self.after(0, self._update_ui_state, active)

    def _update_ui_state(self, active: bool):
        if active:
            self.toggle_btn.configure(
                text="DESACTIVAR",
                fg_color=COLOR_GREEN,
                hover_color="#00a854",
            )
            self.status_label.configure(
                text=f"● Activo — {self.clicker.cps} CPS", text_color=COLOR_GREEN
            )
        else:
            self.toggle_btn.configure(
                text="ACTIVAR",
                fg_color=COLOR_RED,
                hover_color="#c73652",
            )
            self.status_label.configure(
                text="● Inactivo — presiona la tecla asignada para iniciar",
                text_color=COLOR_SUBTEXT,
            )

    # ─── Captura de hotkey ─────────────────────────────────────────────────────

    def _start_hotkey_capture(self):
        if self._capturing_hotkey:
            return
        self._capturing_hotkey = True
        self.clicker.stop_listeners()
        self.capture_btn.configure(text="Esperando tecla...", fg_color=COLOR_ACCENT)
        self.hotkey_label.configure(text="Pulsa cualquier tecla o botón del mouse")

        # Listener temporal de teclado
        def on_key(key):
            name = _key_name(key)
            if name:
                self._finish_capture({"type": "keyboard", "key": name})
                return False  # detener listener

        # Listener temporal de mouse
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
        # Detener ambos listeners de captura
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

        # Actualizar UI desde el hilo de la interfaz
        self.after(0, self._after_capture)

    def _after_capture(self):
        self.capture_btn.configure(text="Asignar tecla", fg_color=COLOR_CARD)
        self.hotkey_label.configure(text=self._hotkey_display())
        self.clicker.start_listeners()

    # ─── Cierre ────────────────────────────────────────────────────────────────

    def _on_close(self):
        self.clicker.shutdown()
        self.destroy()
        sys.exit(0)


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
