# 라이카 시그널 · 프로토타입

라이카시네마 관람 전 경험 '라이카 시그널'의 입력 → 분석 → 출력 검증용 웹 프로토타입.

- 노트북 카메라로 손글씨 카드를 읽고(Tesseract.js, 한국어)
- 기대 문장을 감정 결 6가지(위로 · 쉼 · 설렘 · 용기 · 그리움 · 영감) 퍼센티지로 나눈 뒤
- 가장 가까운 영화 대사를 골라 수신기에서 기록지로 출력합니다 (three.js).

## 실행 (Gemini 손글씨 인식 사용)
1. Google AI Studio 에서 API 키를 발급한다.
2. `.env.example` 을 복사해 `.env` 로 이름을 바꾸고 `GEMINI_API_KEY=` 뒤에 키를 넣는다. (`.env` 는 GitHub 에 올라가지 않음)
3. 이 폴더에서 실행한다.
```bash
python3 server.py
```
4. 브라우저에서 http://localhost:8000 을 연다.

키가 없거나 Gemini 연결이 실패하면 브라우저 OCR + 키워드 분석으로 자동 전환됩니다.

## GitHub Pages 주소에서 Gemini 쓰기
1. https://motionseo.github.io/laika-signal/ 을 연다.
2. 키보드 K 를 누르고 Gemini API 키를 붙여 넣는다.
3. 키는 그 브라우저(localStorage)에만 저장되고, Google 외 다른 곳으로 보내지지 않는다.
   다시 K 를 눌러 비워 두고 확인하면 삭제된다. 공용 컴퓨터에서는 시연 후 꼭 지울 것.

## 조작
- 송신기 클릭 / Space: 카드 인식 후 송신
- 카메라 화면 클릭 / C: 카메라 켜기·끄기
- T: 기대 문장 직접 입력
- 기록지 클릭 / Esc: 기록지 치우기
- K: Gemini API 키 입력·삭제 (이 브라우저에만 저장)

## 데이터
`index.html` 위쪽의 `DIALOGUES`(대사 후보)와 `EMOTIONS`(감정 키워드)를 고쳐 쓰면 됩니다.
`[ ]`로 표시된 대사는 자리표시이니 공식 예고편 · 배급사 자료의 실제 대사로 바꿔 주세요.
