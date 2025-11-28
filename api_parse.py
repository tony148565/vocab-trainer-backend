# api_parse.py
from flask import Blueprint, request, jsonify
import re, json  #  補上 json
from cache import (
    refresh_caches,
    get_ecdict,
    get_user_words,
    load_json_file,
    SEEN_WORDS_FILE,   #  補上 SEEN_WORDS_FILE
    update_seen_words_internal
)


parse_bp = Blueprint("parse", __name__, url_prefix="/api")

@parse_bp.route("/parse", methods=["POST"])
def parse_article():
    refresh_caches()
    text = request.json.get("text", "")
    words = re.findall(r"[A-Za-z']+", text.lower())

    stopwords = {"the","a","an","is","are","was","were","to","of","in","on","for","and","with"}
    filtered = [w for w in words if w not in stopwords]
    unique_words = sorted(set(filtered))

    EC_CACHE = get_ecdict()
    USER_CACHE = get_user_words()

    #  更新 seen_words.json
    '''
    seen = load_json_file(SEEN_WORDS_FILE) or {}
    for w in unique_words:
        seen[w] = seen.get(w, 0) + 1
    '''
    update_seen_words_internal(unique_words)
    '''
    with open(SEEN_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)

    '''
    result = []
    for w in unique_words:
        zh = USER_CACHE.get(w) or EC_CACHE.get(w, "")
        result.append({"word": w, "zh": zh})

    return jsonify(result)
