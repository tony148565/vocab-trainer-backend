from flask import Blueprint, jsonify, request, send_file
import json, csv, io, os
from cache import WORDS_FILE, refresh_caches

api_import_export_bp = Blueprint("import_export", __name__, url_prefix="/api")

# --------------------------------------------------------
# 匯出字彙庫
# --------------------------------------------------------
@api_import_export_bp.route("/export", methods=["GET"])
def export_words():
    fmt = request.args.get("format", "json")

    if not os.path.exists(WORDS_FILE):
        return jsonify({"error": "no data"}), 404

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        words = json.load(f)

    if not words:
        return jsonify({"error": "empty"}), 404

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=words[0].keys())
        writer.writeheader()
        writer.writerows(words)
        mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        mem.seek(0)
        return send_file(
            mem,
            as_attachment=True,
            download_name="words.csv",
            mimetype="text/csv",
        )

    return jsonify(words)


# --------------------------------------------------------
# 匯入字彙庫（加強防呆 + 正確 HTTP 狀態碼）
# --------------------------------------------------------
@api_import_export_bp.route("/import", methods=["POST"])
def import_words():
    """
    支援：
      - JSON (application/json)
      - CSV (multipart/form-data)
    驗證：
      - 必須包含 "word" 欄位
      - 若全錯或無資料 → 回傳 422
    """
    try:
        if os.path.exists(WORDS_FILE):
            with open(WORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
    except Exception as e:
        return jsonify({"error": f"failed to read local words.json: {str(e)}"}), 500

    existing = {w["word"]: w for w in data}
    new_entries, updated, skipped = 0, 0, 0
    incoming = []

    # === 檔案解析階段 ===
    try:
        data = request.content_type
        print(data)
        if request.content_type and "application/json" in request.content_type:
            incoming = request.json
            print(incoming)
            if not isinstance(incoming, list):
                return jsonify({"error": "JSON 必須是 list 格式"}), 400
        elif "file" in request.files:
            file = request.files["file"]
            incoming = list(csv.DictReader(io.StringIO(file.read().decode("utf-8"))))
        else:
            return jsonify({"error": "不支援的內容格式"}), 400
    except Exception as e:
        return jsonify({"error": f"解析失敗: {str(e)}"}), 400

    if not incoming:
        return jsonify({"error": "匯入檔案為空"}), 422

    # === 結構驗證 ===
    required_field = "word"
    valid_fields = {"word", "definition", "reviewed", "count"}
    valid_items = []

    for idx, item in enumerate(incoming, 1):
        if not isinstance(item, dict):
            skipped += 1
            continue

        word = str(item.get(required_field, "")).strip()
        if not word:
            skipped += 1
            continue

        filtered = {k: item[k] for k in item if k in valid_fields}
        valid_items.append(filtered)

    if len(valid_items) == 0:
        return jsonify({"error": "未找到任何有效字彙", "skipped": skipped}), 422

    # === 寫入階段 ===
    try:
        for item in valid_items:
            word = item["word"]
            if word in existing:
                existing[word].update(item)
                updated += 1
            else:
                existing[word] = item
                new_entries += 1

        with open(WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(existing.values()), f, indent=2, ensure_ascii=False)

        refresh_caches()

        return jsonify({
            "status": "ok",
            "added": new_entries,
            "updated": updated,
            "skipped": skipped
        }), 200

    except Exception as e:
        return jsonify({"error": f"寫入失敗: {str(e)}"}), 500
