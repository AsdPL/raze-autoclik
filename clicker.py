import threading
import time
from collections import deque
from pynput import mouse as pynput_mouse
from pynput import keyboard as pynput_keyboard


class AutoClicker:
    """
    Motor del auto clicker con protección anti-kick.

    Lógica del anti-kick:
      - Si el CPS real sube de `antikick_max` (ej. 20): deja de clicar.
      - Reanuda SOLO cuando el CPS real baje del target configurado (ej. 10).
      - Esto crea una oscilación natural sin riesgo de kick por stacking.
    """

    def __init__(self, on_state_change=None, on_cps_update=None):
        self.cps = 10.0             # CPS objetivo (configurado por el usuario)
        self.antikick_enabled = True
        self.antikick_max = 20.0    # Límite duro: se para aquí
        # Se reanuda cuando CPS real < self.cps (el target del usuario)

        self.click_type = "left"   # "left" | "right" | "both"
        self.mode = "toggle"       # "toggle" | "hold"
        self.hotkey = {"type": "keyboard", "key": "f6"}

        self.active = False
        self._click_thread = None
        self._stop_event = threading.Event()
        self._mouse_ctrl = pynput_mouse.Controller()
        self._listener_kb = None
        self._listener_mouse = None
        self._hold_pressed = False
        self._both_turn = "left"

        # Ventana deslizante de timestamps (último segundo)
        self._click_times = deque()
        self._cps_lock = threading.Lock()
        self._paused_by_antikick = False

        self.on_state_change = on_state_change
        self.on_cps_update = on_cps_update

    # ─── Estado ────────────────────────────────────────────────────────────────

    def _set_active(self, value: bool):
        if self.active == value:
            return
        self.active = value
        if value:
            self._stop_event.clear()
            self._paused_by_antikick = False
            with self._cps_lock:
                self._click_times.clear()
            self._click_thread = threading.Thread(target=self._click_loop, daemon=True)
            self._click_thread.start()
        else:
            self._stop_event.set()
            self._paused_by_antikick = False
            if self.on_cps_update:
                self.on_cps_update(0.0, False)
        if self.on_state_change:
            self.on_state_change(self.active)

    # ─── Loop principal ────────────────────────────────────────────────────────

    def _click_loop(self):
        while not self._stop_event.is_set():
            real_cps = self._get_real_cps()

            if self.antikick_enabled:
                if not self._paused_by_antikick:
                    # ¿Superó el límite duro?
                    if real_cps >= self.antikick_max:
                        self._paused_by_antikick = True
                        if self.on_cps_update:
                            self.on_cps_update(real_cps, True)
                        time.sleep(0.02)
                        continue
                else:
                    # Pausado — esperar a que baje del target del usuario
                    if real_cps < self.cps:
                        self._paused_by_antikick = False
                    else:
                        if self.on_cps_update:
                            self.on_cps_update(real_cps, True)
                        time.sleep(0.02)
                        continue

            # Clic normal
            self._do_click()
            self._register_click()
            real_cps = self._get_real_cps()

            if self.on_cps_update:
                self.on_cps_update(real_cps, False)

            delay = 1.0 / max(self.cps, 0.1)
            elapsed = 0.0
            while elapsed < delay and not self._stop_event.is_set():
                time.sleep(0.005)
                elapsed += 0.005

    # ─── CPS real ──────────────────────────────────────────────────────────────

    def _register_click(self):
        now = time.monotonic()
        with self._cps_lock:
            self._click_times.append(now)
            while self._click_times and self._click_times[0] < now - 1.0:
                self._click_times.popleft()

    def _get_real_cps(self) -> float:
        now = time.monotonic()
        with self._cps_lock:
            while self._click_times and self._click_times[0] < now - 1.0:
                self._click_times.popleft()
            return float(len(self._click_times))

    # ─── Clic ──────────────────────────────────────────────────────────────────

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

    def _on_key_press(self, key):
        if self.hotkey["type"] != "keyboard":
            return
        if _key_name(key) == self.hotkey["key"]:
            if self.mode == "toggle":
                self._set_active(not self.active)
            else:
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
            else:
                self._set_active(pressed)

    def shutdown(self):
        self._set_active(False)
        self.stop_listeners()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _key_name(key) -> str:
    try:
        return key.char.lower() if key.char else ""
    except AttributeError:
        return str(key).replace("Key.", "").lower()


def _mouse_button_name(button) -> str:
    mapping = {
        pynput_mouse.Button.left:   "mouse_left",
        pynput_mouse.Button.right:  "mouse_right",
        pynput_mouse.Button.middle: "mouse_middle",
        pynput_mouse.Button.x1:     "mouse_x1",
        pynput_mouse.Button.x2:     "mouse_x2",
    }
    return mapping.get(button, str(button))
