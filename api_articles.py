# api_articles.py
from flask import Blueprint, request, jsonify
import os, json, datetime, re

articles_bp = Blueprint("articles", __name__, url_prefix="/api/articles")

ARTICLES_DIR = os.path.join("data", "articles")
os.makedirs(ARTICLES_DIR, exist_ok=True)


# --------------------------------------------------------
# Internal Function（可給 API 與 n8n callback 使用）
# --------------------------------------------------------
def save_article_internal(title, text, source="manual"):
    """
    核心文章儲存邏輯：
    - 產生 safe title
    - 產生 timestamp
    - 儲存 JSON
    - 回傳 filename 與 metadata
    """

    title = (title or "").strip()
    text = (text or "").strip()
    source = (source or "manual").strip()

    if not text:
        raise ValueError("empty content")

    # 若沒有 title，自動從前幾個字產生
    if not title:
        words = re.findall(r"[A-Za-z']+", text)
        title = " ".join(words[:8]) if words else "untitled"
        title = title[:60]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # 檔名合法化
    safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", title)
    filename = f"{timestamp}_{safe_title}.json"
    full_path = os.path.join(ARTICLES_DIR, filename)

    payload = {
        "title": title,
        "text": text,
        "source": source,
        "created_at": timestamp
    }

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {
        "filename": filename,
        "path": full_path,
        "title": title,
        "created_at": timestamp,
        "source": source
    }


# --------------------------------------------------------
# 原本 API Route（改為呼叫 internal function）
# --------------------------------------------------------
@articles_bp.route("/save", methods=["POST"])
def save_article():
    data = request.json or {}
    try:
        result = save_article_internal(
            title=data.get("title"),
            text=data.get("text"),
            source=data.get("source", "manual")
        )
        return jsonify({"status": "saved", **result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------------
# 列出已儲存文章
# --------------------------------------------------------
@articles_bp.route("/list", methods=["GET"])
def list_articles():
    articles = []
    if not os.path.exists(ARTICLES_DIR):
        return jsonify([])

    for fname in sorted(os.listdir(ARTICLES_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(ARTICLES_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                item = json.load(f)
                articles.append({
                    "filename": fname,
                    "title": item.get("title", "untitled"),
                    "source": item.get("source", "manual"),
                    "created_at": item.get("created_at", "unknown"),
                    "length": len(item.get("text", "")),
                })
        except Exception:
            continue

    return jsonify(articles)


# --------------------------------------------------------
# 載入指定文章
# --------------------------------------------------------
@articles_bp.route("/load/<filename>", methods=["GET"])
def load_article(filename):
    safe_filename = re.sub(r"[^A-Za-z0-9_.-]+", "", filename)
    path = os.path.join(ARTICLES_DIR, safe_filename)

    if not os.path.exists(path):
        return jsonify({"error": "file not found"}), 404

    try:
        with open(path, "r", encoding="utf-8") as f:
            article = json.load(f)
        return jsonify(article)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
