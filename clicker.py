import threading
import time
from pynput import mouse as pynput_mouse
from pynput import keyboard as pynput_keyboard

class AutoClicker:
    """
    Motor del auto clicker.
    Gestiona el hilo de clics, la escucha global de hotkey
    y los dos modos: toggle y hold.
    """

    def __init__(self, on_state_change=None):
        self.cps = 10.0
        self.click_type = "left"  # "left" | "right" | "both"
        self.mode = "toggle"      # "toggle" | "hold"
        self.hotkey = {"type": "keyboard", "key": "f6"}

        self.active = False
        self._click_thread = None
        self._stop_event = threading.Event()
        self._mouse_ctrl = pynput_mouse.Controller()
        self._listener_kb = None
        self._listener_mouse = None
        self._hold_pressed = False
        self._both_turn = "left"  # para alternar en modo "both"

        self.on_state_change = on_state_change  # callback(active: bool)

    # ─── Estado ────────────────────────────────────────────────────────────────

    def _set_active(self, value: bool):
        if self.active == value:
            return
        self.active = value
        if value:
            self._stop_event.clear()
            self._click_thread = threading.Thread(target=self._click_loop, daemon=True)
            self._click_thread.start()
        else:
            self._stop_event.set()
        if self.on_state_change:
            self.on_state_change(self.active)

    # ─── Loop de clics ─────────────────────────────────────────────────────────

    def _click_loop(self):
        while not self._stop_event.is_set():
            self._do_click()
            delay = 1.0 / max(self.cps, 0.1)
            # Espera interruptible en intervalos pequeños
            elapsed = 0.0
            step = 0.005
            while elapsed < delay and not self._stop_event.is_set():
                time.sleep(step)
                elapsed += step

    def _do_click(self):
        btn = self._resolve_button()
        self._mouse_ctrl.press(btn)
        self._mouse_ctrl.release(btn)

    def _resolve_button(self):
        if self.click_type == "right":
            return pynput_mouse.Button.right
        if self.click_type == "both":
            if self._both_turn == "left":
                self._both_turn = "right"
                return pynput_mouse.Button.left
            else:
                self._both_turn = "left"
                return pynput_mouse.Button.right
        return pynput_mouse.Button.left

    # ─── Hotkey global ─────────────────────────────────────────────────────────

    def start_listeners(self):
        self.stop_listeners()

        hk = self.hotkey
        if hk["type"] == "keyboard":
            self._listener_kb = pynput_keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
            )
            self._listener_kb.start()
        else:
            self._listener_mouse = pynput_mouse.Listener(
                on_click=self._on_mouse_click,
            )
            self._listener_mouse.start()

    def stop_listeners(self):
        if self._listener_kb:
            self._listener_kb.stop()
            self._listener_kb = None
        if self._listener_mouse:
            self._listener_mouse.stop()
            self._listener_mouse = None

    # ─── Callbacks de pynput ───────────────────────────────────────────────────

    def _on_key_press(self, key):
        if self.hotkey["type"] != "keyboard":
            return
        if _key_name(key) == self.hotkey["key"]:
            if self.mode == "toggle":
                self._set_active(not self.active)
            else:  # hold
                if not self._hold_pressed:
                    self._hold_pressed = True
                    self._set_active(True)

    def _on_key_release(self, key):
        if self.hotkey["type"] != "keyboard":
            return
        if self.mode == "hold" and _key_name(key) == self.hotkey["key"]:
            self._hold_pressed = False
            self._set_active(False)

    def _on_mouse_click(self, x, y, button, pressed):
        if self.hotkey["type"] != "mouse":
            return
        if _mouse_button_name(button) == self.hotkey["key"]:
            if self.mode == "toggle":
                if pressed:
                    self._set_active(not self.active)
            else:  # hold
                self._set_active(pressed)

    # ─── Ciclo de vida ─────────────────────────────────────────────────────────

    def shutdown(self):
        self._set_active(False)
        self.stop_listeners()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _key_name(key) -> str:
    """Convierte una tecla pynput en string normalizado."""
    try:
        return key.char.lower() if key.char else ""
    except AttributeError:
        return str(key).replace("Key.", "").lower()


def _mouse_button_name(button) -> str:
    """Convierte un botón de ratón pynput en string normalizado."""
    mapping = {
        pynput_mouse.Button.left:   "mouse_left",
        pynput_mouse.Button.right:  "mouse_right",
        pynput_mouse.Button.middle: "mouse_middle",
        pynput_mouse.Button.x1:     "mouse_x1",
        pynput_mouse.Button.x2:     "mouse_x2",
    }
    return mapping.get(button, str(button))
