"""Flask web app for the offline, rule-based Toki Pona <-> English translator."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from tokipona import detect_language, translate_to_english, translate_to_toki_pona

app = Flask(__name__)

MAX_INPUT_CHARS = 2000


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/translate")
def api_translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "")[:MAX_INPUT_CHARS]
    direction = data.get("direction") or "auto"

    if direction not in ("en-tp", "tp-en", "auto"):
        direction = "auto"

    if not text.strip():
        return jsonify(
            ok=True,
            direction_used=direction if direction != "auto" else "en-tp",
            readings=[],
            note=None,
        )

    if direction == "auto":
        direction = "tp-en" if detect_language(text) == "tp" else "en-tp"

    if direction == "tp-en":
        result = translate_to_english(text)
    else:
        result = translate_to_toki_pona(text)

    return jsonify(ok=True, direction_used=direction, readings=result.readings, note=result.note)


if __name__ == "__main__":
    app.run(debug=True)
