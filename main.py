from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Lazy import script modules to handle startup errors
def safe_import_scripts():
    try:
        from scripts.fetch_prices import fetch_prices
        from scripts.fetch_news import fetch_news
        from scripts.fetch_sentiment import fetch_sentiment
        from scripts.fetch_general_info import fetch_general_info
        return fetch_prices, fetch_news, fetch_sentiment, fetch_general_info
    except Exception as e:
        print(f"Warning: Script import error: {e}")
        return None, None, None, None

# Try to import, but don't fail if they're not available
fetch_prices, fetch_news, fetch_sentiment, fetch_general_info = safe_import_scripts()

app = Flask(__name__, static_folder='public')
CORS(app)

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "fetch_prices_available": fetch_prices is not None,
        "fetch_news_available": fetch_news is not None,
        "fetch_sentiment_available": fetch_sentiment is not None,
        "fetch_general_info_available": fetch_general_info is not None
    })

def calculate_sentiment_score(data):
    try:
        if not data or "Data" not in data or not isinstance(data["Data"], list) or not data["Data"]:
            raise ValueError("Empty or malformed sentiment data")
        
        latest = data["Data"][-1]
        reddit = latest.get("Reddit", {})
        twitter = latest.get("Twitter", {})
        code_repo = latest.get("CodeRepository", {})
        
        code_repo_list = code_repo.get("List", [])
        total_stars = sum(repo.get("stars", 0) for repo in code_repo_list)
        total_forks = sum(repo.get("forks", 0) for repo in code_repo_list)

        score = (
            2 * reddit.get("comments_per_day", 0) +
            1.5 * reddit.get("posts_per_day", 0) +
            1.2 * reddit.get("active_users", 0) +
            0.5 * twitter.get("followers", 0) / 1_000_000 +
            0.3 * total_stars / 10_000 +
            0.2 * total_forks / 5_000
        )
        return round(score, 2)
    except Exception as e:
        return None

def interpret_sentiment_score(score, symbol):
    if score is None:
        return f"{symbol}: No data to calculate buzz score."
    if score <= 500:
        return f"{symbol}: Low buzz (Score: {score}). Low online activity."
    elif score <= 3000:
        return f"{symbol}: Medium buzz (Score: {score}). Moderate interest."
    else:
        return f"{symbol}: High buzz (Score: {score}). Strong attention and dev activity."

def format_market_cap(market_cap):
    if market_cap >= 1_000_000_000:
        return f"{market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.2f}M"
    else:
        return f"{market_cap:.2f}"

