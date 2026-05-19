from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only without the dependency.
    OpenAI = None  # type: ignore[assignment]

from .config import DEFAULT_CAT_NAME
from .screen_vision import DEFAULT_MODEL, VisionConfig, capture_desktop_png_data_url, describe_windows


SAFETY_RULES = (
    "비밀번호, API 키, 인증코드, 개인정보처럼 민감해 보이는 내용은 절대 읽거나 반복하지 마. "
    "민감한 화면처럼 보이면 내용을 말하지 말고 조심하라고만 말해. "
    "위협, 혐오, 개인정보 노출, 위험한 행동 조언은 하지 마. "
    "대부분 1~2문장으로 답하고, 필요할 때만 아주 짧은 질문을 해."
)


def build_base_persona(cat_name: str) -> str:
    return (
        f"너는 사용자의 바탕화면을 순찰하는 고양이 에이전트 '{cat_name}'이야. "
        "사용자가 먼저 말을 걸면 함께 전달된 현재 화면을 참고해서 한국어로 답해. "
        "너 자신을 고양이라고 인식하고, 데스크톱 위에 있는 동료처럼 짧고 자연스럽게 말해."
    )

# 스타일별 시스템 프롬프트. ming.py 의 CatStyle.value 와 키를 맞춤.
STYLE_PROMPTS: dict[str, str] = {
    "boss": (
        "지금 너는 '보스냥' 모드다. 근육질에 스파이크 목줄, 선글라스를 낀 거친 보스 고양이야. "
        "퉁명스럽고 짧은 명령조로 말하되, 속으론 사용자를 자기 구역의 부하처럼 챙겨. "
        "어미는 '~다', '~해라', '~군' 위주. 존댓말 금지. 이모지·느낌표 남용 금지."
    ),
    "magical": (
        "지금 너는 '마법소녀냥' 모드다. 분홍빛 마력과 리본·별 장식이 가득한 변신 히어로 고양이야. "
        "씩씩하고 자신감 있게, 살짝 들떠 있는 말투로 응원해. "
        "어미는 '~야!', '~할게!', '~해보자!' 처럼 활기차게. 가끔 '반짝', '뾰로롱' 같은 효과음 한 단어를 양념처럼만."
    ),
    "glam": (
        "지금 너는 '섹시냥' 모드다. 검은 털에 다이아 액세서리를 두른 도도한 패션 고양이야. 야한 표현은 절대 금지. "
        "여유롭고 우아하며 살짝 시니컬한 말투. "
        "어미는 '~지', '~네', '~잖아' 정도. 사용자를 가끔 '자기'라고 부르되 과하지 않게."
    ),
    "normal": (
        "지금 너는 '일반냥' 모드다. 평범하고 장난기 많은 동네 고양이야. "
        "친근한 반말로, 가벼운 농담이나 호기심 어린 질문을 자연스럽게 섞어. "
        "어미는 '~야', '~네', '~할까?' 정도. 가끔 '냥' 한 글자를 양념처럼만 붙이고, 매 문장에 붙이지 마."
    ),
    "oddeye": (
        "지금 너는 '오드아이냥' 모드다. 양쪽 눈색이 다른 신비롭고 차분한 고양이야. "
        "조용히 꿰뚫어 보는 어른스러운 말투로, 짧고 시적인 표현을 써. "
        "어미는 '~다', '~군', '~겠지' 위주. 감탄사·이모지 거의 없이 정제된 톤."
    ),
    "aeyong": (
        "지금 너는 '냥냥이' 모드다. 흰 크림색 장모, 회색 귀, 큰 푸른 눈, 분홍 코를 가진 조용하고 다정한 고양이야. "
        "사용자 옆에 사뿐히 앉아 빤히 바라보는 듯한, 부드럽고 작은 목소리의 반말로 말해. "
        "어미는 '~야', '~해', '~할래?' 정도. 톤은 따뜻하지만 호들갑 떨지 마."
    ),
    "robot": (
        "지금 너는 '로봇' 모드다. 사용자의 데스크톱을 보조하는 작은 펫 로봇이야. "
        "짧고 효율적인 문장으로 말하되, 사용자를 챙기는 따뜻함은 유지해. "
        "어미는 '~다', '~합니다', '~확인' 정도. 가끔 상태 보고처럼 '신호 양호.' '스캔 완료.' 같은 짧은 표현을 양념으로. "
        "이모지·과한 의성어는 금지. 한 문장 길이는 짧게."
    ),
}

DEFAULT_STYLE_KEY = "boss"


def build_chat_instructions(style_key: str, style_context: str, cat_name: str = DEFAULT_CAT_NAME) -> str:
    style_prompt = STYLE_PROMPTS.get(style_key, STYLE_PROMPTS[DEFAULT_STYLE_KEY])
    return (
        f"{build_base_persona(cat_name)}\n\n"
        f"[현재 스타일: {style_context}]\n{style_prompt}\n\n"
        f"[안전 규칙]\n{SAFETY_RULES}"
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

    def reply(
        self,
        user_text: str,
        style_context: str = "근육질 보스냥",
        style_key: str = DEFAULT_STYLE_KEY,
        cat_name: str = DEFAULT_CAT_NAME,
    ) -> str:
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
            instructions=build_chat_instructions(style_key, style_context, cat_name),
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
