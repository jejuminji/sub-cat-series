"""Mischief actions Ming can take on the host computer.

Each action returns True on success, False if a precondition failed (e.g. no
explorer window open). Actions are intentionally short-lived and recoverable.
"""

from __future__ import annotations

import random
import subprocess
import time
import tkinter as tk
from typing import Callable

try:
    import pyautogui
    import pygetwindow
    import pyperclip
    from PIL import Image, ImageChops, ImageDraw, ImageGrab, ImageOps, ImageTk
    DEPS_OK = True
    _import_error: Exception | None = None
except ImportError as exc:
    DEPS_OK = False
    _import_error = exc

try:
    import win32com.client
    import win32gui
    WIN32_OK = True
except ImportError:
    WIN32_OK = False


if DEPS_OK:
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05


class MischiefEngine:
    """Holds available mischief actions and dispatches them on demand."""

    def __init__(self, root: tk.Tk, screen_w: int, screen_h: int) -> None:
        self.root = root
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.actions: dict[str, Callable[[], bool]] = {}
        if DEPS_OK:
            self.actions = {
                "메모장 + 냥!": self.notepad_meow,
                "탐색기 무작위 폴더": self.explorer_random_folder,
                "환각: RGB 분리": self.glitch_rgb_shift,
                "환각: VHS 스캔라인": self.glitch_vhs_scanlines,
                "환각: 거대 고양이 눈": self.glitch_big_eye,
                "환각: 색 반전": self.glitch_invert,
            }

    @property
    def import_error(self) -> Exception | None:
        return _import_error

    def trigger_random(self) -> tuple[str, bool]:
        if not self.actions:
            return ("(의존성 없음)", False)
        name = random.choice(list(self.actions.keys()))
        return name, self.actions[name]()

    # --- input-driving actions ---

    def notepad_meow(self) -> bool:
        try:
            subprocess.Popen("notepad.exe", shell=False)
        except OSError:
            return False
        time.sleep(0.5)

        target = None
        for _ in range(8):
            for win in pygetwindow.getAllWindows():
                title = win.title or ""
                if ("메모장" in title or "Notepad" in title) and win.visible:
                    target = win
                    break
            if target:
                break
            time.sleep(0.15)
        if target is None:
            return False

        try:
            target.activate()
        except Exception:
            pass
        time.sleep(0.2)

        original_clipboard = ""
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            pass
        try:
            pyperclip.copy("냥!")
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.15)
        finally:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
        return True

    def explorer_random_folder(self) -> bool:
        if not WIN32_OK:
            return False
        try:
            shell = win32com.client.Dispatch("Shell.Application")
        except Exception:
            return False

        foreground = win32gui.GetForegroundWindow()
        candidates = []
        for window in shell.Windows():
            try:
                hwnd = int(window.HWND)
            except Exception:
                continue
            try:
                location = window.LocationURL or ""
            except Exception:
                location = ""
            if not location.startswith("file:"):
                continue
            candidates.append((hwnd, window))

        if not candidates:
            return False

        active = next((win for hwnd, win in candidates if hwnd == foreground), None)
        chosen = active if active is not None else candidates[0][1]

        try:
            folder = chosen.Document.Folder
            subfolders = [item for item in folder.Items() if item.IsFolder]
        except Exception:
            return False
        if not subfolders:
            return False

        pick = random.choice(subfolders)
        try:
            chosen.Navigate(pick.Path)
        except Exception:
            return False
        return True

    # --- visual hallucination actions ---

    def _show_overlay_image(self, image: "Image.Image", duration_ms: int = 500, alpha: float = 1.0) -> None:
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        if alpha < 1.0:
            overlay.attributes("-alpha", alpha)
        overlay.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        photo = ImageTk.PhotoImage(image)
        label = tk.Label(overlay, image=photo, borderwidth=0, highlightthickness=0)
        label.image = photo  # GC pin
        label.pack(fill="both", expand=True)
        overlay.after(duration_ms, overlay.destroy)

    def _grab_screen(self) -> "Image.Image | None":
        try:
            return ImageGrab.grab(bbox=(0, 0, self.screen_w, self.screen_h)).convert("RGB")
        except Exception:
            return None

    def glitch_rgb_shift(self) -> bool:
        screen = self._grab_screen()
        if screen is None:
            return False
        r, g, b = screen.split()
        offset = random.randint(4, 10)
        shifted = Image.merge(
            "RGB",
            (
                ImageChops.offset(r, -offset, 0),
                g,
                ImageChops.offset(b, offset, 0),
            ),
        )
        self._show_overlay_image(shifted, duration_ms=550)
        return True

    def glitch_vhs_scanlines(self) -> bool:
        screen = self._grab_screen()
        if screen is None:
            return False
        draw = ImageDraw.Draw(screen)
        for y in range(0, self.screen_h, 3):
            draw.line([(0, y), (self.screen_w, y)], fill=(0, 0, 0), width=1)
        for _ in range(random.randint(4, 8)):
            band_y = random.randint(0, self.screen_h - 8)
            band_h = random.randint(4, 18)
            band_dx = random.randint(-40, 40)
            band = screen.crop((0, band_y, self.screen_w, band_y + band_h))
            screen.paste(band, (band_dx, band_y))
        self._show_overlay_image(screen, duration_ms=650)
        return True

    def glitch_invert(self) -> bool:
        screen = self._grab_screen()
        if screen is None:
            return False
        self._show_overlay_image(ImageOps.invert(screen), duration_ms=220)
        return True

    def glitch_big_eye(self) -> bool:
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.78)
        overlay.geometry(f"{self.screen_w}x{self.screen_h}+0+0")
        overlay.configure(bg="black")

        canvas = tk.Canvas(
            overlay,
            width=self.screen_w,
            height=self.screen_h,
            bg="black",
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True)

        cx = random.randint(self.screen_w // 3, self.screen_w * 2 // 3)
        cy = random.randint(self.screen_h // 3, self.screen_h * 2 // 3)
        rx = random.randint(160, 260)
        ry = int(rx * 0.62)

        canvas.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill="#cfe9ff", outline="#ffffff", width=6)
        canvas.create_oval(cx - rx + 30, cy - ry + 8, cx + rx - 30, cy + ry - 8, fill="#37bdf8", outline="")
        canvas.create_polygon(
            cx - 10, cy - ry + 14,
            cx + 10, cy - ry + 14,
            cx + 3, cy + ry - 14,
            cx - 3, cy + ry - 14,
            fill="#0a0a0a",
        )
        canvas.create_oval(cx - 18, cy - ry + 22, cx - 4, cy - ry + 36, fill="white", outline="")

        overlay.after(420, overlay.destroy)
        return True
