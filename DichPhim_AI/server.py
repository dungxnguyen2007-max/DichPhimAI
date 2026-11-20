#!/usr/bin/env python3
"""
Máy chủ nhỏ cho bản dịch trực tiếp từ âm thanh tab:
nhận đoạn âm thanh từ trang web -> Whisper nhận dạng tiếng Anh -> dịch sang tiếng Việt.
API key chỉ nằm trên máy chủ, không gửi ra trình duyệt.

Cách chạy:
    export OPENAI_API_KEY=sk-...          # Linux/macOS
    $env:OPENAI_API_KEY="sk-..."          # Windows PowerShell
    python3 server.py
Sau đó mở http://localhost:8000
"""
import base64
import json
import os
import re
import uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib import request, error

OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
STT_MODEL = os.environ.get("STT_MODEL", "whisper-1")
TRANSLATE_MODEL = os.environ.get("TRANSLATE_MODEL", "gpt-4o-mini")
PORT = int(os.environ.get("PORT", "8000"))
MAX_BODY = 12 * 1024 * 1024
PAGE = Path(__file__).resolve().parent / "index.html"

# Whisper hay "bịa" các câu này khi im lặng hoặc chỉ có nhạc nền
HALLUCINATIONS = re.compile(
    r"^\W*(thank you[ .!]*|thanks for watching[ .!]*|subtitles? by .*|\[.*\]|\(.*\)|♪.*)\W*$",
    re.I,
)


class UpstreamError(Exception):
    pass


def _post(path, body, content_type):
    if not API_KEY:
        raise UpstreamError("Chưa đặt biến môi trường OPENAI_API_KEY trên máy chủ.")
    req = request.Request(
        OPENAI_BASE + path,
        data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": content_type},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise UpstreamError(f"API lỗi {e.code}: {detail}")
    except error.URLError as e:
        raise UpstreamError(f"Không kết nối được API: {e.reason}")


def transcribe(audio, mime, prompt):
    """Gửi đoạn âm thanh lên Whisper (multipart/form-data)."""
    boundary = uuid.uuid4().hex
    ext = "mp4" if "mp4" in mime else "webm"
    fields = {"model": STT_MODEL, "language": "en", "response_format": "json"}
    if prompt:
        fields["prompt"] = prompt
    parts = []
    for k, v in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8")
        )
    parts.append(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="chunk.{ext}"\r\nContent-Type: {mime}\r\n\r\n'
        ).encode("utf-8")
    )
    parts.append(audio)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    data = _post(
        "/audio/transcriptions",
        b"".join(parts),
        f"multipart/form-data; boundary={boundary}",
    )
    return (data.get("text") or "").strip()


def translate(text, context):
    """Dịch một câu tiếng Anh sang tiếng Việt, có ngữ cảnh các câu trước."""
    system = (
        "You translate English movie/TV dialogue into natural, fluent Vietnamese. "
        "Translate only the final line. Output only the Vietnamese text, with no notes or quotes. "
        "Earlier lines are context for pronouns and tone."
    )
    user = ""
    if context:
        user += "Earlier lines (context only):\n" + "\n".join(context) + "\n\n"
    user += "Line to translate:\n" + text
    body = json.dumps(
        {
            "model": TRANSLATE_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    data = _post("/chat/completions", body, "application/json")
    return data["choices"][0]["message"]["content"].strip()


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/health":
            self._json(
                200,
                {"ok": True, "hasKey": bool(API_KEY), "stt": STT_MODEL, "translate": TRANSLATE_MODEL},
            )
        else:
            self._json(404, {"error": "không tìm thấy"})

    def do_POST(self):
        if self.path != "/api/subtitle":
            return self._json(404, {"error": "không tìm thấy"})
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._json(413, {"error": "đoạn âm thanh quá lớn"})
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            audio = base64.b64decode(payload["audio"])
            mime = (payload.get("mime") or "audio/webm").split(";")[0].strip()
            context = [str(x) for x in payload.get("context", [])][-4:]
            en = transcribe(audio, mime, " ".join(context)[-200:])
            if not en or HALLUCINATIONS.match(en):
                return self._json(200, {"en": "", "vi": ""})
            vi = translate(en, context)
            self._json(200, {"en": en, "vi": vi})
        except UpstreamError as e:
            self._json(502, {"error": str(e)})
        except Exception as e:  # dữ liệu gửi lên không hợp lệ
            self._json(400, {"error": f"yêu cầu không hợp lệ: {e}"})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    print(f"Mở http://localhost:{PORT}  (nhận dạng={STT_MODEL}, dịch={TRANSLATE_MODEL})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
