from flask import Blueprint, request, jsonify
import json
import random

from cache import (
    load_json_file,
    update_seen_words_internal,
    WORDS_FILE,
    SEEN_WORDS_FILE,
    refresh_caches,
)

words_bp = Blueprint("words", __name__, url_prefix="/api")


# ============================================================
# 工具函式（統一寫回）
# ============================================================
def write_words_file(words: list):
    """以統一方式寫回 word list，避免舊 save_json_file 造成錯誤。"""
    with open(WORDS_FILE, "w", encoding="utf-8") as fp:
        json.dump(words, fp, ensure_ascii=False, indent=2)
    refresh_caches()


# ============================================================
# CRUD — 單字查詢 / 新增 / 更新 / 刪除
# ============================================================
@words_bp.route("/words", methods=["GET"])
def get_words():
    refresh_caches()
    return jsonify(load_json_file(WORDS_FILE))


@words_bp.route("/words", methods=["POST"])
def add_or_update_word():
    """統一後端單字存取行為：
    1. 更新 seen_words.json
    2. 寫入 words.json
    """
    payload = request.json or {}
    word = (payload.get("word") or "").strip().lower()
    definition = (payload.get("definition") or "").strip()
    added_by = payload.get("added_by", "manual")

    if not word:
        return jsonify({"error": "missing word"}), 400

    # Step 1 — 更新 seen_words.json
    update_seen_words_internal({word: definition})

    # Step 2 — 更新 words.json
    words = load_json_file(WORDS_FILE)
    existing = next((w for w in words if w["word"] == word), None)

    if existing:
        if definition:
            existing["definition"] = definition
        existing["count"] = existing.get("count", 0) + 1
        status = "updated"
        count = existing["count"]
    else:
        words.append({
            "word": word,
            "definition": definition,
            "reviewed": 0,
            "count": 1,
            "added_by": added_by,
        })
        status = "created"
        count = 1

    write_words_file(words)
    return jsonify({"status": status, "count": count})


@words_bp.route("/words/<word>", methods=["DELETE"])
def delete_word(word):
    words = [w for w in load_json_file(WORDS_FILE) if w["word"] != word]
    write_words_file(words)
    return jsonify({"status": "deleted"})


# ============================================================
# Review — 記憶評分（保持原功能）
# ============================================================
@words_bp.route("/review/<word>", methods=["POST"])
def review_word(word):
    remembered = request.json.get("remembered", False)
    words = load_json_file(WORDS_FILE)

    for w in words:
        if w["word"] == word:
            w["reviewed"] = w.get("reviewed", 0) + (1 if remembered else 0)
            write_words_file(words)
            return jsonify({"word": word, "reviewed": w["reviewed"]})

    return jsonify({"error": "word not found"}), 404


# ============================================================
# 隨機字（維持原本功能）
# ============================================================
@words_bp.route("/random", methods=["GET"])
def random_word():
    words = load_json_file(WORDS_FILE)
    if not words:
        return jsonify({"error": "no words"})
    return jsonify(random.choice(words))


# ============================================================
# 統計資訊
# ============================================================
@words_bp.route("/words/stats", methods=["GET"])
def words_stats():
    words = load_json_file(WORDS_FILE)
    seen = load_json_file(SEEN_WORDS_FILE)

    total_words = len(words)
    total_seen = len(seen)
    avg_count = sum(w.get("count", 0) for w in words) / total_words if total_words else 0

    return jsonify({
        "total_words": total_words,
        "total_seen": total_seen,
        "avg_count": round(avg_count, 2)
    })


# ============================================================
# 批次匯入（可兼容 zh / definition）
# ============================================================
@words_bp.route("/words/batch", methods=["POST"])
def add_words_batch():
    items = request.json or []
    words = load_json_file(WORDS_FILE)
    seen = load_json_file(SEEN_WORDS_FILE)

    existing = {w["word"]: w for w in words}

    added = updated = skipped = 0

    for item in items:
        word = (item.get("word") or "").strip().lower()
        if not word:
            skipped += 1
            continue

        # 自動兼容 zh / definition
        definition = (item.get("definition") or item.get("zh") or "").strip()
        added_by = item.get("added_by", "batch")
        count = seen.get(word, 1)

        if word in existing:
            existing[word]["count"] = existing[word].get("count", 0) + count
            if definition:
                existing[word]["definition"] = definition
            updated += 1
        else:
            existing[word] = {
                "word": word,
                "definition": definition,
                "reviewed": 0,
                "count": count,
                "added_by": added_by
            }
            added += 1

    # 寫回
    write_words_file(list(existing.values()))

    return jsonify({"status": "ok", "added": added, "updated": updated, "skipped": skipped})
