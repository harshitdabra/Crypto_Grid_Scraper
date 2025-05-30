import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_prices():
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'bitcoin,ethereum,binancecoin,cardano,ripple,solana,dogecoin,polkadot,shiba-inu,tron,aptos,near-protocol,hbar',
        'vs_currencies': 'usd'
    }

    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()  
        data = response.json()
        logger.info(f"CoinGecko API response: {data}")  

        if not isinstance(data, dict) or 'error' in data:
            raise ValueError(f"Unexpected API response: {data}")

        if not data:
            raise ValueError("No price data returned from CoinGecko")

        df = pd.DataFrame(data).T
        df.reset_index(inplace=True)
        df.columns = ['coin', 'price_usd']

        name_mapping = {
            'bitcoin': 'Bitcoin',
            'ethereum': 'Ethereum',
            'binancecoin': 'Binance Coin',
            'cardano': 'Cardano',
            'ripple': 'Ripple',
            'solana': 'Solana',
            'dogecoin': 'Dogecoin',
            'polkadot': 'Polkadot',
            'shiba-inu': 'Shiba Inu',
            'tron': 'Tron',
            'aptos': 'Aptos',
            'near-protocol': 'NEAR Protocol',
            'hbar': 'Hedera'
        }

        df['coin'] = df['coin'].map(name_mapping)
        df = df.dropna(subset=['coin'])

        df['price_usd'] = pd.to_numeric(df['price_usd'], errors='coerce')
        df = df.dropna(subset=['price_usd'])

        df = df.sort_values(by='price_usd', ascending=False).reset_index(drop=True)

        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch prices from CoinGecko: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch prices: {str(e)}")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing CoinGecko response: {str(e)}", exc_info=True)
        raise Exception(f"Error parsing price data: {str(e)}")
