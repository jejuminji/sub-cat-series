# sub-cat

<p align="center">
  <img src="assets/banner.png" alt="sub-cat banner: 마법소녀 · 로봇 · 냥냥이" width="720" />
</p>

<p align="center"><em>바탕화면에 사는 작은 펫 — 냥냥이 · 마법소녀 · 로봇</em></p>

OpenAI 비전 API로 사용자의 화면을 보고 짧게 말을 거는 투명 데스크톱 캐릭터입니다.

> **Windows 전용.** 화면 캡처와 투명 항상-위 창이 Windows API에 의존합니다.

## 시작

```powershell
pip install -r requirements.txt
python main.py
```

OpenAI API 키는 실행 후 우클릭 → `설정 > OpenAI API 키 설정...` 으로 입력하면 자동 저장됩니다.

## 조작

- **더블 클릭** — 대화 열기
- **왼쪽 드래그** — 이동
- **우클릭** — 메뉴 (캐릭터 선택 / 이름 바꾸기 / 설정 / 장난 / 종료)

## 설정 저장 위치

이름·API 키·캐릭터 선택은 `%APPDATA%\sub-cat\config.json` 에 저장되어 다음 실행에도 유지됩니다.

## 개인정보

메시지를 보낼 때마다 현재 화면이 캡처되어 OpenAI로 전송됩니다. 민감한 화면 위에서는 대화를 보내지 마세요. 채팅창 하단에도 같은 안내가 표시됩니다.

## License

[MIT](LICENSE)
