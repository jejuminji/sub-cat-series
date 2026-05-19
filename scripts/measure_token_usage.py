"""Make one real chat call and print exact token usage.

Run once with OPENAI_API_KEY set:
    python scripts/measure_token_usage.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from src.sub_cat.conversation import CHAT_INSTRUCTIONS_TEMPLATE
from src.sub_cat.screen_vision import DEFAULT_MODEL, capture_desktop_png_data_url, describe_windows


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    model = os.getenv("SUBCAT_OPENAI_MODEL", DEFAULT_MODEL)
    detail = os.getenv("SUBCAT_OPENAI_IMAGE_DETAIL", "low")
    style_context = "사진 속 애용을 닮은 흰 크림 장모 고양이."

    print(f"model         = {model}")
    print(f"image detail  = {detail}")

    screenshot = capture_desktop_png_data_url(960)
    windows = describe_windows()
    prompt = (
        "이번 답변은 사용자가 대화창에서 메시지를 보낸 직후에만 생성된다.\n"
        f"현재 밍 스타일: {style_context}\n"
        f"현재 창 정보: {windows}\n"
        "사용자: 안녕\n밍:"
    )

    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=CHAT_INSTRUCTIONS_TEMPLATE.format(style_context=style_context),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": screenshot, "detail": detail},
                ],
            }
        ],
        max_output_tokens=160,
    )

    usage = getattr(response, "usage", None)
    print()
    print("=== 응답 ===")
    print(response.output_text)
    print()
    print("=== 사용량 ===")
    if usage is None:
        print("usage 정보 없음")
    else:
        print(usage)


if __name__ == "__main__":
    main()
