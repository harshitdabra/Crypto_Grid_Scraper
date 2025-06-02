import os
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_prices():
    api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
    if not api_key:
        raise ValueError("CRYPTOCOMPARE_API_KEY environment variable not set")

    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,ETH,BNB,ADA,XRP,SOL,DOGE,DOT,TRX,APT,NEAR,HBAR&tsyms=USD&api_key={api_key}"

    session = requests.Session()
    retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(f" response: {data}")

        if data.get("Response") == "Error":
            raise ValueError(f"error: {data.get('Message')}")

        prices = data.get('RAW', {})
        if not prices:
            raise ValueError("No price data returned")

        name_mapping = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'Binance Coin',
            'ADA': 'Cardano',
            'XRP': 'Ripple',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'DOT': 'Polkadot'
            'TRX': 'Tron',
            'APT': 'Aptos',
            'NEAR': 'NEAR Protocol',
            'HBAR': 'Hedera'
        }

        formatted_data = []
        for coin, values in prices.items():
            usd_price = values.get('USD', {}).get('PRICE')
            if usd_price is not None:  
                formatted_data.append({
                    'coin': name_mapping.get(coin, coin),
                    'price_usd': usd_price
                })

        if not formatted_data:
            raise ValueError("No valid price data extracted")

        df = pd.DataFrame(formatted_data)
        df['price_usd'] = pd.to_numeric(df['price_usd'], errors='coerce')
        df['price_usd'] = df['price_usd'].round(2)  
        df = df.dropna(subset=['price_usd'])
        df = df.sort_values(by='price_usd', ascending=False).reset_index(drop=True)

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch prices from CryptoCompare: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch prices: {str(e)}")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing CryptoCompare response: {str(e)}", exc_info=True)
        raise Exception(f"Error parsing price data: {str(e)}")
