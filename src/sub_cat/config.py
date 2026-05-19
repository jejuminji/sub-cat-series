"""사용자가 바꾸는 영구 설정. 지금은 고양이 이름 한 키만 저장."""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_CAT_NAME = "밍"


def config_dir() -> Path:
    """Windows 표준 위치. APPDATA 가 없는 환경(테스트, 비-Windows)에선 홈 폴더로 폴백."""
    base = os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "sub-cat"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_user_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_user_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cat_name() -> str:
    name = (load_user_config().get("cat_name") or "").strip()
    return name or DEFAULT_CAT_NAME


def save_cat_name(name: str) -> None:
    cfg = load_user_config()
    cfg["cat_name"] = name.strip() or DEFAULT_CAT_NAME
    save_user_config(cfg)


def has_jongseong(ch: str) -> bool:
    """한글 마지막 글자에 받침이 있는지. 한글 음절은 0xAC00~0xD7A3."""
    if not ch:
        return False
    code = ord(ch[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def particle_gwa(name: str) -> str:
    """'밍' → '과', '두부' → '와'. 한글이 아닌 마지막 글자는 보수적으로 '와'."""
    return "과" if has_jongseong(name) else "와"
