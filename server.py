"""
라이카 시그널 로컬 서버

- 이 폴더의 웹페이지(index.html)를 http://localhost:8000 으로 열어 줍니다.
- 웹페이지가 보낸 카드 사진을 Google Gemini 에 보내
  손글씨 읽기 + 감정 결 분석 결과를 돌려줍니다.
- API 키는 이 컴퓨터의 .env 파일에만 둡니다 (웹페이지에는 들어가지 않음).

실행:  python3 server.py
필요:  같은 폴더의 .env 파일에  GEMINI_API_KEY=발급받은키
선택:  GEMINI_MODEL=모델이름   (기본값은 아래 DEFAULT_MODEL)
"""

import base64
import json
import os
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8000"))
DEFAULT_MODEL = "gemini-2.5-flash"
EMOTIONS = ["위로", "쉼", "설렘", "용기", "그리움", "영감"]


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

PROMPT = f"""이 사진은 영화관 관객이 손으로 쓴 카드입니다.
카드에는 보통 "이 영화가 나에게 ____ 영화였으면" 같은 문장이 적혀 있습니다.

1. 카드에 적힌 손글씨를 그대로 읽어 text 에 적으세요. 읽을 수 없으면 빈 문자열.
2. 빈칸에 해당하는 관객의 기대 부분만 wish 에 적으세요. (예: "다시 그림을 그리고 싶어지는")
3. 그 기대의 정서를 다음 6가지 감정 결로 나누어 합이 1이 되는 비율로 emotions 에 적으세요:
   {", ".join(EMOTIONS)}
   - 위로: 위안, 따뜻함, 치유   - 쉼: 휴식, 고요, 여유
   - 설렘: 기대, 두근거림, 즐거움   - 용기: 응원, 다시 시작, 힘
   - 그리움: 추억, 지난 시절, 사람   - 영감: 창작, 질문, 생각할 거리
글자가 없거나 카드가 아니면 text 와 wish 를 빈 문자열로, emotions 는 모두 0 으로 두세요.
반드시 JSON 만 출력하세요."""

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "text": {"type": "STRING"},
        "wish": {"type": "STRING"},
        "emotions": {
            "type": "OBJECT",
            "properties": {k: {"type": "NUMBER"} for k in EMOTIONS},
            "required": EMOTIONS,
        },
    },
    "required": ["text", "wish", "emotions"],
}


def ask_gemini(jpeg_b64):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": jpeg_b64}},
                {"text": PROMPT},
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_schema": SCHEMA,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    raw = data["candidates"][0]["content"]["parts"][0]["text"]
    out = json.loads(raw)
    emo = {k: max(0.0, float(out.get("emotions", {}).get(k, 0) or 0)) for k in EMOTIONS}
    total = sum(emo.values())
    out["emotions"] = {k: (v / total if total else 0.0) for k, v in emo.items()}
    out["weak"] = total == 0
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def send_json(self, code, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/status":
            return self.send_json(200, {"ai": bool(API_KEY), "model": MODEL})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/read":
            return self.send_json(404, {"error": "not found"})
        if not API_KEY:
            return self.send_json(503, {"error": ".env 에 GEMINI_API_KEY 가 없습니다"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n).decode("utf-8"))
            img = req.get("image", "")
            if "," in img:
                img = img.split(",", 1)[1]
            base64.b64decode(img, validate=True)
            return self.send_json(200, ask_gemini(img))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            print("Gemini 오류:", e.code, detail)
            return self.send_json(502, {"error": f"Gemini {e.code}", "detail": detail})
        except Exception as e:  # noqa: BLE001
            print("처리 오류:", e)
            return self.send_json(500, {"error": str(e)})


if __name__ == "__main__":
    print(f"라이카 시그널: http://localhost:{PORT}")
    print("AI 인식:", f"켜짐 ({MODEL})" if API_KEY else "꺼짐 — .env 에 GEMINI_API_KEY 를 넣으면 켜집니다")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
