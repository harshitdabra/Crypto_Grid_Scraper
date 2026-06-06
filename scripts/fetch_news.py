import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

# Lazy load NLTK resources to avoid import errors on serverless
_sentiment_analyzer = None
_nltk_initialized = False

def _init_nltk():
    global _sentiment_analyzer, _nltk_initialized
    if not _nltk_initialized:
        try:
            import nltk
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            nltk.download('vader_lexicon', quiet=True)
            _sentiment_analyzer = SentimentIntensityAnalyzer()
            _nltk_initialized = True
        except Exception as e:
            print(f"Warning: NLTK initialization failed: {e}")
            _nltk_initialized = True  # Mark as initialized to avoid retrying
    return _sentiment_analyzer

def fetch_news():
    sid = _init_nltk()
    url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=BTC,ETH&api_key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("Type") != 100 or "Data" not in data:
            raise ValueError("Unexpected API response format")

        news_data = []
        articles = data.get("Data", [])[:10]  

        for article in articles:
            published_time = datetime.utcfromtimestamp(article.get("published_on", 0)).strftime("%Y-%m-%dT%H:%M:%SZ")
            body = article.get("body", "")
            sentiment = sid.polarity_scores(body) if body and sid else {"compound": 0.0}

            news_data.append({
                "title": article.get("title", "N/A"),
                "source": article.get("source_info", {}).get("name", article.get("source", "N/A")),
                "link": article.get("url", "N/A"),
                "time_utc": published_time,
            })

        df = pd.DataFrame(news_data)
        return df
    except Exception as e:
        print(f"Error fetching news: {e}")
        raise