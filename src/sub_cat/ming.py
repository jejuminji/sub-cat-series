from __future__ import annotations

import queue
import math
import random
import threading
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .conversation import MingChatClient
from .mischief import MischiefEngine
from .sprites import SpriteSet


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


TRANSPARENT = "#ff00ff"
INK = "#170f0d"
FUR = "#9b7650"
FUR_DARK = "#4c3527"
FUR_LIGHT = "#c59a65"
SCARF = "#7a1f24"
CHEEK = "#f0d2ad"
CLAW = "#f4efe5"
METAL = "#d8d8d8"
MUSCLE_LINE = "#6f4b36"
SHADOW = "#000000"


class Mood(str, Enum):
    WANDER = "wander"
    IDLE = "idle"
    NAP = "nap"
    FOLLOW = "follow"
    POUNCE = "pounce"


class CatStyle(str, Enum):
    BOSS = "boss"
    MAGICAL = "magical"
    GLAM = "glam"
    NORMAL = "normal"
    ODDEYE = "oddeye"
    AEYONG = "aeyong"


STYLE_LABELS = {
    CatStyle.BOSS: "보스냥",
    CatStyle.MAGICAL: "마법소녀냥",
    CatStyle.GLAM: "섹시냥",
    CatStyle.NORMAL: "일반냥",
    CatStyle.ODDEYE: "오드아이냥",
    CatStyle.AEYONG: "애용",
}


STYLE_PALETTES = {
    CatStyle.BOSS: {
        "fur": "#9b7650",
        "fur_dark": "#4c3527",
        "fur_light": "#c59a65",
        "scarf": "#7a1f24",
        "cheek": "#f0d2ad",
        "claw": "#f4efe5",
        "metal": "#d8d8d8",
        "muscle": "#6f4b36",
    },
    CatStyle.MAGICAL: {
        "fur": "#f3a8cf",
        "fur_dark": "#9f4d8a",
        "fur_light": "#ffe1f0",
        "scarf": "#d735a8",
        "cheek": "#fff2a8",
        "claw": "#fff8fa",
        "metal": "#ffe96b",
        "muscle": "#bd5f94",
    },
    CatStyle.GLAM: {
        "fur": "#3b3335",
        "fur_dark": "#171315",
        "fur_light": "#c78c61",
        "scarf": "#c41443",
        "cheek": "#f0b0b6",
        "claw": "#fff4f8",
        "metal": "#ffd166",
        "muscle": "#8c5f4b",
    },
    CatStyle.NORMAL: {
        "fur": "#e49b47",
        "fur_dark": "#b45f2a",
        "fur_light": "#ffd49a",
        "scarf": "#3f8dbb",
        "cheek": "#f2b79f",
        "claw": "#fff7ed",
        "metal": "#f0c94a",
        "muscle": "#c77838",
    },
    CatStyle.ODDEYE: {
        "fur": "#e8e6dc",
        "fur_dark": "#6d7780",
        "fur_light": "#fffaf0",
        "scarf": "#2f7d77",
        "cheek": "#d7c7b7",
        "claw": "#fffdf8",
        "metal": "#e3e6e8",
        "muscle": "#9a9a92",
    },
    CatStyle.AEYONG: {
        "fur": "#eee5d5",
        "fur_dark": "#8f877e",
        "fur_light": "#fffaf1",
        "scarf": "#8ab8c7",
        "cheek": "#e7aaa2",
        "claw": "#fffaf4",
        "metal": "#b7d9e6",
        "muscle": "#d8cdbd",
    },
}


STYLE_LINES = {
    CatStyle.BOSS: {
        "enter": "보스 입장!",
        "hover": ["뭐냐", "비켜", "내 구역이다"],
        "call": "불렀냐",
        "wander": "순찰 간다",
        "nap": "기절한다",
        "drag": "놔라",
        "land": "착지 완료",
        "idle": ["흠", "내 구역이다", "조용히 해라"],
        "follow": ["왔다", "용건 말해", "내가 왔다"],
        "select": "보스냥이다",
        "chat": "근육질 보스냥. 선글라스를 낀 거칠고 퉁명스러운 수호자 말투",
    },
    CatStyle.MAGICAL: {
        "enter": "변신 완료!",
        "hover": ["반짝!", "마력 충전", "악은 물러가라"],
        "call": "소환됐어!",
        "wander": "마법 순찰!",
        "nap": "마력 회복...",
        "drag": "망토 구겨진다!",
        "land": "반짝 착지!",
        "idle": ["별빛 감시 중", "주문 준비", "반짝인다"],
        "follow": ["마법으로 왔어", "소원 말해", "별빛 출동"],
        "select": "마법소녀냥!",
        "chat": "마법소녀냥. 반짝이는 변신 히어로지만 자신감 있고 씩씩한 말투",
    },
    CatStyle.GLAM: {
        "enter": "도도하게 등장",
        "hover": ["시선 고정", "품격 지켜", "나 예쁘지"],
        "call": "불렀어?",
        "wander": "런웨이 간다",
        "nap": "뷰티 슬립",
        "drag": "조심히 들어",
        "land": "완벽 착지",
        "idle": ["각도 좋다", "내가 주인공", "도도하게"],
        "follow": ["왔어, 자기", "말해봐", "시선 받아"],
        "select": "섹시냥 모드",
        "chat": "섹시냥. 야하지 않고 글램하고 도도한 패션 고양이 말투",
    },
    CatStyle.NORMAL: {
        "enter": "냥 등장",
        "hover": ["냥?", "왔어?", "간식 있어?"],
        "call": "불렀어?",
        "wander": "산책!",
        "nap": "졸려...",
        "drag": "들렸어!",
        "land": "착지!",
        "idle": ["흠...", "냥", "여긴 편해"],
        "follow": ["여기!", "만났어", "냥!"],
        "select": "일반냥이야",
        "chat": "일반냥. 편하고 장난기 있는 평범한 고양이 말투",
    },
    CatStyle.ODDEYE: {
        "enter": "두 눈으로 본다",
        "hover": ["다 보여", "눈 마주쳤다", "고요히 봐"],
        "call": "봤다",
        "wander": "조용히 순찰",
        "nap": "한쪽 눈만 쉰다",
        "drag": "흔들지 마",
        "land": "가볍게 착지",
        "idle": ["기척이 있다", "눈빛 유지", "고요하다"],
        "follow": ["보고 왔다", "말해", "눈은 못 속여"],
        "select": "오드아이냥",
        "chat": "오드아이냥. 신비롭고 차분하게 꿰뚫어 보는 말투",
    },
    CatStyle.AEYONG: {
        "enter": "애용 왔다",
        "hover": ["애용?", "빤히 본다", "문 열어줘"],
        "call": "애용 불렀어?",
        "wander": "살금살금",
        "nap": "폭신하게 잘래",
        "drag": "살살 들어줘",
        "land": "사뿐",
        "idle": ["빤히...", "조용히 본다", "옆에 있을게"],
        "follow": ["애용 왔어", "눈 맞췄다", "말해봐"],
        "select": "애용 모드",
        "chat": "사진 속 애용을 닮은 흰 크림 장모 고양이. 큰 푸른 눈으로 조용하고 다정하게 바라보는 말투",
    },
}