@app.route('/api/general_info', methods=['GET'])
def get_general_info():
    if not fetch_general_info:
        return jsonify({"error": "fetch_general_info not available"}), 503
    try:
        general_df = fetch_general_info()
        general_df['market_cap_usd'] = general_df['market_cap_usd'].apply(format_market_cap)
        return jsonify(general_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/prices', methods=['GET'])
def get_prices():
    if not fetch_prices:
        return jsonify({"error": "fetch_prices not available"}), 503
    try:
        prices_df = fetch_prices()
        return jsonify(prices_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    if not fetch_news:
        return jsonify({"error": "fetch_news not available"}), 503
    try:
        news_df = fetch_news()
        return jsonify(news_df.to_dict(orient='records'))  
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment', methods=['GET'])
def get_sentiment():
    if not fetch_sentiment:
        return jsonify({"error": "fetch_sentiment not available"}), 503
    try:
        cryptocompare_api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
        coins = [
            {"symbol": "BTC", "id": 1182},
            {"symbol": "ETH", "id": 7605},
            {"symbol": "BNB", "id": 204788},
            {"symbol": "SOL", "id": 934443},
            {"symbol": "XRP", "id": 5031},
            {"symbol": "DOGE", "id": 4432},
            {"symbol": "ADA", "id": 321992},
            {"symbol": "AVAX", "id": 935805},
        ]
        
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        sentiment_data = []
        for coin in coins:
            try:
                data = fetch_sentiment(
                    symbol=coin["symbol"],
                    coin_id=coin["id"],
                    api_key=cryptocompare_api_key,
                    session=session
                )
                score = calculate_sentiment_score(data) if data else None
                interpretation = interpret_sentiment_score(score, coin["symbol"])
                sentiment_data.append({
                    "symbol": coin["symbol"],
                    "score": score,
                    "interpretation": interpretation
                })
            except Exception as e:
                sentiment_data.append({
                    "symbol": coin["symbol"],
                    "score": None,
                    "interpretation": f"{coin['symbol']}: Failed to fetch sentiment data: {str(e)}"
                })
        return jsonify(sentiment_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from pathlib import Path
import sys

# Determine the public folder location
# Try multiple possible locations in order of preference
posible_public_paths = [
    Path(__file__).parent / 'public',           # Local: ./public
    Path(__file__).parent.parent / 'api' / 'public',  # Vercel: ../api/public (when main.py in root)
    Path(__file__).parent / 'api' / 'public',   # Alternative
    Path.cwd() / 'public',                      # Current working directory
    Path.cwd() / 'api' / 'public',              # Vercel cwd might be root or api
]

PUBLIC_DIR = None
for path in posible_public_paths:
    if path.exists():
        PUBLIC_DIR = path
        break

if PUBLIC_DIR is None:
    # Fallback to first option even if it doesn't exist
    PUBLIC_DIR = posible_public_paths[0]

print(f"Flask __file__: {__file__}")
print(f"Flask __file__ parent: {Path(__file__).parent}")
print(f"sys.argv[0]: {sys.argv[0] if sys.argv else 'N/A'}")
print(f"Working directory: {Path.cwd()}")
print(f"PUBLIC_DIR: {PUBLIC_DIR}")
print(f"PUBLIC_DIR exists: {PUBLIC_DIR.exists()}")
if PUBLIC_DIR.exists():
    files_in_public = sorted([f.name for f in PUBLIC_DIR.glob('*')])
    print(f"Files in PUBLIC_DIR: {files_in_public}")

@app.route('/styles.css')
def serve_css():
    css_path = PUBLIC_DIR / 'styles.css'
    try:
        if css_path.exists():
            return css_path.read_text(), 200, {'Content-Type': 'text/css'}
        print(f"CSS not found at {css_path}")
        return '', 404
    except Exception as e:
        print(f"Error serving CSS from {css_path}: {e}")
        return '', 404

@app.route('/scripts.js')
def serve_js():
    js_path = PUBLIC_DIR / 'scripts.js'
    try:
        if js_path.exists():
            return js_path.read_text(), 200, {'Content-Type': 'application/javascript'}
        print(f"JS not found at {js_path}")
        return '', 404
    except Exception as e:
        print(f"Error serving JS from {js_path}: {e}")
        return '', 404

@app.route('/')
def index():
    html_path = PUBLIC_DIR / 'index.html'
    try:
        if html_path.exists():
            return html_path.read_text(), 200, {'Content-Type': 'text/html'}
        print(f"HTML not found at {html_path}")
        return 'App loaded but index.html not found', 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        print(f"Error serving index from {html_path}: {e}")
        return f'Error: {e}', 500

@app.route('/favicon.ico')
def favicon():
    favicon_path = PUBLIC_DIR / 'favicon.png'
    try:
        if favicon_path.exists():
            return favicon_path.read_bytes(), 200, {'Content-Type': 'image/png'}
        print(f"Favicon not found at {favicon_path}, using default")
        # Return a 1x1 transparent PNG if favicon is not found
        png_data = bytes.fromhex('89504e470d0a1a0a0000000d494844520000000100000001080202000090773db30000000c49444154789c6364f8cf00050001010502002c19cc700000000049454e44ae426082')
        return png_data, 200, {'Content-Type': 'image/png'}
    except Exception as e:
        print(f"Error serving favicon from {favicon_path}: {e}")
        return '', 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

