# cache.py
import os, json

WORDS_FILE = "words.json"
ECDICT_FILE = "ecdict.json"
SEEN_WORDS_FILE = "seen_words.json"
SETTING_FILE = "setting.json"

_SEEN_CACHE = {}
_SEEN_MTIME = 0
_EC_CACHE = {}
_USER_CACHE = {}
_EC_MTIME = 0
_USER_MTIME = 0

def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def refresh_caches():
    """重新載入 ecdict.json / words.json / seen_words.json"""
    global _EC_CACHE, _USER_CACHE, _SEEN_CACHE, _EC_MTIME, _USER_MTIME, _SEEN_MTIME

    # ECDICT
    if os.path.exists(ECDICT_FILE):
        mtime = os.path.getmtime(ECDICT_FILE)
        if mtime != _EC_MTIME:
            _EC_CACHE = load_json_file(ECDICT_FILE)
            _EC_MTIME = mtime
            print(f"[Cache] Reloaded {ECDICT_FILE} ({len(_EC_CACHE):,})")

    # WORDS（轉為 word -> definition 的查詢表）
    if os.path.exists(WORDS_FILE):
        mtime = os.path.getmtime(WORDS_FILE)
        if mtime != _USER_MTIME:
            raw = load_json_file(WORDS_FILE)
            _USER_CACHE = {item["word"].lower(): item.get("definition", "") for item in raw}
            _USER_MTIME = mtime
            print(f"[Cache] Reloaded {WORDS_FILE} ({len(_USER_CACHE):,})")

    # SEEN
    if os.path.exists(SEEN_WORDS_FILE):
        mtime = os.path.getmtime(SEEN_WORDS_FILE)
        if mtime != _SEEN_MTIME:
            _SEEN_CACHE = load_json_file(SEEN_WORDS_FILE)
            _SEEN_MTIME = mtime
            print(f"[Cache] Reloaded {SEEN_WORDS_FILE} ({len(_SEEN_CACHE):,})")
    
    

def get_ecdict():
    return _EC_CACHE

def get_user_words():
    return _USER_CACHE

def get_seen_words():
    return _SEEN_CACHE

def update_seen_words_internal(word_list):
    """
    統一更新 seen_words.json 的邏輯。
    word_list 接受兩種格式：
      1. ["impact", "company", ...]
      2. [{"word": "impact"}, {"word": "company"}, ...]

    此函式會：
      - 自動過濾空字
      - 小寫化
      - 將出現次數 +1
      - 寫回 seen_words.json
    """
    if not word_list:
        return

    seen = load_json_file(SEEN_WORDS_FILE) or {}

    for w in word_list:
        if isinstance(w, str):
            word = w.strip().lower()
        elif isinstance(w, dict):
            word = w.get("word", "").strip().lower()
        else:
            continue

        if not word:
            continue

        seen[word] = seen.get(word, 0) + 1

    with open(SEEN_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2, ensure_ascii=False)

def get_setting_file():
    try:
        with open(SETTING_FILE, "r", encoding="utf-8") as f:
            datas = json.load(f)
        webhook_url = datas["N8N_WEBHOOK_URL"]
        #print(webhook_url)
    except Exception:
        print("setting.json not found")
    
    return webhook_url