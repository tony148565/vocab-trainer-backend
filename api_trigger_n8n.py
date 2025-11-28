from flask import Blueprint, Flask, request, jsonify
import requests
from api_articles import save_article_internal
from cache import update_seen_words_internal, get_setting_file
import uuid


app = Flask(__name__)

#webhook_url = ""


N8N_WEBHOOK_URL = get_setting_file()

trigger_bp = Blueprint("n8n_trigger", __name__, url_prefix="/api")

job_results = {}

# flask -> n8n
@trigger_bp.route("/trigger", methods=["POST"])
def trigger_n8n_workflow():
    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id}
    try:
        r = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        return jsonify({"status": "ok", "job_id": job_id})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)})

# n8n -> flask
@trigger_bp.route("/n8n_callback", methods=["POST"])
def n8n_callback():
    data = request.json
    
    
    job_id = data["job_id"]

    # 儲存文章
    article = {
        "title": data["title"],
        "text": data["content"],
        "source": "n8n",
    }
    saved = save_article_internal(
        title=article["title"],
        text=article["text"],
        source=article["source"]
    )

    # 更新 seen_words
    words = data["words"]
    update_seen_words_internal(words)
    
    normalized = []
    for item in words:
        k = list(item.keys())[0]
        v = item[k]
        normalized.append({
            "word": k,
            "zh": v
        })
    
    # 回存 job 結果
    job_results[job_id] = {
        "status": "done",
        "article": article,
        "words": normalized
    }
    
    print(normalized)
    return {"status": "ok"}

# fn -> flask
@trigger_bp.route("/job/<job_id>")
def get_job(job_id):
    return job_results.get(job_id, {"status": "pending"})
