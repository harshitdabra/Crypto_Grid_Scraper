import requests
import pandas as pd
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY")

nltk.download('vader_lexicon', quiet=True)
sid = SentimentIntensityAnalyzer()

def fetch_news():
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
            sentiment = sid.polarity_scores(body) if body else {"compound": 0.0}

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