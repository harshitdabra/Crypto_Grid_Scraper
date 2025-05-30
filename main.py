from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
from scripts.fetch_prices import fetch_prices
from scripts.fetch_news import fetch_news
from scripts.fetch_sentiment import fetch_sentiment
from scripts.fetch_general_info import fetch_general_info
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)
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
    try:
        general_df = fetch_general_info()
        general_df['market_cap_usd'] = general_df['market_cap_usd'].apply(format_market_cap)
        return jsonify(general_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/prices', methods=['GET'])
def get_prices():
    try:
        prices_df = fetch_prices()
        return jsonify(prices_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        news_df = fetch_news()
        return jsonify(news_df.to_dict(orient='records'))  
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment', methods=['GET'])
def get_sentiment():
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

@app.route('/styles.css')
def serve_css():
    return send_from_directory('static', 'styles.css')

@app.route('/scripts.js')
def serve_js():
    return send_from_directory('static', 'scripts.js')

@app.route('/')
def index():
    return app.send_static_file('index.html')