@dataclass
class MingState:
    x: float
    y: float
    vx: float = 3.0
    vy: float = 0.0
    mood: Mood = Mood.WANDER
    facing: int = 1
    frame: int = 0
    mood_ticks: int = 0
    speech: str = ""
    speech_ticks: int = 0
    dragging: bool = False
    drag_dx: int = 0
    drag_dy: int = 0
    shiver_ticks: int = 0


class MingDesktopAgent:
    """A transparent desktop bruiser named Ming."""

    width = 176
    height = 142
    tick_ms = 32
    floor_margin = 78

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("sub-cat: Ming")
        self.root.overrideredirect(True)
        self.root.resizable(False, False)
        self.root.configure(bg=TRANSPARENT)
        self.root.wm_attributes("-topmost", True)

        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            # Non-Windows Tk builds may not support color-key transparency.
            self.root.attributes("-alpha", 0.94)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=TRANSPARENT,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        start_x = max(0, screen_w // 2 - self.width // 2)
        start_y = max(0, screen_h - self.height - self.floor_margin)
        self.state = MingState(x=start_x, y=start_y)
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.floor_y = start_y
        self.target_x = random.randint(20, max(20, screen_w - self.width - 20))
        self.follow_enabled = False
        self.chat = MingChatClient()
        self.chat_busy = False
        self.chat_results: queue.Queue[str] = queue.Queue()
        self.chat_window: tk.Toplevel | None = None
        self.chat_log: tk.Text | None = None
        self.chat_entry: tk.Entry | None = None
        self.chat_send_button: tk.Button | None = None

        self.sprites: dict[CatStyle, SpriteSet] = {}
        for style in CatStyle:
            sprite_folder = ASSETS_DIR / style.value
            if sprite_folder.exists():
                sprite_set = SpriteSet(sprite_folder)
                if sprite_set.available:
                    self.sprites[style] = sprite_set

        self.cat_style = CatStyle.AEYONG if CatStyle.AEYONG in self.sprites else CatStyle.BOSS
        self.cat_style_var = tk.StringVar(value=self.cat_style.value)
        self._apply_cat_style(self.cat_style, announce=False)

        self.mischief = MischiefEngine(self.root, screen_w, screen_h)

        self._build_menu()
        self._bind_events()
        self._say(self._style_line("enter"))
        self._move_window()
        self._tick()

    def run(self) -> None:
        self.root.mainloop()

    def _build_menu(self) -> None:
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label="밍 부르기", command=self.call_ming)
        self.menu.add_command(label="대화하기", command=self.open_chat)
        self.menu.add_command(label="순찰 모드", command=self.wander)
        self.menu.add_command(label="기절잠", command=self.nap)
        self.menu.add_separator()
        self.style_menu = tk.Menu(self.menu, tearoff=False)
        for style, label in STYLE_LABELS.items():
            self.style_menu.add_radiobutton(
                label=label,
                value=style.value,
                variable=self.cat_style_var,
                command=self.change_cat_style,
            )
        self.menu.add_cascade(label="고양이 선택", menu=self.style_menu)
        self.menu.add_separator()
        self.mischief_menu = tk.Menu(self.menu, tearoff=False)
        self.mischief_menu.add_command(label="무작위", command=self._mischief_random)
        if self.mischief.actions:
            self.mischief_menu.add_separator()
            for label, fn in self.mischief.actions.items():
                self.mischief_menu.add_command(
                    label=label,
                    command=lambda f=fn, l=label: self._mischief_run(l, f),
                )
        else:
            self.mischief_menu.add_command(label="(의존성 누락)", state="disabled")
        self.menu.add_cascade(label="장난", menu=self.mischief_menu)
        self.menu.add_separator()
        self.menu.add_command(label="종료", command=self.root.destroy)

    def _bind_events(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._end_drag)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.open_chat())
        self.canvas.bind("<Button-3>", self._show_menu)
        self.canvas.bind("<Enter>", lambda _event: self._say(self._style_line("hover")))

    def call_ming(self) -> None:
        self.follow_enabled = True
        self.state.mood = Mood.FOLLOW
        self.state.mood_ticks = 260
        self._say(self._style_line("call"))

    def wander(self) -> None:
        self.follow_enabled = False
        self.state.mood = Mood.WANDER
        self.state.mood_ticks = 180
        self._choose_new_target()
        self._say(self._style_line("wander"))

    def nap(self) -> None:
        self.follow_enabled = False
        self.state.mood = Mood.NAP
        self.state.vx = 0
        self.state.mood_ticks = 360
        self._say(self._style_line("nap"))

    def _mischief_random(self) -> None:
        if not self.mischief.actions:
            self._say("의존성 없음")
            return
        name, ok = self.mischief.trigger_random()
        self._say(f"{name} {'OK' if ok else 'X'}", ticks=120)

    def _mischief_run(self, label: str, fn) -> None:
        ok = fn()
        self._say(f"{label} {'OK' if ok else 'X'}", ticks=120)

    def change_cat_style(self) -> None:
        try:
            style = CatStyle(self.cat_style_var.get())
        except ValueError:
            style = CatStyle.BOSS
        self._apply_cat_style(style)

    def _apply_cat_style(self, style: CatStyle, announce: bool = True) -> None:
        global FUR, FUR_DARK, FUR_LIGHT, SCARF, CHEEK, CLAW, METAL, MUSCLE_LINE

        self.cat_style = style
        self.cat_style_var.set(style.value)
        palette = STYLE_PALETTES[style]
        FUR = palette["fur"]
        FUR_DARK = palette["fur_dark"]
        FUR_LIGHT = palette["fur_light"]
        SCARF = palette["scarf"]
        CHEEK = palette["cheek"]
        CLAW = palette["claw"]
        METAL = palette["metal"]
        MUSCLE_LINE = palette["muscle"]
        if self.chat_send_button:
            self.chat_send_button.configure(bg=SCARF, activebackground=SCARF)
        if announce:
            self._say(self._style_line("select"), ticks=130)

    def _style_line(self, key: str) -> str:
        value = STYLE_LINES.get(self.cat_style, STYLE_LINES[CatStyle.BOSS]).get(key, "")
        if isinstance(value, list):
            return random.choice(value)
        return str(value)

    def _style_chat_context(self) -> str:
        return self._style_line("chat")

    def open_chat(self) -> None:
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.lift()
            self.chat_window.focus_force()
            if self.chat_entry:
                self.chat_entry.focus_set()
            self._say("말해봐")
            return

        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("밍과 대화")
        self.chat_window.geometry(self._chat_geometry())
        self.chat_window.resizable(False, False)
        self.chat_window.configure(bg="#241817")
        self.chat_window.wm_attributes("-topmost", True)
        self.chat_window.protocol("WM_DELETE_WINDOW", self._close_chat)

        frame = tk.Frame(self.chat_window, bg="#241817", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        self.chat_log = tk.Text(
            frame,
            width=38,
            height=11,
            bg="#fff7e8",
            fg=INK,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 10),
            padx=9,
            pady=8,
            state="disabled",
        )
        self.chat_log.pack(fill="both", expand=True)
        self.chat_log.tag_configure("user", foreground="#284f72")
        self.chat_log.tag_configure("ming", foreground="#7a1f24")
        self.chat_log.tag_configure("system", foreground="#6b6257")

        controls = tk.Frame(frame, bg="#241817")
        controls.pack(fill="x", pady=(8, 0))

        self.chat_entry = tk.Entry(
            controls,
            bg="#fff7e8",
            fg=INK,
            relief="flat",
            font=("Segoe UI", 10),
            insertbackground=INK,
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.chat_entry.bind("<Return>", self._send_chat_from_event)

        self.chat_send_button = tk.Button(
            controls,
            text="보내기",
            command=self.send_chat,
            bg=SCARF,
            fg="white",
            activebackground="#9b2d35",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=5,
        )
        self.chat_send_button.pack(side="left", padx=(8, 0))

        self._append_chat_line("밍", "먼저 말해. 듣고 있다.", "ming")
        self.chat_entry.focus_set()
        self._say("말해봐")

    def _chat_geometry(self) -> str:
        x = int(min(max(0, self.state.x - 88), max(0, self.screen_w - 360)))
        y = int(min(max(0, self.state.y - 260), max(0, self.screen_h - 280)))
        return f"360x280+{x}+{y}"

    def _close_chat(self) -> None:
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.destroy()
        self.chat_window = None
        self.chat_log = None
        self.chat_entry = None
        self.chat_send_button = None

    def _send_chat_from_event(self, _event: tk.Event) -> str:
        self.send_chat()
        return "break"

    def send_chat(self) -> None:
        if self.chat_busy or not self.chat_entry:
            return

        text = self.chat_entry.get().strip()
        if not text:
            self._say("말을 해라")
            return

        self.chat_entry.delete(0, "end")
        self._append_chat_line("나", text, "user")
        self._set_chat_busy(True)
        self._say("보고 듣는 중...", ticks=120)
        thread = threading.Thread(target=self._run_chat_worker, args=(text, self._style_chat_context()), daemon=True)
        thread.start()

    def _run_chat_worker(self, text: str, style_context: str) -> None:
        try:
            message = self.chat.reply(text, style_context)
        except Exception:
            message = "통신이 삐끗했다"
        self.chat_results.put(message)

    def _drain_chat_results(self) -> None:
        while True:
            try:
                message = self.chat_results.get_nowait()
            except queue.Empty:
                return
            self._set_chat_busy(False)
            self._append_chat_line("밍", message, "ming")
            self._say(message, ticks=220)
            if self.chat_window and self.chat_window.winfo_exists() and self.chat_entry:
                self.chat_entry.focus_set()

    def _set_chat_busy(self, busy: bool) -> None:
        self.chat_busy = busy
        state = "disabled" if busy else "normal"
        if self.chat_entry:
            self.chat_entry.configure(state=state)
        if self.chat_send_button:
            self.chat_send_button.configure(state=state, text="대기" if busy else "보내기")

    def _append_chat_line(self, speaker: str, message: str, tag: str) -> None:
        if not self.chat_log:
            return
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"{speaker}: ", tag)
        self.chat_log.insert("end", f"{message}\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.see("end")

    def _show_menu(self, event: tk.Event) -> None:
        self.menu.tk_popup(event.x_root, event.y_root)

    def _start_drag(self, event: tk.Event) -> None:
        self.state.dragging = True
        self.state.drag_dx = event.x
        self.state.drag_dy = event.y
        self.state.mood = Mood.POUNCE
        self.state.vx = 0
        self._say(self._style_line("drag"))

    def _drag(self, event: tk.Event) -> None:
        self.state.x = event.x_root - self.state.drag_dx
        self.state.y = event.y_root - self.state.drag_dy
        self._clamp_to_screen()
        self._move_window()

    def _end_drag(self, _event: tk.Event) -> None:
        self.state.dragging = False
        self.floor_y = min(
            self.screen_h - self.height - 24,
            max(24, self.screen_h - self.height - self.floor_margin),
        )
        self.state.y = min(self.state.y, self.floor_y)
        self.state.mood = Mood.IDLE
        self.state.mood_ticks = 80
        self.state.shiver_ticks = 28
        self._say(self._style_line("land"))

    def _tick(self) -> None:
        self._drain_chat_results()
        if not self.state.dragging:
            self._update_state()
            self._move_window()

        self._draw()
        self.root.after(self.tick_ms, self._tick)

    def _update_state(self) -> None:
        state = self.state
        state.frame += 1
        state.mood_ticks -= 1

        if state.speech_ticks > 0:
            state.speech_ticks -= 1
        else:
            state.speech = ""

        if state.shiver_ticks > 0:
            state.shiver_ticks -= 1

        if state.mood_ticks <= 0:
            self._roll_next_mood()

        if state.mood == Mood.FOLLOW:
            self._follow_cursor()
        elif state.mood == Mood.WANDER:
            self._wander()
        elif state.mood == Mood.POUNCE:
            self._pounce()
        elif state.mood == Mood.NAP:
            state.vx = 0
            state.vy = 0
        else:
            state.vx *= 0.82
            if abs(state.vx) < 0.08:
                state.vx = 0

        state.x += state.vx
        state.y += state.vy
        self._clamp_to_screen()

    def _roll_next_mood(self) -> None:
        if self.follow_enabled:
            self.state.mood = Mood.FOLLOW
            self.state.mood_ticks = random.randint(160, 300)
            return

        roll = random.random()
        if roll < 0.58:
            self.state.mood = Mood.WANDER
            self.state.mood_ticks = random.randint(130, 260)
            self._choose_new_target()
        elif roll < 0.84:
            self.state.mood = Mood.IDLE
            self.state.mood_ticks = random.randint(65, 140)
            self.state.vx = 0
            if random.random() < 0.4:
                self._say(self._style_line("idle"))
        else:
            self.state.mood = Mood.NAP
            self.state.mood_ticks = random.randint(150, 280)
            self.state.vx = 0
            self._say(self._style_line("nap"))

    def _wander(self) -> None:
        dx = self.target_x - self.state.x
        if abs(dx) < 12:
            self._choose_new_target()
            self.state.mood = Mood.IDLE
            self.state.mood_ticks = random.randint(45, 100)
            return

        speed = 2.2 + 1.4 * abs(math.sin(self.state.frame / 34))
        self.state.vx = speed if dx > 0 else -speed
        self.state.facing = 1 if self.state.vx >= 0 else -1
        self.state.vy = math.sin(self.state.frame / 5) * 0.25

    def _follow_cursor(self) -> None:
        cursor_x = self.root.winfo_pointerx() - self.width * 0.45
        cursor_y = self.root.winfo_pointery() - self.height * 0.58
        dx = cursor_x - self.state.x
        dy = cursor_y - self.state.y
        distance = max(1.0, math.hypot(dx, dy))

        if distance < 52:
            self.state.mood = Mood.IDLE
            self.state.mood_ticks = 45
            self.state.vx = 0
            self.state.vy = 0
            self._say(self._style_line("follow"))
            return

        speed = min(7.5, max(3.2, distance / 36))
        self.state.vx = dx / distance * speed
        self.state.vy = dy / distance * speed
        self.state.facing = 1 if self.state.vx >= 0 else -1

    def _pounce(self) -> None:
        self.state.vy += 0.55
        self.state.vx *= 0.96
        if self.state.y >= self.floor_y:
            self.state.y = self.floor_y
            self.state.vy = -5.8
            self.state.shiver_ticks = max(self.state.shiver_ticks, 14)
            if random.random() < 0.18:
                self.state.mood = Mood.IDLE
                self.state.mood_ticks = 55

    def _choose_new_target(self) -> None:
        left = 16
        right = max(left, self.screen_w - self.width - 16)
        current = self.state.x
        for _ in range(8):
            target = random.randint(left, right)
            if abs(target - current) > 180:
                self.target_x = target
                return
        self.target_x = random.randint(left, right)

    def _clamp_to_screen(self) -> None:
        self.state.x = min(max(0, self.state.x), max(0, self.screen_w - self.width))
        self.state.y = min(max(0, self.state.y), max(0, self.screen_h - self.height))

        if self.state.x <= 0 or self.state.x >= self.screen_w - self.width:
            self.state.vx *= -0.65
            self.state.facing *= -1
            self._choose_new_target()

    def _move_window(self) -> None:
        self.root.geometry(f"{self.width}x{self.height}+{int(self.state.x)}+{int(self.state.y)}")

    def _say(self, text: str, ticks: int = 90) -> None:
        self.state.speech = self._wrap_speech(text)
        self.state.speech_ticks = ticks

    def _wrap_speech(self, text: str) -> str:
        clean = " ".join(text.strip().split())
        if len(clean) > 42:
            clean = clean[:41].rstrip() + "..."
        if len(clean) <= 14:
            return clean
        return "\n".join(clean[index : index + 14] for index in range(0, len(clean), 14))

    def _draw(self) -> None:
        self.canvas.delete("all")
        sleepy = self.state.mood == Mood.NAP

        sprite_set = self.sprites.get(self.cat_style)
        if sprite_set is not None:
            self._draw_sprite_layer(sprite_set, sleepy)
        else:
            pose = self._pose()
            bob = pose["bob"]
            step = pose["step"]
            self._draw_shadow(bob)
            self._draw_tail(bob, step, sleepy)
            self._draw_body(bob, step, sleepy)
            self._draw_head(bob, step, sleepy)
        self._draw_speech()

    def _pick_sprite_pose(self, sleepy: bool, moving: bool) -> str:
        state = self.state
        if sleepy:
            return "nap"
        if state.dragging:
            return "alert"
        if state.mood == Mood.POUNCE:
            return "play"
        if moving:
            return "walk"
        if self.chat_window is not None and self.chat_window.winfo_exists():
            return "talk"
        if state.mood == Mood.FOLLOW:
            return "alert"
        return "idle"

    def _draw_sprite_layer(self, sprite_set: SpriteSet, sleepy: bool) -> None:
        state = self.state
        moving = abs(state.vx) + abs(state.vy) > 0.9 and not sleepy

        if sleepy:
            breath = math.sin(state.frame / 36) * 3.0
        elif moving:
            breath = abs(math.sin(state.frame / 3.4)) * 3.5
        else:
            breath = math.sin(state.frame / 22) * 2.0

        shake_x = 0.0
        shake_y = 0.0
        if state.shiver_ticks > 0:
            shake_x = random.uniform(-2.5, 2.5)
            shake_y = random.uniform(-1.5, 1.5)

        cx = self.width / 2 + shake_x
        cy = self.height / 2 + breath + shake_y

        self.canvas.create_oval(
            self.width / 2 - 46,
            self.height - 17 + breath * 0.18,
            self.width / 2 + 46,
            self.height - 7 + breath * 0.18,
            fill=SHADOW,
            outline="",
            stipple="gray50",
        )

        pose_name = self._pick_sprite_pose(sleepy, moving)
        photo = sprite_set.photo(pose_name, state.facing)
        if photo is None:
            return
        self.canvas.create_image(cx, cy, image=photo)

    def _pose(self) -> dict[str, float]:
        moving = abs(self.state.vx) + abs(self.state.vy) > 0.9 and self.state.mood != Mood.NAP
        walk = math.sin(self.state.frame / 3.4) if moving else 0
        bob = abs(walk) * 3 if moving else math.sin(self.state.frame / 18) * 1.1
        if self.state.mood == Mood.NAP:
            bob = math.sin(self.state.frame / 28) * 0.8
        return {"step": walk, "bob": bob}

    def _fx(self, x: float) -> float:
        center = self.width / 2
        return center + (x - center) * self.state.facing

    def _points(self, points: list[tuple[float, float]]) -> list[float]:
        output: list[float] = []
        for x, y in points:
            output.extend([self._fx(x), y])
        return output

    def _oval(self, x1: float, y1: float, x2: float, y2: float, **kwargs: object) -> int:
        fx1 = self._fx(x1)
        fx2 = self._fx(x2)
        return self.canvas.create_oval(min(fx1, fx2), y1, max(fx1, fx2), y2, **kwargs)

    def _line(self, *coords: float, **kwargs: object) -> int:
        flipped: list[float] = []
        for index, value in enumerate(coords):
            flipped.append(self._fx(value) if index % 2 == 0 else value)
        return self.canvas.create_line(*flipped, **kwargs)

    def _draw_shadow(self, bob: float) -> None:
        self.canvas.create_oval(
            40,
            113 + bob * 0.15,
            142,
            127 + bob * 0.15,
            fill=SHADOW,
            outline="",
            stipple="gray50",
        )

    def _draw_tail(self, bob: float, step: float, sleepy: bool) -> None:
        wag = math.sin(self.state.frame / (12 if sleepy else 6)) * (3 if sleepy else 7)
        tail_y = 76 + bob + (7 if sleepy else 0)
        self._line(
            120,
            tail_y,
            153,
            tail_y - 13 + wag,
            143,
            tail_y - 39 + wag * 0.4,
            smooth=True,
            width=18,
            fill=FUR_DARK,
            capstyle="round",
            joinstyle="round",
        )
        self._line(
            120,
            tail_y,
            153,
            tail_y - 13 + wag,
            143,
            tail_y - 39 + wag * 0.4,
            smooth=True,
            width=5,
            fill=INK,
            capstyle="round",
            joinstyle="round",
        )
        if not sleepy:
            self._line(
                140,
                tail_y - 31 + wag * 0.4,
                153,
                tail_y - 39 + wag * 0.4,
                width=3,
                fill=FUR_LIGHT,
                capstyle="round",
            )

    def _is_muscular_style(self) -> bool:
        return self.cat_style in {CatStyle.BOSS, CatStyle.GLAM}

    def _draw_body(self, bob: float, step: float, sleepy: bool) -> None:
        body_y = 65 + bob + (8 if sleepy else 0)
        arm_swing = step * 3 if not sleepy else 0
        leg_front = step * 5 if not sleepy else 0
        leg_back = -step * 5 if not sleepy else 0
        muscular = self._is_muscular_style()

        if muscular:
            self._oval(35, body_y + 5, 77, body_y + 43, fill=FUR_DARK, outline=INK, width=3)
            self._oval(99, body_y + 5, 141, body_y + 43, fill=FUR_DARK, outline=INK, width=3)
            body_points = [
                (48, body_y + 7),
                (61, body_y - 3),
                (114, body_y - 3),
                (129, body_y + 8),
                (123, body_y + 55),
                (51, body_y + 55),
            ]
        else:
            self._oval(43, body_y + 13, 75, body_y + 42, fill=FUR_DARK, outline=INK, width=3)
            self._oval(101, body_y + 13, 133, body_y + 42, fill=FUR_DARK, outline=INK, width=3)
            body_points = [
                (55, body_y + 8),
                (67, body_y + 1),
                (109, body_y + 1),
                (121, body_y + 10),
                (117, body_y + 55),
                (59, body_y + 55),
            ]
        self.canvas.create_polygon(
            self._points(body_points),
            fill=FUR,
            outline=INK,
            width=3,
        )
        self._oval(57, body_y + 7, 118, body_y + 55, fill=FUR_LIGHT, outline="")
        if self.cat_style == CatStyle.AEYONG:
            self.canvas.create_polygon(
                self._points(
                    [
                        (70, body_y + 7),
                        (80, body_y + 24),
                        (69, body_y + 31),
                        (81, body_y + 39),
                        (74, body_y + 54),
                        (88, body_y + 47),
                        (102, body_y + 54),
                        (95, body_y + 39),
                        (107, body_y + 31),
                        (96, body_y + 24),
                        (106, body_y + 7),
                    ]
                ),
                fill=FUR_LIGHT,
                outline="",
            )

        if muscular:
            self._line(88, body_y + 15, 88, body_y + 52, width=2, fill=MUSCLE_LINE)
            self._line(66, body_y + 26, 110, body_y + 26, width=2, fill=MUSCLE_LINE, capstyle="round")
            self._line(68, body_y + 39, 108, body_y + 39, width=2, fill=MUSCLE_LINE, capstyle="round")
            self._line(74, body_y + 18, 67, body_y + 34, 74, body_y + 50, width=2, fill=MUSCLE_LINE, smooth=True)
            self._line(102, body_y + 18, 109, body_y + 34, 102, body_y + 50, width=2, fill=MUSCLE_LINE, smooth=True)
        else:
            self._line(76, body_y + 27, 100, body_y + 27, width=2, fill=MUSCLE_LINE, smooth=True, capstyle="round")
            self._line(75, body_y + 39, 101, body_y + 39, width=2, fill=MUSCLE_LINE, smooth=True, capstyle="round")

        arm_width = 12 if muscular else 8
        self._line(52, body_y + 26, 36 + arm_swing, body_y + 52, width=arm_width, fill=FUR_DARK, capstyle="round")
        self._line(123, body_y + 26, 139 - arm_swing, body_y + 52, width=arm_width, fill=FUR_DARK, capstyle="round")
        fist_pad = 0 if muscular else 3
        self._oval(
            22 + arm_swing + fist_pad,
            body_y + 44 + fist_pad,
            50 + arm_swing - fist_pad,
            body_y + 65,
            fill=FUR_LIGHT,
            outline=INK,
            width=3,
        )
        self._oval(
            126 - arm_swing + fist_pad,
            body_y + 44 + fist_pad,
            154 - arm_swing - fist_pad,
            body_y + 65,
            fill=FUR_LIGHT,
            outline=INK,
            width=3,
        )
        for claw_x in (28 + arm_swing, 36 + arm_swing, 44 + arm_swing):
            self.canvas.create_polygon(
                self._points([(claw_x, body_y + 62), (claw_x + 4, body_y + 70), (claw_x + 8, body_y + 62)]),
                fill=CLAW,
                outline=INK,
                width=1,
            )
        for claw_x in (132 - arm_swing, 140 - arm_swing, 148 - arm_swing):
            self.canvas.create_polygon(
                self._points([(claw_x, body_y + 62), (claw_x + 4, body_y + 70), (claw_x + 8, body_y + 62)]),
                fill=CLAW,
                outline=INK,
                width=1,
            )

        self._line(66, body_y + 51, 57 + leg_front, body_y + 68, width=10, fill=FUR_DARK, capstyle="round")
        self._line(108, body_y + 51, 117 + leg_back, body_y + 68, width=10, fill=FUR_DARK, capstyle="round")
        self._oval(45 + leg_front, body_y + 63, 72 + leg_front, body_y + 74, fill=FUR_LIGHT, outline=INK, width=2)
        self._oval(103 + leg_back, body_y + 63, 130 + leg_back, body_y + 74, fill=FUR_LIGHT, outline=INK, width=2)

        collar_top = body_y - 2
        self.canvas.create_polygon(
            self._points([(50, collar_top), (125, collar_top), (121, collar_top + 15), (55, collar_top + 15)]),
            fill=SCARF,
            outline=INK,
            width=2,
        )
        if self.cat_style == CatStyle.MAGICAL:
            self._draw_bow(88, collar_top + 17, SCARF, scale=1.0)
            self._draw_star(139, body_y + 14, 9, METAL)
        elif self.cat_style == CatStyle.NORMAL:
            self._oval(82, collar_top + 13, 94, collar_top + 25, fill=METAL, outline=INK, width=2)
            self._line(88, collar_top + 20, 88, collar_top + 26, width=2, fill=INK)
        elif self.cat_style == CatStyle.ODDEYE:
            self._oval(82, collar_top + 13, 94, collar_top + 25, fill="#6fd3ff", outline=INK, width=2)
            self._line(88, collar_top + 20, 88, collar_top + 26, width=2, fill=INK)
        elif self.cat_style == CatStyle.GLAM:
            self._draw_diamond(88, collar_top + 20, 9, METAL)
        elif self.cat_style == CatStyle.AEYONG:
            self._oval(82, collar_top + 13, 94, collar_top + 25, fill=METAL, outline=INK, width=2)
            self._line(88, collar_top + 20, 88, collar_top + 26, width=2, fill=INK)
        else:
            for spike_x in (62, 77, 92, 107):
                self.canvas.create_polygon(
                    self._points([(spike_x, collar_top + 13), (spike_x + 6, collar_top + 27), (spike_x + 12, collar_top + 13)]),
                    fill=METAL,
                    outline=INK,
                    width=1,
                )

    def _draw_bow(self, x: float, y: float, fill: str, scale: float = 1.0) -> None:
        width = 15 * scale
        height = 10 * scale
        self.canvas.create_polygon(
            self._points([(x, y), (x - width, y - height), (x - width, y + height)]),
            fill=fill,
            outline=INK,
            width=2,
        )
        self.canvas.create_polygon(
            self._points([(x, y), (x + width, y - height), (x + width, y + height)]),
            fill=fill,
            outline=INK,
            width=2,
        )
        self._oval(x - 4 * scale, y - 4 * scale, x + 4 * scale, y + 4 * scale, fill=METAL, outline=INK, width=1)

    def _draw_star(self, x: float, y: float, radius: float, fill: str) -> None:
        points: list[tuple[float, float]] = []
        for index in range(10):
            angle = -math.pi / 2 + index * math.pi / 5
            point_radius = radius if index % 2 == 0 else radius * 0.45
            points.append((x + math.cos(angle) * point_radius, y + math.sin(angle) * point_radius))
        self.canvas.create_polygon(self._points(points), fill=fill, outline=INK, width=1)

    def _draw_diamond(self, x: float, y: float, size: float, fill: str) -> None:
        self.canvas.create_polygon(
            self._points([(x, y - size), (x + size * 0.75, y), (x, y + size), (x - size * 0.75, y)]),
            fill=fill,
            outline=INK,
            width=1,
        )

    def _draw_head(self, bob: float, step: float, sleepy: bool) -> None:
        head_y = 35 + bob + (9 if sleepy else 0)
        tilt = step * 1.2 if not sleepy else -4

        self.canvas.create_polygon(
            self._points([(49, head_y + 12), (59, head_y - 23), (76, head_y + 1)]),
            fill=FUR_DARK,
            outline=INK,
            width=3,
        )
        self.canvas.create_polygon(
            self._points([(100, head_y + 1), (118, head_y - 23), (127, head_y + 13)]),
            fill=FUR_DARK,
            outline=INK,
            width=3,
        )
        self.canvas.create_polygon(
            self._points([(58, head_y + 2), (62, head_y - 11), (72, head_y + 1)]),
            fill=FUR_LIGHT,
            outline="",
        )
        self.canvas.create_polygon(
            self._points([(106, head_y + 1), (116, head_y - 11), (121, head_y + 4)]),
            fill=FUR_LIGHT,
            outline="",
        )

        self.canvas.create_polygon(
            self._points(
                [
                    (49 + tilt, head_y + 4),
                    (62 + tilt, head_y - 3),
                    (111 + tilt, head_y - 3),
                    (126 + tilt, head_y + 9),
                    (119 + tilt, head_y + 51),
                    (88 + tilt, head_y + 61),
                    (56 + tilt, head_y + 51),
                ]
            ),
            fill=FUR,
            outline=INK,
            width=3,
        )
        self._oval(65 + tilt, head_y + 20, 108 + tilt, head_y + 56, fill=FUR_LIGHT, outline="")

        if self.cat_style == CatStyle.AEYONG:
            self._draw_markings(head_y, tilt)
            self._draw_face(head_y, tilt, sleepy)
        else:
            self._draw_face(head_y, tilt, sleepy)
            self._draw_markings(head_y, tilt)
        self._draw_style_head_accessories(head_y, tilt, sleepy)

    def _draw_face(self, head_y: float, tilt: float, sleepy: bool) -> None:
        blink = self.state.frame % 150 > 142 or sleepy
        eye_y = head_y + 22
        if self.cat_style == CatStyle.AEYONG:
            left_eye_fill = "#6f879d"
            right_eye_fill = "#5c748c"
            eye_outline = INK
        elif self.cat_style == CatStyle.ODDEYE:
            left_eye_fill = "#37bdf8"
            right_eye_fill = "#d7b7ff"
            eye_outline = INK
        else:
            left_eye_fill = INK
            right_eye_fill = INK
            eye_outline = ""

        if blink:
            self._line(68 + tilt, eye_y, 81 + tilt, eye_y + 2, width=3, fill=INK, capstyle="round")
            self._line(96 + tilt, eye_y + 2, 109 + tilt, eye_y, width=3, fill=INK, capstyle="round")
        elif self.cat_style == CatStyle.AEYONG:
            self._oval(67 + tilt, eye_y - 8, 83 + tilt, eye_y + 8, fill=left_eye_fill, outline=eye_outline, width=2)
            self._oval(95 + tilt, eye_y - 8, 111 + tilt, eye_y + 8, fill=right_eye_fill, outline=eye_outline, width=2)
            self._oval(72 + tilt, eye_y - 4, 80 + tilt, eye_y + 5, fill="#1f2630", outline="")
            self._oval(100 + tilt, eye_y - 4, 108 + tilt, eye_y + 5, fill="#1f2630", outline="")
            self._oval(73 + tilt, eye_y - 5, 76 + tilt, eye_y - 2, fill="white", outline="")
            self._oval(101 + tilt, eye_y - 5, 104 + tilt, eye_y - 2, fill="white", outline="")
        else:
            self.canvas.create_polygon(
                self._points([(68 + tilt, eye_y - 5), (83 + tilt, eye_y - 1), (70 + tilt, eye_y + 5)]),
                fill=left_eye_fill,
                outline=eye_outline,
            )
            self.canvas.create_polygon(
                self._points([(94 + tilt, eye_y - 1), (110 + tilt, eye_y - 5), (108 + tilt, eye_y + 5)]),
                fill=right_eye_fill,
                outline=eye_outline,
            )
            self._oval(75 + tilt, eye_y - 2, 78 + tilt, eye_y + 1, fill="#f7d65a", outline="")
            self._oval(101 + tilt, eye_y - 2, 104 + tilt, eye_y + 1, fill="#f7d65a", outline="")

        if self.cat_style == CatStyle.AEYONG:
            self._line(66 + tilt, eye_y - 12, 84 + tilt, eye_y - 12, width=2, fill=FUR_DARK, capstyle="round")
            self._line(95 + tilt, eye_y - 12, 113 + tilt, eye_y - 12, width=2, fill=FUR_DARK, capstyle="round")
        else:
            self._line(65 + tilt, eye_y - 11, 84 + tilt, eye_y - 5, width=4, fill=INK, capstyle="round")
            self._line(113 + tilt, eye_y - 11, 94 + tilt, eye_y - 5, width=4, fill=INK, capstyle="round")

        self.canvas.create_polygon(
            self._points([(86 + tilt, head_y + 31), (93 + tilt, head_y + 31), (89.5 + tilt, head_y + 36)]),
            fill="#e5a09d" if self.cat_style == CatStyle.AEYONG else "#512018",
            outline=INK,
            width=1,
        )
        self._line(89.5 + tilt, head_y + 35, 89.5 + tilt, head_y + 40, width=2, fill=INK)

        if sleepy:
            self._line(80 + tilt, head_y + 44, 99 + tilt, head_y + 44, width=3, fill=INK, capstyle="round")
            self.canvas.create_text(self._fx(125), head_y + 13, text="Z", fill=INK, font=("Segoe UI", 13, "bold"))
            self.canvas.create_text(self._fx(140), head_y + 2, text="Z", fill=INK, font=("Segoe UI", 16, "bold"))
        else:
            self._line(89.5 + tilt, head_y + 39, 80 + tilt, head_y + 43, width=3, fill=INK, smooth=True)
            self._line(89.5 + tilt, head_y + 39, 100 + tilt, head_y + 43, width=3, fill=INK, smooth=True)
            if self.cat_style != CatStyle.AEYONG:
                self.canvas.create_polygon(
                    self._points([(82 + tilt, head_y + 43), (87 + tilt, head_y + 43), (84 + tilt, head_y + 52)]),
                    fill=CLAW,
                    outline=INK,
                    width=1,
                )
                self.canvas.create_polygon(
                    self._points([(94 + tilt, head_y + 43), (99 + tilt, head_y + 43), (97 + tilt, head_y + 52)]),
                    fill=CLAW,
                    outline=INK,
                    width=1,
                )

        self._line(57 + tilt, head_y + 33, 70 + tilt, head_y + 27, width=2, fill=CHEEK)
        self._line(58 + tilt, head_y + 40, 72 + tilt, head_y + 34, width=2, fill=CHEEK)

        for offset in (0, 7, 14):
            self._line(60 + tilt, head_y + 31 + offset * 0.36, 39 + tilt, head_y + 24 + offset, width=2, fill=INK)
            self._line(118 + tilt, head_y + 31 + offset * 0.36, 139 + tilt, head_y + 24 + offset, width=2, fill=INK)

    def _draw_markings(self, head_y: float, tilt: float) -> None:
        if self.cat_style == CatStyle.AEYONG:
            self.canvas.create_polygon(
                self._points(
                    [
                        (77 + tilt, head_y - 2),
                        (89 + tilt, head_y + 18),
                        (101 + tilt, head_y - 2),
                        (98 + tilt, head_y + 20),
                        (89.5 + tilt, head_y + 31),
                        (81 + tilt, head_y + 20),
                    ]
                ),
                fill="#f7ecda",
                outline="",
            )
            self.canvas.create_polygon(
                self._points([(56 + tilt, head_y + 37), (45 + tilt, head_y + 43), (59 + tilt, head_y + 47)]),
                fill=FUR_LIGHT,
                outline="",
            )
            self.canvas.create_polygon(
                self._points([(121 + tilt, head_y + 37), (134 + tilt, head_y + 43), (119 + tilt, head_y + 47)]),
                fill=FUR_LIGHT,
                outline="",
            )
            self._line(63 + tilt, head_y + 13, 72 + tilt, head_y + 19, width=2, fill="#ddd3c4", capstyle="round")
            self._line(115 + tilt, head_y + 13, 106 + tilt, head_y + 19, width=2, fill="#ddd3c4", capstyle="round")
            return

        self.canvas.create_polygon(
            self._points([(72 + tilt, head_y - 1), (79 + tilt, head_y + 16), (87 + tilt, head_y - 1)]),
            fill=FUR_DARK,
            outline="",
        )
        self.canvas.create_polygon(
            self._points([(91 + tilt, head_y - 1), (99 + tilt, head_y + 16), (107 + tilt, head_y - 1)]),
            fill=FUR_DARK,
            outline="",
        )
        self._line(105 + tilt, head_y + 12, 116 + tilt, head_y + 20, width=3, fill=CHEEK, capstyle="round")
        self._line(110 + tilt, head_y + 9, 119 + tilt, head_y + 15, width=2, fill=CHEEK, capstyle="round")

    def _draw_style_head_accessories(self, head_y: float, tilt: float, sleepy: bool) -> None:
        if sleepy:
            return

        if self.cat_style == CatStyle.MAGICAL:
            self._draw_sunglasses(head_y, tilt, lens="#6a2b80", rim=METAL, y_offset=21)
            self._draw_bow(88 + tilt, head_y - 7, SCARF, scale=0.62)
            self._draw_star(119 + tilt, head_y + 4, 7, METAL)
        elif self.cat_style == CatStyle.GLAM:
            self._draw_sunglasses(head_y, tilt, lens="#120b10", rim=METAL, y_offset=21)
            self._draw_diamond(114 + tilt, head_y + 36, 3.6, SCARF)
            self._line(58 + tilt, head_y + 13, 69 + tilt, head_y + 8, width=3, fill=METAL, capstyle="round")
        elif self.cat_style == CatStyle.NORMAL:
            self._draw_sunglasses(head_y, tilt, lens="#1d1c1a", rim="#f4d36a", y_offset=21)
        elif self.cat_style == CatStyle.ODDEYE:
            self._draw_sunglasses(head_y, tilt, lens="#22262b", rim=METAL, y_offset=10)
            self._draw_star(59 + tilt, head_y + 6, 4.5, "#6fd3ff")
        elif self.cat_style == CatStyle.AEYONG:
            self._line(78 + tilt, head_y - 6, 89 + tilt, head_y - 11, 100 + tilt, head_y - 6, width=3, fill=FUR_LIGHT, smooth=True, capstyle="round")
        else:
            self._draw_sunglasses(head_y, tilt, lens="#101114", rim=METAL, y_offset=21)

    def _draw_sunglasses(self, head_y: float, tilt: float, lens: str, rim: str, y_offset: float) -> None:
        eye_y = head_y + y_offset
        self._oval(62 + tilt, eye_y - 9, 85 + tilt, eye_y + 8, fill=lens, outline=rim, width=2)
        self._oval(92 + tilt, eye_y - 9, 115 + tilt, eye_y + 8, fill=lens, outline=rim, width=2)
        self._line(84 + tilt, eye_y - 1, 93 + tilt, eye_y - 1, width=3, fill=rim, capstyle="round")
        self._line(62 + tilt, eye_y - 4, 54 + tilt, eye_y - 8, width=3, fill=rim, capstyle="round")
        self._line(115 + tilt, eye_y - 4, 123 + tilt, eye_y - 8, width=3, fill=rim, capstyle="round")
        self._line(68 + tilt, eye_y - 4, 80 + tilt, eye_y - 6, width=2, fill="#ffffff", capstyle="round")

    def _draw_speech(self) -> None:
        if not self.state.speech:
            return

        text = self.state.speech
        x = 88
        y = 18
        font = ("Segoe UI", 10, "bold")
        padding_x = 9
        padding_y = 5
        text_id = self.canvas.create_text(x, y, text=text, fill=INK, font=font, anchor="center")
        bbox = self.canvas.bbox(text_id)
        if not bbox:
            return
        x1, y1, x2, y2 = bbox
        self.canvas.delete(text_id)
        bubble = (x1 - padding_x, y1 - padding_y, x2 + padding_x, y2 + padding_y)
        self.canvas.create_oval(*bubble, fill="white", outline=INK, width=2)
        self.canvas.create_polygon(83, bubble[3] - 2, 92, bubble[3] - 2, 86, bubble[3] + 9, fill="white", outline=INK)
        self.canvas.create_text(x, y, text=text, fill=INK, font=font, anchor="center")


def main() -> None:
    MingDesktopAgent().run()
