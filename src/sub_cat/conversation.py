from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only without the dependency.
    OpenAI = None  # type: ignore[assignment]

from .screen_vision import DEFAULT_MODEL, VisionConfig, capture_desktop_png_data_url, describe_windows


CHAT_INSTRUCTIONS_TEMPLATE = (
    "너는 사용자의 바탕화면을 순찰하는 고양이 에이전트 '밍'이야. "
    "현재 밍의 스타일은 {style_context}야. "
    "사용자가 먼저 말을 걸면 함께 전달된 현재 화면을 참고해서 한국어로 답해. "
    "선택된 스타일에 맞는 말투를 쓰되, 사용자를 챙기는 편이어야 해. "
    "너 자신을 고양이라고 인식하고, 데스크톱 위에 있는 동료처럼 짧고 자연스럽게 말해. "
    "비밀번호, API 키, 인증코드, 개인정보처럼 민감해 보이는 내용은 절대 읽거나 반복하지 마. "
    "민감한 화면처럼 보이면 내용을 말하지 말고 조심하라고만 말해. "
    "위협, 혐오, 개인정보 노출, 위험한 행동 조언은 하지 마. "
    "대부분 1~2문장으로 답하고, 필요할 때만 아주 짧은 질문을 해."
)


@dataclass(frozen=True)
class ChatConfig:
    model: str
    max_history_turns: int
    image_detail: str
    max_image_side: int

    @classmethod
    def from_env(cls) -> "ChatConfig":
        vision_config = VisionConfig.from_env()
        return cls(
            model=os.getenv("SUBCAT_OPENAI_MODEL", DEFAULT_MODEL),
            max_history_turns=_env_int("SUBCAT_CHAT_HISTORY_TURNS", 8, 0, 30),
            image_detail=vision_config.image_detail,
            max_image_side=vision_config.max_image_side,
        )


class MingChatClient:
    def __init__(self, config: ChatConfig | None = None) -> None:
        self.config = config or ChatConfig.from_env()
        self.history: list[tuple[str, str]] = []

    def reply(self, user_text: str, style_context: str = "근육질 보스냥") -> str:
        if OpenAI is None:
            return "openai부터 설치해라"
        if not os.getenv("OPENAI_API_KEY"):
            return "API 키부터 걸어라"

        clean_text = user_text.strip()
        if not clean_text:
            return "말을 해라"

        screen_context = self._capture_screen_context()
        client = OpenAI()
        response = client.responses.create(
            model=self.config.model,
            instructions=CHAT_INSTRUCTIONS_TEMPLATE.format(style_context=style_context),
            input=[
                {
                    "role": "user",
                    "content": self._build_content(clean_text, screen_context, style_context),
                }
            ],
            max_output_tokens=160,
        )
        answer = normalize_chat_reply(getattr(response, "output_text", ""))
        self.history.append((clean_text, answer))
        self._trim_history()
        return answer

    def clear(self) -> None:
        self.history.clear()

    def _capture_screen_context(self) -> tuple[str, str] | None:
        try:
            screenshot = capture_desktop_png_data_url(self.config.max_image_side)
            windows = describe_windows()
        except Exception:
            return None
        return screenshot, windows

    def _build_content(
        self,
        user_text: str,
        screen_context: tuple[str, str] | None,
        style_context: str,
    ) -> list[dict[str, str]]:
        content = [{"type": "input_text", "text": self._build_text_prompt(user_text, screen_context, style_context)}]
        if screen_context:
            screenshot, _windows = screen_context
            content.append(
                {
                    "type": "input_image",
                    "image_url": screenshot,
                    "detail": self.config.image_detail,
                }
            )
        return content

    def _build_text_prompt(
        self,
        user_text: str,
        screen_context: tuple[str, str] | None,
        style_context: str,
    ) -> str:
        recent = self.history[-self.config.max_history_turns :] if self.config.max_history_turns else []
        windows = screen_context[1] if screen_context else "화면 캡처 실패. 사용자의 말만 보고 답해."
        lines = [
            "이번 답변은 사용자가 대화창에서 메시지를 보낸 직후에만 생성된다.",
            f"현재 밍 스타일: {style_context}",
            f"현재 창 정보: {windows}",
        ]
        if not recent:
            lines.append(f"사용자: {user_text}")
            lines.append("밍:")
            return "\n".join(lines)

        lines.append("최근 대화:")
        for user, assistant in recent:
            lines.append(f"사용자: {user}")
            lines.append(f"밍: {assistant}")
        lines.append(f"사용자: {user_text}")
        lines.append("밍:")
        return "\n".join(lines)

    def _trim_history(self) -> None:
        if self.config.max_history_turns <= 0:
            self.history.clear()
            return
        overflow = len(self.history) - self.config.max_history_turns
        if overflow > 0:
            del self.history[:overflow]


def normalize_chat_reply(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return "뭐라 할 말이 없군"
    if len(cleaned) > 120:
        return cleaned[:119].rstrip() + "..."
    return cleaned


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return min(max(value, minimum), maximum)
