from __future__ import annotations

import base64
import ctypes
import os
import struct
import sys
import zlib
from ctypes import wintypes
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only without the dependency.
    OpenAI = None  # type: ignore[assignment]


SUBCAT_TITLE = "sub-cat: Ming"
DEFAULT_MODEL = "gpt-5.4-mini"


@dataclass(frozen=True)
class VisionConfig:
    model: str
    image_detail: str
    max_image_side: int
    auto_interval_seconds: int

    @classmethod
    def from_env(cls) -> "VisionConfig":
        image_detail = os.getenv("SUBCAT_OPENAI_IMAGE_DETAIL", "low")
        if image_detail not in {"low", "auto", "high"}:
            image_detail = "low"
        return cls(
            model=os.getenv("SUBCAT_OPENAI_MODEL", DEFAULT_MODEL),
            image_detail=image_detail,
            max_image_side=_env_int("SUBCAT_SCREEN_MAX_SIDE", 960, 320, 1600),
            auto_interval_seconds=_env_int("SUBCAT_AUTO_LOOK_SECONDS", 90, 20, 3600),
        )


class ScreenVisionClient:
    def __init__(self, config: VisionConfig | None = None) -> None:
        self.config = config or VisionConfig.from_env()

    def describe_screen(self) -> str:
        if OpenAI is None:
            return "openai 설치가 필요해"
        if not os.getenv("OPENAI_API_KEY"):
            return "API 키가 필요해"

        screenshot = capture_desktop_png_data_url(self.config.max_image_side)
        windows = describe_windows()
        prompt = _build_prompt(windows)

        client = OpenAI()
        response = client.responses.create(
            model=self.config.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": screenshot,
                            "detail": self.config.image_detail,
                        },
                    ],
                }
            ],
            max_output_tokens=80,
        )

        return normalize_cat_line(getattr(response, "output_text", ""))


def _build_prompt(window_summary: str) -> str:
    return (
        "너는 사용자의 바탕화면에서 순찰하는 근육질 보스 고양이 에이전트 '밍'이야.\n"
        "스크린샷과 창 제목을 보고 지금 상황에 맞는 말을 한국어로 딱 한 문장만 해.\n"
        "말투는 거칠고 짧지만 사용자를 지키는 편이어야 해. 28자 이하로 말해.\n"
        "사람을 해치겠다는 위협이나 혐오 표현은 하지 말고, 투덜대는 보스 느낌만 내.\n"
        "비밀번호, API 키, 인증코드, 개인정보처럼 민감해 보이는 내용은 절대 읽거나 반복하지 마.\n"
        "민감한 화면처럼 보이면 내용을 말하지 말고 '그 화면 조심해라'처럼 짧게 알려줘.\n"
        f"보이는 창 정보: {window_summary}"
    )


def normalize_cat_line(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return "별거 없군"
    if len(cleaned) > 42:
        return cleaned[:41].rstrip() + "..."
    return cleaned


def describe_windows(limit: int = 8) -> str:
    if sys.platform != "win32":
        return "창 제목을 가져올 수 없는 환경"

    try:
        active = _foreground_window_title()
        titles = _visible_window_titles(limit)
    except OSError:
        return "창 제목 확인 실패"

    active_part = active if active and active != SUBCAT_TITLE else "알 수 없음"
    title_part = ", ".join(titles) if titles else "제목 있는 창 없음"
    return f"활성 창: {active_part}. 보이는 창: {title_part}"


def capture_desktop_png_data_url(max_side: int = 960) -> str:
    if sys.platform != "win32":
        raise RuntimeError("Windows 화면 캡처만 지원해요")

    width, height, bgra = _capture_virtual_screen_bgra()
    out_width, out_height, rgb = _resize_bgra_to_rgb(width, height, bgra, max_side)
    png = _encode_png_rgb(out_width, out_height, rgb)
    encoded = base64.b64encode(png).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)


def _foreground_window_title() -> str:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    hwnd = user32.GetForegroundWindow()
    return _window_text(user32, hwnd)


