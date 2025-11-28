from flask import Flask
from flask_cors import CORS
from api_words import words_bp
from api_parse import parse_bp
from cache import refresh_caches
from api_import_export import api_import_export_bp
from api_articles import articles_bp
from api_trigger_n8n import trigger_bp


app = Flask(__name__)
CORS(app)

# 載入各模組
app.register_blueprint(words_bp)
app.register_blueprint(parse_bp)
app.register_blueprint(api_import_export_bp)
app.register_blueprint(articles_bp)
app.register_blueprint(trigger_bp)

if __name__ == "__main__":
    refresh_caches()  # 啟動時預先快取
    app.run(host="0.0.0.0", port=5000, debug=True)