def _visible_window_titles(limit: int) -> list[str]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    titles: list[str] = []
    ignored = {SUBCAT_TITLE, "Program Manager", "Windows Input Experience"}

    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    def callback(hwnd: wintypes.HWND, _lparam: wintypes.LPARAM) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _window_text(user32, hwnd)
        if len(titles) < limit and title and title not in ignored and not title.startswith("sub-cat"):
            titles.append(title)
        return True

    proc = enum_proc(callback)
    if not user32.EnumWindows(proc, 0) and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    return titles


def _window_text(user32: ctypes.WinDLL, hwnd: wintypes.HWND) -> str:
    if not hwnd:
        return ""
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    copied = user32.GetWindowTextW(hwnd, buffer, length + 1)
    if copied <= 0:
        return ""
    return buffer.value.strip()


class BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BitmapInfo(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BitmapInfoHeader),
        ("bmiColors", wintypes.DWORD * 3),
    ]


def _capture_virtual_screen_bgra() -> tuple[int, int, bytes]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    sm_xvirtualscreen = 76
    sm_yvirtualscreen = 77
    sm_cxvirtualscreen = 78
    sm_cyvirtualscreen = 79
    left = user32.GetSystemMetrics(sm_xvirtualscreen)
    top = user32.GetSystemMetrics(sm_yvirtualscreen)
    width = user32.GetSystemMetrics(sm_cxvirtualscreen)
    height = user32.GetSystemMetrics(sm_cyvirtualscreen)
    if width <= 0 or height <= 0:
        raise RuntimeError("화면 크기를 읽지 못했어")

    src_dc = user32.GetDC(None)
    if not src_dc:
        raise ctypes.WinError(ctypes.get_last_error())

    mem_dc = None
    bitmap = None
    old_obj = None
    try:
        mem_dc = gdi32.CreateCompatibleDC(src_dc)
        if not mem_dc:
            raise ctypes.WinError(ctypes.get_last_error())

        bitmap = gdi32.CreateCompatibleBitmap(src_dc, width, height)
        if not bitmap:
            raise ctypes.WinError(ctypes.get_last_error())

        old_obj = gdi32.SelectObject(mem_dc, bitmap)
        srccopy = 0x00CC0020
        captureblt = 0x40000000
        if not gdi32.BitBlt(mem_dc, 0, 0, width, height, src_dc, left, top, srccopy | captureblt):
            raise ctypes.WinError(ctypes.get_last_error())

        info = BitmapInfo()
        info.bmiHeader.biSize = ctypes.sizeof(BitmapInfoHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = -height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = 0

        buffer = ctypes.create_string_buffer(width * height * 4)
        dib_rgb_colors = 0
        scanlines = gdi32.GetDIBits(mem_dc, bitmap, 0, height, buffer, ctypes.byref(info), dib_rgb_colors)
        if scanlines != height:
            raise ctypes.WinError(ctypes.get_last_error())
        return width, height, buffer.raw
    finally:
        if old_obj and mem_dc:
            gdi32.SelectObject(mem_dc, old_obj)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if mem_dc:
            gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, src_dc)


def _resize_bgra_to_rgb(width: int, height: int, bgra: bytes, max_side: int) -> tuple[int, int, bytes]:
    scale = min(1.0, max_side / max(width, height))
    out_width = max(1, int(width * scale))
    out_height = max(1, int(height * scale))
    output = bytearray(out_width * out_height * 3)

    for out_y in range(out_height):
        src_y = min(height - 1, out_y * height // out_height)
        for out_x in range(out_width):
            src_x = min(width - 1, out_x * width // out_width)
            src_index = (src_y * width + src_x) * 4
            out_index = (out_y * out_width + out_x) * 3
            output[out_index] = bgra[src_index + 2]
            output[out_index + 1] = bgra[src_index + 1]
            output[out_index + 2] = bgra[src_index]

    return out_width, out_height, bytes(output)


def _encode_png_rgb(width: int, height: int, rgb: bytes) -> bytes:
    stride = width * 3
    rows = bytearray()
    for row in range(height):
        rows.append(0)
        start = row * stride
        rows.extend(rgb[start : start + stride])

    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind)
        checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
        return struct.pack("!I", len(payload)) + kind + payload + struct.pack("!I", checksum)

    header = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", header),
            chunk(b"IDAT", zlib.compress(bytes(rows), 6)),
            chunk(b"IEND", b""),
        ]
    )
